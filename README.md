# CepApp – Diagnóstico agrícola con IA

Aplicación web desarrollada como Trabajo de Fin de Grado en la Universitat Politècnica de València. Permite a los agricultores subir imágenes de hojas de vid, diagnosticar automáticamente enfermedades con IA, consultar resultados previos y recibir alertas si se detectan brotes cercanos.

---

## 🚀 Funcionalidades destacadas

- Diagnóstico en tiempo real con EfficientNetB0
- Recorte interactivo de la hoja
- Geolocalización automática del usuario
- Alertas comunitarias si se detectan enfermedades en zonas próximas
- Interfaz diferenciada para agricultores y administradores
- Backend en FastAPI y frontend web sin frameworks
- Integración con Orion Context Broker (FIWARE)

---

## 📁 Estructura del repositorio

```bash
CepApp/
├── diagnostico_uvas/
│     ├── cepapp_ssl/                 # Certificados SSL para acceso seguro (HTTPS)
│     ├── imagenes_etiquetadas/       # Imágenes clasificadas por enfermedad
│     ├── imagenes_recibidas/         # Imágenes temporales subidas por los usuarios
│     ├── main.py                     # Archivo principal de FastAPI
│     ├── usuarios.db                 # Base de datos SQLite con usuarios
│     │
│     ├── modelo/                     # Carpeta con el modelo de IA (.keras)
│     │   └── modelo_mejorado_v2.keras
│     │
│     ├── routes/                     # Endpoints del backend
│     │   ├── auth_routes.py
│     │   ├── labeled_images_routes.py
│     │   ├── predict_routes.py
│     │   └── user_routes.py
│     │
│     ├── static/                     # Archivos del frontend (HTML)
│     │   ├── app.html
│     │   ├── cooperativa.html
│     │   └── login.html
│     │
│     └── utils/                      # Funciones auxiliares y configuración
│         ├── .env                    # Variables de entorno
│         ├── auth.py
│         ├── database.py
│         └── orion.py
├── EntrenamientoEfficientNet.ipynb   # Cuaderno Jupyter para el entrenamiento del modelo IA
└── README.md                         # Este archivo
```

---

## ⚙️ Instalación y ejecución local

### 1. Clonar el repositorio

```bash
git clone https://github.com/tuusuario/CepApp.git
cd CepApp/diagnostico_uvas
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Ejecutar el backend (FastAPI)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Accede a http://localhost:8000 para usar la aplicación.
