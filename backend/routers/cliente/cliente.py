"""
RUTAS DEL CLIENTE – PERFIL Y DATOS PERSONALES
----------------------------------------------
Módulo que gestiona toda la información relacionada al cliente:
- Perfil personal y actualización de datos.
- Consulta de membresía activa (subscripción).
- Gestión de direcciones de entrega (CRUD).
- Manejo de imágenes de perfil.

Notas:
- Los IDs se envían y devuelven como `str` (compatibles con BIGINT).
- Las claves nuevas se generan con utils.keygen.generate_uint64_key().
- Las imágenes se almacenan en utils.globals.CLIENTE (default.png si no hay personalizada).
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from utils import keygen, globals
from sqlalchemy.orm import joinedload, Session
from utils.db import get_db
from models import Cliente
import os
router = APIRouter(prefix="/cliente", tags=["Cliente"])

# ---------------------------------------------------------------------------
# GET /cliente/{cliente_id}
# ---------------------------------------------------------------------------
# Retorna los datos completos del cliente:
# nombre, teléfono, correo, membresía activa, foto y direcciones registradas.
# ---------------------------------------------------------------------------
# GET /cliente/{cliente_id}
# ---------------------------------------------------------------------------
@router.get("/id/{cliente_id}")
def obtener_perfil_cliente(cliente_id: str, db: Session = Depends(get_db)):
    cliente = (
        db.query(Cliente)
        .options(
            joinedload(Cliente.cuenta_usuario),
            joinedload(Cliente.membresia_subscripcion),
            joinedload(Cliente.direccion)
        )
        .filter(Cliente.id == cliente_id, Cliente.estado_registro == "A")
        .first()
    )

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    cuenta = cliente.cuenta_usuario
    membresia = cliente.membresia_subscripcion
    foto_path = cliente.foto or os.path.join(globals.CLIENTE, "default.png")

    direcciones = [
        {
            "id": str(d.id),
            "nombre": d.nombre,
            "referencia": d.referencia,
            "latitud": float(d.latitud),
            "longitud": float(d.longitud),
            "es_principal": bool(d.es_principal),
        }
        for d in cliente.direccion if d.estado_registro == "A"
    ]

    return {
        "id": str(cliente.id),
        "nombre": cliente.nombre,
        "telefono": cliente.telefono,
        "correo": cuenta.correo_electronico if cuenta else None,
        "foto": foto_path,
        "membresia_activa": {
            "id": str(membresia.id),
            "nombre": membresia.nombre,
            "duracion": membresia.duracion,
            "precio": float(membresia.precio),
        } if membresia else None,
        "direcciones": direcciones,
    }


# ---------------------------------------------------------------------------
# PUT /cliente/{cliente_id}
# ---------------------------------------------------------------------------
# Actualiza los datos del cliente: nombre, teléfono, correo (opcional), foto.
# Si no se sube imagen nueva, mantiene o asigna CLIENTE/default.png.
@router.put("/{cliente_id}")
def actualizar_datos_cliente(
    cliente_id: str,
    nombre: str = Form(...),
    telefono: str = Form(...),
    correo: str = Form(None),
    foto: UploadFile | None = None,
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    cliente.nombre = nombre
    cliente.telefono = telefono

    # Actualizar correo en CuentaUsuario
    if correo and cliente.cuenta_usuario:
        cliente.cuenta_usuario.correo_electronico = correo

    uploads_dir = globals.CLIENTE
    os.makedirs(uploads_dir, exist_ok=True)

    if foto:
        filename = f"cliente_{cliente_id}_{foto.filename}"
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "wb") as f:
            f.write(foto.file.read())
        cliente.foto = file_path
    else:
        if not cliente.foto:
            cliente.foto = os.path.join(uploads_dir, "default.png")

    db.commit()
    db.refresh(cliente)

    return {
        "mensaje": "Datos del cliente actualizados correctamente.",
        "cliente": {
            "id": str(cliente.id),
            "nombre": cliente.nombre,
            "telefono": cliente.telefono,
            "correo": cliente.cuenta_usuario.correo_electronico if cliente.cuenta_usuario else None,
            "foto": cliente.foto,
        },
    }


@router.get("/{cliente_id}/membresia")
def obtener_membresia_cliente(cliente_id: str, db: Session = Depends(get_db)):
    cliente = (
        db.query(Cliente)
        .options(joinedload(Cliente.membresia_subscripcion))
        .filter(Cliente.id == cliente_id)
        .first()
    )
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    membresia = cliente.membresia_subscripcion
    if not membresia:
        return {"mensaje": "El cliente no tiene membresía activa."}

    return {
        "id": str(membresia.id),
        "nombre": membresia.nombre,
        "duracion_dias": membresia.duracion,
        "precio": float(membresia.precio),
        "descripcion": membresia.descripcion,
        "beneficios": membresia.beneficios,
    }
# ---------------------------------------------------------------------------
# CRUD de Direcciones
# ---------------------------------------------------------------------------
@router.post("/{cliente_id}/direccion")
def crear_direccion(
    cliente_id: str,
    nombre: str = Form(...),
    latitud: float = Form(...),
    longitud: float = Form(...),
    referencia: str = Form(None),
    es_principal: bool = Form(False),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")

    if es_principal:
        db.query(Direccion).filter(Direccion.cliente_id == cliente_id).update({"es_principal": False})

    direccion = Direccion(
        id=keygen.generate_uint64_key(),
        cliente_id=cliente_id,
        nombre=nombre,
        latitud=latitud,
        longitud=longitud,
        referencia=referencia,
        es_principal=es_principal,
        estado_registro="A",
    )
    db.add(direccion)
    db.commit()
    return {"mensaje": "Dirección creada correctamente.", "direccion_id": str(direccion.id)}

# ---------------------------------------------------------------------------
# POST /cliente/{cliente_id}/direccion
# ---------------------------------------------------------------------------
# Registra una nueva dirección de entrega.
# Se genera un id nuevo con keygen y se asocia al cliente.
# Campos: nombre, latitud, longitud, referencia, es_principal (bool).
@router.post("/{cliente_id}/direccion")
def crear_direccion(
    cliente_id: str,
    nombre: str = Form(...),
    latitud: float = Form(...),
    longitud: float = Form(...),
    referencia: str = Form(None),
    es_principal: bool = Form(False),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    if es_principal:
        db.query(Direccion).filter(Direccion.cliente_id == cliente_id).update({"es_principal": False})
    direccion_id = keygen.generate_uint64_key()
    direccion = Direccion(
        id=direccion_id,
        cliente_id=cliente_id,
        nombre=nombre,
        latitud=latitud,
        longitud=longitud,
        referencia=referencia,
        es_principal=es_principal,
        estado_registro="A",
    )
    db.add(direccion)
    db.commit()
    return {
        "mensaje": "Dirección registrada correctamente.",
        "direccion": {
            "id": str(direccion.id),
            "nombre": direccion.nombre,
            "latitud": direccion.latitud,
            "longitud": direccion.longitud,
            "referencia": direccion.referencia,
            "es_principal": direccion.es_principal,
        },
    }

# ---------------------------------------------------------------------------
# GET /cliente/{cliente_id}/direcciones
# ---------------------------------------------------------------------------
# Lista todas las direcciones del cliente.
# Incluye cuál está marcada como principal.
@router.get("/{cliente_id}/direcciones")
def listar_direcciones(
    cliente_id: str,
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    direcciones = (
        db.query(Direccion)
        .filter(Direccion.cliente_id == cliente_id, Direccion.estado_registro == "A")
        .order_by(Direccion.es_principal.desc())
        .all()
    )
    if not direcciones:
        return {"mensaje": "El cliente no tiene direcciones registradas."}
    resultado = [
        {
            "id": str(d.id),
            "nombre": d.nombre,
            "latitud": float(d.latitud),
            "longitud": float(d.longitud),
            "referencia": d.referencia,
            "es_principal": bool(d.es_principal),
        }
        for d in direcciones
    ]
    return {"total": len(resultado), "direcciones": resultado}

# ---------------------------------------------------------------------------
# PUT /cliente/direccion/{direccion_id}
# ---------------------------------------------------------------------------
# Actualiza los datos de una dirección existente.
# Permite cambiar nombre, referencia, coordenadas o marcarla como principal.
@router.put("/direccion/{direccion_id}")
def actualizar_direccion(
    direccion_id: str,
    nombre: str = Form(None),
    latitud: float = Form(None),
    longitud: float = Form(None),
    referencia: str = Form(None),
    es_principal: bool = Form(None),
    db: Session = Depends(get_db),
):
    direccion = db.query(Direccion).filter(Direccion.id == direccion_id, Direccion.estado_registro == "A").first()
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada o inactiva.")
    if nombre:
        direccion.nombre = nombre
    if referencia:
        direccion.referencia = referencia
    if latitud is not None:
        direccion.latitud = latitud
    if longitud is not None:
        direccion.longitud = longitud
    if es_principal is not None:
        if es_principal:
            db.query(Direccion).filter(
                Direccion.cliente_id == direccion.cliente_id,
                Direccion.id != direccion_id
            ).update({"es_principal": False})
        direccion.es_principal = es_principal

    db.commit()
    return {
        "mensaje": "Dirección actualizada correctamente.",
        "direccion": {
            "id": str(direccion.id),
            "nombre": direccion.nombre,
            "latitud": direccion.latitud,
            "longitud": direccion.longitud,
            "referencia": direccion.referencia,
            "es_principal": direccion.es_principal,
        },
    }

# ---------------------------------------------------------------------------
# DELETE /cliente/direccion/{direccion_id}
# ---------------------------------------------------------------------------
# Elimina (o marca inactiva) una dirección del cliente.
# Si era la principal, se reasigna automáticamente otra si existe.
@router.delete("/direccion/{direccion_id}")
def eliminar_direccion(
    direccion_id: str,
    db: Session = Depends(get_db),
):
    direccion = db.query(Direccion).filter(Direccion.id == direccion_id, Direccion.estado_registro == "A").first()
    if not direccion:
        raise HTTPException(status_code=404, detail="Dirección no encontrada o ya inactiva.")
    cliente_id = direccion.cliente_id
    era_principal = direccion.es_principal
    direccion.estado_registro = "I"
    direccion.es_principal = False
    db.commit()
    if era_principal:
        nueva_principal = (
            db.query(Direccion)
            .filter(Direccion.cliente_id == cliente_id, Direccion.estado_registro == "A")
            .order_by(Direccion.id.desc())
            .first()
        )
        if nueva_principal:
            nueva_principal.es_principal = True
            db.commit()
            return {
                "mensaje": "Dirección eliminada. Se ha reasignado una nueva dirección principal.",
                "nueva_principal": {
                    "id": str(nueva_principal.id),
                    "nombre": nueva_principal.nombre,
                    "referencia": nueva_principal.referencia,
                    "latitud": nueva_principal.latitud,
                    "longitud": nueva_principal.longitud,
                },
            }
    return {"mensaje": "Dirección eliminada correctamente."}