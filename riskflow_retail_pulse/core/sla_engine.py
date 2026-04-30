"""
sla_engine.py – Cálculo de disponibilidad (SLA).

Calcula porcentajes de disponibilidad:
  - Por endpoint individual.
  - Por sucursal (promedio de sus endpoints).
  - Por tipo de dispositivo (promedio entre todas las sucursales).

La disponibilidad se define como:
    eventos_vivo + eventos_degradado
    ──────────────────────────────── × 100
          total_eventos_del_endpoint

Los estados CAIDO y DESCONOCIDO cuentan como no disponible.
MANTENIMIENTO se excluye del cálculo (no cuenta ni a favor ni en contra).
"""

from collections import defaultdict
from typing import Dict, List

from core.models import Event, SiteAvailability, State


# ---------------------------------------------------------------------------
# Disponibilidad por endpoint
# ---------------------------------------------------------------------------

def availability_by_endpoint(events: List[Event]) -> Dict[str, float]:
    """
    Calcula el porcentaje de disponibilidad de cada endpoint
    basándose en el histórico de eventos.

    Returns:
        Dict  device_id → porcentaje (0.0 – 100.0)
    """
    totals: Dict[str, int] = defaultdict(int)
    available: Dict[str, int] = defaultdict(int)

    for e in events:
        if e.new_state == State.MAINTENANCE:
            continue  # No cuenta en el cálculo

        totals[e.device_id] += 1
        if e.new_state in (State.ALIVE, State.DEGRADED):
            available[e.device_id] += 1

    result: Dict[str, float] = {}
    for device_id, total in totals.items():
        result[device_id] = round(available[device_id] / total * 100, 2) if total else 0.0

    return result


# ---------------------------------------------------------------------------
# Disponibilidad por sucursal
# ---------------------------------------------------------------------------

def availability_by_branch(events: List[Event]) -> Dict[str, float]:
    """
    Calcula el porcentaje de disponibilidad de cada sucursal como
    promedio de la disponibilidad de sus endpoints.

    Returns:
        Dict  branch_id → porcentaje (0.0 – 100.0)
    """
    ep_avail = availability_by_endpoint(events)

    # Agrupa device_id por branch_id usando los eventos
    branch_devices: Dict[str, set] = defaultdict(set)
    for e in events:
        branch_devices[e.branch_id].add(e.device_id)

    result: Dict[str, float] = {}
    for branch_id, devices in branch_devices.items():
        avails = [ep_avail.get(d, 0.0) for d in devices]
        result[branch_id] = round(sum(avails) / len(avails), 2) if avails else 0.0

    return result


# ---------------------------------------------------------------------------
# Disponibilidad por tipo de dispositivo
# ---------------------------------------------------------------------------

def availability_by_device_type(events: List[Event]) -> Dict[str, float]:
    """
    Calcula el porcentaje de disponibilidad por tipo de dispositivo
    como promedio entre todos los endpoints de ese tipo.

    Returns:
        Dict  device_type → porcentaje (0.0 – 100.0)
    """
    ep_avail = availability_by_endpoint(events)

    type_devices: Dict[str, set] = defaultdict(set)
    type_device_id: Dict[str, str] = {}  # device_id → device_type

    for e in events:
        type_devices[e.device_type].add(e.device_id)
        type_device_id[e.device_id] = e.device_type

    result: Dict[str, float] = {}
    for dtype, devices in type_devices.items():
        avails = [ep_avail.get(d, 0.0) for d in devices]
        result[dtype] = round(sum(avails) / len(avails), 2) if avails else 0.0

    return result


# ---------------------------------------------------------------------------
# Resumen de sitio (conteos de estado actual)
# ---------------------------------------------------------------------------

def build_site_availability(
    branch_id: str,
    branch_name: str,
    current_states: Dict[str, str],   # device_id → state
) -> SiteAvailability:
    """
    Construye un resumen SiteAvailability a partir de los estados actuales
    de los endpoints de una sucursal.
    """
    counts = {s: 0 for s in State.ALL}
    for state in current_states.values():
        if state in counts:
            counts[state] += 1

    total = len(current_states)
    avail_count = counts[State.ALIVE] + counts[State.DEGRADED]
    avail_pct = round(avail_count / total * 100, 2) if total else 0.0

    return SiteAvailability(
        branch_id=branch_id,
        branch_name=branch_name,
        total_endpoints=total,
        alive_count=counts[State.ALIVE],
        degraded_count=counts[State.DEGRADED],
        down_count=counts[State.DOWN],
        unknown_count=counts[State.UNKNOWN],
        maintenance_count=counts[State.MAINTENANCE],
        availability_pct=avail_pct,
    )
