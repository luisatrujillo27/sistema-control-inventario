"""Capa de persistencia en SQLite.

El inventario deja de vivir en memoria: lo que se registra en el navegador
queda guardado en el archivo `inventario.db` y sigue ahí al reiniciar.

Se usa `sqlite3`, que viene con Python: el proyecto no suma dependencias.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime

# Ruta del archivo de base de datos, junto al código del proyecto.
RUTA_BD = os.path.join(os.path.dirname(os.path.abspath(__file__)), "inventario.db")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS productos (
    codigo      TEXT PRIMARY KEY,
    nombre      TEXT    NOT NULL,
    categoria   TEXT    NOT NULL,
    unidad      TEXT    NOT NULL,
    precio      REAL    NOT NULL DEFAULT 0,
    existencia  INTEGER NOT NULL DEFAULT 0,
    minimo      INTEGER NOT NULL DEFAULT 0,
    maximo      INTEGER NOT NULL DEFAULT 0,
    activo      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS movimientos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha        TEXT    NOT NULL,
    tipo         TEXT    NOT NULL CHECK (tipo IN ('entrada', 'salida')),
    producto     TEXT    NOT NULL REFERENCES productos(codigo),
    cantidad     INTEGER NOT NULL,
    resultante   INTEGER NOT NULL,
    detalle      TEXT    NOT NULL DEFAULT '',
    responsable  TEXT    NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_mov_producto ON movimientos(producto);
CREATE INDEX IF NOT EXISTS idx_mov_fecha    ON movimientos(fecha);
"""

# Catálogo de arranque: una tienda de barrio de Medellín.
# (codigo, nombre, categoria, unidad, precio, existencia, minimo, maximo)
CATALOGO_INICIAL = [
    ("P001", "Arroz Diana 500 g", "Granos y Cereales", "Unidad", 2400, 45, 15, 80),
    ("P002", "Aceite Girasol 1 L", "Aceites y Grasas", "Botella", 8900, 8, 10, 40),
    ("P003", "Leche Colanta 1 L", "Lácteos", "Bolsa", 4200, 47, 20, 60),
    ("P004", "Fríjol cargamanto 500 g", "Granos y Cereales", "Bolsa", 5600, 25, 10, 50),
    ("P005", "Azúcar Manuelita 1 kg", "Endulzantes", "Bolsa", 4800, 12, 12, 45),
    ("P006", "Huevos AA cubeta x30", "Huevos y Lácteos", "Cubeta", 16500, 18, 8, 30),
    ("P007", "Café Sello Rojo 250 g", "Bebidas", "Paquete", 7200, 30, 10, 50),
    ("P008", "Jabón Rey barra", "Aseo Hogar", "Unidad", 3100, 5, 10, 40),
    ("P009", "Panela redonda 500 g", "Endulzantes", "Unidad", 2800, 28, 20, 60),
    ("P010", "Arepa de maíz blanco x5", "Panadería", "Paquete", 3500, 12, 20, 50),
    ("P011", "Chocolate Corona 500 g", "Bebidas", "Paquete", 9100, 60, 20, 90),
    ("P012", "Atún Van Camp's 160 g", "Enlatados", "Unidad", 6400, 70, 30, 120),
    ("P013", "Gaseosa Postobón 1.5 L", "Bebidas", "Botella", 4500, 48, 24, 90),
    ("P014", "Agua Cristal 600 ml", "Bebidas", "Botella", 2000, 120, 50, 200),
    ("P015", "Plátano maduro", "Frutas y Verduras", "Kilo", 3800, 7, 15, 60),
    ("P016", "Papa criolla", "Frutas y Verduras", "Kilo", 4100, 55, 20, 90),
    ("P017", "Salchichón Zenú 500 g", "Carnes Frías", "Unidad", 11200, 9, 10, 35),
    ("P018", "Pan tajado 500 g", "Panadería", "Paquete", 5300, 16, 12, 40),
]

# Movimientos de ejemplo para que el historial no arranque vacío.
# (codigo, tipo, cantidad, detalle)
MOVIMIENTOS_INICIALES = [
    ("P001", "entrada", 45, "Proveedor: Distribuidora del Valle"),
    ("P003", "entrada", 20, "Proveedor: Colanta"),
    ("P002", "salida", 5, "Motivo: Venta en mostrador"),
    ("P008", "salida", 7, "Motivo: Pedido a domicilio"),
    ("P015", "salida", 8, "Motivo: Venta en mostrador"),
]


