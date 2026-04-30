"""
simulator.py – Simulación de estados de endpoints.

En producción este módulo se reemplazará por validaciones reales
(ping, socket, SNMP).  Por ahora genera estados aleatorios con
probabilidades realistas para demostrar el flujo completo.

Placeholders marcados con  # TODO: REAL MONITORING
"""

import random
from datetime import datetime
from typing import List

from core.models import Device, EndpointStatus, State


# ---------------------------------------------------------------------------
# Probabilidades de estado por criticidad (ajústelas libremente)
# ---------------------------------------------------------------------------

_STATE_WEIGHTS: dict = {
    "high":   {State.ALIVE: 70, State.DEGRADED: 15, State.DOWN: 10, State.UNKNOWN: 5, State.MAINTENANCE: 0},
    "medium": {State.ALIVE: 65, State.DEGRADED: 15, State.DOWN: 10, State.UNKNOWN: 5, State.MAINTENANCE: 5},
    "low":    {State.ALIVE: 60, State.DEGRADED: 15, State.DOWN: 10, State.UNKNOWN: 10, State.MAINTENANCE: 5},
}


def _pick_state(criticality: str) -> str:
    """Elige un estado basado en pesos probabilísticos."""
    weights_map = _STATE_WEIGHTS.get(criticality, _STATE_WEIGHTS["medium"])
    states = list(weights_map.keys())
    weights = list(weights_map.values())
    return random.choices(states, weights=weights, k=1)[0]


# ---------------------------------------------------------------------------
# Placeholders para monitoreo real (implementar después)
# ---------------------------------------------------------------------------

def check_ping(ip: str) -> EndpointStatus:  # TODO: REAL MONITORING
    """Placeholder: verifica disponibilidad mediante ICMP ping."""
    raise NotImplementedError("check_ping no implementado aún.")


def check_socket(ip: str, port: int) -> EndpointStatus:  # TODO: REAL MONITORING
    """Placeholder: verifica disponibilidad abriendo un socket TCP."""
    raise NotImplementedError("check_socket no implementado aún.")


def check_snmp(ip: str, port: int) -> EndpointStatus:  # TODO: REAL MONITORING
    """Placeholder: verifica disponibilidad consultando un agente SNMP."""
    raise NotImplementedError("check_snmp no implementado aún.")


# ---------------------------------------------------------------------------
# Función principal de simulación
# ---------------------------------------------------------------------------

def simulate_endpoint(device: Device) -> EndpointStatus:
    """
    Simula el estado de un endpoint.

    Cuando el monitoreo real esté listo, reemplaza este cuerpo por:
        if device.validation_method == "ping":
            return check_ping(device.ip)
        elif device.validation_method == "socket":
            return check_socket(device.ip, device.port)
        elif device.validation_method == "snmp":
            return check_snmp(device.ip, device.port)
    """
    state = _pick_state(device.criticality)

    # Simulamos latencia solo para dispositivos vivos o degradados
    response_ms: float | None = None
    if state in (State.ALIVE, State.DEGRADED):
        base_ms = random.uniform(5, 50)
        if state == State.DEGRADED:
            base_ms += random.uniform(100, 500)
        response_ms = round(base_ms, 2)

    detail_map = {
        State.ALIVE:       "Respondiendo correctamente.",
        State.DEGRADED:    "Respuesta lenta o paquetes perdidos.",
        State.DOWN:        "Sin respuesta.",
        State.UNKNOWN:     "No se pudo determinar el estado.",
        State.MAINTENANCE: "En ventana de mantenimiento programado.",
    }

    return EndpointStatus(
        device_id=device.id,
        state=state,
        checked_at=datetime.utcnow(),
        response_ms=response_ms,
        detail=detail_map[state],
    )


def simulate_all(devices: List[Device]) -> List[EndpointStatus]:
    """Simula el estado de todos los dispositivos en la lista."""
    return [simulate_endpoint(d) for d in devices]
