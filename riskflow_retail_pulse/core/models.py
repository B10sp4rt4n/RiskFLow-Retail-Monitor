"""
models.py – Dataclasses centrales del proyecto.

Define las entidades clave que circulan entre los módulos:
  - Device         : configuración estática de un endpoint.
  - EndpointStatus : snapshot de estado en un momento dado.
  - Event          : registro de cambio de estado.
  - SiteAvailability: resumen de disponibilidad de una sucursal.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


# ---------------------------------------------------------------------------
# Constantes de estado
# ---------------------------------------------------------------------------

class State:
    ALIVE = "VIVO"
    DEGRADED = "DEGRADADO"
    DOWN = "CAIDO"
    UNKNOWN = "DESCONOCIDO"
    MAINTENANCE = "MANTENIMIENTO"

    ALL = [ALIVE, DEGRADED, DOWN, UNKNOWN, MAINTENANCE]


# ---------------------------------------------------------------------------
# Configuración de dispositivo (cargado desde devices.yaml)
# ---------------------------------------------------------------------------

@dataclass
class Device:
    id: str                       # Identificador único, ej. "SUC001-POS-01"
    name: str                     # Nombre legible en español
    branch_id: str                # ID de la sucursal a la que pertenece
    branch_name: str              # Nombre de la sucursal
    device_type: str              # POS | Printer | Router | Scanner | etc.
    ip: str                       # Dirección IP del endpoint
    port: int                     # Puerto TCP (para socket / SNMP)
    criticality: str              # high | medium | low
    validation_method: str        # ping | socket | snmp


# ---------------------------------------------------------------------------
# Estado puntual de un endpoint
# ---------------------------------------------------------------------------

@dataclass
class EndpointStatus:
    device_id: str
    state: str                            # Uno de State.*
    checked_at: datetime = field(default_factory=datetime.utcnow)
    response_ms: Optional[float] = None  # Latencia en ms (None si no aplica)
    detail: str = ""                      # Mensaje descriptivo adicional


# ---------------------------------------------------------------------------
# Evento generado al detectar un cambio de estado
# ---------------------------------------------------------------------------

@dataclass
class Event:
    device_id: str
    branch_id: str
    device_type: str
    previous_state: str
    new_state: str
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    detail: str = ""


# ---------------------------------------------------------------------------
# Resumen de disponibilidad de una sucursal
# ---------------------------------------------------------------------------

@dataclass
class SiteAvailability:
    branch_id: str
    branch_name: str
    total_endpoints: int
    alive_count: int
    degraded_count: int
    down_count: int
    unknown_count: int
    maintenance_count: int
    availability_pct: float   # (alive + degraded) / total * 100
