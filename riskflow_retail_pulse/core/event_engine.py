"""
event_engine.py – Generación de eventos por cambio de estado.

Solo crea un Event cuando el estado de un endpoint realmente cambia.
Los eventos se envían a local_store para persistencia.
"""

from datetime import datetime
from typing import Optional

from core.models import Device, Event


def build_event(
    device: Device,
    previous_state: Optional[str],
    new_state: str,
    detail: str = "",
) -> Event:
    """
    Construye un objeto Event dado un cambio de estado.

    Args:
        device:         Configuración del dispositivo afectado.
        previous_state: Estado anterior (None si es la primera medición).
        new_state:      Nuevo estado detectado.
        detail:         Mensaje descriptivo opcional.

    Returns:
        Objeto Event listo para persistir.
    """
    prev = previous_state if previous_state is not None else "NINGUNO"

    return Event(
        device_id=device.id,
        branch_id=device.branch_id,
        device_type=device.device_type,
        previous_state=prev,
        new_state=new_state,
        occurred_at=datetime.utcnow(),
        detail=detail,
    )
