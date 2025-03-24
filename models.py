from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import datetime

db = SQLAlchemy()

class Cliente(UserMixin, db.Model):
    __tablename__ = 'cliente'
    id = db.Column(db.Integer, primary_key=True)
    contrasenia = db.Column(db.String(50))
    nombre = db.Column(db.String(50))
    direccion = db.Column(db.String(50))
    telefono = db.Column(db.String(50))
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Pedidos(db.Model):
    __tablename__ = 'pizza'
    id = db.Column(db.Integer, primary_key=True)
    tamanio = db.Column(db.String(50))
    ingredientes = db.Column(db.String(50))
    cantidad = db.Column(db.Integer)
    created_date = db.Column(db.DateTime, default=datetime.datetime.now)

class Venta(db.Model):
    __tablename__ = 'ventas'
    idVenta = db.Column(db.Integer, primary_key=True)
    idPedido = db.Column(db.Integer, db.ForeignKey('pizza.id'), nullable=False)
    idCliente = db.Column(db.Integer, db.ForeignKey('cliente.id'), nullable=False)
    fechaVenta = db.Column(db.DateTime, default=datetime.datetime.now)
    montoTotal = db.Column(db.Float, nullable=False)
    size = db.Column(db.String(20), nullable=False)
    ingredientes = db.Column(db.String(200), nullable=False)
    num_pizzas = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    cliente = db.relationship('Cliente', backref='ventas')
    pedido = db.relationship('Pedidos', backref='ventas')
