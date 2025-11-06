from typing import Optional
import datetime
import decimal

from sqlalchemy import CHAR, DECIMAL, Date, DateTime, ForeignKeyConstraint, Index, Integer, String, Text
from sqlalchemy.dialects.mysql import BIGINT, TINYINT
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass


class Categoria(Base):
    __tablename__ = 'categoria'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    plato_combinado: Mapped[list['PlatoCombinado']] = relationship('PlatoCombinado', back_populates='categoria')

class CuentaUsuario(Base):
    __tablename__ = 'cuenta_usuario'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    correo_electronico: Mapped[str] = mapped_column(String(80), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    nombre_usuario: Mapped[Optional[str]] = mapped_column(String(40))
    contrasena: Mapped[Optional[str]] = mapped_column(String(80))
    ultimo_acceso: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime)

    cliente: Mapped[list['Cliente']] = relationship('Cliente', back_populates='cuenta_usuario')
    nutricionista: Mapped[list['Nutricionista']] = relationship('Nutricionista', back_populates='cuenta_usuario')
    repartidor: Mapped[list['Repartidor']] = relationship('Repartidor', back_populates='cuenta_usuario')
    usuario_rol: Mapped[list['UsuarioRol']] = relationship('UsuarioRol', back_populates='cuenta_usuario')


class Especie(Base):
    __tablename__ = 'especie'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    alergia_especie: Mapped[list['AlergiaEspecie']] = relationship('AlergiaEspecie', back_populates='especie')
    plato_combinado: Mapped[list['PlatoCombinado']] = relationship('PlatoCombinado', back_populates='especie')
    registro_mascota: Mapped[list['RegistroMascota']] = relationship('RegistroMascota', back_populates='especie')


class Etiqueta(Base):
    __tablename__ = 'etiqueta'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)

    etiqueta_plato: Mapped[list['EtiquetaPlato']] = relationship('EtiquetaPlato', back_populates='etiqueta')


class MembresiaSubscripcion(Base):
    __tablename__ = 'membresia_subscripcion'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    duracion: Mapped[int] = mapped_column(Integer, nullable=False)
    precio: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(100))
    beneficios: Mapped[Optional[str]] = mapped_column(Text)

    cliente: Mapped[list['Cliente']] = relationship('Cliente', back_populates='membresia_subscripcion')


class PasarelaPago(Base):
    __tablename__ = 'pasarela_pago'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(100))
    imagen_qr: Mapped[Optional[str]] = mapped_column(Text)

    pago: Mapped[list['Pago']] = relationship('Pago', back_populates='pasarela_pago')


class Rol(Base):
    __tablename__ = 'rol'

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(20), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(String(100))

    usuario_rol: Mapped[list['UsuarioRol']] = relationship('UsuarioRol', back_populates='rol')


