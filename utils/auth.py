# Importación módulos
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

import os

# Configura FastAPI para extraer automáticamente el token de la cabecera Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Clave secreta para firmar los tokens. Se puede configurar como variable de entorno
SECRET_KEY = os.getenv("SECRET_KEY", "clave_muy_secreta")

# Algoritmo utilizado para firmar el token JWT
ALGORITHM = "HS256"

# Tiempo de expiración del token (60 minutos por defecto)
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Configuración del sistema de encriptación de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Verifica si una contraseña en texto plano coincide con su versión hasheada
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Hashea una contraseña para guardarla en la base de datos de forma segura
def get_password_hash(password):
    return pwd_context.hash(password)

# Crea un token JWT con los datos del usuario y fecha de expiración
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()                                                 # Crea una copia de los datos (ej. username, rol)
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})                                       # Añade fecha de expiración al token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)    # Firma el token
    return encoded_jwt