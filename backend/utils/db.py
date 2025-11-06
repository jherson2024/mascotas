#utils/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
# Datos de conexión a MySQL
DATABASE_URL = "mysql+pymysql://root:1234@localhost:3306/mascotas"
# Crea el motor de conexión
engine = create_engine(DATABASE_URL, echo=True)
# Sesión para interactuar con la base de datos
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Clase base para modelos (ORM)
Base = declarative_base()
# 🔹 ESTA FUNCIÓN ES CLAVE
def get_db():
    """Crea y cierra la sesión de base de datos para cada solicitud."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()