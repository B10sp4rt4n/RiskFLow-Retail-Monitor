"""
tables.py – Helpers para construir tablas en Streamlit.

Convierte datos crudos en DataFrames listos para mostrar con st.dataframe
o st.table, aplicando colores y etiquetas en español.
"""

import pandas as pd
from typing import Dict, List

from core.models import Device, State


# ---------------------------------------------------------------------------
# Colores por estado (para st.dataframe con Styler)
# ---------------------------------------------------------------------------

STATE_COLORS: Dict[str, str] = {
    State.ALIVE:       "#28a745",   # verde
    State.DEGRADED:    "#ffc107",   # amarillo
    State.DOWN:        "#dc3545",   # rojo
    State.UNKNOWN:     "#6c757d",   # gris
    State.MAINTENANCE: "#17a2b8",   # azul
}

STATE_LABELS: Dict[str, str] = {
    State.ALIVE:       "🟢 VIVO",
    State.DEGRADED:    "🟡 DEGRADADO",
    State.DOWN:        "🔴 CAÍDO",
    State.UNKNOWN:     "⚫ DESCONOCIDO",
    State.MAINTENANCE: "🔵 MANTENIMIENTO",
}


def _color_state(val: str) -> str:
    """Retorna estilo CSS para colorear una celda según su estado."""
    color = STATE_COLORS.get(val, "#ffffff")
    return f"background-color: {color}; color: white; font-weight: bold;"


# ---------------------------------------------------------------------------
# Tabla de estado actual de endpoints
# ---------------------------------------------------------------------------

def build_status_table(
    devices: List[Device],
    current_states: Dict[str, str],
) -> pd.DataFrame:
    """
    Construye un DataFrame con el estado actual de todos los endpoints.

    Columnas: Sucursal, Dispositivo, Tipo, IP, Criticidad, Estado.
    """
    rows = []
    for device in devices:
        state = current_states.get(device.id, State.UNKNOWN)
        rows.append({
            "Sucursal":   device.branch_name,
            "ID":         device.id,
            "Dispositivo": device.name,
            "Tipo":       device.device_type,
            "IP":         device.ip,
            "Criticidad": device.criticality.upper(),
            "Estado":     STATE_LABELS.get(state, state),
            "_state_raw": state,  # columna auxiliar para colorear
        })
    df = pd.DataFrame(rows)
    return df


def style_status_table(df: pd.DataFrame) -> pd.io.formats.style.Styler:
    """Aplica colores a la columna Estado en el DataFrame."""
    return df.style.applymap(_color_state, subset=["Estado"])


# ---------------------------------------------------------------------------
# Tabla de bitácora de eventos
# ---------------------------------------------------------------------------

def build_event_table(raw_events: List[dict]) -> pd.DataFrame:
    """
    Construye un DataFrame con el historial de eventos.

    Args:
        raw_events: Lista de dicts provenientes de local_store.load_events().
    """
    if not raw_events:
        return pd.DataFrame(columns=[
            "Fecha/Hora", "Sucursal", "Dispositivo", "Tipo",
            "Estado Anterior", "Nuevo Estado", "Detalle",
        ])

    rows = []
    for e in raw_events:
        rows.append({
            "Fecha/Hora":     e.get("occurred_at", ""),
            "Sucursal":       e.get("branch_id", ""),
            "Dispositivo":    e.get("device_id", ""),
            "Tipo":           e.get("device_type", ""),
            "Estado Anterior": STATE_LABELS.get(e.get("previous_state", ""), e.get("previous_state", "")),
            "Nuevo Estado":   STATE_LABELS.get(e.get("new_state", ""), e.get("new_state", "")),
            "Detalle":        e.get("detail", ""),
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tabla de disponibilidad SLA
# ---------------------------------------------------------------------------

def build_sla_table(avail_dict: Dict[str, float], label_col: str = "Entidad") -> pd.DataFrame:
    """
    Construye un DataFrame de disponibilidad a partir de un dict
    {entidad: porcentaje}.

    Args:
        avail_dict: Dict retornado por sla_engine (branch/endpoint/type).
        label_col:  Nombre de la primera columna.
    """
    rows = [
        {label_col: entity, "Disponibilidad (%)": pct}
        for entity, pct in sorted(avail_dict.items(), key=lambda x: -x[1])
    ]
    return pd.DataFrame(rows)
