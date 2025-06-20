# Importación módulos y funciones auxiliares propias
from datetime import datetime
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from fastapi.responses import StreamingResponse

from routes.auth_routes import get_current_user

import os
import io
import zipfile
import shutil

# Creación del router para agrupar las rutas relacionadas con autenticación
router = APIRouter()

# Carpeta base donde se guardan las imágenes etiquetadas por clase
BASE_FOLDER = "imagenes_etiquetadas"
os.makedirs(BASE_FOLDER, exist_ok=True)

# Clases válidas y su representación como nombres de carpeta
CLASES_VALIDAS = {
    "Podredumbre negra": "Podredumbre_negra",
    "Mildiu": "Mildiu",
    "Esca": "Esca",
    "Sana": "Sana",
    "Tizon Foliar": "Tizon_Foliar"
}

# Ruta POST para subir imágenes etiquetadas manualmente
@router.post("/upload_labeled_image")
async def upload_labeled_image(
    file: UploadFile = File(...),
    etiqueta: str = Form(...),
    current_user = Depends(get_current_user)
):
    # Verifica que el archivo subido sea una imagen
    if file.content_type.split('/')[0] != 'image':
        raise HTTPException(status_code=400, detail="Archivo no es una imagen")

    # Verifica que la etiqueta proporcionada sea válida
    if etiqueta not in CLASES_VALIDAS:
        raise HTTPException(status_code=400, detail="Etiqueta no válida")

    # Determina la subcarpeta correspondiente a la etiqueta
    carpeta = CLASES_VALIDAS[etiqueta]
    carpeta_path = os.path.join(BASE_FOLDER, carpeta)
    os.makedirs(carpeta_path, exist_ok=True)

    # Genera un nombre único para el archivo basado en usuario y fecha/hora
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    ext = os.path.splitext(file.filename)[1]
    filename = f"{current_user.username}_{timestamp}{ext}"
    filepath = os.path.join(carpeta_path, filename)

    # Guarda la imagen físicamente en la carpeta correspondiente
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Registra metadatos en un CSV simple
    with open(os.path.join(BASE_FOLDER, "metadata.csv"), "a") as f:
        f.write(f"{carpeta}/{filename},{etiqueta},{current_user.username},{timestamp}\n")

    return {"mensaje": f"Imagen guardada en carpeta '{carpeta}' correctamente", "archivo": filename}

# Ruta GET para descargar las imágenes de una clase en formato ZIP
@router.get("/download_images/{carpeta}")
async def download_images(carpeta: str, current_user = Depends(get_current_user)):
    # Verifica que la carpeta solicitada sea válida
    carpetas_validas = set(CLASES_VALIDAS.values())  # valores, no claves
    if carpeta not in carpetas_validas:
        raise HTTPException(status_code=400, detail="Carpeta no válida")

    carpeta_path = os.path.join(BASE_FOLDER, carpeta)
    if not os.path.exists(carpeta_path):
        raise HTTPException(status_code=404, detail="Carpeta no encontrada")

    # Crea un archivo ZIP en memoria
    zip_io = io.BytesIO()
    with zipfile.ZipFile(zip_io, mode="w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        for root, dirs, files in os.walk(carpeta_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, carpeta_path)
                zip_file.write(file_path, arcname)
    # Rebobina el ZIP para leer desde el principio
    zip_io.seek(0)

    # Envía el ZIP como descarga al cliente
    return StreamingResponse(
        zip_io,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={carpeta}.zip"}
    )