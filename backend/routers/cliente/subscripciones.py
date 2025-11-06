"""
RUTAS DEL CLIENTE – SUBSCRIPCIONES Y MEMBRESÍAS
------------------------------------------------
Permite al cliente consultar los planes disponibles, suscribirse a uno,
ver su suscripción activa y cancelar su membresía si lo desea.

Incluye:
- Listado de planes activos
- Detalle de un plan
- Suscripción a un plan
- Consulta de la membresía actual del cliente
- Cancelación o cambio de suscripción

Notas:
- IDs en formato `str` (por BIGINT).
- Los planes se gestionan en la tabla `membresia_subscripcion`.
- La relación cliente–plan está en `cliente.membresia_subscripcion_id`.
- Campo `estado_registro`: "A" (activo), "I" (inactivo).
"""

from fastapi import APIRouter, Depends, HTTPException
from utils import keygen

router = APIRouter(prefix="/cliente/subscripciones", tags=["Subscripciones del Cliente"])


# ---------------------------------------------------------------------------
# GET /cliente/subscripciones
# ---------------------------------------------------------------------------
# Lista todos los planes de membresía activos disponibles.
# Incluye nombre, duración, precio y beneficios.
@router.get("/")
def listar_planes_activos():
    pass


# ---------------------------------------------------------------------------
# GET /cliente/subscripciones/{subscripcion_id}
# ---------------------------------------------------------------------------
# Obtiene los detalles de un plan específico.
# Retorna precio, descripción y beneficios.
@router.get("/{subscripcion_id}")
def obtener_detalle_plan(subscripcion_id: str):
    pass


# ---------------------------------------------------------------------------
# GET /cliente/subscripciones/{cliente_id}/actual
# ---------------------------------------------------------------------------
# Devuelve la membresía actual del cliente (si tiene una activa).
# Incluye nombre del plan, fecha de inicio y duración restante.
@router.get("/{cliente_id}/actual")
def obtener_subscripcion_actual(cliente_id: str):
    pass


# ---------------------------------------------------------------------------
# POST /cliente/subscripciones/{cliente_id}/suscribirse/{subscripcion_id}
# ---------------------------------------------------------------------------
# Permite al cliente suscribirse a un plan.
# Si ya tiene una membresía activa, puede actualizarla o reemplazarla.
@router.post("/{cliente_id}/suscribirse/{subscripcion_id}")
def suscribirse_plan(cliente_id: str, subscripcion_id: str):
    pass


# ---------------------------------------------------------------------------
# DELETE /cliente/subscripciones/{cliente_id}/cancelar
# ---------------------------------------------------------------------------
# Cancela la suscripción actual del cliente.
# Actualiza `cliente.membresia_subscripcion_id` a NULL.
@router.delete("/{cliente_id}/cancelar")
def cancelar_subscripcion(cliente_id: str):
    pass
