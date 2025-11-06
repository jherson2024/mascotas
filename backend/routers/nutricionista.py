"""
RUTAS DEL NUTRICIONISTA – REVISIÓN Y APROBACIÓN DE PEDIDOS
------------------------------------------------------------
Permite al nutricionista revisar, aprobar o sugerir modificaciones en
pedidos especializados de los clientes.

Incluye:
- Consulta de pedidos especializados pendientes de revisión
- Revisión de recetas médicas y archivos adjuntos
- Aprobación o rechazo de pedidos especializados
- Creación de platos personalizados para mascotas específicas
- Registro de observaciones y recomendaciones

Notas:
- IDs en formato `str` (por BIGINT).
- Las claves nuevas (por ejemplo, de platos creados) se generan con
  utils.keygen.generate_uint64_key().
- Los platos creados por nutricionista se guardan con:
  creado_nutricionista = 1 y publicado = 0 (por defecto).
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from utils import keygen, globals

router = APIRouter(prefix="/nutricionista", tags=["Nutricionista"])


# ---------------------------------------------------------------------------
# GET /nutricionista/pedidos/pendientes
# ---------------------------------------------------------------------------
# Lista los pedidos especializados pendientes de revisión.
# Muestra información de la mascota, cliente, objetivo de dieta y fecha de solicitud.
@router.get("/pedidos/pendientes")
def listar_pedidos_pendientes():
    pass


# ---------------------------------------------------------------------------
# GET /nutricionista/pedidos/{pedido_id}
# ---------------------------------------------------------------------------
# Devuelve los detalles de un pedido especializado específico:
# mascota, archivos adjuntos, receta médica, y observaciones previas.
@router.get("/pedidos/{pedido_id}")
def obtener_detalle_pedido_especializado(pedido_id: str):
    pass


# ---------------------------------------------------------------------------
# POST /nutricionista/pedidos/{pedido_id}/revisar
# ---------------------------------------------------------------------------
# Permite al nutricionista registrar una revisión:
# Campos: observaciones, recomendaciones, aprobado (bool).
# Si se aprueba, se actualiza el estado del pedido especializado.
@router.post("/pedidos/{pedido_id}/revisar")
def revisar_pedido_especializado(pedido_id: str):
    pass


# ---------------------------------------------------------------------------
# POST /nutricionista/pedidos/{pedido_id}/receta
# ---------------------------------------------------------------------------
# Adjunta o actualiza una receta médica relacionada a un pedido especializado.
# Permite subir un archivo (PDF, imagen, etc.) que se guarda en el servidor.
@router.post("/pedidos/{pedido_id}/receta")
def subir_receta_medica(pedido_id: str, archivo: UploadFile):
    pass


# ---------------------------------------------------------------------------
# POST /nutricionista/platos/personalizados
# ---------------------------------------------------------------------------
# Crea un nuevo plato personalizado asociado a una mascota específica.
# Campos: nombre, descripcion, precio, especie_id, registro_mascota_id, imagen (opcional).
# Estos platos no se publican globalmente.
@router.post("/platos/personalizados")
def crear_plato_personalizado(imagen: UploadFile = None):
    pass


# ---------------------------------------------------------------------------
# GET /nutricionista/platos/personalizados/{mascota_id}
# ---------------------------------------------------------------------------
# Lista los platos personalizados creados para una mascota específica.
@router.get("/platos/personalizados/{mascota_id}")
def listar_platos_personalizados(mascota_id: str):
    pass


# ---------------------------------------------------------------------------
# GET /nutricionista/historial
# ---------------------------------------------------------------------------
# Devuelve el historial de pedidos revisados por el nutricionista.
# Incluye fecha, mascota, cliente y resultado (aprobado/rechazado).
@router.get("/historial")
def listar_historial_revisiones():
    pass
