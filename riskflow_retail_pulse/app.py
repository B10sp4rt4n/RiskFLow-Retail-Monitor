"""
app.py – Punto de entrada de RiskFlow Retail Pulse.

Ejecutar con:
    streamlit run app.py

Flujo principal:
  1. Cargar configuración de dispositivos (devices.yaml).
  2. Inicializar la base de datos SQLite.
  3. En cada ciclo de refresco:
     a. Simular estados de todos los endpoints.
     b. Comparar con estado previo (state_engine).
     c. Generar eventos si hubo cambios (event_engine).
     d. Persistir estados y eventos (local_store).
     e. Renderizar dashboard (dashboard.py).
"""

import sys
import time
from pathlib import Path

import streamlit as st
import yaml

# Permite importar módulos del proyecto sin instalar como paquete
sys.path.insert(0, str(Path(__file__).parent))

from core.event_engine import build_event
from core.models import Device
from core.simulator import simulate_all
from core.sla_engine import (
    availability_by_branch,
    availability_by_device_type,
    build_site_availability,
)
from core.state_engine import is_state_change, resolve_state
from storage.local_store import (
    init_db,
    insert_event,
    load_current_states,
    load_events,
    load_events_as_objects,
    upsert_status,
)
from ui.dashboard import (
    render_event_log,
    render_kpis,
    render_legend,
    render_site_cards,
    render_sla,
    render_status_table,
    setup_page,
)


# ---------------------------------------------------------------------------
# Helpers de carga de configuración
# ---------------------------------------------------------------------------

def _load_devices(yaml_path: Path) -> list[Device]:
    """Lee devices.yaml y devuelve una lista de objetos Device."""
    with open(yaml_path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    devices: list[Device] = []
    for branch in config.get("branches", []):
        for ep in branch.get("endpoints", []):
            devices.append(Device(
                id=ep["id"],
                name=ep["name"],
                branch_id=branch["id"],
                branch_name=branch["name"],
                device_type=ep["device_type"],
                ip=ep["ip"],
                port=int(ep["port"]),
                criticality=ep.get("criticality", "medium"),
                validation_method=ep.get("validation_method", "ping"),
            ))
    return devices


# ---------------------------------------------------------------------------
# Ciclo principal de monitoreo (simulado)
# ---------------------------------------------------------------------------

def run_monitoring_cycle(devices: list[Device]) -> None:
    """
    Ejecuta un ciclo completo de simulación/monitoreo:
      - Simula estados.
      - Detecta cambios.
      - Genera y persiste eventos.
      - Guarda estado actual.
    """
    previous_states = load_current_states()
    new_statuses = simulate_all(devices)

    device_map = {d.id: d for d in devices}

    for status in new_statuses:
        prev = previous_states.get(status.device_id)
        resolved = resolve_state(prev, status.state)
        status.state = resolved

        if is_state_change(prev, resolved):
            device = device_map[status.device_id]
            event = build_event(
                device=device,
                previous_state=prev,
                new_state=resolved,
                detail=status.detail,
            )
            insert_event(event)

        upsert_status(status)


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def main() -> None:
    setup_page()

    config_path = Path(__file__).parent / "config" / "devices.yaml"
    init_db()
    devices = _load_devices(config_path)

    # ── Barra lateral ──────────────────────────────────────────────────────
    st.sidebar.title("⚙️ RiskFlow Retail Pulse")
    st.sidebar.markdown("---")

    auto_refresh = st.sidebar.checkbox("🔄 Auto-refresco", value=False)
    refresh_interval = st.sidebar.slider(
        "Intervalo (segundos)", min_value=5, max_value=60, value=15, step=5
    )
    run_now = st.sidebar.button("▶️ Ejecutar ciclo ahora")

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"**Dispositivos configurados:** {len(devices)}"
    )
    branches = {d.branch_id: d.branch_name for d in devices}
    for bid, bname in branches.items():
        count = sum(1 for d in devices if d.branch_id == bid)
        st.sidebar.markdown(f"- {bname}: {count} endpoints")

    # ── Ejecutar ciclo si corresponde ─────────────────────────────────────
    if run_now or auto_refresh:
        run_monitoring_cycle(devices)
        if auto_refresh:
            time.sleep(refresh_interval)
            st.rerun()

    # ── Cargar datos actuales ─────────────────────────────────────────────
    current_states = load_current_states()
    raw_events = load_events(limit=300)
    events_objs = load_events_as_objects(limit=2000)

    # ── Encabezado ────────────────────────────────────────────────────────
    st.title("📡 RiskFlow Retail Pulse")
    st.caption("Monitor de vida operativa de POS, impresoras y periféricos en ambiente distribuido")

    if not current_states:
        st.warning("⚠️ No hay datos aún. Pulsa **▶️ Ejecutar ciclo ahora** en la barra lateral.")
        render_legend()
        return

    # ── KPIs ──────────────────────────────────────────────────────────────
    render_kpis(current_states)
    st.markdown("---")

    # ── Tarjetas por sucursal ─────────────────────────────────────────────
    site_summaries = []
    for bid, bname in branches.items():
        site_states = {
            did: state
            for did, state in current_states.items()
            if did.startswith(bid)
        }
        if site_states:
            site_summaries.append(build_site_availability(bid, bname, site_states))

    render_site_cards(site_summaries)
    st.markdown("---")

    # ── Tabla de endpoints ────────────────────────────────────────────────
    render_status_table(devices, current_states)
    st.markdown("---")

    # ── SLA ───────────────────────────────────────────────────────────────
    if events_objs:
        avail_branch = availability_by_branch(events_objs)
        avail_type = availability_by_device_type(events_objs)
        render_sla(avail_branch, avail_type)
        st.markdown("---")

    # ── Bitácora ──────────────────────────────────────────────────────────
    render_event_log(raw_events)
    st.markdown("---")

    # ── Leyenda ───────────────────────────────────────────────────────────
    render_legend()


if __name__ == "__main__":
    main()
