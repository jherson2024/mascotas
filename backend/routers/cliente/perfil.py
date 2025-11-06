"""
RUTAS DEL CLIENTE – PERFIL Y DIRECCIONES DE ENTREGA
----------------------------------------------------
Permite al cliente actualizar su información personal y administrar sus
direcciones de entrega.

Incluye:
- Modificación de datos personales del cliente
- Cambio de foto de perfil
- Gestión de direcciones (crear, listar, editar, eliminar)
- Selección de dirección principal

Notas:
- IDs en formato `str` (por BIGINT).
- Las fotos de cliente se guardan en utils.globals.CLIENTE.
- Si no hay imagen, se usa CLIENTE/default.png.
- Solo accesibles para el propio cliente autenticado.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from utils import globals

router = APIRouter(prefix="/cliente/perfil", tags=["Perfil del Cliente"])


# ---------------------------------------------------------------------------
# GET /cliente/perfil/{cliente_id}
# ---------------------------------------------------------------------------
# Devuelve los datos completos del perfil del cliente:
# nombre, teléfono, correo, membresía y foto.
@router.get("/{cliente_id}")
def obtener_perfil_cliente(cliente_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /cliente/perfil/{cliente_id}
# ---------------------------------------------------------------------------
# Actualiza la información personal del cliente.
# Campos editables: nombre, teléfono, correo electrónico.
@router.put("/{cliente_id}")
def actualizar_perfil_cliente(cliente_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /cliente/perfil/{cliente_id}/foto
# ---------------------------------------------------------------------------
# Permite subir o actualizar la foto de perfil del cliente.
# Si no se envía, se mantiene la actual; si se borra, vuelve a default.png.
@router.put("/{cliente_id}/foto")
def actualizar_foto_cliente(cliente_id: str, foto: UploadFile = None):
    pass


# ---------------------------------------------------------------------------
# GET /cliente/perfil/{cliente_id}/direcciones
# ---------------------------------------------------------------------------
# Lista todas las direcciones de entrega registradas por el cliente.
# Indica cuál es la dirección principal.
@router.get("/{cliente_id}/direcciones")
def listar_direcciones_cliente(cliente_id: str):
    pass


# ---------------------------------------------------------------------------
# POST /cliente/perfil/{cliente_id}/direcciones
# ---------------------------------------------------------------------------
# Crea una nueva dirección de entrega.
# Campos: nombre, latitud, longitud, referencia, es_principal.
@router.post("/{cliente_id}/direcciones")
def crear_direccion_cliente(cliente_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /cliente/perfil/direcciones/{direccion_id}
# ---------------------------------------------------------------------------
# Edita una dirección existente.
# Permite modificar nombre, coordenadas, referencia o marcar como principal.
@router.put("/direcciones/{direccion_id}")
def actualizar_direccion(direccion_id: str):
    pass


# ---------------------------------------------------------------------------
# DELETE /cliente/perfil/direcciones/{direccion_id}
# ---------------------------------------------------------------------------
# Elimina (o marca como inactiva) una dirección de entrega del cliente.
@router.delete("/direcciones/{direccion_id}")
def eliminar_direccion(direccion_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /cliente/perfil/direcciones/{direccion_id}/principal
# ---------------------------------------------------------------------------
# Marca una dirección como principal y desmarca las demás.
@router.put("/direcciones/{direccion_id}/principal")
def establecer_direccion_principal(direccion_id: str):
    pass
