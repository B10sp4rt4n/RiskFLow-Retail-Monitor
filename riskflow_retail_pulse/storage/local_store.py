"""
local_store.py – Persistencia en SQLite.

Tablas:
  endpoint_status  – Estado más reciente de cada endpoint.
  event_log        – Bitácora histórica de eventos de cambio de estado.

El archivo SQLite se guarda en el directorio de trabajo.
El nombre del archivo puede configurarse con DB_PATH.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from core.models import EndpointStatus, Event

# Ruta por defecto de la base de datos (junto al proyecto)
DB_PATH = Path(__file__).parent / "riskflow_data.db"


# ---------------------------------------------------------------------------
# Inicialización de la base de datos
# ---------------------------------------------------------------------------

def init_db(db_path: Path = DB_PATH) -> None:
    """Crea las tablas si no existen."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS endpoint_status (
                device_id     TEXT PRIMARY KEY,
                state         TEXT NOT NULL,
                checked_at    TEXT NOT NULL,
                response_ms   REAL,
                detail        TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS event_log (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id       TEXT NOT NULL,
                branch_id       TEXT NOT NULL,
                device_type     TEXT NOT NULL,
                previous_state  TEXT NOT NULL,
                new_state       TEXT NOT NULL,
                occurred_at     TEXT NOT NULL,
                detail          TEXT
            )
        """)
        conn.commit()


# ---------------------------------------------------------------------------
# Guardar / leer estado actual
# ---------------------------------------------------------------------------

def upsert_status(status: EndpointStatus, db_path: Path = DB_PATH) -> None:
    """Inserta o actualiza el estado de un endpoint."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO endpoint_status (device_id, state, checked_at, response_ms, detail)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(device_id) DO UPDATE SET
                state       = excluded.state,
                checked_at  = excluded.checked_at,
                response_ms = excluded.response_ms,
                detail      = excluded.detail
        """, (
            status.device_id,
            status.state,
            status.checked_at.isoformat(),
            status.response_ms,
            status.detail,
        ))
        conn.commit()


def load_current_states(db_path: Path = DB_PATH) -> Dict[str, str]:
    """
    Devuelve un dict  device_id → state  con el estado más reciente
    de cada endpoint registrado.
    """
    with sqlite3.connect(db_path) as conn:
        rows = conn.execute(
            "SELECT device_id, state FROM endpoint_status"
        ).fetchall()
    return {row[0]: row[1] for row in rows}


def load_status_detail(db_path: Path = DB_PATH) -> List[dict]:
    """Devuelve todos los registros de estado actuales como lista de dicts."""
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM endpoint_status ORDER BY device_id"
        ).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Guardar / leer eventos
# ---------------------------------------------------------------------------

def insert_event(event: Event, db_path: Path = DB_PATH) -> None:
    """Persiste un evento de cambio de estado."""
    with sqlite3.connect(db_path) as conn:
        conn.execute("""
            INSERT INTO event_log
                (device_id, branch_id, device_type, previous_state, new_state, occurred_at, detail)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            event.device_id,
            event.branch_id,
            event.device_type,
            event.previous_state,
            event.new_state,
            event.occurred_at.isoformat(),
            event.detail,
        ))
        conn.commit()


def load_events(
    limit: int = 500,
    branch_id: Optional[str] = None,
    db_path: Path = DB_PATH,
) -> List[dict]:
    """
    Carga eventos del log histórico.

    Args:
        limit:     Máximo de registros a retornar (más recientes primero).
        branch_id: Filtrar por sucursal (None = todas).
    """
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        if branch_id:
            rows = conn.execute("""
                SELECT * FROM event_log
                WHERE branch_id = ?
                ORDER BY occurred_at DESC
                LIMIT ?
            """, (branch_id, limit)).fetchall()
        else:
            rows = conn.execute("""
                SELECT * FROM event_log
                ORDER BY occurred_at DESC
                LIMIT ?
            """, (limit,)).fetchall()
    return [dict(r) for r in rows]


def load_events_as_objects(
    limit: int = 2000,
    db_path: Path = DB_PATH,
) -> List[Event]:
    """
    Carga los eventos y los devuelve como objetos Event
    (útil para sla_engine).
    """
    raw = load_events(limit=limit, db_path=db_path)
    events = []
    for r in raw:
        events.append(Event(
            device_id=r["device_id"],
            branch_id=r["branch_id"],
            device_type=r["device_type"],
            previous_state=r["previous_state"],
            new_state=r["new_state"],
            occurred_at=datetime.fromisoformat(r["occurred_at"]),
            detail=r.get("detail", ""),
        ))
    return events
