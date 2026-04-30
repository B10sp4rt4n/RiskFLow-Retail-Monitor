"""
csv_exporter.py – Exportación de la bitácora de eventos a CSV.

Convierte la lista de eventos crudos (dicts de local_store)
en un archivo CSV descargable desde Streamlit.
"""

import csv
import io
from typing import List


# Columnas que se incluirán en el CSV exportado
CSV_COLUMNS = [
    "id",
    "occurred_at",
    "branch_id",
    "device_id",
    "device_type",
    "previous_state",
    "new_state",
    "detail",
]


def events_to_csv_bytes(raw_events: List[dict]) -> bytes:
    """
    Convierte la lista de eventos a CSV en memoria.

    Args:
        raw_events: Lista de dicts proveniente de local_store.load_events().

    Returns:
        Bytes del CSV codificados en UTF-8, listos para st.download_button.
    """
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=CSV_COLUMNS,
        extrasaction="ignore",   # Ignora columnas extras
        lineterminator="\n",
    )
    writer.writeheader()

    for event in raw_events:
        # Asegura que todas las columnas esperadas existan
        row = {col: event.get(col, "") for col in CSV_COLUMNS}
        writer.writerow(row)

    return output.getvalue().encode("utf-8")