@contextmanager
def conectar():
    """Abre una conexión, confirma al salir y la cierra siempre.

    Es un gestor propio a propósito: `with sqlite3.connect(...)` confirma la
    transacción pero *no* cierra la conexión, y en Windows eso deja el archivo
    bloqueado.
    """
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    # Hace respetar las claves foráneas, que SQLite desactiva por defecto.
    conexion.execute("PRAGMA foreign_keys = ON")
    try:
        yield conexion
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def inicializar(forzar=False):
    """Crea las tablas y, si el catálogo está vacío, siembra los datos.

    Con `forzar=True` borra el contenido y lo vuelve a sembrar: es lo que
    hace el botón «Reiniciar datos» de la interfaz.
    """
    with conectar() as conexion:
        conexion.executescript(ESQUEMA)

        if forzar:
            conexion.execute("DELETE FROM movimientos")
            conexion.execute("DELETE FROM productos")
            # Deja los IDs de movimiento empezando otra vez en 1.
            conexion.execute("DELETE FROM sqlite_sequence WHERE name = 'movimientos'")

        hay_datos = conexion.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        if hay_datos:
            return

        conexion.executemany(
            """INSERT INTO productos
               (codigo, nombre, categoria, unidad, precio, existencia, minimo, maximo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            CATALOGO_INICIAL,
        )

        # Los movimientos de ejemplo se fechan hacia atrás para que el
        # historial muestre un orden creíble.
        marca = datetime.now().replace(microsecond=0)
        for posicion, (codigo, tipo, cantidad, detalle) in enumerate(MOVIMIENTOS_INICIALES):
            fila = conexion.execute(
                "SELECT existencia FROM productos WHERE codigo = ?", (codigo,)
            ).fetchone()
            conexion.execute(
                """INSERT INTO movimientos
                   (fecha, tipo, producto, cantidad, resultante, detalle, responsable)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    marca.isoformat(timespec="seconds"),
                    tipo,
                    codigo,
                    cantidad,
                    fila["existencia"],
                    detalle,
                    "sistema",
                ),
            )


# --------------------------------------------------------------------------
# Productos
# --------------------------------------------------------------------------

def listar_productos(solo_activos=False, busqueda=""):
    """Devuelve los productos del catálogo como lista de diccionarios."""
    sentencia = "SELECT * FROM productos"
    condiciones = []
    parametros = []

    if solo_activos:
        condiciones.append("activo = 1")

    if busqueda:
        condiciones.append("(codigo LIKE ? OR nombre LIKE ? OR categoria LIKE ?)")
        comodin = f"%{busqueda}%"
        parametros += [comodin, comodin, comodin]

    if condiciones:
        sentencia += " WHERE " + " AND ".join(condiciones)
    sentencia += " ORDER BY codigo"

    with conectar() as conexion:
        return [dict(fila) for fila in conexion.execute(sentencia, parametros)]


def obtener_producto(codigo):
    """Devuelve un producto por su código, o None si no existe."""
    with conectar() as conexion:
        fila = conexion.execute(
            "SELECT * FROM productos WHERE codigo = ?", (codigo,)
        ).fetchone()
    return dict(fila) if fila else None


def siguiente_codigo():
    """Propone el siguiente código libre con el formato P###."""
    with conectar() as conexion:
        filas = conexion.execute(
            "SELECT codigo FROM productos WHERE codigo LIKE 'P%'"
        ).fetchall()

    numeros = []
    for fila in filas:
        resto = fila["codigo"][1:]
        if resto.isdigit():
            numeros.append(int(resto))

    return "P%03d" % ((max(numeros) + 1) if numeros else 1)


