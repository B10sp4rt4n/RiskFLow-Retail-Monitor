"""
state_engine.py – Lógica de transiciones de estado.

Recibe el estado previo (guardado en SQLite) y el nuevo estado medido
y decide el estado final que se persistirá.

Reglas:
  - Si el nuevo estado es MANTENIMIENTO, siempre se respeta.
  - Si el estado anterior era MANTENIMIENTO y el nuevo es distinto,
    se regresa al nuevo estado sin generar alarma (es esperado).
  - Cualquier otro cambio es una transición legítima.
  - Si no había estado previo, el estado inicial es DESCONOCIDO.
"""

from typing import Optional
from core.models import State


# ---------------------------------------------------------------------------
# Tabla de transiciones permitidas
# ---------------------------------------------------------------------------
# Clave  = estado_anterior
# Valor  = conjunto de estados a los que puede transitar

ALLOWED_TRANSITIONS: dict = {
    State.ALIVE:       {State.ALIVE, State.DEGRADED, State.DOWN, State.UNKNOWN, State.MAINTENANCE},
    State.DEGRADED:    {State.ALIVE, State.DEGRADED, State.DOWN, State.UNKNOWN, State.MAINTENANCE},
    State.DOWN:        {State.ALIVE, State.DEGRADED, State.DOWN, State.UNKNOWN, State.MAINTENANCE},
    State.UNKNOWN:     {State.ALIVE, State.DEGRADED, State.DOWN, State.UNKNOWN, State.MAINTENANCE},
    State.MAINTENANCE: {State.ALIVE, State.DEGRADED, State.DOWN, State.UNKNOWN, State.MAINTENANCE},
}


def resolve_state(previous_state: Optional[str], new_state: str) -> str:
    """
    Determina el estado final a persistir.

    Args:
        previous_state: Estado almacenado anteriormente (None si es el primero).
        new_state:      Estado recién medido / simulado.

    Returns:
        Estado resuelto (str de State.*).
    """
    if previous_state is None:
        # Primera vez que vemos este endpoint
        return new_state

    if previous_state not in ALLOWED_TRANSITIONS:
        # Estado desconocido previo → aceptar el nuevo
        return new_state

    if new_state in ALLOWED_TRANSITIONS[previous_state]:
        return new_state

    # Si la transición no está permitida (actualmente todas lo están),
    # conservar el estado previo como medida de seguridad.
    return previous_state


def is_state_change(previous_state: Optional[str], new_state: str) -> bool:
    """
    Indica si el estado realmente cambió respecto al anterior.

    Returns:
        True  → el estado cambió y se debe generar un evento.
        False → sin cambio, no generar evento.
    """
    if previous_state is None:
        return True   # Primer registro siempre genera evento
    return previous_state != new_state
