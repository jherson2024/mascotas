"""
RUTAS DEL CLIENTE – MASCOTAS
-----------------------------
Permite al cliente administrar el registro de sus mascotas y sus datos
vinculados: especie, alergias, condiciones de salud, recetas médicas, etc.

Incluye:
- Registro, edición y eliminación de mascotas
- Consulta de detalles individuales
- Gestión de alergias y condiciones de salud
- Subida de foto de mascota
- Visualización de recetas médicas vinculadas

Notas:
- IDs en formato `str` (por BIGINT).
- Fotos de mascotas se guardan en utils.globals.MASCOTA.
- Si no se proporciona foto, usar MASCOTA/perro.png o MASCOTA/gato.png
  según la especie; si no se sabe, usar default.png.
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, Form
from utils import globals
from utils.db import get_db
from sqlalchemy.orm import Session
router = APIRouter(prefix="/cliente/mascotas", tags=["Mascotas del Cliente"])

# ---------------------------------------------------------------------------
# GET /cliente/mascotas/{cliente_id}
# ---------------------------------------------------------------------------
# Lista todas las mascotas registradas por el cliente.
# Incluye especie, edad, peso y foto.
@router.get("/{cliente_id}")
def listar_mascotas_cliente(
    cliente_id: str,
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    mascotas = (
        db.query(RegistroMascota)
        .join(Especie)
        .filter(RegistroMascota.cliente_id == cliente_id, RegistroMascota.estado_registro == "A")
        .all()
    )
    if not mascotas:
        return {"mensaje": "El cliente no tiene mascotas registradas."}
    resultado = []
    for m in mascotas:
        especie_nombre = m.especie.nombre if m.especie else "Sin especie"
        if not m.foto:
            if "perro" in especie_nombre.lower():
                foto = os.path.join(globals.MASCOTA, "perro.png")
            elif "gato" in especie_nombre.lower():
                foto = os.path.join(globals.MASCOTA, "gato.png")
            else:
                foto = os.path.join(globals.MASCOTA, "default.png")
        else:
            foto = m.foto
        resultado.append({
            "id": str(m.id),
            "nombre": m.nombre,
            "especie": especie_nombre,
            "raza": m.raza,
            "edad": m.edad,
            "peso": float(m.peso) if m.peso else None,
            "foto": foto,
        })
    return {"total": len(resultado), "mascotas": resultado}

# ---------------------------------------------------------------------------
# POST /cliente/mascotas/{cliente_id}
# ---------------------------------------------------------------------------
# Registra una nueva mascota para el cliente.
# Campos: nombre, especie_id, raza, edad. La foto se asigna automáticamente.
@router.post("/{cliente_id}")
def registrar_mascota(
    cliente_id: str,
    nombre: str = Form(...),
    especie_id: str = Form(...),
    raza: str = Form(...),
    edad: int = Form(...),
    db: Session = Depends(get_db),
):
    cliente = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado.")
    especie = db.query(Especie).filter(Especie.id == especie_id).first()
    if not especie:
        raise HTTPException(status_code=404, detail="Especie no encontrada.")
    mascota_id = keygen.generate_uint64_key()
    especie_nombre = especie.nombre.lower()
    if "perro" in especie_nombre:
        foto_path = os.path.join(globals.MASCOTA, "perro.png")
    elif "gato" in especie_nombre:
        foto_path = os.path.join(globals.MASCOTA, "gato.png")
    else:
        foto_path = os.path.join(globals.MASCOTA, "default.png")
    mascota = RegistroMascota(
        id=mascota_id,
        cliente_id=cliente_id,
        nombre=nombre,
        especie_id=especie_id,
        raza=raza,
        edad=edad,
        foto=foto_path,
        estado_registro="A",
    )
    db.add(mascota)
    db.commit()
    return {
        "mensaje": "Mascota registrada exitosamente.",
        "mascota": {
            "id": str(mascota.id),
            "nombre": mascota.nombre,
            "especie": especie.nombre,
            "raza": mascota.raza,
            "edad": mascota.edad,
            "foto": mascota.foto,
        },
    }

# ---------------------------------------------------------------------------
# GET /cliente/mascotas/detalle/{mascota_id}
# ---------------------------------------------------------------------------
# Obtiene los datos completos de una mascota registrada.
# Incluye especie, edad, alergias, condiciones de salud, recetas y observaciones.
@router.get("/detalle/{mascota_id}")
def obtener_detalle_mascota(
    mascota_id: str,
    db: Session = Depends(get_db),
):
    mascota = (
        db.query(RegistroMascota)
        .options(
            joinedload(RegistroMascota.especie),
            joinedload(RegistroMascota.alergias),
            joinedload(RegistroMascota.condiciones_salud),
            joinedload(RegistroMascota.recetas_medicas),
        )
        .filter(RegistroMascota.id == mascota_id, RegistroMascota.estado_registro == "A")
        .first()
    )
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    especie_nombre = mascota.especie.nombre if mascota.especie else "Sin especie"
    if not mascota.foto:
        if "perro" in especie_nombre.lower():
            foto = os.path.join(globals.MASCOTA, "perro.png")
        elif "gato" in especie_nombre.lower():
            foto = os.path.join(globals.MASCOTA, "gato.png")
        else:
            foto = os.path.join(globals.MASCOTA, "default.png")
    else:
        foto = mascota.foto
    alergias = [
        {
            "id": str(a.id),
            "alergia": a.alergia_especie.nombre if a.alergia_especie else None,
            "severidad": a.severidad,
        }
        for a in mascota.alergias
    ]
    condiciones = [
        {
            "id": str(c.id),
            "nombre": c.nombre,
            "fecha": c.fecha.isoformat() if c.fecha else None,
            "estado_registro": c.estado_registro,
        }
        for c in mascota.condiciones_salud
    ]
    recetas = [
        {
            "id": str(r.id),
            "fecha": r.fecha.isoformat() if r.fecha else None,
            "archivo": r.archivo,
            "estado_registro": r.estado_registro,
        }
        for r in mascota.recetas_medicas
    ]
    return {
        "id": str(mascota.id),
        "nombre": mascota.nombre,
        "especie": especie_nombre,
        "raza": mascota.raza,
        "edad": mascota.edad,
        "peso": float(mascota.peso) if mascota.peso else None,
        "foto": foto,
        "alergias": alergias,
        "condiciones_salud": condiciones,
        "recetas_medicas": recetas,
        "observaciones": mascota.observaciones,
    }

# ---------------------------------------------------------------------------
# PUT /cliente/mascotas/{mascota_id}
# ---------------------------------------------------------------------------
# Edita los datos de una mascota existente (nombre, peso, edad, observaciones, etc.).
@router.put("/{mascota_id}")
def actualizar_mascota(
    mascota_id: str,
    nombre: str = Form(None),
    edad: int = Form(None),
    peso: float = Form(None),
    raza: str = Form(None),
    observaciones: str = Form(None),
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(RegistroMascota.id == mascota_id, RegistroMascota.estado_registro == "A").first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    if nombre:
        mascota.nombre = nombre
    if edad is not None:
        mascota.edad = edad
    if peso is not None:
        mascota.peso = peso
    if raza:
        mascota.raza = raza
    if observaciones:
        mascota.observaciones = observaciones
    db.commit()
    return {
        "mensaje": "Datos de la mascota actualizados correctamente.",
        "mascota": {
            "id": str(mascota.id),
            "nombre": mascota.nombre,
            "edad": mascota.edad,
            "peso": float(mascota.peso) if mascota.peso else None,
            "raza": mascota.raza,
            "observaciones": mascota.observaciones,
        },
    }

# ---------------------------------------------------------------------------
# PUT /cliente/mascotas/{mascota_id}/foto
# ---------------------------------------------------------------------------
# Cambia la foto de la mascota. Si no se envía imagen, mantiene la actual.
@router.put("/{mascota_id}/foto")
def actualizar_foto_mascota(
    mascota_id: str,
    foto: UploadFile = None,
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(RegistroMascota.id == mascota_id, RegistroMascota.estado_registro == "A").first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    uploads_dir = os.path.join("static", "uploads", "mascotas")
    os.makedirs(uploads_dir, exist_ok=True)
    if foto:
        extension = os.path.splitext(foto.filename)[1].lower()
        if extension not in [".jpg", ".jpeg", ".png"]:
            raise HTTPException(status_code=400, detail="Formato de imagen no permitido.")
        nuevo_nombre = f"mascota_{mascota_id}{extension}"
        foto_path = os.path.join(uploads_dir, nuevo_nombre)
        with open(foto_path, "wb") as f:
            f.write(foto.file.read())
        mascota.foto = foto_path
    db.commit()
    return {
        "mensaje": "Foto de mascota actualizada correctamente.",
        "foto": mascota.foto,
    }

# ---------------------------------------------------------------------------
# DELETE /cliente/mascotas/{mascota_id}
# ---------------------------------------------------------------------------
# Elimina o marca como inactiva una mascota del cliente.
# Si tiene pedidos activos asociados, no se borra físicamente.
@router.delete("/{mascota_id}")
def eliminar_mascota(
    mascota_id: str,
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(RegistroMascota.id == mascota_id).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada.")
    pedidos_activos = (
        db.query(PedidoEspecializado)
        .filter(
            PedidoEspecializado.registro_mascota_id == mascota_id,
            PedidoEspecializado.estado_registro == "A",
        )
        .count()
    )
    if pedidos_activos > 0:
        mascota.estado_registro = "I"
        db.commit()
        return {"mensaje": "Mascota marcada como inactiva por tener pedidos asociados."}
    db.delete(mascota)
    db.commit()
    return {"mensaje": "Mascota eliminada correctamente."}

# ---------------------------------------------------------------------------
# GET /cliente/mascotas/{mascota_id}/alergias
# ---------------------------------------------------------------------------
# Devuelve la lista de alergias registradas para la mascota.
# Incluye nombre, severidad y descripción.
@router.get("/{mascota_id}/alergias")
def listar_alergias_mascota(
    mascota_id: str,
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(RegistroMascota.id == mascota_id, RegistroMascota.estado_registro == "A").first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    alergias = (
        db.query(AlergiaMascota)
        .options(joinedload(AlergiaMascota.alergia_especie))
        .filter(AlergiaMascota.registro_mascota_id == mascota_id)
        .all()
    )
    if not alergias:
        return {"mensaje": "No se encontraron alergias registradas para esta mascota."}
    resultado = [
        {
            "id": str(a.id),
            "nombre": a.alergia_especie.nombre if a.alergia_especie else None,
            "severidad": a.severidad,
            "descripcion": a.descripcion,
        }
        for a in alergias
    ]
    return {"total": len(resultado), "alergias": resultado}

# ---------------------------------------------------------------------------
# POST /cliente/mascotas/{mascota_id}/alergias
# ---------------------------------------------------------------------------
# Registra una nueva alergia asociada a la mascota.
# Campos: alergia_especie_id, severidad, descripcion (opcional).
@router.post("/{mascota_id}/alergias")
def registrar_alergia_mascota(
    mascota_id: str,
    alergia_especie_id: str = Form(...),
    severidad: str = Form(...),
    descripcion: str = Form(None),
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(RegistroMascota.id == mascota_id, RegistroMascota.estado_registro == "A").first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    alergia = db.query(AlergiaEspecie).filter(AlergiaEspecie.id == alergia_especie_id).first()
    if not alergia:
        raise HTTPException(status_code=404, detail="Alergia no encontrada en catálogo de especies.")
    # Evitar duplicados
    existente = (
        db.query(AlergiaMascota)
        .filter(
            AlergiaMascota.registro_mascota_id == mascota_id,
            AlergiaMascota.alergia_especie_id == alergia_especie_id,
        )
        .first()
    )
    if existente:
        raise HTTPException(status_code=400, detail="La mascota ya tiene registrada esta alergia.")
    nueva = AlergiaMascota(
        id=keygen.generate_uint64_key(),
        registro_mascota_id=mascota_id,
        alergia_especie_id=alergia_especie_id,
        severidad=severidad,
        descripcion=descripcion,
    )
    db.add(nueva)
    db.commit()
    return {
        "mensaje": "Alergia registrada exitosamente.",
        "alergia": {
            "id": str(nueva.id),
            "nombre": alergia.nombre,
            "severidad": nueva.severidad,
            "descripcion": nueva.descripcion,
        },
    }

# ---------------------------------------------------------------------------
# GET /cliente/mascotas/{mascota_id}/condiciones
# ---------------------------------------------------------------------------
# Devuelve la lista de condiciones de salud asociadas a la mascota.
# Incluye nombre, fecha y estado_registro.
@router.get("/{mascota_id}/condiciones")
def listar_condiciones_mascota(
    mascota_id: str,
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(RegistroMascota.id == mascota_id, RegistroMascota.estado_registro == "A").first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    condiciones = (
        db.query(CondicionSalud)
        .filter(CondicionSalud.registro_mascota_id == mascota_id)
        .order_by(CondicionSalud.fecha.desc())
        .all()
    )
    if not condiciones:
        return {"mensaje": "No se encontraron condiciones de salud registradas para esta mascota."}
    resultado = [
        {
            "id": str(c.id),
            "nombre": c.nombre,
            "fecha": c.fecha.isoformat() if c.fecha else None,
            "estado_registro": c.estado_registro,
        }
        for c in condiciones
    ]
    return {"total": len(resultado), "condiciones_salud": resultado}

# ---------------------------------------------------------------------------
# POST /cliente/mascotas/{mascota_id}/condiciones
# ---------------------------------------------------------------------------
# Registra una nueva condición de salud (ej. “gastroenteritis”, “anemia leve”).
@router.post("/{mascota_id}/condiciones")
def registrar_condicion_mascota(
    mascota_id: str,
    nombre: str = Form(...),
    descripcion: str = Form(None),
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(
        RegistroMascota.id == mascota_id,
        RegistroMascota.estado_registro == "A"
    ).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    condicion = CondicionSalud(
        id=keygen.generate_uint64_key(),
        registro_mascota_id=mascota_id,
        nombre=nombre,
        descripcion=descripcion,
        fecha=datetime.now(),
        estado_registro="A",
    )
    db.add(condicion)
    db.commit()
    return {
        "mensaje": "Condición de salud registrada exitosamente.",
        "condicion": {
            "id": str(condicion.id),
            "nombre": condicion.nombre,
            "descripcion": condicion.descripcion,
            "fecha": condicion.fecha.isoformat(),
            "estado_registro": condicion.estado_registro,
        },
    }

# ---------------------------------------------------------------------------
# GET /cliente/mascotas/{mascota_id}/recetas
# ---------------------------------------------------------------------------
# Lista las recetas médicas asociadas a la mascota.
# Incluye fecha, estado y archivo descargable.
@router.get("/{mascota_id}/recetas")
def listar_recetas_mascota(
    mascota_id: str,
    db: Session = Depends(get_db),
):
    mascota = db.query(RegistroMascota).filter(
        RegistroMascota.id == mascota_id,
        RegistroMascota.estado_registro == "A"
    ).first()
    if not mascota:
        raise HTTPException(status_code=404, detail="Mascota no encontrada o inactiva.")
    recetas = (
        db.query(RecetaMedica)
        .filter(RecetaMedica.registro_mascota_id == mascota_id)
        .order_by(RecetaMedica.fecha.desc())
        .all()
    )
    if not recetas:
        return {"mensaje": "No se encontraron recetas médicas para esta mascota."}
    resultado = [
        {
            "id": str(r.id),
            "fecha": r.fecha.isoformat() if r.fecha else None,
            "estado_registro": r.estado_registro,
            "archivo": r.archivo,
        }
        for r in recetas
    ]
    return {"total": len(resultado), "recetas_medicas": resultado}