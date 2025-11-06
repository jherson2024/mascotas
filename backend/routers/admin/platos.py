"""
RUTAS DEL ADMINISTRADOR – GESTIÓN DE PLATOS
--------------------------------------------
Permite al administrador crear, editar, publicar y eliminar platos combinados.

Incluye funcionalidades para:
- Crear y actualizar platos
- Cambiar su estado de publicación (activo/inactivo)
- Asociar platos a categorías y especies
- Asignar etiquetas (por ejemplo: “bajo en grasa”, “sin gluten”)

Notas:
- IDs como `str` (por BIGINT).
- Las imágenes se almacenan en utils.globals.PLATO.
- Si no se proporciona imagen, se usa PLATO/default.png.
- Solo los administradores pueden acceder a estas rutas.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from utils import keygen, globals

router = APIRouter(prefix="/admin/platos", tags=["Platos (Administrador)"])


# ---------------------------------------------------------------------------
# POST /admin/platos
# ---------------------------------------------------------------------------
# Crea un nuevo plato combinado.
# Campos: nombre, precio, categoria_id, especie_id, descripcion, publicado, incluye_plato, es_crudo.
# Se puede subir imagen opcional.
@router.post("/")
def crear_plato(imagen: UploadFile = None):
    pass


# ---------------------------------------------------------------------------
# GET /admin/platos
# ---------------------------------------------------------------------------
# Lista todos los platos registrados (activos e inactivos).
# Incluye información de categoría, especie y estado.
@router.get("/")
def listar_platos_admin():
    pass


# ---------------------------------------------------------------------------
# GET /admin/platos/{plato_id}
# ---------------------------------------------------------------------------
# Devuelve los detalles completos de un plato específico.
@router.get("/{plato_id}")
def obtener_detalle_plato_admin(plato_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /admin/platos/{plato_id}
# ---------------------------------------------------------------------------
# Edita los datos de un plato existente.
# Permite cambiar nombre, descripción, imagen, categoría, especie, etc.
@router.put("/{plato_id}")
def editar_plato(plato_id: str, imagen: UploadFile = None):
    pass

# ---------------------------------------------------------------------------
# DELETE /admin/platos/{plato_id}
# ---------------------------------------------------------------------------
# Elimina (o marca como inactivo) un plato.
# Si tiene pedidos asociados, no se borra físicamente.
@router.delete("/{plato_id}")
def eliminar_plato(plato_id: str):
    pass


# ---------------------------------------------------------------------------
# PUT /admin/platos/{plato_id}/publicar
# ---------------------------------------------------------------------------
# Cambia el estado de publicación de un plato (visible/no visible al cliente).
@router.put("/{plato_id}/publicar")
def cambiar_estado_publicacion(plato_id: str):
    pass


# ---------------------------------------------------------------------------
# POST /admin/platos/{plato_id}/etiquetas
# ---------------------------------------------------------------------------
# Asigna una o más etiquetas a un plato.
# Campos: lista de id_etiqueta.
@router.post("/{plato_id}/etiquetas")
def asignar_etiquetas(plato_id: str):
    pass


# ---------------------------------------------------------------------------
# DELETE /admin/platos/{plato_id}/etiquetas
# ---------------------------------------------------------------------------
# Elimina etiquetas asociadas a un plato.
# Campos: lista de id_etiqueta.
@router.delete("/{plato_id}/etiquetas")
def eliminar_etiquetas(plato_id: str):
    pass
