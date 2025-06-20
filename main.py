# Importación módulos y rutas necesarias
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes import auth_routes, user_routes, predict_routes, labeled_images_routes

# Inicialización de la app
app = FastAPI()

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://sofia-domain.satrd-cpd1.imm.upv.es"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar las rutas API bajo el prefijo /api
app.include_router(auth_routes.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(predict_routes.router, prefix="/api")
app.include_router(labeled_images_routes.router, prefix="/api")