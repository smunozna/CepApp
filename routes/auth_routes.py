# Importación módulos y funciones auxiliares propias
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt

from utils.auth import verify_password, create_access_token, SECRET_KEY, ALGORITHM, oauth2_scheme
from utils.database import get_user

# Creación del router para agrupar las rutas relacionadas con autenticación
router = APIRouter()

# Modelos de datos (para documentación automática y validación)
class Token(BaseModel):
    # Estructura que devuelve el endpoint /token (acceso + tipo)
    access_token: str
    token_type: str

class User(BaseModel):
    # Representación del usuario autenticado que se puede devolver desde /me
    username: str
    full_name: str = None
    is_active: bool = True
    role: str = "agricultor"

# Función que obtiene el usuario actual y lo verifica a partir del token JWT
def get_current_user(token: str = Depends(oauth2_scheme)):
    # Mensaje de error estándar para credenciales inválidas o token incorrecto
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No autorizado - token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Se decodifica el token JWT usando la clave secreta y el algoritmo definido
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Se obtiene el usuario de la base de datos a partir del username incluido en el token
    user_dict = get_user(username)
    if user_dict is None:
        raise credentials_exception
    user = User(**user_dict)
    # Si el usuario está inactivo, se deniega el acceso
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Usuario inactivo")
    return user

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # Se obtiene el usuario por nombre de usuario y se valida la contraseña
    user_dict = get_user(form_data.username)
    if not user_dict or not verify_password(form_data.password, user_dict["hashed_password"]):
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos")
    # Se genera un token JWT con el username y el rol del usuario
    access_token = create_access_token(
        data={"sub": user_dict["username"], "role": user_dict["role"]},
        expires_delta=None,
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    # Si se llama con un token válido, se devuelve la información del usuario autenticado (nombre, rol, estado...)
    return current_user
