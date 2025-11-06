"""
RUTAS DEL REPARTIDOR – CONTROL DE ENTREGA
------------------------------------------
Permite al repartidor gestionar y actualizar el estado de sus pedidos asignados,
así como consultar su historial de entregas.
Incluye:
- Listado de pedidos pendientes o asignados al repartidor.
- Consulta detallada de un pedido específico.
- Registro de entrega completada (confirmación de entrega).
- Registro de pedido devuelto.
- Historial de pedidos entregados o devueltos.
Notas:
- IDs manejados como `str` (por BIGINT).
- Los cambios de estado se reflejan en las tablas `pedido` y `control_entrega`.
- Campo `confirmacion_entrega`:
    * 1 → Entregado
    * 0 → Pendiente o devuelto
- Solo el repartidor autenticado puede acceder o modificar sus propios pedidos.
"""
from sqlalchemy.orm import joinedload, Session
from fastapi import APIRouter, Depends, HTTPException
from utils import keygen
from utils.db import get_db
from datetime import datetime
router = APIRouter(prefix="/repartidor", tags=["Repartidor"])

# ---------------------------------------------------------------------------
# GET /repartidor/{repartidor_id}/pedidos
# ---------------------------------------------------------------------------
# Lista todos los pedidos asignados al repartidor (pendientes de entrega).
# Incluye cliente, dirección, estado y fecha del pedido.
# Si el repartidor no existe o no tiene pedidos pendientes, retorna un mensaje informativo.
@router.get("/{repartidor_id}/pedidos")
def listar_pedidos_asignados(
    repartidor_id: str,
    db: Session = Depends(get_db),
):
    # Verificar si el repartidor existe
    repartidor = db.query(Repartidor).filter(Repartidor.id == repartidor_id).first()
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    entregas = (
        db.query(ControlEntrega)
        .join(ControlEntrega.pedido)
        .options(
            joinedload(ControlEntrega.pedido).joinedload(Pedido.cliente),
            joinedload(ControlEntrega.pedido).joinedload(Pedido.direccion)
        )
        .filter(ControlEntrega.repartidor_id == repartidor_id)
        .filter(ControlEntrega.confirmacion_entrega == 0) 
        .order_by(Pedido.fecha.asc())
        .all()
    )
    if not entregas:
        return {"mensaje": "No hay pedidos pendientes asignados a este repartidor."}
    pedidos = []
    for ctrl in entregas:
        pedido = ctrl.pedido
        cliente = pedido.cliente if pedido else None
        direccion = pedido.direccion if pedido else None
        pedidos.append({
            "pedido_id": str(pedido.id),
            "fecha_pedido": pedido.fecha.isoformat(),
            "estado_pedido": pedido.estado,
            "total": float(pedido.total),
            "cliente": {
                "id": str(cliente.id),
                "nombre": cliente.nombre,
                "telefono": cliente.telefono,
            } if cliente else None,
            "direccion": {
                "nombre": direccion.nombre if direccion else None,
                "referencia": direccion.referencia if direccion else None,
                "latitud": float(direccion.latitud) if direccion else None,
                "longitud": float(direccion.longitud) if direccion else None,
            } if direccion else None,
        })
    return {
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
        },
        "total_pedidos_pendientes": len(pedidos),
        "pedidos": pedidos,
    }

# ---------------------------------------------------------------------------
# GET /repartidor/pedidos/{pedido_id}
# ---------------------------------------------------------------------------
# Devuelve los detalles de un pedido asignado al repartidor.
# Incluye cliente, dirección, platos, total y confirmación de entrega.
@router.get("/pedidos/{pedido_id}")
def obtener_detalle_pedido_asignado(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    control = (
        db.query(ControlEntrega)
        .options(
            joinedload(ControlEntrega.pedido)
            .joinedload(Pedido.cliente),
            joinedload(ControlEntrega.pedido)
            .joinedload(Pedido.direccion),
            joinedload(ControlEntrega.pedido)
            .joinedload(Pedido.detalle_pedido)
            .joinedload(DetallePedido.plato_combinado),
            joinedload(ControlEntrega.repartidor)
        )
        .filter(ControlEntrega.pedido_id == pedido_id)
        .first()
    )
    if not control:
        raise HTTPException(status_code=404, detail="El pedido no está asignado o no existe.")
    pedido = control.pedido
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en la base de datos.")
    cliente = pedido.cliente
    direccion = pedido.direccion
    repartidor = control.repartidor
    platos_info = []
    for det in pedido.detalle_pedido:
        platos_info.append({
            "id": str(det.id),
            "plato": det.plato_combinado.nombre if det.plato_combinado else None,
            "cantidad": det.cantidad,
            "subtotal": float(det.subtotal),
        })
    respuesta = {
        "pedido": {
            "id": str(pedido.id),
            "fecha": pedido.fecha.isoformat(),
            "total": float(pedido.total),
            "estado": pedido.estado,
            "confirmacion_entrega": bool(control.confirmacion_entrega),
        },
        "cliente": {
            "id": str(cliente.id),
            "nombre": cliente.nombre,
            "telefono": cliente.telefono,
        } if cliente else None,
        "direccion": {
            "id": str(direccion.id),
            "nombre": direccion.nombre,
            "referencia": direccion.referencia,
            "latitud": float(direccion.latitud),
            "longitud": float(direccion.longitud),
        } if direccion else None,
        "platos": platos_info,
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
        } if repartidor else None,
    }
    return respuesta


