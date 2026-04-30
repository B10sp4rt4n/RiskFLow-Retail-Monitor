"""
dashboard.py – Construcción de la UI principal en Streamlit.

Orquesta la visualización de:
  1. Métricas de resumen (KPIs globales).
  2. Estado actual por sucursal.
  3. Tabla detallada de endpoints.
  4. Bitácora de eventos recientes.
  5. Disponibilidad SLA (por sucursal, por tipo de dispositivo).
  6. Botón de exportación CSV.
"""

import streamlit as st
from typing import Dict, List

from core.models import Device, SiteAvailability, State
from exports.csv_exporter import events_to_csv_bytes
from ui.tables import (
    build_event_table,
    build_sla_table,
    build_status_table,
    STATE_COLORS,
    STATE_LABELS,
)


# ---------------------------------------------------------------------------
# Configuración de página (llamar una sola vez desde app.py)
# ---------------------------------------------------------------------------

def setup_page() -> None:
    st.set_page_config(
        page_title="RiskFlow Retail Pulse",
        page_icon="📡",
        layout="wide",
    )


# ---------------------------------------------------------------------------
# KPIs globales
# ---------------------------------------------------------------------------

def render_kpis(current_states: Dict[str, str]) -> None:
    """Muestra métricas globales en la parte superior."""
    total = len(current_states)
    alive = sum(1 for s in current_states.values() if s == State.ALIVE)
    degraded = sum(1 for s in current_states.values() if s == State.DEGRADED)
    down = sum(1 for s in current_states.values() if s == State.DOWN)
    avail_pct = round((alive + degraded) / total * 100, 1) if total else 0.0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Endpoints", total)
    col2.metric("🟢 Vivos", alive)
    col3.metric("🟡 Degradados", degraded)
    col4.metric("🔴 Caídos", down)
    col5.metric("📊 Disponibilidad Global", f"{avail_pct}%")


# ---------------------------------------------------------------------------
# Resumen por sucursal (tarjetas)
# ---------------------------------------------------------------------------

def render_site_cards(site_summaries: List[SiteAvailability]) -> None:
    """Muestra una tarjeta de resumen para cada sucursal."""
    st.subheader("📍 Resumen por Sucursal")

    cols = st.columns(len(site_summaries)) if site_summaries else []

    for idx, site in enumerate(site_summaries):
        with cols[idx]:
            color = (
                "#28a745" if site.availability_pct >= 90 else
                "#ffc107" if site.availability_pct >= 70 else
                "#dc3545"
            )
            st.markdown(
                f"""
                <div style='border:1px solid {color}; border-radius:8px;
                            padding:12px; text-align:center;'>
                  <b style='font-size:16px'>{site.branch_name}</b><br>
                  <span style='font-size:28px; color:{color}'>
                    {site.availability_pct:.1f}%
                  </span><br>
                  <small>
                    🟢 {site.alive_count} &nbsp;
                    🟡 {site.degraded_count} &nbsp;
                    🔴 {site.down_count} &nbsp;
                    ⚫ {site.unknown_count}
                  </small>
                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------------------------
# Tabla detallada de endpoints
# ---------------------------------------------------------------------------

def render_status_table(devices: List[Device], current_states: Dict[str, str]) -> None:
    """Muestra la tabla completa de estado de todos los endpoints."""
    st.subheader("🖥️ Estado Detallado de Endpoints")

    df = build_status_table(devices, current_states)

    # Filtros rápidos
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        branch_filter = st.multiselect(
            "Filtrar por Sucursal",
            options=sorted(df["Sucursal"].unique()),
            default=[],
        )
    with col_f2:
        type_filter = st.multiselect(
            "Filtrar por Tipo",
            options=sorted(df["Tipo"].unique()),
            default=[],
        )
    with col_f3:
        state_options = sorted(df["Estado"].unique())
        state_filter = st.multiselect(
            "Filtrar por Estado",
            options=state_options,
            default=[],
        )

    filtered_df = df.copy()
    if branch_filter:
        filtered_df = filtered_df[filtered_df["Sucursal"].isin(branch_filter)]
    if type_filter:
        filtered_df = filtered_df[filtered_df["Tipo"].isin(type_filter)]
    if state_filter:
        filtered_df = filtered_df[filtered_df["Estado"].isin(state_filter)]

    # Ocultar columna auxiliar antes de mostrar
    display_df = filtered_df.drop(columns=["_state_raw"], errors="ignore")
    st.dataframe(display_df, use_container_width=True, height=300)


# ---------------------------------------------------------------------------
# Bitácora de eventos
# ---------------------------------------------------------------------------

def render_event_log(raw_events: List[dict]) -> None:
    """Muestra la bitácora de eventos recientes."""
    st.subheader("📋 Bitácora de Eventos")

    if not raw_events:
        st.info("No hay eventos registrados aún.")
        return

    event_df = build_event_table(raw_events)
    st.dataframe(event_df, use_container_width=True, height=280)

    # Botón de exportación
    csv_bytes = events_to_csv_bytes(raw_events)
    st.download_button(
        label="⬇️ Exportar Bitácora (CSV)",
        data=csv_bytes,
        file_name="bitacora_eventos.csv",
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# Disponibilidad SLA
# ---------------------------------------------------------------------------

def render_sla(
    avail_by_branch: Dict[str, float],
    avail_by_type: Dict[str, float],
) -> None:
    """Muestra tablas y gráficas de disponibilidad SLA."""
    st.subheader("📈 Disponibilidad (SLA)")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Por Sucursal**")
        df_branch = build_sla_table(avail_by_branch, label_col="Sucursal")
        st.dataframe(df_branch, use_container_width=True, hide_index=True)
        if not df_branch.empty:
            st.bar_chart(df_branch.set_index("Sucursal"))

    with col_b:
        st.markdown("**Por Tipo de Dispositivo**")
        df_type = build_sla_table(avail_by_type, label_col="Tipo de Dispositivo")
        st.dataframe(df_type, use_container_width=True, hide_index=True)
        if not df_type.empty:
            st.bar_chart(df_type.set_index("Tipo de Dispositivo"))


# ---------------------------------------------------------------------------
# Leyenda de estados
# ---------------------------------------------------------------------------

def render_legend() -> None:
    """Muestra la leyenda de colores de estados."""
    with st.expander("ℹ️ Leyenda de Estados"):
        for state, label in STATE_LABELS.items():
            color = STATE_COLORS[state]
            st.markdown(
                f"<span style='background:{color};color:white;padding:2px 8px;"
                f"border-radius:4px;'>{label}</span>",
                unsafe_allow_html=True,
            )
