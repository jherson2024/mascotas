from passlib.context import CryptContext

# Configurar el contexto de encriptación
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica si la contraseña en texto plano coincide con la contraseña hasheada.
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Genera un hash de una contraseña en texto plano.
    """
    return pwd_context.hash(password)