def crear_producto(datos):
    """Inserta un producto nuevo. Devuelve (ok, mensaje)."""
    if obtener_producto(datos["codigo"]):
        return False, f"Ya existe un producto con el código {datos['codigo']}."

    with conectar() as conexion:
        conexion.execute(
            """INSERT INTO productos
               (codigo, nombre, categoria, unidad, precio, existencia, minimo, maximo, activo)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (
                datos["codigo"],
                datos["nombre"],
                datos["categoria"],
                datos["unidad"],
                datos["precio"],
                datos["existencia"],
                datos["minimo"],
                datos["maximo"],
            ),
        )
    return True, f"Producto {datos['codigo']} creado."


def actualizar_producto(codigo, datos):
    """Edita los datos de un producto. La existencia solo cambia por movimientos."""
    if not obtener_producto(codigo):
        return False, "El producto no existe."

    with conectar() as conexion:
        conexion.execute(
            """UPDATE productos
               SET nombre = ?, categoria = ?, unidad = ?, precio = ?,
                   minimo = ?, maximo = ?
               WHERE codigo = ?""",
            (
                datos["nombre"],
                datos["categoria"],
                datos["unidad"],
                datos["precio"],
                datos["minimo"],
                datos["maximo"],
                codigo,
            ),
        )
    return True, f"Producto {codigo} actualizado."


def alternar_estado(codigo):
    """Activa o desactiva un producto. Devuelve (ok, mensaje)."""
    producto = obtener_producto(codigo)
    if not producto:
        return False, "El producto no existe."

    nuevo = 0 if producto["activo"] else 1
    with conectar() as conexion:
        conexion.execute(
            "UPDATE productos SET activo = ? WHERE codigo = ?", (nuevo, codigo)
        )

    estado = "activado" if nuevo else "desactivado"
    return True, f"Producto {codigo} {estado}."


# --------------------------------------------------------------------------
# Movimientos
# --------------------------------------------------------------------------

def pluralizar(unidad, cantidad):
    """Pone la unidad en plural cuando hace falta: 1 unidad, 24 unidades.

    Basta con la regla simple del español, porque todas las unidades que
    maneja el catálogo terminan en vocal o en consonante sencilla.
    """
    unidad = unidad.lower()
    if cantidad == 1:
        return unidad
    return unidad + ("s" if unidad[-1] in "aeiou" else "es")


def registrar_movimiento(codigo, tipo, cantidad, detalle, responsable):
    """Aplica una entrada o salida y la deja asentada en el historial.

    Devuelve (ok, mensaje, producto_actualizado).
    """
    producto = obtener_producto(codigo)
    if not producto:
        return False, "El producto no existe.", None

    if not producto["activo"]:
        return False, f"{producto['nombre']} está desactivado.", None

    if cantidad <= 0:
        return False, "La cantidad debe ser mayor que cero.", None

    if tipo == "entrada":
        nueva = producto["existencia"] + cantidad
    elif tipo == "salida":
        if cantidad > producto["existencia"]:
            return (
                False,
                f"Solo hay {producto['existencia']} de {producto['nombre']}.",
                None,
            )
        nueva = producto["existencia"] - cantidad
    else:
        return False, "Tipo de movimiento no válido.", None

    with conectar() as conexion:
        conexion.execute(
            "UPDATE productos SET existencia = ? WHERE codigo = ?", (nueva, codigo)
        )
        conexion.execute(
            """INSERT INTO movimientos
               (fecha, tipo, producto, cantidad, resultante, detalle, responsable)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now().isoformat(timespec="seconds"),
                tipo,
                codigo,
                cantidad,
                nueva,
                detalle,
                responsable,
            ),
        )

    producto["existencia"] = nueva
    verbo = "Entrada" if tipo == "entrada" else "Salida"
    mensaje = (
        f"{verbo} de {cantidad} {pluralizar(producto['unidad'], cantidad)} "
        f"de {producto['nombre']}."
    )
    return True, mensaje, producto


def listar_movimientos(tipo="", producto="", desde="", hasta="", limite=None):
    """Devuelve el historial, de lo más reciente a lo más antiguo."""
    sentencia = """
        SELECT m.*, p.nombre AS producto_nombre, p.unidad AS producto_unidad
        FROM movimientos m
        LEFT JOIN productos p ON p.codigo = m.producto
    """
    condiciones = []
    parametros = []

    if tipo in ("entrada", "salida"):
        condiciones.append("m.tipo = ?")
        parametros.append(tipo)

    if producto:
        condiciones.append("(m.producto LIKE ? OR p.nombre LIKE ?)")
        comodin = f"%{producto}%"
        parametros += [comodin, comodin]

    if desde:
        condiciones.append("date(m.fecha) >= date(?)")
        parametros.append(desde)

    if hasta:
        condiciones.append("date(m.fecha) <= date(?)")
        parametros.append(hasta)

    if condiciones:
        sentencia += " WHERE " + " AND ".join(condiciones)

    sentencia += " ORDER BY m.id DESC"
    if limite:
        sentencia += f" LIMIT {int(limite)}"

    with conectar() as conexion:
        return [dict(fila) for fila in conexion.execute(sentencia, parametros)]


def contar_movimientos_de_hoy():
    """Cuántas entradas y salidas se registraron hoy."""
    with conectar() as conexion:
        fila = conexion.execute(
            """SELECT
                 SUM(CASE WHEN tipo = 'entrada' THEN 1 ELSE 0 END) AS entradas,
                 SUM(CASE WHEN tipo = 'salida'  THEN 1 ELSE 0 END) AS salidas
               FROM movimientos
               WHERE date(fecha) = date('now', 'localtime')"""
        ).fetchone()

    return {"entradas": fila["entradas"] or 0, "salidas": fila["salidas"] or 0}
