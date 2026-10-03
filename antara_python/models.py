"""
Antara - Modelos y base de datos.
POO + SQLAlchemy. Funciona con SQLite local y PostgreSQL en producción.
"""
import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    pelotitas = db.relationship("TipoPelotita", backref="usuario", cascade="all, delete-orphan")
    extras = db.relationship("Extra", backref="usuario", cascade="all, delete-orphan")
    compras = db.relationship("Compra", backref="usuario", cascade="all, delete-orphan")
    pulseras = db.relationship("Pulsera", backref="usuario", cascade="all, delete-orphan")

    def establecer_password(self, password):
        self.password_hash = generate_password_hash(password)

    def verificar_password(self, password):
        return check_password_hash(self.password_hash, password)

class TipoPelotita(db.Model):
    __tablename__ = "tipo_pelotita"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    color = db.Column(db.String(20), default="#2FA89C")
    cantidad = db.Column(db.Integer, default=0, nullable=False)

class Extra(db.Model):
    __tablename__ = "extras"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    cantidad = db.Column(db.Integer, default=0, nullable=False)

class Compra(db.Model):
    __tablename__ = "compras"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey("tipo_pelotita.id"), nullable=False)
    pelotitas_por_ristra = db.Column(db.Integer, nullable=False)
    cantidad_ristras = db.Column(db.Integer, nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tipo = db.relationship("TipoPelotita")

class Pulsera(db.Model):
    __tablename__ = "pulseras"
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    nombre = db.Column(db.String(120), nullable=False)
    extra_id = db.Column(db.Integer, db.ForeignKey("extras.id"), nullable=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    componentes = db.relationship("ComponentePulsera", backref="pulsera", cascade="all, delete-orphan")
    extra = db.relationship("Extra")

class ComponentePulsera(db.Model):
    __tablename__ = "componentes_pulsera"
    id = db.Column(db.Integer, primary_key=True)
    pulsera_id = db.Column(db.Integer, db.ForeignKey("pulseras.id"), nullable=False)
    tipo_id = db.Column(db.Integer, db.ForeignKey("tipo_pelotita.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    tipo = db.relationship("TipoPelotita")

class Taller:
    """Lógica de negocio del inventario de un usuario."""
    def __init__(self, usuario):
        self.usuario = usuario

    @property
    def pelotitas(self):
        return TipoPelotita.query.filter_by(usuario_id=self.usuario.id).order_by(TipoPelotita.nombre).all()

    @property
    def extras(self):
        return Extra.query.filter_by(usuario_id=self.usuario.id).order_by(Extra.nombre).all()

    @property
    def compras(self):
        return Compra.query.filter_by(usuario_id=self.usuario.id).order_by(Compra.fecha.desc()).all()

    @property
    def pulseras(self):
        return Pulsera.query.filter_by(usuario_id=self.usuario.id).order_by(Pulsera.fecha.desc()).all()

    def buscar_o_crear_tipo(self, nombre, color=None):
        tipo = TipoPelotita.query.filter(
            db.func.lower(TipoPelotita.nombre) == nombre.lower(),
            TipoPelotita.usuario_id == self.usuario.id
        ).first()
        if tipo:
            if color:
                tipo.color = color
            return tipo
        tipo = TipoPelotita(usuario_id=self.usuario.id, nombre=nombre,
                            color=color or "#2FA89C", cantidad=0)
        db.session.add(tipo)
        return tipo

    def registrar_compra(self, nombre, color, por_ristra, cantidad_ristras):
        tipo = self.buscar_o_crear_tipo(nombre, color)
        tipo.cantidad += por_ristra * cantidad_ristras
        db.session.add(Compra(usuario_id=self.usuario.id, tipo=tipo,
                              pelotitas_por_ristra=por_ristra,
                              cantidad_ristras=cantidad_ristras))
        db.session.commit()

    def registrar_extra(self, nombre, cantidad):
        extra = Extra.query.filter(
            db.func.lower(Extra.nombre) == nombre.lower(),
            Extra.usuario_id == self.usuario.id
        ).first()
        if extra:
            extra.cantidad += cantidad
        else:
            db.session.add(Extra(usuario_id=self.usuario.id, nombre=nombre, cantidad=cantidad))
        db.session.commit()

    def crear_pulsera(self, nombre, componentes, extra_id):
        # Validar que todos los tipos pertenecen al usuario y tienen stock.
        validados = []
        for item in componentes:
            try:
                tipo_id = int(item["tipo_id"])
                cantidad = int(item["cantidad"])
            except (ValueError, TypeError, KeyError):
                return False, "Hay una cantidad o tipo de pelotita inválido."
            if cantidad <= 0:
                return False, "Las cantidades deben ser mayores que cero."
            tipo = TipoPelotita.query.filter_by(id=tipo_id, usuario_id=self.usuario.id).first()
            if not tipo:
                return False, "Una de las pelotitas seleccionadas no existe."
            if tipo.cantidad < cantidad:
                return False, f'No hay suficientes pelotitas de "{tipo.nombre}".'
            validados.append((tipo, cantidad))

        extra = None
        if extra_id:
            try:
                extra_id = int(extra_id)
            except ValueError:
                return False, "Extra inválido."
            extra = Extra.query.filter_by(id=extra_id, usuario_id=self.usuario.id).first()
            if not extra or extra.cantidad < 1:
                return False, "No hay ese dije/extra en inventario."

        for tipo, cantidad in validados:
            tipo.cantidad -= cantidad
        if extra:
            extra.cantidad -= 1

        pulsera = Pulsera(
            usuario_id=self.usuario.id,
            nombre=nombre.strip() if nombre.strip() else f"Pulsera {len(self.pulseras) + 1}",
            extra=extra
        )
        db.session.add(pulsera)
        db.session.flush()
        for tipo, cantidad in validados:
            db.session.add(ComponentePulsera(
                pulsera_id=pulsera.id, tipo_id=tipo.id, cantidad=cantidad
            ))
        db.session.commit()
        return True, None

def crear_usuario(username, password):
    username = username.strip()
    if Usuario.query.filter_by(username=username).first():
        return False, "Ese usuario ya existe."
    usuario = Usuario(username=username)
    usuario.establecer_password(password)
    db.session.add(usuario)
    db.session.commit()
    return True, None

def validar_usuario(username, password):
    usuario = Usuario.query.filter_by(username=username.strip()).first()
    if not usuario:
        return False, "No existe esa cuenta."
    if not usuario.verificar_password(password):
        return False, "Contraseña incorrecta."
    return True, usuario
