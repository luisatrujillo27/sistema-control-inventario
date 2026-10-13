
from flask import Flask, render_template, request, redirect, url_for
from observer import Subject, StockObserver

app = Flask(__name__)

productos = [
    {"id": 1, "nombre": "Arroz", "cantidad": 6, "minimo": 10},
    {"id": 2, "nombre": "Leche", "cantidad": 25, "minimo": 10},
    {"id": 3, "nombre": "Aceite", "cantidad": 4, "minimo": 8},
]

# Configurar el patron Observer
inventario = Subject()
observador_stock = StockObserver()
inventario.attach(observador_stock)

# Revisar el estado inicial de los productos
for producto in productos:
    inventario.notify(producto)


@app.route("/")
def inicio():
    return render_template("index.html", productos=productos)


@app.route("/salida", methods=["POST"])
def registrar_salida():
    producto_id = int(request.form["producto_id"])
    cantidad = int(request.form["cantidad"])

    for producto in productos:
        if producto["id"] == producto_id:
            if 0 < cantidad <= producto["cantidad"]:
                producto["cantidad"] -= cantidad

                # Notificar el cambio al observador
                inventario.notify(producto)
            break

    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)

