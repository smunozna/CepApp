# Importación módulos y funciones auxiliares propias
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from PIL import Image
from math import radians, cos, sin, sqrt, atan2

from routes.auth_routes import get_current_user
from utils.orion import enviar_a_orion

import requests
import os
import shutil
import numpy as np

# Configuración de carpetas y modelo IA
UPLOAD_FOLDER = "imagenes_recibidas"
MODEL_PATH = "modelo/modelo_mejorado_v2.keras"
CLASSES = ['Podredumbre negra', 'Mildiu', 'Esca', 'Sana', 'Tizón foliar']

# Mapa de carpetas para cada clase, nombres sin espacios
CLASES_CARPETAS = {
    "Podredumbre negra": "Podredumbre_negra",
    "Mildiu": "Mildiu",
    "Esca": "Esca",
    "Sana": "Sana",
    "Tizón foliar": "Tizon_Foliar"
}
# Creación del router para agrupar rutas relacionadas con predicción y Orion
router = APIRouter()

# Carga del modelo IA previamente entrenado
model = load_model(MODEL_PATH)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class User(BaseModel):
    # Modelo de usuario necesario para autenticación e identificación en rutas protegidas
    username: str
    full_name: str = None
    is_active: bool = True
    role: str = "agricultor"

# Función que recorta y redimensiona una imagen centrada (224x224 tamaño de entrada del modelo IA)
def cargar_y_recortar_centrado(ruta, size=(224, 224)):
    img = Image.open(ruta)
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    right = left + min_dim
    bottom = top + min_dim
    img = img.crop((left, top, right, bottom))
    img = img.resize(size)
    return img

# Cálculo de distancia entre dos puntos geográficos usando fórmula de Haversine
def distancia_km(lat1, lon1, lat2, lon2):
    R = 6371  # Radio de la Tierra en km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Ruta que recibe una imagen y localización, realiza la predicción y guarda resultados
@router.post("/predict")
async def predict_image(
    file: UploadFile = File(...),
    latitud: str = Form(...),
    longitud: str = Form(...),
    current_user: User = Depends(get_current_user)
):
    # Se permite que la predicción se haga incluso si no se pudo obtener ubicación desde el navegador
    if latitud == "Desconocida" or longitud == "Desconocida":
        print("Ubicación no disponible, procesando sin ubicación.")
    print(f"Usuario: {current_user.username} - Latitud: {latitud}, Longitud: {longitud}")

    # Generación de un nombre de archivo único con fecha y extensión original, y se define su ruta en imagenes_recibidas/
    ext = os.path.splitext(file.filename)[1]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"imagen_{timestamp}{ext}"
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    # Guardar imagen original en imagenes_recibidas
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Preprocesamiento de la imagen antes de enviarla al modelo
    img = cargar_y_recortar_centrado(filepath)
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    # Predicción con el modelo IA
    pred = model.predict(img_array)
    idx = np.argmax(pred[0])
    clase = CLASSES[idx]
    confianza = float(pred[0][idx])

    # Si es 'Sana' pero con confianza menor al 95%, se reconsidera la segunda mejor predicción
    if clase == "Sana" and confianza < 0.95:
        pred[0][idx] = -1
        new_idx = np.argmax(pred[0])
        clase = CLASSES[new_idx]
        confianza = float(pred[0][new_idx])

    # Guardado de la imagen también en carpeta según clase detectada
    carpeta = CLASES_CARPETAS.get(clase, "Otras")
    carpeta_path = os.path.join("imagenes_etiquetadas", carpeta)
    os.makedirs(carpeta_path, exist_ok=True)
    filename_clase = f"{current_user.username}_{timestamp}{ext}"
    filepath_clase = os.path.join(carpeta_path, filename_clase)
    # Copia del archivo a la carpeta de clase (lee desde imagenes_recibidas)
    shutil.copyfile(filepath, filepath_clase)

    # Se envía la predicción al Context Broker Orion
    enviar_a_orion(
        diagnostico={"clase": clase, "confianza": round(confianza, 4)},
        usuario=current_user.username,
        filename=filename,
        latitud=latitud,
        longitud=longitud
    )

    # Devuelve al frontend los resultados de la predicción
    return {
        "mensaje": "Predicción realizada correctamente",
        "archivo": filename,
        "clase": clase,
        "confianza": round(confianza, 4),
        "latitud": latitud,
        "longitud": longitud,
        "usuario": current_user.username
    }

