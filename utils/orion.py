# Importación módulos
from datetime import datetime

import os
import requests

# URL base de Orion Context Broker (por defecto localhost, pero puede venir de variable de entorno)
ORION_URL = os.getenv("ORION_URL", "http://localhost:1026")

# Función que envía una predicción como entidad NGSI v2 al broker Orion
def enviar_a_orion(diagnostico, usuario, filename, latitud, longitud):
    entidad = {
        "id": f"Prediccion:{filename}",
        "type": "Prediccion",
        "usuario": {"value": usuario, "type": "Text"},
        "enfermedad": {"value": diagnostico["clase"], "type": "Text"},
        "confianza": {"value": diagnostico["confianza"], "type": "Number"},
        "latitud": {"value": latitud, "type": "Text"},
        "longitud": {"value": longitud, "type": "Text"},
        "fecha": {"value": datetime.utcnow().isoformat(), "type": "Text"}
    }

    try:
        # Envío a Orion
        r = requests.post(f"{ORION_URL}/v2/entities", json=entidad)
        r.raise_for_status()
        print(f"✅ Entidad enviada a Orion: {entidad['id']}")
    except Exception as e:
        print(f"❌ Error al enviar entidad a Orion: {e}")
        print("Entidad fallida:", entidad)