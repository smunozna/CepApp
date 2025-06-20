# Importación módulos y funciones auxiliares propias
from utils.auth import get_password_hash

import sqlite3

# Nombre del archivo de la base de datos SQLite
DB_NAME = "usuarios.db"

# Inicializa la base de datos si no existe
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Crea la tabla 'usuarios' si aún no está creada
    c.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            username TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL,
            full_name TEXT,
            is_active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'agricultor'
        )
    """)
    conn.commit()
    conn.close()

# Devuelve la información de un usuario dado su nombre de usuario
def get_user(username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Busca el usuario por su nombre (clave primaria)
    c.execute("SELECT username, hashed_password, full_name, is_active, role FROM usuarios WHERE username = ?", (username,))
    row = c.fetchone()
    conn.close()
    if row:
        # Devuelve un diccionario con los campos relevantes
        return {
            "username": row[0],
            "hashed_password": row[1],
            "full_name": row[2],
            "is_active": bool(row[3]),
            "role": row[4]
        }
    return None

# Crea un nuevo usuario y lo guarda en la base de datos
def create_user(username, password, full_name="", role="agricultor"):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Hashea la contraseña antes de guardarla por seguridad
    hashed = get_password_hash(password)
    # Inserta el nuevo usuario en la tabla
    c.execute("INSERT INTO usuarios (username, hashed_password, full_name, role) VALUES (?, ?, ?, ?)",
              (username, hashed, full_name, role))
    conn.commit()
    conn.close()

# Actualiza el nombre completo y el rol de un usuario existente
def update_user(username: str, full_name: str, new_role: str):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Modifica el usuario identificado por username
    c.execute("UPDATE usuarios SET full_name = ?, role = ? WHERE username = ?", (full_name, new_role, username))
    conn.commit()
    conn.close()