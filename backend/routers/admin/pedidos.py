"""
RUTAS DEL ADMINISTRADOR – GESTIÓN DE PEDIDOS
----------------------------------------------
Permite al administrador consultar y controlar todos los pedidos registrados,
tanto normales como especializados.
Incluye:
- Listado general y filtrado por estado
- Consulta de detalles completos
- Cambio manual de estado del pedido
- Asignación y reasignación de pedidos a repartidores
- Revisión de historial y control de entregas
Notas:
- IDs en formato `str` (por BIGINT).
- Los estados válidos incluyen:
  ["pendiente", "en_preparacion", "asignado", 
   "en_camino", "entregado", "devuelto", "cancelado"]
  Descripción:
    pendiente: pedido recién creado, aún no procesado.
    en_preparacion: pedido confirmado y en proceso de preparación o empaquetado.
    asignado: pedido asignado a un repartidor (registro en control_entrega).
    en_camino: pedido en tránsito hacia el cliente.
    entregado: pedido recibido y confirmado por el cliente.
    devuelto: pedido regresado al almacén (no entregado o rechazado).
    cancelado: pedido anulado por el cliente o el administrador.
- El control de entrega se actualiza en la tabla `control_entrega`.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from utils.db import get_db
from utils import keygen
from sqlalchemy.orm import joinedload, Session
from models import Pedido, ControlEntrega, Repartidor
router = APIRouter(prefix="/admin/pedidos", tags=["Pedidos (Administrador)"])

# ---------------------------------------------------------------------------
# GET /admin/pedidos
# ---------------------------------------------------------------------------
# Lista todos los pedidos registrados en el sistema.
# Permite aplicar filtros opcionales:
#   - estado: filtra por estado logístico del pedido.
#   - cliente_id: filtra los pedidos de un cliente específico.
#   - fecha_inicio / fecha_fin: acota el rango temporal de consulta.
# Retorna una lista de pedidos con id, cliente, fecha, total y estado.
@router.get("/")
def listar_pedidos_admin(
    estado: str | None = Query(None, description="Filtrar por estado del pedido"),
    cliente_id: str | None = Query(None, description="Filtrar por ID de cliente"),
    fecha_inicio: str | None = Query(None, description="Fecha inicial en formato YYYY-MM-DD"),
    fecha_fin: str | None = Query(None, description="Fecha final en formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    query = db.query(Pedido).options(joinedload(Pedido.cliente))
    if estado:
        query = query.filter(Pedido.estado == estado)
    if cliente_id:
        query = query.filter(Pedido.cliente_id == cliente_id)
    if fecha_inicio:
        try:
            fecha_inicio_dt = datetime.strptime(fecha_inicio, "%Y-%m-%d")
            query = query.filter(Pedido.fecha >= fecha_inicio_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato inválido en fecha_inicio (usar YYYY-MM-DD)")
    if fecha_fin:
        try:
            fecha_fin_dt = datetime.strptime(fecha_fin, "%Y-%m-%d")
            query = query.filter(Pedido.fecha <= fecha_fin_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato inválido en fecha_fin (usar YYYY-MM-DD)")
    pedidos = query.order_by(Pedido.fecha.desc()).all()
    if not pedidos:
        return {"mensaje": "No se encontraron pedidos con los filtros aplicados."}
    resultado = [
        {
            "id": str(p.id),
            "cliente": p.cliente.nombre if p.cliente else None,
            "fecha": p.fecha.isoformat(),
            "total": float(p.total),
            "estado": p.estado,
        }
        for p in pedidos
    ]
    return {"total": len(resultado), "pedidos": resultado}


# ---------------------------------------------------------------------------
# GET /admin/pedidos/{pedido_id}
# ---------------------------------------------------------------------------
# Devuelve los detalles completos de un pedido específico.
# Incluye:
# - Datos del cliente y su contacto
# - Dirección de entrega
# - Lista de platos con cantidades y subtotales
# - Total y estado del pedido
# - Información del pago (monto, fecha, estado, pasarela)
# Si el pedido no existe, retorna error 404.
@router.get("/{pedido_id}")
def obtener_detalle_pedido_admin(pedido_id: str, db: Session = Depends(get_db)):
    pedido = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.cliente),
            joinedload(Pedido.direccion),
            joinedload(Pedido.detalle_pedido).joinedload(DetallePedido.plato_combinado),
            joinedload(Pedido.pago),
        )
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    cliente_info = None
    if pedido.cliente:
        cliente_info = {
            "id": str(pedido.cliente.id),
            "nombre": pedido.cliente.nombre,
            "telefono": pedido.cliente.telefono,
        }
    direccion_info = None
    if pedido.direccion:
        direccion_info = {
            "id": str(pedido.direccion.id),
            "nombre": pedido.direccion.nombre,
            "referencia": pedido.direccion.referencia,
            "latitud": float(pedido.direccion.latitud),
            "longitud": float(pedido.direccion.longitud),
        }
    platos_info = []
    for det in pedido.detalle_pedido:
        platos_info.append({
            "id": str(det.id),
            "plato": det.plato_combinado.nombre if det.plato_combinado else None,
            "cantidad": det.cantidad,
            "subtotal": float(det.subtotal),
        })
    pago_info = None
    if pedido.pago and len(pedido.pago) > 0:
        p = pedido.pago[0]
        pago_info = {
            "id": str(p.id),
            "monto": float(p.monto),
            "fecha": p.fecha.isoformat(),
            "estado": p.estado,
            "referencia_pago": p.referencia_pago,
            "pasarela": p.pasarela_pago.nombre if p.pasarela_pago else None,
        }
    respuesta = {
        "pedido": {
            "id": str(pedido.id),
            "fecha": pedido.fecha.isoformat(),
            "total": float(pedido.total),
            "incluye_plato": bool(pedido.incluye_plato),
            "estado": pedido.estado,
        },
        "cliente": cliente_info,
        "direccion": direccion_info,
        "platos": platos_info,
        "pago": pago_info,
    }
    return respuesta

# ---------------------------------------------------------------------------
# PUT /admin/pedidos/{pedido_id}/estado
# ---------------------------------------------------------------------------
# Cambia manualmente el estado de un pedido.
# Valida que la transición sea coherente con el flujo logístico:
#   pendiente → en_preparacion / cancelado
#   en_preparacion → asignado / cancelado
#   asignado → en_camino / cancelado
#   en_camino → entregado / devuelto
#   devuelto → asignado / cancelado
# Los estados "entregado" y "cancelado" son finales (no admiten cambios).
@router.put("/{pedido_id}/estado")
def actualizar_estado_pedido(
    pedido_id: str,
    nuevo_estado: str,
    db: Session = Depends(get_db)
):
    """
    Cambia el estado de un pedido de forma manual.
    Solo se permiten transiciones válidas dentro del flujo logístico.
    """
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    estado_actual = pedido.estado
    transiciones_validas = {
        "pendiente": ["en_preparacion", "cancelado"],
        "en_preparacion": ["asignado", "cancelado"],
        "asignado": ["en_camino", "cancelado"],
        "en_camino": ["entregado", "devuelto"],
        "devuelto": ["asignado", "cancelado"],
        "entregado": [],
        "cancelado": [],
    }
    if estado_actual not in transiciones_validas:
        raise HTTPException(status_code=400, detail=f"Estado actual desconocido: {estado_actual}")

    if nuevo_estado not in transiciones_validas[estado_actual]:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede cambiar de '{estado_actual}' a '{nuevo_estado}'."
        )
    pedido.estado = nuevo_estado
    db.commit()
    return {
        "mensaje": f"Estado del pedido actualizado correctamente de '{estado_actual}' a '{nuevo_estado}'.",
        "pedido": {
            "id": str(pedido.id),
            "estado_anterior": estado_actual,
            "estado_actual": nuevo_estado,
        },
    }

# ---------------------------------------------------------------------------
# PUT /admin/pedidos/{pedido_id}/asignar/{repartidor_id}
# ---------------------------------------------------------------------------
# Asigna o reasigna un pedido a un repartidor.
# - Si no existe registro previo en `control_entrega`, lo crea.
# - Si ya está asignado, actualiza el repartidor y la fecha de asignación.
# - Cambia el estado del pedido a "asignado" (si no lo estaba).
# - Marca la entrega como pendiente (`confirmacion_entrega = 0`).
@router.put("/{pedido_id}/asignar/{repartidor_id}")
def asignar_pedido_a_repartidor(
    pedido_id: str,
    repartidor_id: str,
    db: Session = Depends(get_db)
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    repartidor = db.query(Repartidor).filter(Repartidor.id == repartidor_id).first()
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    control = db.query(ControlEntrega).filter(ControlEntrega.pedido_id == pedido_id).first()
    if control:
        control.repartidor_id = repartidor_id
        control.fecha_entrega = datetime.now()  
        control.confirmacion_entrega = 0       
        mensaje = "Pedido reasignado a un nuevo repartidor."
    else:
        control = ControlEntrega(
            id=keygen.generate_uint64_key(),
            pedido_id=pedido_id,
            fecha_entrega=datetime.now(),
            confirmacion_entrega=0,
            repartidor_id=repartidor_id,
        )
        db.add(control)
        mensaje = "Pedido asignado correctamente."
    if pedido.estado not in ["asignado", "en_camino", "entregado"]:
        pedido.estado = "asignado"
    db.commit()
    return {
        "mensaje": mensaje,
        "pedido": {
            "id": str(pedido.id),
            "estado": pedido.estado,
        },
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
        },
    }

# ---------------------------------------------------------------------------
# GET /admin/pedidos/asignados
# ---------------------------------------------------------------------------
# Lista todos los pedidos con un repartidor asignado (registro en `control_entrega`).
# Muestra:
# - ID del pedido, fecha y estado
# - Repartidor asignado (id, nombre, teléfono)
# - Fecha de asignación
# - Confirmación de entrega (True / False)
# Retorna una lista consolidada de entregas en curso o finalizadas.
@router.get("/asignados")
def listar_pedidos_asignados(db: Session = Depends(get_db)):
    asignaciones = (
        db.query(ControlEntrega)
        .options(
            joinedload(ControlEntrega.pedido),
            joinedload(ControlEntrega.repartidor),
        )
        .all()
    )
    if not asignaciones:
        return {"mensaje": "No hay pedidos asignados actualmente."}
    resultado = []
    for ctrl in asignaciones:
        pedido = ctrl.pedido
        repartidor = ctrl.repartidor
        resultado.append({
            "pedido_id": str(pedido.id) if pedido else None,
            "fecha_pedido": pedido.fecha.isoformat() if pedido else None,
            "estado_pedido": pedido.estado if pedido else None,
            "total": float(pedido.total) if pedido else None,
            "repartidor": {
                "id": str(repartidor.id) if repartidor else None,
                "nombre": repartidor.nombre if repartidor else None,
                "telefono": repartidor.telefono if repartidor else None,
            },
            "fecha_asignacion": ctrl.fecha_entrega.isoformat(),
            "confirmacion_entrega": bool(ctrl.confirmacion_entrega),
        })
    return {"total": len(resultado), "asignaciones": resultado}


# ---------------------------------------------------------------------------
# GET /admin/pedidos/especializados
# ---------------------------------------------------------------------------
# Lista todos los pedidos especializados del sistema.
# Incluye:
# - ID, fecha y estado del pedido
# - Cliente asociado (nombre y contacto)
# - Mascota vinculada (nombre, especie)
# - Indicador de consulta con nutricionista
# - Frecuencia y estado del registro especializado
# Permite al administrador revisar qué pedidos están en evaluación o seguimiento nutricional.
@router.get("/especializados")
def listar_pedidos_especializados_admin(db: Session = Depends(get_db)):
    especializados = (
        db.query(PedidoEspecializado)
        .options(
            joinedload(PedidoEspecializado.pedido)
            .joinedload(Pedido.cliente),
            joinedload(PedidoEspecializado.registro_mascota),
        )
        .all()
    )
    if not especializados:
        return {"mensaje": "No se encontraron pedidos especializados."}
    resultado = []
    for esp in especializados:
        pedido = esp.pedido
        cliente = pedido.cliente if pedido else None
        mascota = esp.registro_mascota
        resultado.append({
            "pedido_id": str(pedido.id) if pedido else None,
            "fecha": pedido.fecha.isoformat() if pedido else None,
            "estado_pedido": pedido.estado if pedido else None,
            "cliente": {
                "id": str(cliente.id) if cliente else None,
                "nombre": cliente.nombre if cliente else None,
                "telefono": cliente.telefono if cliente else None,
            } if cliente else None,
            "mascota": {
                "id": str(mascota.id) if mascota else None,
                "nombre": mascota.nombre if mascota else None,
                "especie": mascota.especie.nombre if mascota.especie else None,
            } if mascota else None,
            "consulta_nutricionista": bool(esp.consulta_nutricionista),
            "frecuencia_cantidad": esp.frecuencia_cantidad,
            "estado_registro": esp.estado_registro,
        })
    return {"total": len(resultado), "pedidos_especializados": resultado}


# ---------------------------------------------------------------------------
# GET /admin/pedidos/{pedido_id}/entrega
# ---------------------------------------------------------------------------
# Muestra la información de control de entrega asociada a un pedido.
# Incluye:
# - ID, fecha y estado del pedido
# - Repartidor asignado (nombre, contacto)
# - Fecha de asignación de entrega
# - Confirmación de entrega (True / False)
# Si el pedido no tiene registro en `control_entrega`, devuelve error 404.
@router.get("/{pedido_id}/entrega")
def obtener_control_entrega(pedido_id: str, db: Session = Depends(get_db)):
    control = (
        db.query(ControlEntrega)
        .options(
            joinedload(ControlEntrega.repartidor),
            joinedload(ControlEntrega.pedido),
        )
        .filter(ControlEntrega.pedido_id == pedido_id)
        .first()
    )
    if not control:
        raise HTTPException(status_code=404, detail="No se encontró información de entrega para este pedido.")
    pedido = control.pedido
    repartidor = control.repartidor
    respuesta = {
        "pedido": {
            "id": str(pedido.id) if pedido else None,
            "fecha": pedido.fecha.isoformat() if pedido else None,
            "estado": pedido.estado if pedido else None,
        } if pedido else None,
        "repartidor": {
            "id": str(repartidor.id) if repartidor else None,
            "nombre": repartidor.nombre if repartidor else None,
            "telefono": repartidor.telefono if repartidor else None,
        } if repartidor else None,
        "control_entrega": {
            "id": str(control.id),
            "fecha_asignacion": control.fecha_entrega.isoformat(),
            "confirmacion_entrega": bool(control.confirmacion_entrega),
        },
    }
    return respuesta