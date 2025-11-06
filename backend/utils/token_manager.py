import jwt
from datetime import datetime, timedelta
SECRET_KEY = "mi_clave_secreta"  # ⚠️ cambia esto en producción
ALGORITHM = "HS256"
def generar_token(user_id: int, rol_id: str) -> str:
    """
    Genera un token JWT con ID de usuario y rol.
    """
    payload = {
        "sub": str(user_id),
        "rol": rol_id,
        "exp": datetime.utcnow() + timedelta(hours=12)  # Expira en 12h
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token