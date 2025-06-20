# Importación módulos y funciones auxiliares propias
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from utils.database import create_user, update_user
from routes.auth_routes import get_current_user

# Creación del router para agrupar las rutas relacionadas con autenticación
router = APIRouter()

class NewUserRequest(BaseModel):
    # Modelo de datos que define cómo debe ser la petición para crear un nuevo usuario
    username: str
    password: str
    full_name: str = ""
    role: str = "agricultor"

class UserUpdate(BaseModel):
    # Modelo de datos para actualizar el rol o nombre completo de un usuario
    username: str
    full_name: str
    new_role: str

# Función que comprueba si el usuario actual es administrador
def check_admin(current_user = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para acceder a esta ruta"
        )

# Ruta POST para crear un nuevo usuario, solo para administradores
@router.post("/create_user")
async def create_user_admin(user: NewUserRequest, current_user = Depends(check_admin)):
    create_user(user.username, user.password, user.full_name, user.role)
    return {"msg": "Usuario creado con éxito"}

# Ruta PUT para actualizar datos de un usuario (nombre completo o rol), solo para administradores
@router.put("/update_user")
async def update_user_data(data: UserUpdate, current_user = Depends(check_admin)):
    update_user(data.username, data.full_name, data.new_role)
    return {"msg": "Usuario actualizado correctamente"}