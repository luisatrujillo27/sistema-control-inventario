"""Sistema de gestión y control de inventario.

Aplicación Flask con cinco módulos: resumen, productos, entradas y salidas,
historial y alertas. Los datos se guardan en SQLite (ver `db.py`), así que
todo lo que se registra en el navegador sigue ahí al reiniciar el servidor.

Las alertas de stock se resuelven con el patrón Observer (ver `observer.py`).
"""

import os
from functools import wraps

from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

import db
from observer import (
    NIVEL_BAJO,
    NIVEL_EXCESO,
    ConsolaObserver,
    StockObserver,
    Subject,
    clasificar,
    describir,
)

app = Flask(__name__)
# Clave fija: es un proyecto académico de demostración, no maneja datos reales.
app.secret_key = os.environ.get("SECRET_KEY", "sistema-control-inventario-itm")

# --------------------------------------------------------------------------
# Usuarios del sistema
#
# Credenciales fijas de demostración: no hay registro ni contraseñas reales,
# y por eso tampoco se cifran. El rol decide qué puede hacer cada quien.
# --------------------------------------------------------------------------
USUARIOS = {
    "laura": {
        "clave": "1234",
        "nombre": "Laura Gómez",
        "rol": "encargado",
        "cargo": "Encargada de inventario",
    },
    "admin": {
        "clave": "1234",
        "nombre": "Carlos Restrepo",
        "rol": "administrador",
        "cargo": "Administrador",
    },
}

# Unidades y categorías que ofrece el formulario de productos.
UNIDADES = ["Unidad", "Bolsa", "Botella", "Paquete", "Cubeta", "Kilo", "Litro", "Caja"]

MOTIVOS_SALIDA = [
    "Venta en mostrador",
    "Pedido a domicilio",
    "Producto vencido",
    "Avería o daño",
    "Devolución a proveedor",
    "Consumo interno",
]

# --------------------------------------------------------------------------
# Montaje del patrón Observer
# --------------------------------------------------------------------------
inventario = Subject()
observador_stock = StockObserver()
inventario.attach(observador_stock)
inventario.attach(ConsolaObserver())


# --------------------------------------------------------------------------
# Sesión y permisos
# --------------------------------------------------------------------------

