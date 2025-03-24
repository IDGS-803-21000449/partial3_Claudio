from flask import Flask, flash, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from config import DevelopmentConfig
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import forms
from models import db, Pedidos, Venta, Cliente  

app = Flask(__name__)
app.config.from_object(DevelopmentConfig)

db.init_app(app)
csrf = CSRFProtect(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, inicia sesión para continuar."
login_manager.login_message_category = "warning"


@login_manager.user_loader
def load_user(user_id):
    return Cliente.query.get(int(user_id))

PEDIDOS_FILE = "pedidos.txt"

def guardar_pedido(pedido):
    """Guarda un pedido en un archivo de texto"""
    with open(PEDIDOS_FILE, "a") as f:
        f.write(f"{pedido['nombre']}|{pedido['direccion']}|{pedido['telefono']}|{pedido['size']}|{','.join(pedido['ingredientes'])}|{pedido['num_pizzas']}|{pedido['subtotal']}\n")

def cargar_pedidos():
    """Carga los pedidos desde el archivo con validación para evitar errores."""
    pedidos = []
    if os.path.exists(PEDIDOS_FILE):
        with open(PEDIDOS_FILE, "r") as f:
            for linea in f:
                datos = linea.strip().split("|")
                
                if len(datos) != 7:
                    print(f"Error: Línea mal formada en pedidos.txt -> {linea.strip()}")
                    continue  

                try:
                    pedidos.append({
                        "nombre": datos[0],
                        "direccion": datos[1],
                        "telefono": datos[2],
                        "size": datos[3],
                        "ingredientes": datos[4].split(",") if datos[4] else [],
                        "num_pizzas": int(datos[5]),
                        "subtotal": float(datos[6])
                    })
                except ValueError as e:
                    print(f"Error al convertir datos: {e}, en línea: {linea.strip()}")
                    continue  

    return pedidos


@app.route('/index')
@login_required
def index():
    create_form = forms.ClientesForm(request.form)
    pedidos = cargar_pedidos()  
    ventas = Venta.query.all()
    total_ventas = sum(venta.montoTotal for venta in ventas)

    return render_template("index.html", pedidos=pedidos, form=create_form, ventas=ventas, total_ventas=total_ventas)

@app.route('/pedido', methods=['GET', 'POST'])
def pedido():
    if request.method == 'POST':
        nombre = request.form['nombre']
        direccion = request.form['direccion']
        telefono = request.form['telefono']
        size = request.form['size']
        ingredientes = request.form.getlist('ingredientes')
        num_pizzas = int(request.form['num_pizzas'])

        precios = {"chica": 40, "mediana": 80, "grande": 120}
        precio_unitario = precios.get(size, 40)
        precio_ingrediente = 10
        subtotal = (precio_unitario + (precio_ingrediente * len(ingredientes))) * num_pizzas

        pedido = {
            "nombre": nombre,
            "direccion": direccion,
            "telefono": telefono,
            "size": size,
            "ingredientes": ingredientes,
            "num_pizzas": num_pizzas,
            "subtotal": subtotal
        }
        guardar_pedido(pedido)  

        flash(f"Pedido guardado en archivo correctamente. Total: ${subtotal:.2f}", "success")
        return redirect(url_for('index'))

    return render_template('index.html')


@app.route('/terminar', methods=['POST'])
def terminar_pedidos():
    """Transfiere los pedidos del archivo a la base de datos y limpia el archivo."""
    pedidos = cargar_pedidos()

    if not pedidos:
        flash("No hay pedidos para transferir.", "warning")
        return redirect(url_for('index'))

    for pedido in pedidos:
        cliente = Cliente.query.filter_by(nombre=pedido["nombre"], telefono=pedido["telefono"]).first()
        if not cliente:
            cliente = Cliente(nombre=pedido["nombre"], direccion=pedido["direccion"], telefono=pedido["telefono"])
            db.session.add(cliente)
            db.session.commit()

        nuevo_pedido = Pedidos(
            tamanio=pedido["size"],
            ingredientes=", ".join(pedido["ingredientes"]),
            cantidad=pedido["num_pizzas"]
        )
        db.session.add(nuevo_pedido)
        db.session.commit()

        precios = {"chica": 40, "mediana": 80, "grande": 120}
        precio_unitario = precios.get(pedido["size"], 40)
        precio_ingrediente = 10
        subtotal = (precio_unitario + (precio_ingrediente * len(pedido["ingredientes"]))) * pedido["num_pizzas"]

        nueva_venta = Venta(
            idPedido=nuevo_pedido.id,
            idCliente=cliente.id,
            montoTotal=subtotal,
            size=pedido["size"],
            ingredientes=", ".join(pedido["ingredientes"]),
            num_pizzas=pedido["num_pizzas"],
            subtotal=subtotal
        )
        db.session.add(nueva_venta)

    db.session.commit()

    open(PEDIDOS_FILE, "w").close()  

    flash("Pedidos enviados a la base de datos correctamente.", "success")
    return redirect(url_for('index'))


@app.route('/quitar_pedido/<int:index>', methods=['POST'])
def quitar_pedido(index):
    with open("pedidos.txt", "r") as file:
        pedidos = file.readlines()
    
    if 0 <= index < len(pedidos):
        del pedidos[index]  

        with open("pedidos.txt", "w") as file:
            file.writelines(pedidos) 

    return redirect(url_for('index'))  


@app.route('/ventas-clientes', methods=['GET'])
@login_required
def ventas_clientes():
    ventas = Venta.query.order_by(Venta.fechaVenta.desc()).all()
    
    clientes = Cliente.query.all()
    
    total_ventas = sum(venta.subtotal for venta in ventas)
    total_clientes = len(clientes)
    total_pizzas = sum(venta.num_pizzas for venta in ventas)
    
    return render_template(
        'clientes.html',
        ventas=ventas,
        clientes=clientes,
        total_ventas=total_ventas,
        total_clientes=total_clientes,
        total_pizzas=total_pizzas
    )

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nombre = request.form['nombre']
        contrasenia = request.form['contrasenia']

        cliente = Cliente.query.filter_by(nombre=nombre).first()

        if cliente and cliente.contrasenia == contrasenia:  # En un caso real, usa hashes
            login_user(cliente)
            flash("Inicio de sesión exitoso.", "success")
            return redirect(url_for('index'))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Has cerrado sesión.", "success")
    return redirect(url_for('index'))

with app.app_context():
    db.create_all()

# Iniciar la aplicación
if __name__ == '__main__':
    app.run(debug=True)