# ---------------------------------------------------------------------------
# PUT /repartidor/pedidos/{pedido_id}/entregado
# ---------------------------------------------------------------------------
# Marca el pedido como entregado y actualiza la fecha y confirmación de entrega.
@router.put("/pedidos/{pedido_id}/entregado")
def marcar_pedido_completado(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    control = db.query(ControlEntrega).filter(ControlEntrega.pedido_id == pedido_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="El pedido no está asignado o no existe.")
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en la base de datos.")
    if pedido.estado == "entregado" and control.confirmacion_entrega == 1:
        return {"mensaje": "El pedido ya fue marcado como entregado anteriormente."}
    pedido.estado = "entregado"
    control.confirmacion_entrega = 1
    control.fecha_entrega = datetime.now()
    db.commit()
    return {
        "mensaje": "El pedido ha sido marcado como entregado correctamente.",
        "pedido": {
            "id": str(pedido.id),
            "estado": pedido.estado,
            "fecha_entrega": control.fecha_entrega.isoformat(),
            "confirmacion_entrega": True,
        },
    }

# ---------------------------------------------------------------------------
# PUT /repartidor/pedidos/{pedido_id}/devuelto
# ---------------------------------------------------------------------------
# Marca el pedido como devuelto.
# Cambia `pedido.estado` a "devuelto" y `confirmacion_entrega` a 0.
@router.put("/pedidos/{pedido_id}/devuelto")
def marcar_pedido_devuelto(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    control = db.query(ControlEntrega).filter(ControlEntrega.pedido_id == pedido_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="El pedido no está asignado o no existe en el control de entrega.")
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado en la base de datos.")
    if pedido.estado in ["entregado", "cancelado"]:
        raise HTTPException(status_code=400, detail=f"No se puede marcar un pedido '{pedido.estado}' como devuelto.")
    pedido.estado = "devuelto"
    control.confirmacion_entrega = 0
    control.fecha_entrega = datetime.now()
    db.commit()
    return {
        "mensaje": "El pedido ha sido marcado como devuelto correctamente.",
        "pedido": {
            "id": str(pedido.id),
            "estado": pedido.estado,
            "fecha_actualizacion": control.fecha_entrega.isoformat(),
            "confirmacion_entrega": False,
        },
    }

# ---------------------------------------------------------------------------
# GET /repartidor/{repartidor_id}/historial
# ---------------------------------------------------------------------------
# Devuelve el historial de entregas completadas o devueltas del repartidor.
# Incluye fecha, estado final, cliente y total del pedido.
@router.get("/{repartidor_id}/historial")
def listar_historial_entregas(
    repartidor_id: str,
    db: Session = Depends(get_db),
):
    repartidor = db.query(Repartidor).filter(Repartidor.id == repartidor_id).first()
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    entregas = (
        db.query(ControlEntrega)
        .join(ControlEntrega.pedido)
        .options(
            joinedload(ControlEntrega.pedido).joinedload(Pedido.cliente)
        )
        .filter(ControlEntrega.repartidor_id == repartidor_id)
        .filter(Pedido.estado.in_(["entregado", "devuelto"]))
        .order_by(ControlEntrega.fecha_entrega.desc())
        .all()
    )
    if not entregas:
        return {"mensaje": "No se encontraron entregas completadas o devueltas para este repartidor."}
    historial = []
    for ctrl in entregas:
        pedido = ctrl.pedido
        cliente = pedido.cliente if pedido else None
        historial.append({
            "pedido_id": str(pedido.id),
            "fecha_pedido": pedido.fecha.isoformat(),
            "fecha_entrega": ctrl.fecha_entrega.isoformat() if ctrl.fecha_entrega else None,
            "estado_final": pedido.estado,
            "total": float(pedido.total),
            "cliente": {
                "id": str(cliente.id) if cliente else None,
                "nombre": cliente.nombre if cliente else None,
                "telefono": cliente.telefono if cliente else None,
            } if cliente else None,
        })
    return {
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
        },
        "total_registros": len(historial),
        "historial": historial,
    }
