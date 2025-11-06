"""
RUTAS DEL ADMINISTRADOR – GESTIÓN DE SUBSCRIPCIONES
----------------------------------------------------
Permite al administrador administrar los planes de membresía o suscripción
que pueden adquirir los clientes.

Incluye:
- Creación de nuevos planes de suscripción
- Actualización de planes existentes
- Activación o desactivación de planes
- Consulta general o individual de planes

Notas:
- IDs en formato `str` (por BIGINT).
- Claves generadas con utils.keygen.generate_uint64_key().
- Campo `estado_registro`: "A" = activo, "I" = inactivo.
- Campos de modelo: nombre, duración (en días), precio, descripción, beneficios.
"""

from fastapi import APIRouter, Depends, HTTPException
from utils import keygen

router = APIRouter(prefix="/admin/subscripciones", tags=["Subscripciones (Administrador)"])


# ---------------------------------------------------------------------------
# POST /admin/subscripciones
# ---------------------------------------------------------------------------
# Crea un nuevo plan de suscripción.
# Campos requeridos:
#   - nombre
#   - duracion (días)
#   - precio
#   - descripcion (opcional)
#   - beneficios (opcional)
@router.post("/")
def crear_subscripcion():
    pass


# ---------------------------------------------------------------------------
# GET /admin/subscripciones
# ---------------------------------------------------------------------------
# Lista todas las suscripciones disponibles en el sistema.
# Puede filtrarse por estado (activas/inactivas).
@router.get("/")
def listar_subscripciones_admin(estado: str = None):
    pass


# ---------------------------------------------------------------------------
# GET /admin/subscripciones/{subscripcion_id}
# ---------------------------------------------------------------------------
# Obtiene los detalles de un plan de suscripción específico.
@router.get("/{subscripcion_id}")
def obtener_detalle_subscripcion(subscripcion_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /admin/subscripciones/{subscripcion_id}
# ---------------------------------------------------------------------------
# Actualiza los datos de un plan de suscripción.
# Permite modificar nombre, precio, duración, descripción, beneficios.
@router.put("/{subscripcion_id}")
def actualizar_subscripcion(subscripcion_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /admin/subscripciones/{subscripcion_id}/estado
# ---------------------------------------------------------------------------
# Activa o desactiva un plan de suscripción.
# Cambia el valor de `estado_registro` (A o I).
@router.put("/{subscripcion_id}/estado")
def cambiar_estado_subscripcion(subscripcion_id: str):
    pass
