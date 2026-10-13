"""Mock-up del sistema de control de inventario de un supermercado."""

from copy import deepcopy

from flask import Flask, flash, get_flashed_messages, redirect, render_template, request, url_for

from observer import ConsolaObserver, StockObserver, Subject

app = Flask(__name__)
# Clave fija: es un mock-up de demostración, no maneja datos reales.
app.secret_key = "sistema-control-inventario-mockup"

# Inventario base de una tienda de barrio en Medellín.
INVENTARIO_INICIAL = [
    {"id": "001", "nombre": "Arroz Diana (1 kg)", "cantidad": 150, "minimo": 50},
    {"id": "002", "nombre": "Fríjol cargamanto (500 g)", "cantidad": 40, "minimo": 25},
    {"id": "003", "nombre": "Panela redonda (500 g)", "cantidad": 28, "minimo": 20},
    {"id": "004", "nombre": "Maíz trillado para mazamorra (500 g)", "cantidad": 18, "minimo": 15},
    {"id": "005", "nombre": "Arepa de maíz blanco (x5)", "cantidad": 12, "minimo": 20},
    {"id": "006", "nombre": "Chocolate Corona (500 g)", "cantidad": 60, "minimo": 20},
    {"id": "007", "nombre": "Café Sello Rojo (250 g)", "cantidad": 35, "minimo": 20},
    {"id": "008", "nombre": "Leche Colanta (1 L)", "cantidad": 90, "minimo": 40},
    {"id": "009", "nombre": "Huevos AA (cubeta x30)", "cantidad": 14, "minimo": 10},
    {"id": "010", "nombre": "Aceite Girasol (1 L)", "cantidad": 85, "minimo": 30},
    {"id": "011", "nombre": "Azúcar Manuelita (1 kg)", "cantidad": 22, "minimo": 25},
    {"id": "012", "nombre": "Pan tajado (500 g)", "cantidad": 16, "minimo": 12},
    {"id": "013", "nombre": "Salchichón Zenú (500 g)", "cantidad": 9, "minimo": 10},
    {"id": "014", "nombre": "Atún Van Camp's (160 g)", "cantidad": 70, "minimo": 30},
    {"id": "015", "nombre": "Gaseosa Postobón Manzana (1.5 L)", "cantidad": 48, "minimo": 24},
    {"id": "016", "nombre": "Agua Cristal (600 ml)", "cantidad": 120, "minimo": 50},
    {"id": "017", "nombre": "Plátano maduro (kg)", "cantidad": 7, "minimo": 15},
    {"id": "018", "nombre": "Papa criolla (kg)", "cantidad": 55, "minimo": 20},
]

# Estado en memoria. Al ser un mock-up no hay base de datos.
productos = deepcopy(INVENTARIO_INICIAL)

# Montaje del patrón Observer.
inventario = Subject()
observador_stock = StockObserver()
inventario.attach(observador_stock)
inventario.attach(ConsolaObserver())


def revisar_inventario_completo():
    """Notifica todos los productos para que tengan estado calculado."""
    for producto in productos:
        inventario.notify(producto)


def buscar_producto(producto_id):
    """Devuelve el producto con ese id, o None si no existe."""
    for producto in productos:
        if producto["id"] == producto_id:
            return producto
    return None


revisar_inventario_completo()
# El arranque no es un movimiento del usuario: no se muestran esas alertas.
observador_stock.recoger_alertas()


@app.route("/")
def inicio():
    return render_template("index.html", productos=productos)


@app.route("/movimiento", methods=["POST"])
def registrar_movimiento():
    """Registra una entrada o una salida y notifica al observador."""
    producto = buscar_producto(request.form.get("producto_id", ""))
    tipo = request.form.get("tipo", "")

    try:
        cantidad = int(request.form.get("cantidad", 0))
    except ValueError:
        cantidad = 0

    if producto is None:
        flash("El producto seleccionado no existe.", "error")
        return redirect(url_for("inicio"))

    if cantidad <= 0:
        flash("La cantidad debe ser mayor que cero.", "error")
        return redirect(url_for("inicio"))

    if tipo == "entrada":
        producto["cantidad"] += cantidad
    elif tipo == "salida":
        if cantidad > producto["cantidad"]:
            flash(
                f"Solo hay {producto['cantidad']} unidades de "
                f"{producto['nombre']}.",
                "error",
            )
            return redirect(url_for("inicio"))
        producto["cantidad"] -= cantidad
    else:
        flash("Tipo de movimiento no válido.", "error")
        return redirect(url_for("inicio"))

    # El cambio se comunica al inventario, que avisa a sus observadores.
    inventario.notify(producto)

    flash(
        f"Se registró una {tipo} de {cantidad} unidades de "
        f"{producto['nombre']}.",
        "exito",
    )
    for alerta in observador_stock.recoger_alertas():
        flash(f"{alerta['nombre']}|{alerta['cantidad']}", "alerta")

    return redirect(url_for("inicio"))


@app.route("/reiniciar", methods=["POST"])
def reiniciar_inventario():
    """Devuelve el inventario a su estado inicial."""
    global productos
    productos = deepcopy(INVENTARIO_INICIAL)
    revisar_inventario_completo()
    observador_stock.recoger_alertas()
    get_flashed_messages()
    flash("Inventario reiniciado.", "exito")
    return redirect(url_for("inicio"))


if __name__ == "__main__":
    app.run(debug=True)
