from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from utils.db import get_db
from utils.globals import PLATO
from models import PlatoCombinado, Categoria, Especie, EtiquetaPlato, Etiqueta
from slugify import slugify

router = APIRouter(
    prefix="/cliente/platos-mascotas",
    tags=["Cliente - Platos para Mascotas"]
)

# ---------------------------------------------------------------------------
# 🖼️ Utilidad: construir URL completa para la imagen
# ---------------------------------------------------------------------------
def construir_url_imagen(request: Request, nombre_archivo: str | None):
    """Construye una URL completa para acceder a la imagen."""
    if not nombre_archivo:
        return None
    base = str(request.base_url).rstrip("/")
    path = PLATO.strip("/")
    return f"{base}/{path}/{nombre_archivo.lstrip('/')}"

# ---------------------------------------------------------------------------
# 🧩 Utilidad: convertir PlatoCombinado → dict JSON serializable
# ---------------------------------------------------------------------------
def plato_to_dict(p: PlatoCombinado, request: Request):
    """Convierte un PlatoCombinado en un diccionario listo para JSON."""
    return {
        "id": str(p.id),
        "nombre": p.nombre,
        "descripcion": p.descripcion,
        "precio": float(p.precio),
        "imagen": construir_url_imagen(request, p.imagen),
        "categoria": p.categoria.nombre if p.categoria else None,
        "especie": p.especie.nombre if p.especie else None,
        "etiquetas": [ep.etiqueta.nombre for ep in p.etiqueta_plato],
    }

# ---------------------------------------------------------------------------
# 🥘 GET /cliente/platos-mascotas
# ---------------------------------------------------------------------------
@router.get(
    "/", 
    summary="Listar platos con filtros por categoría, especie o etiquetas",
)
def listar_platos(
    request: Request,
    db: Session = Depends(get_db),
    categoria_id: str | None = Query(None, description="ID de la categoría"),
    especie_id: str | None = Query(None, description="ID de la especie"),
    etiquetas: list[str] | None = Query(None, description="IDs de etiquetas"),
    search: str | None = Query(None, description="Texto libre para búsqueda"),
):
    """
    Lista platos combinados filtrando por:
    - categoría
    - especie
    - etiquetas (una o varias)
    - texto libre (nombre o descripción)

    Solo devuelve platos activos y publicados.
    """
    query = (
        db.query(PlatoCombinado)
        .options(
            joinedload(PlatoCombinado.categoria),
            joinedload(PlatoCombinado.especie),
            joinedload(PlatoCombinado.etiqueta_plato).joinedload(EtiquetaPlato.etiqueta),
        )
        .filter(
            PlatoCombinado.estado_registro == "A",
            PlatoCombinado.publicado == 1,
        )
    )
    print("📥 Filtros recibidos →", categoria_id, especie_id, etiquetas, search)
    # Filtros combinados
    if categoria_id:
        query = query.filter(PlatoCombinado.categoria_id == categoria_id)
    if especie_id:
        query = query.filter(PlatoCombinado.especie_id == especie_id)
    if etiquetas and len(etiquetas) > 0:
        query = query.filter(
            PlatoCombinado.etiqueta_plato.any(
                EtiquetaPlato.etiqueta_id.in_(etiquetas)
            )
        )
    if search:
        search_like = f"%{search.lower()}%"
        query = query.filter(
            or_(
                PlatoCombinado.nombre.ilike(search_like),
                PlatoCombinado.descripcion.ilike(search_like),
                PlatoCombinado.etiqueta_plato.any(
                    EtiquetaPlato.etiqueta.has(Etiqueta.nombre.ilike(search_like))
                ),
            )
        )
    platos = query.all()
    return [plato_to_dict(p, request) for p in platos]
# ---------------------------------------------------------------------------
# 🔍 GET /cliente/platos-mascotas/id/{plato_id}
# ---------------------------------------------------------------------------
@router.get("/id/{plato_id}", summary="Obtener detalles de un plato")
def obtener_plato(plato_id: str, request: Request, db: Session = Depends(get_db)):
    """Devuelve la información detallada de un plato específico."""
    plato = (
        db.query(PlatoCombinado)
        .options(
            joinedload(PlatoCombinado.categoria),
            joinedload(PlatoCombinado.especie),
            joinedload(PlatoCombinado.etiqueta_plato).joinedload(EtiquetaPlato.etiqueta),
        )
        .filter(
            PlatoCombinado.id == plato_id,
            PlatoCombinado.estado_registro == "A",
            PlatoCombinado.publicado == 1,
        )
        .first()
    )

    if not plato:
        raise HTTPException(status_code=404, detail="Plato no encontrado")

    return plato_to_dict(plato, request)

# ---------------------------------------------------------------------------
# 📂 GET /cliente/platos-mascotas/categorias
# ---------------------------------------------------------------------------
@router.get("/categorias", summary="Listar categorías activas")
def listar_categorias(db: Session = Depends(get_db)):
    """Devuelve todas las categorías activas con slug."""
    categorias = db.query(Categoria).filter(Categoria.estado_registro == "A").all()
    return [
        {
            "id": str(c.id),
            "nombre": c.nombre,
            "descripcion": c.descripcion,
            "slug": slugify(c.nombre, separator="-"),
        }
        for c in categorias
    ]

# ---------------------------------------------------------------------------
# 🧬 GET /cliente/platos-mascotas/especies
# ---------------------------------------------------------------------------
@router.get("/especies", summary="Listar especies (solo perros y gatos)")
def listar_especies(db: Session = Depends(get_db)):
    """Devuelve las especies activas (solo Perros y Gatos)."""
    especies = db.query(Especie).filter(Especie.estado_registro == "A").all()
    return [{"id": str(e.id), "nombre": e.nombre} for e in especies]

# ---------------------------------------------------------------------------
# 🏷️ GET /cliente/platos-mascotas/etiquetas
# ---------------------------------------------------------------------------
@router.get("/etiquetas", summary="Listar etiquetas asociadas a platos publicados")
def listar_etiquetas(db: Session = Depends(get_db)):
    """Devuelve las etiquetas vinculadas a platos activos y publicados."""
    etiquetas = (
        db.query(Etiqueta)
        .join(Etiqueta.etiqueta_plato)
        .join(EtiquetaPlato.plato_combinado)
        .filter(
            PlatoCombinado.estado_registro == "A",
            PlatoCombinado.publicado == 1,
        )
        .distinct()
        .all()
    )
    return [{"id": str(e.id), "nombre": e.nombre} for e in etiquetas]
