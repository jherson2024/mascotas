"""
RUTAS DE AUTENTICACIÓN Y GESTIÓN DE SESIONES
---------------------------------------------
Este módulo controla el ciclo de vida de las cuentas de usuario:
- Registro de nuevos usuarios (cliente por defecto)
- Inicio y cierre de sesión
- Gestión de roles (admin, nutricionista, repartidor)
- Recuperación de contraseña (opcional a futuro)

Notas:
- Los identificadores (id) se manejan como `str` en JSON.
- Las claves primarias deben generarse usando utils.keygen.generate_uint64_key()
- Las contraseñas deben almacenarse hasheadas con utils.security:
    • get_password_hash(password): genera el hash seguro.
    • verify_password(plain, hashed): compara contraseña ingresada con la almacenada.
- Los tokens de sesión se gestionan con utils.token_manager:
    • generar_token(user_id, rol_id): crea un JWT válido por 12 horas.
    • decodificar_token(token): valida y extrae el contenido del JWT.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from utils.db import get_db
from pydantic import BaseModel
from utils import keygen,security,token_manager
from models import CuentaUsuario, Cliente, UsuarioRol
router = APIRouter(prefix="/auth", tags=["Autenticación"])
class RegisterRequest(BaseModel):
    nombre: str
    correo: str
    contrasena: str
class LoginRequest(BaseModel):
    correo: str
    contrasena: str
# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------
# Registra una nueva cuenta de usuario con rol CLIENTE (rol_id = 2).
# Crea registros en las tablas `CuentaUsuario`, `UsuarioRol` y `Cliente`.
# Valida que el correo no esté registrado previamente.
# Las contraseñas se almacenan en formato hash seguro.
# Retorna un token JWT de sesión junto con la información básica del usuario.
@router.post("/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    nombre = data.nombre
    correo = data.correo
    contrasena = data.contrasena
    existe = db.query(CuentaUsuario).filter(CuentaUsuario.correo_electronico == correo).first()
    if existe:
        raise HTTPException(status_code=400, detail="El correo ya está registrado.")
    user_id = keygen.generate_uint64_key()
    hashed_pass = security.get_password_hash(contrasena)
    nueva_cuenta = CuentaUsuario(
        id=user_id,
        correo_electronico=correo,
        nombre_usuario=nombre,
        contrasena=hashed_pass,
        estado_registro="A",
    )
    db.add(nueva_cuenta)
    db.flush()
    usuario_rol = UsuarioRol(
        id=keygen.generate_uint64_key(),
        cuenta_usuario_id=user_id,
        rol_id=2,  # Rol CLIENTE
        estado_registro="A",
    )
    db.add(usuario_rol)
    nuevo_cliente = Cliente(
        id=keygen.generate_uint64_key(),
        cuenta_usuario_id=user_id,
        nombre=nombre,
        estado_registro="A",
    )
    db.add(nuevo_cliente)
    db.commit()
    token = token_manager.generar_token(user_id, 2)
    return {
        "mensaje": "Cuenta creada exitosamente.",
        "token": token,
        "usuario": {
            "id": str(user_id),
            "nombre": nombre,
            "correo": correo,
            "rol_id": 2,
        }
    }
# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------
# Inicia sesión con correo y contraseña.
# Verifica credenciales en `CuentaUsuario` y `estado_registro`.
# Devuelve token JWT con información básica del usuario y su rol.
@router.post("/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    correo = data.correo
    contrasena = data.contrasena

    usuario = db.query(CuentaUsuario).filter(
        CuentaUsuario.correo_electronico == correo
    ).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Correo no registrado.")
    if usuario.estado_registro != "A":
        raise HTTPException(status_code=403, detail="La cuenta no está activa.")
    if not security.verify_password(contrasena, usuario.contrasena):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta.")

    usuario_rol = db.query(UsuarioRol).filter(
        UsuarioRol.cuenta_usuario_id == usuario.id
    ).first()
    if not usuario_rol or usuario_rol.rol_id is None:
        raise HTTPException(status_code=400, detail="No se ha asignado un rol al usuario.")

    rol_id = usuario_rol.rol_id
    token = token_manager.generar_token(usuario.id, rol_id)

    from datetime import datetime
    usuario.ultimo_acceso = datetime.now()
    db.commit()

    return {
        "mensaje": "Inicio de sesión exitoso.",
        "token": token,
        "usuario": {
            "id": str(usuario.id),
            "nombre": usuario.nombre_usuario,
            "correo": usuario.correo_electronico,
            "rol_id": rol_id,
        },
    }


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------
# Cierra la sesión del usuario autenticado invalidando su token actual.
# Requiere el token JWT en los encabezados de autorización.
# En esta versión básica, la sesión se considera cerrada al descartar el token.
# (Opcional) Puede integrarse con una lista negra para invalidación inmediata.
@router.post("/logout")
def logout_user(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token no proporcionado.")
    token = auth_header.split(" ")[1]
    try:
        token_manager.decodificar_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    return {"mensaje": "Sesión cerrada exitosamente."}

# ---------------------------------------------------------------------------
# POST /auth/assign-role
# ---------------------------------------------------------------------------
# Asigna un rol específico a una cuenta (solo para administradores).
# Afecta las tablas `UsuarioRol` y `Rol`.
# Ejemplo de roles: ADMIN, CLIENTE, NUTRICIONISTA, REPARTIDOR.
@router.post("/assign-role")
def assign_role():
    pass

# ---------------------------------------------------------------------------
# POST /auth/forgot-password
# ---------------------------------------------------------------------------
# Envía un enlace de recuperación de contraseña al correo del usuario.
# Genera un token JWT temporal (válido por 30 minutos).
# El token debe ser usado en el endpoint `/auth/reset-password` para definir una nueva clave.
# (En entorno real, requiere integración con un servicio de correo electrónico).
@router.post("/forgot-password")
def forgot_password(correo: str, db: Session = Depends(get_db)):
    usuario = db.query(CuentaUsuario).filter(
        CuentaUsuario.correo_electronico == correo
    ).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="No existe una cuenta con ese correo.")
    token_reset = token_manager.generar_token(usuario.id, rol_id=None, duracion_horas=0.5)
    enlace = f"https://tu-dominio.com/reset-password?token={token_reset}"
    return {
        "mensaje": "Se ha enviado un enlace de recuperación a tu correo.",
        "token_demo": token_reset,  # 💡 Deja visible temporalmente para pruebas en desarrollo
        "valido_hasta": (datetime.utcnow() + timedelta(minutes=30)).isoformat() + "Z",
    }

# ---------------------------------------------------------------------------
# POST /auth/reset-password
# ---------------------------------------------------------------------------
# Restablece la contraseña de una cuenta usando un token de recuperación.
# El token JWT debe haber sido generado previamente por `/auth/forgot-password`.
# Valida que la cuenta esté activa antes de actualizar la contraseña.
# Las contraseñas se almacenan en formato hash seguro.
# Retorna un mensaje de confirmación y los datos básicos del usuario.
@router.post("/reset-password")
def reset_password(token: str, nueva_contrasena: str, db: Session = Depends(get_db)):
    try:
        datos = token_manager.decodificar_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Token inválido o expirado.")
    user_id = datos.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Token inválido: no contiene ID de usuario.")
    usuario = db.query(CuentaUsuario).filter(CuentaUsuario.id == user_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if usuario.estado_registro != "A":
        raise HTTPException(status_code=403, detail="La cuenta no está activa.")
    nueva_hash = security.get_password_hash(nueva_contrasena)
    usuario.contrasena = nueva_hash
    db.commit()
    return {
        "mensaje": "Contraseña actualizada correctamente.",
        "usuario": {
            "id": str(usuario.id),
            "correo": usuario.correo_electronico,
            "nombre": usuario.nombre_usuario,
        }
    }