def requiere_sesion(vista):
    """Manda al login a quien no haya iniciado sesión."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login", siguiente=request.path))
        return vista(*args, **kwargs)

    return envoltura


def requiere_administrador(vista):
    """Restringe la vista al rol de administrador."""

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login", siguiente=request.path))
        if session.get("rol") != "administrador":
            flash("Esa acción es solo para el administrador.", "danger")
            return redirect(url_for("productos"))
        return vista(*args, **kwargs)

    return envoltura


@app.context_processor
def datos_comunes():
    """Variables que todas las plantillas necesitan (barra superior y menú)."""
    if "usuario" not in session:
        return {}

    productos = db.listar_productos(solo_activos=True)
    alertas = [p for p in productos if clasificar(p) != "normal"]
    return {
        "total_alertas": len(alertas),
        "usuario_nombre": session.get("nombre"),
        "usuario_cargo": session.get("cargo"),
        "usuario_rol": session.get("rol"),
    }


# --------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------

def leer_entero(campo, defecto=0):
    """Lee un entero del formulario sin reventar si viene vacío o con texto."""
    try:
        return int(request.form.get(campo, defecto))
    except (TypeError, ValueError):
        return defecto


def leer_decimal(campo, defecto=0.0):
    """Lee un número con decimales del formulario."""
    try:
        return float(str(request.form.get(campo, defecto)).replace(",", "."))
    except (TypeError, ValueError):
        return defecto


def avisar_alertas():
    """Convierte en mensajes flash las alertas que levantó el observador."""
    for alerta in observador_stock.recoger_alertas():
        if alerta["tipo"] == NIVEL_BAJO:
            flash(
                f"{alerta['nombre']} quedó en {alerta['existencia']} "
                f"(mínimo {alerta['minimo']}). Hay que reponer.",
                "warning",
            )
        elif alerta["tipo"] == NIVEL_EXCESO:
            flash(
                f"{alerta['nombre']} llegó a {alerta['existencia']} "
                f"(máximo {alerta['maximo']}). Hay sobre stock.",
                "warning",
            )


def revisar_todo():
    """Notifica cada producto activo para refrescar la memoria del observador."""
    for producto in db.listar_productos(solo_activos=True):
        inventario.notify(producto)


# --------------------------------------------------------------------------
# Autenticación
# --------------------------------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip().lower()
        clave = request.form.get("clave", "")
        datos = USUARIOS.get(usuario)

        if datos is None or datos["clave"] != clave:
            flash("Usuario o contraseña incorrectos.", "danger")
            return render_template("login.html", usuario=usuario), 401

        session["usuario"] = usuario
        session["nombre"] = datos["nombre"]
        session["rol"] = datos["rol"]
        session["cargo"] = datos["cargo"]

        # Al entrar se revisa el inventario para que el observador sepa en qué
        # nivel está cada producto, pero sin anunciar alertas: no hubo un
        # movimiento del usuario que las provoque.
        observador_stock.olvidar()
        revisar_todo()
        observador_stock.recoger_alertas()

        destino = request.args.get("siguiente") or url_for("resumen")
        # Solo se acepta una ruta interna, nunca una URL de otro sitio.
        if not destino.startswith("/"):
            destino = url_for("resumen")
        return redirect(destino)

    if "usuario" in session:
        return redirect(url_for("resumen"))
    return render_template("login.html", usuario="")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "info")
    return redirect(url_for("login"))


# --------------------------------------------------------------------------
# Módulo 1: resumen general
# --------------------------------------------------------------------------

@app.route("/")
@requiere_sesion
def resumen():
    productos = [describir(p) for p in db.listar_productos(solo_activos=True)]

    bajos = [p for p in productos if p["nivel"] == NIVEL_BAJO]
    excesos = [p for p in productos if p["nivel"] == NIVEL_EXCESO]
    valor = sum(p["existencia"] * p["precio"] for p in productos)

    # Reparto por categoría, para la tabla de distribución.
    categorias = {}
    for producto in productos:
        datos = categorias.setdefault(
            producto["categoria"], {"productos": 0, "unidades": 0, "valor": 0}
        )
        datos["productos"] += 1
        datos["unidades"] += producto["existencia"]
        datos["valor"] += producto["existencia"] * producto["precio"]

    categorias = sorted(
        ({"nombre": k, **v} for k, v in categorias.items()),
        key=lambda c: c["valor"],
        reverse=True,
    )

    return render_template(
        "resumen.html",
        activo="resumen",
        productos=productos,
        bajos=bajos,
        excesos=excesos,
        valor_total=valor,
        categorias=categorias,
        hoy=db.contar_movimientos_de_hoy(),
        ultimos=db.listar_movimientos(limite=8),
    )


# --------------------------------------------------------------------------
# Módulo 2: productos
# --------------------------------------------------------------------------

@app.route("/productos")
@requiere_sesion
def productos():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado", "activos")

    lista = db.listar_productos(
        solo_activos=(estado == "activos"), busqueda=busqueda
    )
    lista = [describir(p) for p in lista]

    return render_template(
        "productos.html",
        activo="productos",
        productos=lista,
        busqueda=busqueda,
        estado=estado,
        unidades=UNIDADES,
        codigo_sugerido=db.siguiente_codigo(),
    )


@app.route("/productos/nuevo", methods=["POST"])
@requiere_administrador
def producto_nuevo():
    codigo = request.form.get("codigo", "").strip().upper()
    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "").strip()

    if not codigo or not nombre or not categoria:
        flash("Código, nombre y categoría son obligatorios.", "danger")
        return redirect(url_for("productos"))

    minimo = leer_entero("minimo")
    maximo = leer_entero("maximo")
    if maximo and maximo <= minimo:
        flash("El nivel máximo debe ser mayor que el mínimo.", "danger")
        return redirect(url_for("productos"))

    ok, mensaje = db.crear_producto({
        "codigo": codigo,
        "nombre": nombre,
        "categoria": categoria,
        "unidad": request.form.get("unidad", "Unidad"),
        "precio": leer_decimal("precio"),
        "existencia": leer_entero("existencia"),
        "minimo": minimo,
        "maximo": maximo,
    })

    flash(mensaje, "success" if ok else "danger")
    if ok:
        inventario.notify(db.obtener_producto(codigo))
        avisar_alertas()
    return redirect(url_for("productos"))


@app.route("/productos/<codigo>/editar", methods=["POST"])
@requiere_administrador
def producto_editar(codigo):
    nombre = request.form.get("nombre", "").strip()
    categoria = request.form.get("categoria", "").strip()

    if not nombre or not categoria:
        flash("Nombre y categoría son obligatorios.", "danger")
        return redirect(url_for("productos"))

    minimo = leer_entero("minimo")
    maximo = leer_entero("maximo")
    if maximo and maximo <= minimo:
        flash("El nivel máximo debe ser mayor que el mínimo.", "danger")
        return redirect(url_for("productos"))

    ok, mensaje = db.actualizar_producto(codigo, {
        "nombre": nombre,
        "categoria": categoria,
        "unidad": request.form.get("unidad", "Unidad"),
        "precio": leer_decimal("precio"),
        "minimo": minimo,
        "maximo": maximo,
    })

    flash(mensaje, "success" if ok else "danger")
    if ok:
        # Cambiar los límites puede dejar el producto fuera de rango.
        inventario.notify(db.obtener_producto(codigo))
        avisar_alertas()
    return redirect(url_for("productos"))


@app.route("/productos/<codigo>/estado", methods=["POST"])
@requiere_administrador
def producto_estado(codigo):
    ok, mensaje = db.alternar_estado(codigo)
    flash(mensaje, "success" if ok else "danger")
    return redirect(url_for("productos", q=request.form.get("q", ""),
                            estado=request.form.get("estado", "activos")))


# --------------------------------------------------------------------------
# Módulo 3: entradas y salidas
# --------------------------------------------------------------------------

@app.route("/movimientos")
@requiere_sesion
def movimientos():
    lista = [describir(p) for p in db.listar_productos(solo_activos=True)]
    return render_template(
        "movimientos.html",
        activo="movimientos",
        productos=lista,
        motivos=MOTIVOS_SALIDA,
        seleccionado=request.args.get("producto", ""),
        ultimos=db.listar_movimientos(limite=10),
    )


@app.route("/movimientos", methods=["POST"])
@requiere_sesion
def movimiento_registrar():
    codigo = request.form.get("producto", "")
    tipo = request.form.get("tipo", "")
    cantidad = leer_entero("cantidad")

    if tipo == "entrada":
        proveedor = request.form.get("proveedor", "").strip()
        if not proveedor:
            flash("Indica el proveedor de la entrada.", "danger")
            return redirect(url_for("movimientos", producto=codigo))
        factura = request.form.get("factura", "").strip()
        detalle = f"Proveedor: {proveedor}"
        if factura:
            detalle += f" · Factura {factura}"
    else:
        motivo = request.form.get("motivo", "").strip()
        detalle = f"Motivo: {motivo}" if motivo else "Motivo: no indicado"

    ok, mensaje, producto = db.registrar_movimiento(
        codigo, tipo, cantidad, detalle, session.get("nombre", "")
    )

    if not ok:
        flash(mensaje, "danger")
        return redirect(url_for("movimientos", producto=codigo))

    flash(mensaje, "success")
    # El cambio se comunica al inventario, que avisa a sus observadores.
    inventario.notify(producto)
    avisar_alertas()
    return redirect(url_for("movimientos", producto=codigo))


# --------------------------------------------------------------------------
# Módulo 4: historial
# --------------------------------------------------------------------------

@app.route("/historial")
@requiere_sesion
def historial():
    filtros = {
        "tipo": request.args.get("tipo", ""),
        "producto": request.args.get("producto", "").strip(),
        "desde": request.args.get("desde", ""),
        "hasta": request.args.get("hasta", ""),
    }
    lista = db.listar_movimientos(**filtros)

    return render_template(
        "historial.html",
        activo="historial",
        movimientos=lista,
        filtros=filtros,
    )


# --------------------------------------------------------------------------
# Módulo 5: niveles y alertas
# --------------------------------------------------------------------------

@app.route("/alertas")
@requiere_sesion
def alertas():
    productos = [describir(p) for p in db.listar_productos(solo_activos=True)]

    return render_template(
        "alertas.html",
        activo="alertas",
        bajos=[p for p in productos if p["nivel"] == NIVEL_BAJO],
        excesos=[p for p in productos if p["nivel"] == NIVEL_EXCESO],
        normales=[p for p in productos if p["nivel"] == "normal"],
    )


# --------------------------------------------------------------------------
# Reinicio de la demostración
# --------------------------------------------------------------------------

@app.route("/reiniciar", methods=["POST"])
@requiere_administrador
def reiniciar():
    db.inicializar(forzar=True)
    observador_stock.olvidar()
    revisar_todo()
    observador_stock.recoger_alertas()
    flash("Los datos volvieron a su estado inicial.", "info")
    return redirect(url_for("resumen"))


# La base se prepara al importar el módulo, para que las pruebas y el
# servidor encuentren siempre las tablas creadas.
db.inicializar()


if __name__ == "__main__":
    app.run(debug=True)
