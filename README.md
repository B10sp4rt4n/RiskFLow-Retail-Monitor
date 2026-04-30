# RiskFlow Retail Pulse

Monitor de vida operativa de POS, impresoras y periféricos críticos en ambientes distribuidos.

> **Estado actual:** prototipo con simulación de estados.  
> El módulo está diseñado para que la simulación pueda reemplazarse por monitoreo real (ping / socket / SNMP) sin cambiar la arquitectura.

---

## Estructura del proyecto

```
riskflow_retail_pulse/
├── app.py                  # Punto de entrada Streamlit
├── requirements.txt        # Dependencias Python
├── config/
│   └── devices.yaml        # Configuración de clientes, sucursales y endpoints
├── core/
│   ├── models.py           # Dataclasses: Device, EndpointStatus, Event, SiteAvailability
│   ├── simulator.py        # Simulación de estados (con placeholders para monitoreo real)
│   ├── state_engine.py     # Lógica de transiciones de estado
│   ├── event_engine.py     # Generación de eventos por cambio de estado
│   └── sla_engine.py       # Cálculo de disponibilidad por endpoint, sucursal y tipo
├── storage/
│   └── local_store.py      # Persistencia en SQLite
├── ui/
│   ├── dashboard.py        # UI principal de Streamlit
│   └── tables.py           # Helpers para construir tablas y estilos
└── exports/
    └── csv_exporter.py     # Exportación de bitácora a CSV
```

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/B10sp4rt4n/RiskFLow-Retail-Monitor.git
cd RiskFLow-Retail-Monitor/riskflow_retail_pulse
```

### 2. Crear y activar un entorno virtual (recomendado)

```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

---

## Ejecución

```bash
streamlit run app.py
```

Abre el navegador en `http://localhost:8501`.

En la barra lateral:
- Pulsa **▶️ Ejecutar ciclo ahora** para simular un ciclo de monitoreo.
- Activa **🔄 Auto-refresco** para que los ciclos se ejecuten automáticamente.

---

## Configuración de dispositivos

Edita `config/devices.yaml` para agregar o quitar sucursales y endpoints.

Ejemplo de entrada de endpoint:

```yaml
- id: "SUC001-POS-01"
  name: "POS Caja 1"
  device_type: "POS"
  ip: "192.168.1.10"
  port: 9100
  criticality: "high"       # high | medium | low
  validation_method: "socket" # ping | socket | snmp
```

No hay límite de sucursales ni de endpoints por sucursal.

---

## Estados de un endpoint

| Estado | Significado |
|---|---|
| 🟢 VIVO | Responde correctamente |
| 🟡 DEGRADADO | Respuesta lenta o con pérdidas |
| 🔴 CAÍDO | Sin respuesta |
| ⚫ DESCONOCIDO | No se pudo determinar el estado |
| 🔵 MANTENIMIENTO | En ventana de mantenimiento programado |

---

## Persistencia

Los datos se guardan en `storage/riskflow_data.db` (SQLite).  
El archivo se crea automáticamente en el primer ciclo.

- **endpoint_status** – estado más reciente de cada endpoint.
- **event_log** – bitácora histórica de cambios de estado.

---

## Exportar bitácora

En la sección **Bitácora de Eventos** del dashboard hay un botón  
**⬇️ Exportar Bitácora (CSV)** que descarga todos los eventos visibles.

---

## Cómo agregar monitoreo real

### 1. Ping

En `core/simulator.py` implementa la función `check_ping`:

```python
import subprocess

def check_ping(ip: str) -> EndpointStatus:
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", ip],
        capture_output=True
    )
    state = State.ALIVE if result.returncode == 0 else State.DOWN
    return EndpointStatus(device_id="", state=state)
```

### 2. Socket TCP

```python
import socket, time

def check_socket(ip: str, port: int) -> EndpointStatus:
    try:
        start = time.monotonic()
        with socket.create_connection((ip, port), timeout=2):
            ms = (time.monotonic() - start) * 1000
        return EndpointStatus(device_id="", state=State.ALIVE, response_ms=ms)
    except OSError:
        return EndpointStatus(device_id="", state=State.DOWN)
```

### 3. SNMP

Instala `pysnmp` y consulta la OID `sysUpTime`:

```python
from pysnmp.hlapi import *

def check_snmp(ip: str, port: int) -> EndpointStatus:
    iterator = getCmd(
        SnmpEngine(),
        CommunityData("public"),
        UdpTransportTarget((ip, port), timeout=2, retries=0),
        ContextData(),
        ObjectType(ObjectIdentity("SNMPv2-MIB", "sysUpTime", 0)),
    )
    error_indication, error_status, _, _ = next(iterator)
    state = State.DOWN if (error_indication or error_status) else State.ALIVE
    return EndpointStatus(device_id="", state=state)
```

### 4. Conectar con `simulate_endpoint`

Sustituye el cuerpo de `simulate_endpoint` en `simulator.py`:

```python
def simulate_endpoint(device: Device) -> EndpointStatus:
    if device.validation_method == "ping":
        status = check_ping(device.ip)
    elif device.validation_method == "socket":
        status = check_socket(device.ip, device.port)
    elif device.validation_method == "snmp":
        status = check_snmp(device.ip, device.port)
    else:
        status = EndpointStatus(device_id=device.id, state=State.UNKNOWN)

    status.device_id = device.id
    return status
```

---

## Tecnologías utilizadas

| Librería | Uso |
|---|---|
| [Streamlit](https://streamlit.io) | Interfaz web |
| [PyYAML](https://pyyaml.org) | Lectura de configuración |
| [Pandas](https://pandas.pydata.org) | Tablas y exportación CSV |
| SQLite (stdlib) | Persistencia de datos |

---

## Licencia

MIT – libre para uso y modificación.