# Ruta para consultar todas las entidades almacenadas en Orion
@router.get("/orion/entidades")
def obtener_entidades(current_user: User = Depends(get_current_user)):
    # Ruta protegida, solo accesible para usuarios autenticados
    try:
        # Petición HTTP GET a Orion Context Broker para obtener hasta 1000 entidades tipo Prediccion
        r = requests.get("http://localhost:1026/v2/entities?type=Prediccion&limit=1000")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Ruta para generar alertas si hay enfermedades cercanas detectadas en las últimas 24h
@router.post("/notificaciones")
async def obtener_alertas(
    latitud: str = Form(...), 
    longitud: str = Form(...), 
    current_user: User = Depends(get_current_user)
):
    try:
        # Petición HTTP GET a Orion Context Broker para obtener hasta 1000 entidades tipo Prediccion
        r = requests.get("http://localhost:1026/v2/entities?type=Prediccion&limit=1000")
        r.raise_for_status()
        entidades = r.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al consultar Orion: {e}")

    # Configuración de ubicación y hora actual
    lat1 = float(latitud)
    lon1 = float(longitud)
    ahora = datetime.utcnow()
    alertas = []

    # Recorre todas las predicciones para filtrar alertas relevantes
    for ent in entidades:
        try:
            clase = ent.get("enfermedad", {}).get("value", "")
            usuario = ent.get("usuario", {}).get("value", "")

            # Omitir las predicciones hechas por el usuario actual
            if usuario == current_user.username:
                continue

            # Omitir las predicciones de hojas sanas
            if clase == "Sana":
                continue

            # Solo se consideran predicciones de las últimas 24 horas
            fecha_str = ent.get("fecha", {}).get("value", "")
            fecha_diag = datetime.fromisoformat(fecha_str.split(".")[0])
            if (ahora - fecha_diag) > timedelta(hours=24):
                continue

            # Se calcula la distancia en kilómetros entre la ubicación del usuario actual y la predicción
            lat2 = float(ent.get("latitud", {}).get("value", "0"))
            lon2 = float(ent.get("longitud", {}).get("value", "0"))
            dist = distancia_km(lat1, lon1, lat2, lon2)

            # Si la enfermedad está a menos de 3 km, se añade como alerta
            if dist <= 3.0:
                alertas.append({
                    "enfermedad": clase,
                    "fecha": fecha_diag.strftime("%Y-%m-%d %H:%M"),
                    "distancia_km": round(dist, 2),
                    "usuario": usuario
                })
        except Exception:
            continue

    return {"alertas": alertas}

# Ruta para eliminar una entidad de Orion y borrar las imágenes asociadas
@router.delete("/orion/eliminar")
def eliminar_entidad_orion(entity_id: str = Query(...), current_user: User = Depends(get_current_user)):
    # Solo los usuarios con rol admin pueden ejecutar esta acción
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="No autorizado")

    try:
        # Petición HTTP GET a Orion Context Broker para obtener la entidad actual de Orion
        r_get = requests.get(f"http://localhost:1026/v2/entities/{entity_id}")
        r_get.raise_for_status()
        entidad = r_get.json()
    except Exception as e:
        return {"detalle": f"No se pudo obtener la entidad para eliminación extendida: {e}"}

    try:
        # Eliminar entidad en Orion
        r_del = requests.delete(f"http://localhost:1026/v2/entities/{entity_id}")
        r_del.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo eliminar la entidad de Orion: {e}")

    # Borrar imágenes del sistema de archivos
    nombre_archivo = entity_id.replace("Prediccion:", "")
    clase = entidad.get("enfermedad", {}).get("value", "")
    usuario = entidad.get("usuario", {}).get("value", "")

    # Ruta imagen original
    ruta_original = os.path.join("imagenes_recibidas", nombre_archivo)
    # Ruta imagen copiada en carpeta etiquetada
    carpeta_etiquetada = CLASES_CARPETAS.get(clase, "Otras")
    nombre_etiquetado = f"{usuario}_{nombre_archivo.split('_', 1)[-1]}"
    ruta_etiquetada = os.path.join("imagenes_etiquetadas", carpeta_etiquetada, nombre_etiquetado)

    borradas = []
    for ruta in [ruta_original, ruta_etiquetada]:
        if os.path.exists(ruta):
            os.remove(ruta)
            borradas.append(ruta)

    return {
        "mensaje": f"Entidad '{entity_id}' eliminada correctamente.",
        "imagenes_borradas": borradas
    }