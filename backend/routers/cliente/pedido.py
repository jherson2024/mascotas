"""
RUTAS DEL CLIENTE – PEDIDOS Y PEDIDOS ESPECIALIZADOS
-----------------------------------------------------
Este módulo gestiona todo el flujo de pedidos del cliente, incluyendo la
creación de pedidos normales y especializados, consulta de historial y
confirmación de entrega.
Incluye:
- Creación de pedidos normales (desde el carrito de compras).
- Creación y seguimiento de pedidos especializados (con revisión del nutricionista).
- Consulta de historial y detalles de pedidos.
- Confirmación de recepción de pedido.
- Generación y visualización del código QR asociado al pedido.
Notas:
- Todos los IDs se manejan como `str` (por uso de BIGINT en la base de datos).
- Las claves se generan con `utils.keygen.generate_uint64_key()`.
- Los QR se almacenan y sirven desde `utils.globals.QR`.
- Las rutas requieren validación del cliente correspondiente.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Body, Form, UploadFile, File, Query
from datetime import datetime
from utils import keygen, globals
from sqlalchemy.orm import joinedload, Session
from utils.db import get_db
import os, json 
from typing import Optional

router = APIRouter(prefix="/cliente/pedido", tags=["Pedidos del Cliente"])

# ---------------------------------------------------------------------------
# POST /cliente/pedido/{cliente_id}
# ---------------------------------------------------------------------------
# Crea un nuevo pedido normal a partir del carrito del cliente.
# Incluye dirección, lista de platos y total.
# Retorna el ID del pedido generado.
@router.post("/{cliente_id}")
def crear_pedido(
    cliente_id: str,
    data: dict = Body(..., description="Datos del pedido: dirección, platos y total"),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    direccion_id = data.get("direccion_id")
    platos = data.get("platos", [])
    total = data.get("total")
    if not direccion_id:
        raise HTTPException(status_code=400, detail="Debe especificar una dirección de entrega.")
    if not platos or len(platos) == 0:
        raise HTTPException(status_code=400, detail="Debe incluir al menos un plato en el pedido.")
    if not total or total <= 0:
        raise HTTPException(status_code=400, detail="El total del pedido debe ser mayor que 0.")
    direccion = (
        db.query(Direccion)
        .filter(Direccion.id == direccion_id, Direccion.cliente_id == cliente_id)
        .first()
    )
    if not direccion:
        raise HTTPException(status_code=400, detail="La dirección no pertenece al cliente o no existe.")
    pedido_id = keygen.generate_uint64_key()
    pedido = Pedido(
        id=pedido_id,
        cliente_id=cliente_id,
        direccion_id=direccion_id,
        fecha=datetime.now(),
        total=total,
        estado="pendiente",
        incluye_plato=True,
    )
    db.add(pedido)
    for item in platos:
        det = DetallePedido(
            id=keygen.generate_uint64_key(),
            pedido_id=pedido_id,
            plato_id=item["plato_id"],
            cantidad=item["cantidad"],
            subtotal=item["cantidad"] * db.query(Plato).get(item["plato_id"]).precio,
        )
        db.add(det)
    db.commit()
    return {
        "mensaje": "Pedido creado exitosamente.",
        "pedido_id": str(pedido_id),
        "estado": pedido.estado,
        "total": float(pedido.total),
        "fecha": pedido.fecha.isoformat(),
    }

# ---------------------------------------------------------------------------
# GET /cliente/pedido/{cliente_id}/historial
# ---------------------------------------------------------------------------
# Lista todos los pedidos realizados por el cliente.
# Incluye estado, fecha, total y si tiene pedido especializado asociado.
@router.get("/{cliente_id}/historial")
def listar_pedidos_cliente(
    cliente_id: str,
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    pedidos = (
        db.query(Pedido)
        .options(joinedload(Pedido.pedido_especializado))
        .filter(Pedido.cliente_id == cliente_id)
        .order_by(Pedido.fecha.desc())
        .all()
    )
    if not pedidos:
        return {"mensaje": "El cliente no tiene pedidos registrados."}
    resultado = []
    for p in pedidos:
        resultado.append({
            "pedido_id": str(p.id),
            "fecha": p.fecha.isoformat(),
            "estado": p.estado,
            "total": float(p.total),
            "especializado": bool(p.pedido_especializado),
        })
    return {"total": len(resultado), "pedidos": resultado}

# ---------------------------------------------------------------------------
# GET /cliente/pedido/detalle/{pedido_id}
# ---------------------------------------------------------------------------
# Devuelve los detalles del pedido:
# platos, cantidades, subtotal, dirección y estado actual.
@router.get("/detalle/{pedido_id}")
def obtener_detalle_pedido(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    pedido = (
        db.query(Pedido)
        .options(
            joinedload(Pedido.detalle_pedido).joinedload(DetallePedido.plato_combinado),
            joinedload(Pedido.direccion),
            joinedload(Pedido.cliente),
        )
        .filter(Pedido.id == pedido_id)
        .first()
    )
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    direccion = pedido.direccion
    cliente = pedido.cliente
    platos = [
        {
            "plato": det.plato_combinado.nombre if det.plato_combinado else None,
            "cantidad": det.cantidad,
            "subtotal": float(det.subtotal),
        }
        for det in pedido.detalle_pedido
    ]
    return {
        "pedido": {
            "id": str(pedido.id),
            "fecha": pedido.fecha.isoformat(),
            "estado": pedido.estado,
            "total": float(pedido.total),
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
        "platos": platos,
    }

# ---------------------------------------------------------------------------
# POST /cliente/pedido/{pedido_id}/recibido
# ---------------------------------------------------------------------------
# Marca un pedido como recibido por el cliente.
# Actualiza el estado del pedido y la confirmación de entrega.
@router.post("/{pedido_id}/recibido")
def marcar_pedido_recibido(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    pedido = db.query(Pedido).filter(Pedido.id == pedido_id).first()
    if not pedido:
        raise HTTPException(status_code=404, detail="Pedido no encontrado.")
    control = db.query(ControlEntrega).filter(ControlEntrega.pedido_id == pedido_id).first()
    if not control:
        raise HTTPException(status_code=404, detail="El pedido no tiene registro de entrega asignado.")
    if pedido.estado == "entregado" and control.confirmacion_entrega == 1:
        return {"mensaje": "El pedido ya fue confirmado como recibido."}
    pedido.estado = "entregado"
    control.confirmacion_entrega = 1
    control.fecha_entrega = datetime.now()
    db.commit()
    return {
        "mensaje": "El pedido ha sido confirmado como recibido.",
        "pedido": {
            "id": str(pedido.id),
            "estado": pedido.estado,
            "fecha_confirmacion": control.fecha_entrega.isoformat(),
            "confirmacion_entrega": True
        },
    }

# ---------------------------------------------------------------------------
# GET /cliente/pedido/{pedido_id}/qr
# ---------------------------------------------------------------------------
# Devuelve la URL o archivo del QR correspondiente al pedido.
# Si no existe, genera uno en utils.globals.QR y lo guarda.
@router.get("/{pedido_id}/qr")
def obtener_qr_pedido(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    return {"message": f"QR de pedido {pedido_id} en construcción"}

# ---------------------------------------------------------------------------
# POST /cliente/pedido-especializado/{cliente_id}
# ---------------------------------------------------------------------------
# Crea un pedido especializado vinculado a una mascota e inserta:
# - Pedido + PedidoEspecializado
# - (opcional) Receta médica (PDF/imagen)
# - (opcional) Varias alergias (AlergiaMascota)
# - (opcional) Una descripción libre de alergias (DescripcionAlergias)
# - (opcional) Varias condiciones de salud (CondicionSalud)
# - (opcional) Varias preferencias alimentarias (PreferenciaAlimentaria)
# - (opcional) Archivo adicional
@router.post("/especializado/{cliente_id}")
def crear_pedido_especializado(
    cliente_id: str,
    registro_mascota_id: str = Form(..., description="ID del registro de mascota"),
    frecuencia_cantidad: str = Form(..., description="Frecuencia y cantidad, p. ej. '2 veces/semana'"),
    objetivo_dieta: str = Form(..., description="Objetivo de la dieta"),
    indicaciones_adicionales: Optional[str] = Form(None, description="Indicaciones adicionales"),
    consulta_nutricionista: bool = Form(False, description="¿Requiere revisión de nutricionista?"),
    alergias_ids: Optional[str] = Form(None, description="JSON list de IDs de alergias de especie"),
    descripcion_alergias: Optional[str] = Form(None, description="Descripción libre de alergias"),
    condiciones_salud: Optional[str] = Form(None, description="JSON list de objetos {nombre, fecha?}"),
    preferencias_alimentarias: Optional[str] = Form(None, description="JSON list (strings u objetos {nombre, descripcion?})"),
    receta_medica: UploadFile | None = File(None),
    archivo_adicional: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    mascota = (
        db.query(RegistroMascota)
        .options(joinedload(RegistroMascota.especie))
        .filter(
            RegistroMascota.id == registro_mascota_id,
            RegistroMascota.cliente_id == cliente_id
        )
        .first()
    )
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o no pertenece al cliente.")
    if not frecuencia_cantidad or not objetivo_dieta:
        raise HTTPException(status_code=400, detail="Debe proporcionar 'frecuencia_cantidad' y 'objetivo_dieta'.")
    def parse_json_list(value: Optional[str], fallback_empty=True):
        if not value:
            return [] if fallback_empty else None
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            return [parsed]
        except Exception:
            raise HTTPException(status_code=400, detail="Formato JSON inválido en uno de los campos de lista.")
    alergias_list = parse_json_list(alergias_ids)  # lista de IDs (int/str)
    condiciones_list = parse_json_list(condiciones_salud)  # lista de objetos
    preferencias_list = parse_json_list(preferencias_alimentarias)  # lista (str u obj)
    pedido_id = keygen.generate_uint64_key()
    pedido = Pedido(
        id=pedido_id,
        cliente_id=cliente_id,
        fecha=datetime.now(),
        total=0,
        incluye_plato=False,
        estado="pendiente",
        direccion_id=None
    )
    db.add(pedido)
    db.flush()
    pedido_esp_id = keygen.generate_uint64_key()
    pedido_esp = PedidoEspecializado(
        id=pedido_esp_id,
        pedido_id=pedido_id,
        registro_mascota_id=registro_mascota_id,
        frecuencia_cantidad=frecuencia_cantidad,
        objetivo_dieta=objetivo_dieta,
        indicaciones_adicionales=indicaciones_adicionales,
        consulta_nutricionista=1 if consulta_nutricionista else 0,
        estado_registro="A",
    )
    db.add(pedido_esp)
    db.flush()
    uploads_dir = os.path.join("static", "uploads", "pedido_especializado")
    os.makedirs(uploads_dir, exist_ok=True)
    if archivo_adicional:
        extra_path = os.path.join(uploads_dir, f"extra_{pedido_esp_id}_{archivo_adicional.filename}")
        with open(extra_path, "wb") as f:
            f.write(archivo_adicional.file.read())
        pedido_esp.archivo_adicional = extra_path
    if receta_medica:
        receta_path = os.path.join(uploads_dir, f"receta_{pedido_esp_id}_{receta_medica.filename}")
        with open(receta_path, "wb") as f:
            f.write(receta_medica.file.read())
        receta = RecetaMedica(
            id=keygen.generate_uint64_key(),
            registro_mascota_id=registro_mascota_id,
            pedido_especializado_id=pedido_esp_id,
            fecha=datetime.now(),
            estado_registro="A",
            archivo=receta_path,
        )
        db.add(receta)
    for alergia_id in alergias_list:
        alergia_registro = AlergiaMascota(
            id=keygen.generate_uint64_key(),
            registro_mascota_id=registro_mascota_id,
            alergia_especie_id=int(alergia_id),
            severidad="moderada",
            estado_registro="A",
        )
        db.add(alergia_registro)
    if descripcion_alergias:
        desc = DescripcionAlergias(
            id=keygen.generate_uint64_key(),
            registro_mascota_id=registro_mascota_id,
            descripcion=descripcion_alergias,
            fecha=datetime.now(),
            estado_registro="A",
        )
        db.add(desc)
    for cond in condiciones_list:
        if isinstance(cond, dict):
            nombre = cond.get("nombre")
            fecha_txt = cond.get("fecha")
        else:
            nombre = str(cond)
            fecha_txt = None
        if not nombre:
            continue
        fecha_val = None
        if fecha_txt:
            try:
                fecha_val = datetime.fromisoformat(fecha_txt)
            except Exception:
                fecha_val = datetime.now()
        else:
            fecha_val = datetime.now()
        db.add(CondicionSalud(
            id=keygen.generate_uint64_key(),
            registro_mascota_id=registro_mascota_id,
            nombre=nombre,
            fecha=fecha_val,
            estado_registro="A",
        ))
    for pref in preferencias_list:
        if isinstance(pref, dict):
            nombre = pref.get("nombre")
            descripcion = pref.get("descripcion")
        else:
            nombre = str(pref)
            descripcion = None
        if not nombre:
            continue
        db.add(PreferenciaAlimentaria(
            id=keygen.generate_uint64_key(),
            registro_mascota_id=registro_mascota_id,
            nombre=nombre,
            estado_registro="A",
            descripcion=descripcion
        ))
    db.commit()
    return {
        "mensaje": "Pedido especializado creado exitosamente.",
        "pedido_id": str(pedido_id),
        "pedido_especializado_id": str(pedido_esp_id),
        "registro_mascota_id": str(registro_mascota_id),
        "consulta_nutricionista": bool(consulta_nutricionista),
        "resumen": {
            "alergias_registradas": len(alergias_list),
            "condiciones_salud_registradas": len(condiciones_list),
            "preferencias_alimentarias_registradas": len(preferencias_list),
            "descripcion_alergias_incluida": bool(descripcion_alergias),
            "receta_medica_adjunta": bool(receta_medica),
            "archivo_adicional_adjuntado": bool(archivo_adicional),
        }
    }

# ---------------------------------------------------------------------------
# GET /cliente/pedido-especializado/{cliente_id}
# ---------------------------------------------------------------------------
# Lista los pedidos especializados del cliente.
# Incluye estado, mascota asociada, objetivo, frecuencia y si requiere nutricionista.
@router.get("/especializado/{cliente_id}")
def listar_pedidos_especializados(
    cliente_id: str,
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    pedidos = (
        db.query(PedidoEspecializado)
        .join(Pedido)
        .join(RegistroMascota)
        .filter(Pedido.cliente_id == cliente_id)
        .options(
            joinedload(PedidoEspecializado.pedido),
            joinedload(PedidoEspecializado.registro_mascota),
        )
        .order_by(Pedido.fecha.desc())
        .all()
    )
    if not pedidos:
        return {"mensaje": "No se encontraron pedidos especializados para este cliente."}
    resultado = []
    for p in pedidos:
        resultado.append({
            "pedido_especializado_id": str(p.id),
            "pedido_id": str(p.pedido_id),
            "fecha": p.pedido.fecha.isoformat() if p.pedido else None,
            "estado_pedido": p.pedido.estado if p.pedido else None,
            "mascota": {
                "id": str(p.registro_mascota.id) if p.registro_mascota else None,
                "nombre": p.registro_mascota.nombre if p.registro_mascota else None,
                "especie": p.registro_mascota.especie.nombre if p.registro_mascota and p.registro_mascota.especie else None,
            } if p.registro_mascota else None,
            "frecuencia_cantidad": p.frecuencia_cantidad,
            "objetivo_dieta": p.objetivo_dieta,
            "consulta_nutricionista": bool(p.consulta_nutricionista),
            "estado_registro": p.estado_registro,
        })
    return {"total": len(resultado), "pedidos_especializados": resultado}

# ---------------------------------------------------------------------------
# GET /cliente/pedido-especializado/detalle/{pedido_id}
# ---------------------------------------------------------------------------
# Devuelve los datos detallados de un pedido especializado:
# mascota, alergias, condiciones, preferencias, objetivo dieta, archivos adjuntos.
@router.get("/especializado/detalle/{pedido_id}")
def obtener_detalle_pedido_especializado(
    pedido_id: str,
    db: Session = Depends(get_db),
):
    pedido_esp = (
        db.query(PedidoEspecializado)
        .options(
            joinedload(PedidoEspecializado.pedido).joinedload(Pedido.cliente),
            joinedload(PedidoEspecializado.registro_mascota)
                .joinedload(RegistroMascota.especie),
            joinedload(PedidoEspecializado.receta_medica),
        )
        .filter(PedidoEspecializado.pedido_id == pedido_id)
        .first()
    )
    if not pedido_esp:
        raise HTTPException(status_code=404, detail="Pedido especializado no encontrado.")
    pedido = pedido_esp.pedido
    mascota = pedido_esp.registro_mascota
    receta = pedido_esp.receta_medica[0] if pedido_esp.receta_medica else None
    alergias = db.query(AlergiaMascota).filter(AlergiaMascota.registro_mascota_id == mascota.id).all()
    condiciones = db.query(CondicionSalud).filter(CondicionSalud.registro_mascota_id == mascota.id).all()
    preferencias = db.query(PreferenciaAlimentaria).filter(PreferenciaAlimentaria.registro_mascota_id == mascota.id).all()
    descripcion = db.query(DescripcionAlergias).filter(DescripcionAlergias.registro_mascota_id == mascota.id).order_by(DescripcionAlergias.fecha.desc()).first()
    return {
        "pedido": {
            "id": str(pedido.id),
            "fecha": pedido.fecha.isoformat() if pedido.fecha else None,
            "estado": pedido.estado,
            "cliente": {
                "id": str(pedido.cliente.id) if pedido.cliente else None,
                "nombre": pedido.cliente.nombre if pedido.cliente else None,
                "telefono": pedido.cliente.telefono if pedido.cliente else None,
            } if pedido.cliente else None,
        },
        "pedido_especializado": {
            "id": str(pedido_esp.id),
            "frecuencia_cantidad": pedido_esp.frecuencia_cantidad,
            "objetivo_dieta": pedido_esp.objetivo_dieta,
            "indicaciones_adicionales": pedido_esp.indicaciones_adicionales,
            "consulta_nutricionista": bool(pedido_esp.consulta_nutricionista),
            "estado_registro": pedido_esp.estado_registro,
        },
        "mascota": {
            "id": str(mascota.id),
            "nombre": mascota.nombre,
            "especie": mascota.especie.nombre if mascota.especie else None,
            "edad": mascota.edad,
            "raza": mascota.raza,
            "peso": float(mascota.peso) if mascota.peso else None,
            "foto": mascota.foto,
        } if mascota else None,
        "detalles_nutricionales": {
            "alergias": [
                {
                    "id": str(a.id),
                    "alergia_especie_id": a.alergia_especie_id,
                    "severidad": a.severidad,
                } for a in alergias
            ],
            "descripcion_alergias": descripcion.descripcion if descripcion else None,
            "condiciones_salud": [
                {
                    "id": str(c.id),
                    "nombre": c.nombre,
                    "fecha": c.fecha.isoformat() if c.fecha else None,
                } for c in condiciones
            ],
            "preferencias_alimentarias": [
                {
                    "id": str(pf.id),
                    "nombre": pf.nombre,
                    "descripcion": pf.descripcion,
                } for pf in preferencias
            ],
        },
        "archivos": {
            "receta_medica": receta.archivo if receta else None,
            "archivo_adicional": pedido_esp.archivo_adicional,
        },
    }
