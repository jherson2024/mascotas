#/utils/keygen.py
import secrets

# Máximo número permitido por BIGINT UNSIGNED de MySQL
MAX_UINT64 = 18446744073709551615

def generate_uint64_key() -> str:
    """
    Genera un número aleatorio válido para BIGINT UNSIGNED (hasta 20 dígitos).
    Puede variar en longitud (no siempre 20 dígitos).
    """
    val = secrets.randbelow(MAX_UINT64) + 1
    return str(val)

def generate_full_20digit_key() -> str:
    """
    Genera una clave de exactamente 20 dígitos.
    Se debe almacenar como CHAR(20) o VARCHAR(20) si quieres conservar los dígitos completos.
    """
    digits = ''.join(str(secrets.randbelow(10)) for _ in range(20))
    if digits[0] == '0':  # evitar que empiece en 0 si no lo quieres
        digits = str(secrets.randbelow(9) + 1) + digits[1:]
    return digits
