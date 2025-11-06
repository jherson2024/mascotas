"""
RUTAS DEL ADMINISTRADOR – GESTIÓN DE REPARTIDORES
---------------------------------------------------
Permite al administrador crear y administrar las cuentas de repartidores,
asignarles pedidos y controlar su estado de registro.
Incluye:
- Creación de cuentas de repartidor
- Consulta general de repartidores activos/inactivos
- Actualización de datos (nombre, teléfono, estado)
- Desactivación de cuentas
- Visualización de pedidos asignados a cada repartidor
Notas:
- IDs en formato `str` (por BIGINT).
- Claves generadas con utils.keygen.generate_uint64_key().
- Solo accesible por administradores.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session, joinedload
from utils import keygen
from utils.db import get_db
from models import CuentaUsuario, Repartidor, UsuarioRol, Rol
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/admin/repartidores", tags=["Repartidores (Administrador)"])

# ---------------------------------------------------------------------------
# POST /admin/repartidores
# ---------------------------------------------------------------------------
# Crea una nueva cuenta de repartidor.
# Campos requeridos:
# - nombre (str): nombre completo del repartidor.
# - telefono (str): número de contacto.
# - correo (EmailStr): correo electrónico para su cuenta.
# - contrasena (str): contraseña inicial.
# Opcional:
# - estado_registro (str): estado del registro (A=Activo, I=Inactivo). Default: 'A'
# Operaciones realizadas:
# 1. Verifica que el correo no esté en uso.
# 2. Crea una cuenta en `cuenta_usuario`.
# 3. Crea el registro de `repartidor`.
# 4. Asigna el rol de repartidor en `usuario_rol`.
# Retorna:
# - ID del repartidor creado y resumen de su cuenta.
@router.post("/")
def crear_repartidor(
    nombre: str = Query(..., description="Nombre completo del repartidor"),
    telefono: str = Query(..., description="Número de contacto del repartidor"),
    correo: EmailStr = Query(..., description="Correo electrónico del repartidor"),
    contrasena: str = Query(..., description="Contraseña inicial del repartidor"),
    estado_registro: Optional[str] = Query("A", description="Estado del registro (A=Activo, I=Inactivo)"),
    db: Session = Depends(get_db),
):
    correo_existente = db.query(CuentaUsuario).filter(
        CuentaUsuario.correo_electronico == correo
    ).first()
    if correo_existente:
        raise HTTPException(status_code=400, detail="El correo electrónico ya está registrado.")
    cuenta_id = keygen.generate_uint64_key()
    cuenta = CuentaUsuario(
        id=cuenta_id,
        correo_electronico=correo,
        contrasena=contrasena,
        nombre_usuario=nombre,
        estado_registro=estado_registro,
        ultimo_acceso=None
    )
    db.add(cuenta)
    db.flush()  
    repartidor_id = keygen.generate_uint64_key()
    repartidor = Repartidor(
        id=repartidor_id,
        cuenta_usuario_id=cuenta_id,
        nombre=nombre,
        telefono=telefono,
        estado_registro=estado_registro
    )
    db.add(repartidor)
    rol_repartidor = db.query(Rol).filter(Rol.nombre == "repartidor").first()
    if not rol_repartidor:
        raise HTTPException(status_code=404, detail="Rol 'repartidor' no definido en la base de datos.")
    usuario_rol = UsuarioRol(
        id=keygen.generate_uint64_key(),
        cuenta_usuario_id=cuenta_id,
        rol_id=rol_repartidor.id,
        estado_registro="A"
    )
    db.add(usuario_rol)
    db.commit()
    return {
        "mensaje": "Repartidor creado exitosamente.",
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
            "estado_registro": repartidor.estado_registro,
        },
        "cuenta_usuario": {
            "id": str(cuenta.id),
            "correo": cuenta.correo_electronico,
            "nombre_usuario": cuenta.nombre_usuario,
        },
    }

# ---------------------------------------------------------------------------
# GET /admin/repartidores
# ---------------------------------------------------------------------------
# Lista todos los repartidores registrados (activos o inactivos).
# Permite filtrar por estado_registro (A/I) o nombre parcial.
# Ejemplo de uso:
#   /admin/repartidores?estado=A
#   /admin/repartidores?nombre=juan
# Retorna una lista con los repartidores y su información básica.
@router.get("/")
def listar_repartidores(
    estado: Optional[str] = Query(None, description="Filtrar por estado del registro (A=activo, I=inactivo)"),
    nombre: Optional[str] = Query(None, description="Filtrar por coincidencia parcial en nombre"),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Repartidor)
        .join(Repartidor.cuenta_usuario)
        .options(
            joinedload(Repartidor.cuenta_usuario)
        )
    )
    if estado:
        if estado not in ["A", "I"]:
            raise HTTPException(status_code=400, detail="El estado debe ser 'A' (activo) o 'I' (inactivo).")
        query = query.filter(Repartidor.estado_registro == estado)
    if nombre:
        query = query.filter(Repartidor.nombre.ilike(f"%{nombre}%"))
    repartidores = query.order_by(Repartidor.nombre.asc()).all()
    if not repartidores:
        return {"mensaje": "No se encontraron repartidores con los filtros aplicados."}
    resultado = []
    for r in repartidores:
        cuenta = r.cuenta_usuario
        resultado.append({
            "id": str(r.id),
            "nombre": r.nombre,
            "telefono": r.telefono,
            "estado_registro": r.estado_registro,
            "correo": cuenta.correo_electronico if cuenta else None,
            "ultimo_acceso": cuenta.ultimo_acceso.isoformat() if cuenta and cuenta.ultimo_acceso else None,
        })
    return {"total": len(resultado), "repartidores": resultado}


# ---------------------------------------------------------------------------
# GET /admin/repartidores/{repartidor_id}
# ---------------------------------------------------------------------------
# Obtiene la información completa de un repartidor:
# - Datos personales (nombre, teléfono, estado)
# - Cuenta asociada (correo, último acceso)
# - Pedidos asignados (control_entrega)
# Si no existe el repartidor, retorna error 404.
from sqlalchemy.orm import joinedload
@router.get("/{repartidor_id}")
def obtener_detalle_repartidor(
    repartidor_id: str,
    db: Session = Depends(get_db),
):
    repartidor = (
        db.query(Repartidor)
        .options(
            joinedload(Repartidor.cuenta_usuario),
            joinedload(Repartidor.control_entrega)
            .joinedload(ControlEntrega.pedido)
            .joinedload(Pedido.cliente)
        )
        .filter(Repartidor.id == repartidor_id)
        .first()
    )
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    cuenta = repartidor.cuenta_usuario
    cuenta_info = None
    if cuenta:
        cuenta_info = {
            "id": str(cuenta.id),
            "correo": cuenta.correo_electronico,
            "ultimo_acceso": cuenta.ultimo_acceso.isoformat() if cuenta.ultimo_acceso else None,
            "estado_registro": cuenta.estado_registro,
        }
    pedidos_info = []
    for c in repartidor.control_entrega:
        pedido = c.pedido
        cliente = pedido.cliente if pedido else None
        pedidos_info.append({
            "pedido_id": str(pedido.id) if pedido else None,
            "fecha_pedido": pedido.fecha.isoformat() if pedido else None,
            "estado_pedido": pedido.estado if pedido else None,
            "confirmacion_entrega": bool(c.confirmacion_entrega),
            "cliente": {
                "id": str(cliente.id) if cliente else None,
                "nombre": cliente.nombre if cliente else None,
                "telefono": cliente.telefono if cliente else None,
            } if cliente else None,
        })
    respuesta = {
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
            "estado_registro": repartidor.estado_registro,
        },
        "cuenta_usuario": cuenta_info,
        "pedidos_asignados": pedidos_info,
        "total_pedidos_asignados": len(pedidos_info),
    }
    return respuesta


# ---------------------------------------------------------------------------
# PUT /admin/repartidores/{repartidor_id}
# ---------------------------------------------------------------------------
# Actualiza los datos de un repartidor:
# - nombre
# - teléfono
# - estado_registro (A=activo, I=inactivo)
# Si no se encuentra el repartidor, devuelve error 404.
# Si no se especifica ningún campo válido, devuelve error 400.
@router.put("/{repartidor_id}")
def actualizar_repartidor(
    repartidor_id: str,
    nombre: Optional[str] = Body(None, description="Nuevo nombre del repartidor"),
    telefono: Optional[str] = Body(None, description="Nuevo número de teléfono"),
    estado_registro: Optional[str] = Body(None, description="Nuevo estado del registro (A/I)"),
    db: Session = Depends(get_db),
):
    repartidor = (
        db.query(Repartidor)
        .options(joinedload(Repartidor.cuenta_usuario))
        .filter(Repartidor.id == repartidor_id)
        .first()
    )
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    if not any([nombre, telefono, estado_registro]):
        raise HTTPException(status_code=400, detail="Debe especificar al menos un campo para actualizar.")
    if estado_registro and estado_registro not in ["A", "I"]:
        raise HTTPException(status_code=400, detail="El estado_registro debe ser 'A' (activo) o 'I' (inactivo).")
    if nombre:
        repartidor.nombre = nombre
        if repartidor.cuenta_usuario:
            repartidor.cuenta_usuario.nombre_usuario = nombre  # sincroniza también en la cuenta
    if telefono:
        repartidor.telefono = telefono
    if estado_registro:
        repartidor.estado_registro = estado_registro
        if repartidor.cuenta_usuario:
            repartidor.cuenta_usuario.estado_registro = estado_registro

    db.commit()
    db.refresh(repartidor)
    return {
        "mensaje": "Datos del repartidor actualizados correctamente.",
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
            "estado_registro": repartidor.estado_registro,
        },
        "cuenta_usuario": {
            "id": str(repartidor.cuenta_usuario.id) if repartidor.cuenta_usuario else None,
            "correo": repartidor.cuenta_usuario.correo_electronico if repartidor.cuenta_usuario else None,
            "estado_registro": repartidor.cuenta_usuario.estado_registro if repartidor.cuenta_usuario else None,
        } if repartidor.cuenta_usuario else None,
    }

# ---------------------------------------------------------------------------
# PUT /admin/repartidores/{repartidor_id}/estado
# ---------------------------------------------------------------------------
# Activa o desactiva una cuenta de repartidor.
# Cambia el campo `estado_registro` (A = activo, I = inactivo)
# tanto en la tabla `repartidor` como en la `cuenta_usuario`.
@router.put("/{repartidor_id}/estado")
def cambiar_estado_repartidor(
    repartidor_id: str,
    nuevo_estado: str = Body(..., description="Nuevo estado del registro (A=activo, I=inactivo)"),
    db: Session = Depends(get_db),
):
    repartidor = (
        db.query(Repartidor)
        .options(joinedload(Repartidor.cuenta_usuario))
        .filter(Repartidor.id == repartidor_id)
        .first()
    )
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    if nuevo_estado not in ["A", "I"]:
        raise HTTPException(status_code=400, detail="El estado debe ser 'A' (activo) o 'I' (inactivo).")
    if repartidor.estado_registro == nuevo_estado:
        return {
            "mensaje": f"El repartidor ya se encuentra en estado '{nuevo_estado}'.",
            "repartidor": {
                "id": str(repartidor.id),
                "nombre": repartidor.nombre,
                "telefono": repartidor.telefono,
                "estado_registro": repartidor.estado_registro,
            },
        }
    repartidor.estado_registro = nuevo_estado
    if repartidor.cuenta_usuario:
        repartidor.cuenta_usuario.estado_registro = nuevo_estado
    db.commit()
    db.refresh(repartidor)
    estado_texto = "activado" if nuevo_estado == "A" else "desactivado"
    return {
        "mensaje": f"Repartidor {estado_texto} correctamente.",
        "repartidor": {
            "id": str(repartidor.id),
            "nombre": repartidor.nombre,
            "telefono": repartidor.telefono,
            "estado_registro": repartidor.estado_registro,
        },
        "cuenta_usuario": {
            "id": str(repartidor.cuenta_usuario.id) if repartidor.cuenta_usuario else None,
            "correo": repartidor.cuenta_usuario.correo_electronico if repartidor.cuenta_usuario else None,
            "estado_registro": repartidor.cuenta_usuario.estado_registro if repartidor.cuenta_usuario else None,
        } if repartidor.cuenta_usuario else None,
    }

# ---------------------------------------------------------------------------
# GET /admin/repartidores/{repartidor_id}/pedidos
# ---------------------------------------------------------------------------
# Lista los pedidos asignados a un repartidor específico.
# Incluye:
# - ID del pedido
# - Fecha y estado del pedido
# - Total
# - Confirmación de entrega
# - Cliente asociado (nombre, teléfono)
# Si el repartidor no existe o no tiene pedidos asignados, retorna 404 o mensaje vacío.
from sqlalchemy.orm import joinedload
@router.get("/{repartidor_id}/pedidos")
def listar_pedidos_repartidor(
    repartidor_id: str,
    db: Session = Depends(get_db),
):
    repartidor = db.query(Repartidor).filter(Repartidor.id == repartidor_id).first()
    if not repartidor:
        raise HTTPException(status_code=404, detail="Repartidor no encontrado.")
    entregas = (
        db.query(ControlEntrega)
        .options(
            joinedload(ControlEntrega.pedido).joinedload(Pedido.cliente)
        )
        .filter(ControlEntrega.repartidor_id == repartidor_id)
        .order_by(Pedido.fecha.desc())
        .all()
    )
    if not entregas:
        return {"mensaje": "El repartidor no tiene pedidos asignados actualmente."}
    resultado = []
    for ctrl in entregas:
        pedido = ctrl.pedido
        cliente = pedido.cliente if pedido else None
        resultado.append({
            "pedido_id": str(pedido.id) if pedido else None,
            "fecha_pedido": pedido.fecha.isoformat() if pedido else None,
            "estado_pedido": pedido.estado if pedido else None,
            "total": float(pedido.total) if pedido else None,
            "confirmacion_entrega": bool(ctrl.confirmacion_entrega),
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
            "estado_registro": repartidor.estado_registro,
        },
        "total_pedidos": len(resultado),
        "pedidos": resultado,
    }