class AlergiaEspecie(Base):
    __tablename__ = 'alergia_especie'
    __table_args__ = (
        ForeignKeyConstraint(['especie_id'], ['especie.id'], ondelete='CASCADE', name='alergia_especie_ibfk_1'),
        Index('especie_id', 'especie_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    especie_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    especie: Mapped['Especie'] = relationship('Especie', back_populates='alergia_especie')
    alergia_mascota: Mapped[list['AlergiaMascota']] = relationship('AlergiaMascota', back_populates='alergia_especie')


class Cliente(Base):
    __tablename__ = 'cliente'
    __table_args__ = (
        ForeignKeyConstraint(['cuenta_usuario_id'], ['cuenta_usuario.id'], ondelete='CASCADE', name='cliente_ibfk_1'),
        ForeignKeyConstraint(['membresia_subscripcion_id'], ['membresia_subscripcion.id'], name='cliente_ibfk_2'),
        Index('cuenta_usuario_id', 'cuenta_usuario_id', unique=True),
        Index('membresia_subscripcion_id', 'membresia_subscripcion_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cuenta_usuario_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(11))
    foto: Mapped[Optional[str]] = mapped_column(Text)
    membresia_subscripcion_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    cuenta_usuario: Mapped['CuentaUsuario'] = relationship('CuentaUsuario', back_populates='cliente')
    membresia_subscripcion: Mapped[Optional['MembresiaSubscripcion']] = relationship('MembresiaSubscripcion', back_populates='cliente')
    direccion: Mapped[list['Direccion']] = relationship('Direccion', back_populates='cliente')
    registro_mascota: Mapped[list['RegistroMascota']] = relationship('RegistroMascota', back_populates='cliente')
    pedido: Mapped[list['Pedido']] = relationship('Pedido', back_populates='cliente')


class Nutricionista(Base):
    __tablename__ = 'nutricionista'
    __table_args__ = (
        ForeignKeyConstraint(['cuenta_usuario_id'], ['cuenta_usuario.id'], ondelete='CASCADE', name='nutricionista_ibfk_1'),
        Index('cuenta_usuario_id', 'cuenta_usuario_id', unique=True)
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cuenta_usuario_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    telefono: Mapped[str] = mapped_column(String(15), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    especialidad: Mapped[Optional[str]] = mapped_column(String(60))
    colegio_veterinario: Mapped[Optional[str]] = mapped_column(String(40))

    cuenta_usuario: Mapped['CuentaUsuario'] = relationship('CuentaUsuario', back_populates='nutricionista')
    consulta: Mapped[list['Consulta']] = relationship('Consulta', back_populates='nutricionista')


class PlatoCombinado(Base):
    __tablename__ = 'plato_combinado'
    __table_args__ = (
        ForeignKeyConstraint(['categoria_id'], ['categoria.id'], ondelete='SET NULL', name='plato_combinado_ibfk_1'),
        ForeignKeyConstraint(['especie_id'], ['especie.id'], ondelete='SET NULL', name='plato_combinado_ibfk_2'),
        Index('categoria_id', 'categoria_id'),
        Index('especie_id', 'especie_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    precio: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    incluye_plato: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    es_crudo: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    publicado: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    creado_nutricionista: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    categoria_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    especie_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    imagen: Mapped[Optional[str]] = mapped_column(Text)

    categoria: Mapped[Optional['Categoria']] = relationship('Categoria', back_populates='plato_combinado')
    especie: Mapped[Optional['Especie']] = relationship('Especie', back_populates='plato_combinado')
    etiqueta_plato: Mapped[list['EtiquetaPlato']] = relationship('EtiquetaPlato', back_populates='plato_combinado')
    plato_personal: Mapped[list['PlatoPersonal']] = relationship('PlatoPersonal', back_populates='plato_combinado')
    detalle_pedido: Mapped[list['DetallePedido']] = relationship('DetallePedido', back_populates='plato_combinado')
    detalle_dieta: Mapped[list['DetalleDieta']] = relationship('DetalleDieta', back_populates='plato_combinado')


class Repartidor(Base):
    __tablename__ = 'repartidor'
    __table_args__ = (
        ForeignKeyConstraint(['cuenta_usuario_id'], ['cuenta_usuario.id'], ondelete='CASCADE', name='repartidor_ibfk_1'),
        Index('cuenta_usuario_id', 'cuenta_usuario_id', unique=True)
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cuenta_usuario_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    telefono: Mapped[str] = mapped_column(String(15), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)

    cuenta_usuario: Mapped['CuentaUsuario'] = relationship('CuentaUsuario', back_populates='repartidor')
    control_entrega: Mapped[list['ControlEntrega']] = relationship('ControlEntrega', back_populates='repartidor')


class UsuarioRol(Base):
    __tablename__ = 'usuario_rol'
    __table_args__ = (
        ForeignKeyConstraint(['cuenta_usuario_id'], ['cuenta_usuario.id'], ondelete='CASCADE', name='usuario_rol_ibfk_1'),
        ForeignKeyConstraint(['rol_id'], ['rol.id'], ondelete='SET NULL', name='usuario_rol_ibfk_2'),
        Index('cuenta_usuario_id', 'cuenta_usuario_id', unique=True),
        Index('rol_id', 'rol_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cuenta_usuario_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    rol_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    cuenta_usuario: Mapped['CuentaUsuario'] = relationship('CuentaUsuario', back_populates='usuario_rol')
    rol: Mapped[Optional['Rol']] = relationship('Rol', back_populates='usuario_rol')


class Direccion(Base):
    __tablename__ = 'direccion'
    __table_args__ = (
        ForeignKeyConstraint(['cliente_id'], ['cliente.id'], name='direccion_ibfk_1'),
        Index('cliente_id', 'cliente_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    latitud: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    longitud: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    es_principal: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    referencia: Mapped[Optional[str]] = mapped_column(String(100))

    cliente: Mapped['Cliente'] = relationship('Cliente', back_populates='direccion')
    pedido: Mapped[list['Pedido']] = relationship('Pedido', back_populates='direccion')


class EtiquetaPlato(Base):
    __tablename__ = 'etiqueta_plato'
    __table_args__ = (
        ForeignKeyConstraint(['etiqueta_id'], ['etiqueta.id'], ondelete='CASCADE', name='etiqueta_plato_ibfk_2'),
        ForeignKeyConstraint(['plato_combinado_id'], ['plato_combinado.id'], ondelete='CASCADE', name='etiqueta_plato_ibfk_1'),
        Index('etiqueta_id', 'etiqueta_id'),
        Index('plato_combinado_id', 'plato_combinado_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    plato_combinado_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    etiqueta_id: Mapped[int] = mapped_column(BIGINT, nullable=False)

    etiqueta: Mapped['Etiqueta'] = relationship('Etiqueta', back_populates='etiqueta_plato')
    plato_combinado: Mapped['PlatoCombinado'] = relationship('PlatoCombinado', back_populates='etiqueta_plato')


class RegistroMascota(Base):
    __tablename__ = 'registro_mascota'
    __table_args__ = (
        ForeignKeyConstraint(['cliente_id'], ['cliente.id'], ondelete='CASCADE', name='registro_mascota_ibfk_1'),
        ForeignKeyConstraint(['especie_id'], ['especie.id'], name='registro_mascota_ibfk_2'),
        Index('cliente_id', 'cliente_id'),
        Index('especie_id', 'especie_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(40), nullable=False)
    sexo: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    cambio_edad: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    edad: Mapped[int] = mapped_column(Integer, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    especie_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    raza: Mapped[Optional[str]] = mapped_column(String(40))
    peso: Mapped[Optional[decimal.Decimal]] = mapped_column(DECIMAL(10, 2))
    foto: Mapped[Optional[str]] = mapped_column(Text)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)

    cliente: Mapped['Cliente'] = relationship('Cliente', back_populates='registro_mascota')
    especie: Mapped[Optional['Especie']] = relationship('Especie', back_populates='registro_mascota')
    alergia_mascota: Mapped[list['AlergiaMascota']] = relationship('AlergiaMascota', back_populates='registro_mascota')
    condicion_salud: Mapped[list['CondicionSalud']] = relationship('CondicionSalud', back_populates='registro_mascota')
    consulta: Mapped[list['Consulta']] = relationship('Consulta', back_populates='registro_mascota')
    descripcion_alergias: Mapped[list['DescripcionAlergias']] = relationship('DescripcionAlergias', back_populates='registro_mascota')
    plato_personal: Mapped[list['PlatoPersonal']] = relationship('PlatoPersonal', back_populates='registro_mascota')
    preferencia_alimentaria: Mapped[list['PreferenciaAlimentaria']] = relationship('PreferenciaAlimentaria', back_populates='registro_mascota')
    pedido_especializado: Mapped[list['PedidoEspecializado']] = relationship('PedidoEspecializado', back_populates='registro_mascota')
    receta_medica: Mapped[list['RecetaMedica']] = relationship('RecetaMedica', back_populates='registro_mascota')


class AlergiaMascota(Base):
    __tablename__ = 'alergia_mascota'
    __table_args__ = (
        ForeignKeyConstraint(['alergia_especie_id'], ['alergia_especie.id'], name='alergia_mascota_ibfk_2'),
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='alergia_mascota_ibfk_1'),
        Index('alergia_especie_id', 'alergia_especie_id'),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    severidad: Mapped[str] = mapped_column(String(20), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    alergia_especie_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    alergia_especie: Mapped[Optional['AlergiaEspecie']] = relationship('AlergiaEspecie', back_populates='alergia_mascota')
    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='alergia_mascota')


class CondicionSalud(Base):
    __tablename__ = 'condicion_salud'
    __table_args__ = (
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='condicion_salud_ibfk_1'),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)

    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='condicion_salud')


class Consulta(Base):
    __tablename__ = 'consulta'
    __table_args__ = (
        ForeignKeyConstraint(['nutricionista_id'], ['nutricionista.id'], name='consulta_ibfk_2'),
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='consulta_ibfk_1'),
        Index('nutricionista_id', 'nutricionista_id'),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    nutricionista_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    observaciones: Mapped[Optional[str]] = mapped_column(Text)
    recomendaciones: Mapped[Optional[str]] = mapped_column(Text)

    nutricionista: Mapped[Optional['Nutricionista']] = relationship('Nutricionista', back_populates='consulta')
    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='consulta')
    dieta: Mapped[list['Dieta']] = relationship('Dieta', back_populates='consulta')


class DescripcionAlergias(Base):
    __tablename__ = 'descripcion_alergias'
    __table_args__ = (
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='descripcion_alergias_ibfk_1'),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)

    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='descripcion_alergias')


class Pedido(Base):
    __tablename__ = 'pedido'
    __table_args__ = (
        ForeignKeyConstraint(['cliente_id'], ['cliente.id'], ondelete='CASCADE', name='pedido_ibfk_1'),
        ForeignKeyConstraint(['direccion_id'], ['direccion.id'], name='pedido_ibfk_2'),
        Index('cliente_id', 'cliente_id'),
        Index('direccion_id', 'direccion_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    cliente_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    total: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    incluye_plato: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    direccion_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    cliente: Mapped['Cliente'] = relationship('Cliente', back_populates='pedido')
    direccion: Mapped[Optional['Direccion']] = relationship('Direccion', back_populates='pedido')
    control_entrega: Mapped[list['ControlEntrega']] = relationship('ControlEntrega', back_populates='pedido')
    detalle_pedido: Mapped[list['DetallePedido']] = relationship('DetallePedido', back_populates='pedido')
    pago: Mapped[list['Pago']] = relationship('Pago', back_populates='pedido')
    pedido_especializado: Mapped[list['PedidoEspecializado']] = relationship('PedidoEspecializado', back_populates='pedido')


class PlatoPersonal(Base):
    __tablename__ = 'plato_personal'
    __table_args__ = (
        ForeignKeyConstraint(['plato_combinado_id'], ['plato_combinado.id'], name='plato_personal_ibfk_1'),
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='plato_personal_ibfk_2'),
        Index('plato_combinado_id', 'plato_combinado_id'),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    plato_combinado_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)

    plato_combinado: Mapped['PlatoCombinado'] = relationship('PlatoCombinado', back_populates='plato_personal')
    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='plato_personal')


class PreferenciaAlimentaria(Base):
    __tablename__ = 'preferencia_alimentaria'
    __table_args__ = (
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='preferencia_alimentaria_ibfk_1'),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='preferencia_alimentaria')


class ControlEntrega(Base):
    __tablename__ = 'control_entrega'
    __table_args__ = (
        ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ondelete='CASCADE', name='control_entrega_ibfk_1'),
        ForeignKeyConstraint(['repartidor_id'], ['repartidor.id'], name='control_entrega_ibfk_2'),
        Index('pedido_id', 'pedido_id', unique=True),
        Index('repartidor_id', 'repartidor_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    fecha_entrega: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    confirmacion_entrega: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    repartidor_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    pedido: Mapped['Pedido'] = relationship('Pedido', back_populates='control_entrega')
    repartidor: Mapped[Optional['Repartidor']] = relationship('Repartidor', back_populates='control_entrega')


class DetallePedido(Base):
    __tablename__ = 'detalle_pedido'
    __table_args__ = (
        ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ondelete='CASCADE', name='detalle_pedido_ibfk_1'),
        ForeignKeyConstraint(['plato_combinado_id'], ['plato_combinado.id'], name='detalle_pedido_ibfk_2'),
        Index('pedido_id', 'pedido_id'),
        Index('plato_combinado_id', 'plato_combinado_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    subtotal: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    plato_combinado_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    pedido: Mapped['Pedido'] = relationship('Pedido', back_populates='detalle_pedido')
    plato_combinado: Mapped[Optional['PlatoCombinado']] = relationship('PlatoCombinado', back_populates='detalle_pedido')


class Dieta(Base):
    __tablename__ = 'dieta'
    __table_args__ = (
        ForeignKeyConstraint(['consulta_id'], ['consulta.id'], ondelete='CASCADE', name='dieta_ibfk_1'),
        Index('consulta_id', 'consulta_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    consulta_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    nombre: Mapped[str] = mapped_column(String(60), nullable=False)
    descripcion: Mapped[str] = mapped_column(Text, nullable=False)
    fecha_inicio: Mapped[datetime.date] = mapped_column(Date, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    fecha_fin: Mapped[Optional[datetime.date]] = mapped_column(Date)

    consulta: Mapped['Consulta'] = relationship('Consulta', back_populates='dieta')
    detalle_dieta: Mapped[list['DetalleDieta']] = relationship('DetalleDieta', back_populates='dieta')


class Pago(Base):
    __tablename__ = 'pago'
    __table_args__ = (
        ForeignKeyConstraint(['pasarela_pago_id'], ['pasarela_pago.id'], name='pago_ibfk_2'),
        ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ondelete='CASCADE', name='pago_ibfk_1'),
        Index('pasarela_pago_id', 'pasarela_pago_id'),
        Index('pedido_id', 'pedido_id', unique=True)
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    monto: Mapped[decimal.Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    estado: Mapped[str] = mapped_column(String(20), nullable=False)
    pasarela_pago_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    referencia_pago: Mapped[Optional[str]] = mapped_column(String(60))

    pasarela_pago: Mapped[Optional['PasarelaPago']] = relationship('PasarelaPago', back_populates='pago')
    pedido: Mapped['Pedido'] = relationship('Pedido', back_populates='pago')


class PedidoEspecializado(Base):
    __tablename__ = 'pedido_especializado'
    __table_args__ = (
        ForeignKeyConstraint(['pedido_id'], ['pedido.id'], ondelete='CASCADE', name='pedido_especializado_ibfk_1'),
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], name='pedido_especializado_ibfk_2'),
        Index('pedido_id', 'pedido_id', unique=True),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    pedido_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    frecuencia_cantidad: Mapped[str] = mapped_column(Text, nullable=False)
    consulta_nutricionista: Mapped[int] = mapped_column(TINYINT(1), nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    registro_mascota_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    indicaciones_adicionales: Mapped[Optional[str]] = mapped_column(Text)
    objetivo_dieta: Mapped[Optional[str]] = mapped_column(Text)
    archivo_adicional: Mapped[Optional[str]] = mapped_column(Text)

    pedido: Mapped['Pedido'] = relationship('Pedido', back_populates='pedido_especializado')
    registro_mascota: Mapped[Optional['RegistroMascota']] = relationship('RegistroMascota', back_populates='pedido_especializado')
    receta_medica: Mapped[list['RecetaMedica']] = relationship('RecetaMedica', back_populates='pedido_especializado')


class DetalleDieta(Base):
    __tablename__ = 'detalle_dieta'
    __table_args__ = (
        ForeignKeyConstraint(['dieta_id'], ['dieta.id'], ondelete='CASCADE', name='detalle_dieta_ibfk_1'),
        ForeignKeyConstraint(['plato_combinado_id'], ['plato_combinado.id'], name='detalle_dieta_ibfk_2'),
        Index('dieta_id', 'dieta_id'),
        Index('plato_combinado_id', 'plato_combinado_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    dieta_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    instruccion: Mapped[str] = mapped_column(Text, nullable=False)
    frecuencia: Mapped[str] = mapped_column(String(40), nullable=False)
    plato_combinado_id: Mapped[Optional[int]] = mapped_column(BIGINT)

    dieta: Mapped['Dieta'] = relationship('Dieta', back_populates='detalle_dieta')
    plato_combinado: Mapped[Optional['PlatoCombinado']] = relationship('PlatoCombinado', back_populates='detalle_dieta')


class RecetaMedica(Base):
    __tablename__ = 'receta_medica'
    __table_args__ = (
        ForeignKeyConstraint(['pedido_especializado_id'], ['pedido_especializado.id'], name='receta_medica_ibfk_2'),
        ForeignKeyConstraint(['registro_mascota_id'], ['registro_mascota.id'], ondelete='CASCADE', name='receta_medica_ibfk_1'),
        Index('pedido_especializado_id', 'pedido_especializado_id', unique=True),
        Index('registro_mascota_id', 'registro_mascota_id')
    )

    id: Mapped[int] = mapped_column(BIGINT, primary_key=True)
    registro_mascota_id: Mapped[int] = mapped_column(BIGINT, nullable=False)
    fecha: Mapped[datetime.datetime] = mapped_column(DateTime, nullable=False)
    estado_registro: Mapped[str] = mapped_column(CHAR(1), nullable=False)
    pedido_especializado_id: Mapped[Optional[int]] = mapped_column(BIGINT)
    archivo: Mapped[Optional[str]] = mapped_column(Text)

    pedido_especializado: Mapped[Optional['PedidoEspecializado']] = relationship('PedidoEspecializado', back_populates='receta_medica')
    registro_mascota: Mapped['RegistroMascota'] = relationship('RegistroMascota', back_populates='receta_medica')
