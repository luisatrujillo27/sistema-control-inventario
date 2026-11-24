"""Pruebas de las rutas, los movimientos y las validaciones.

Cada prueba corre contra una base de datos temporal propia, así no toca
el `inventario.db` real ni deja residuos entre pruebas.
"""

import os
import tempfile
import unittest

import app as aplicacion
import db


class PruebaConBaseTemporal(unittest.TestCase):
    """Base común: BD temporal, cliente de prueba y sesión iniciada."""

    usuario = "admin"

    def setUp(self):
        descriptor, self.ruta_bd = tempfile.mkstemp(suffix=".db")
        os.close(descriptor)

        self.ruta_original = db.RUTA_BD
        db.RUTA_BD = self.ruta_bd
        db.inicializar(forzar=True)

        aplicacion.app.config["TESTING"] = True
        self.cliente = aplicacion.app.test_client()
        aplicacion.observador_stock.olvidar()

        if self.usuario:
            self.entrar(self.usuario)

    def tearDown(self):
        db.RUTA_BD = self.ruta_original
        os.unlink(self.ruta_bd)

    def entrar(self, usuario, clave="1234"):
        return self.cliente.post(
            "/login", data={"usuario": usuario, "clave": clave}, follow_redirects=True
        )

    def mover(self, **datos):
        """Registra un movimiento y devuelve la respuesta ya seguida."""
        datos.setdefault("tipo", "salida")
        datos.setdefault("producto", "P001")
        datos.setdefault("proveedor", "Proveedor de prueba")
        return self.cliente.post("/movimientos", data=datos, follow_redirects=True)

    def existencia(self, codigo="P001"):
        return db.obtener_producto(codigo)["existencia"]


class TestAcceso(PruebaConBaseTemporal):

    usuario = None

    def test_sin_sesion_redirige_al_login(self):
        respuesta = self.cliente.get("/")
        self.assertEqual(respuesta.status_code, 302)
        self.assertIn("/login", respuesta.headers["Location"])

    def test_login_correcto_entra_al_resumen(self):
        respuesta = self.entrar("laura")
        self.assertEqual(respuesta.status_code, 200)
        # Se comprueba un rótulo del panel, no el título, que cambia con el diseño.
        self.assertIn("Productos activos", respuesta.get_data(as_text=True))

    def test_login_con_clave_incorrecta_falla(self):
        respuesta = self.cliente.post("/login", data={"usuario": "laura", "clave": "mala"})
        self.assertEqual(respuesta.status_code, 401)

    def test_login_con_usuario_inexistente_falla(self):
        respuesta = self.cliente.post("/login", data={"usuario": "nadie", "clave": "1234"})
        self.assertEqual(respuesta.status_code, 401)

    def test_logout_cierra_la_sesion(self):
        self.entrar("laura")
        self.cliente.post("/logout")
        self.assertEqual(self.cliente.get("/").status_code, 302)

    def test_el_login_no_redirige_a_otro_sitio(self):
        """`siguiente` solo puede ser una ruta interna."""
        respuesta = self.cliente.post(
            "/login?siguiente=https://ejemplo.invalido/",
            data={"usuario": "laura", "clave": "1234"},
        )
        self.assertEqual(respuesta.headers["Location"], "/")


class TestModulos(PruebaConBaseTemporal):

    def test_todos_los_modulos_responden(self):
        for ruta in ["/", "/productos", "/movimientos", "/historial", "/alertas"]:
            with self.subTest(ruta=ruta):
                self.assertEqual(self.cliente.get(ruta).status_code, 200)

    def test_el_resumen_muestra_el_conteo_de_productos(self):
        texto = self.cliente.get("/").get_data(as_text=True)
        self.assertIn(str(len(db.listar_productos(solo_activos=True))), texto)

    def test_la_busqueda_de_productos_filtra(self):
        texto = self.cliente.get("/productos?q=arroz").get_data(as_text=True)
        self.assertIn("Arroz Diana", texto)
        self.assertNotIn("Leche Colanta", texto)


class TestMovimientos(PruebaConBaseTemporal):

    def test_la_entrada_aumenta_las_existencias(self):
        antes = self.existencia()
        self.mover(tipo="entrada", cantidad=10)
        self.assertEqual(self.existencia(), antes + 10)

    def test_la_salida_descuenta_las_existencias(self):
        antes = self.existencia()
        self.mover(tipo="salida", cantidad=5, motivo="Venta en mostrador")
        self.assertEqual(self.existencia(), antes - 5)

    def test_el_movimiento_queda_en_el_historial(self):
        self.mover(tipo="entrada", cantidad=7)
        ultimo = db.listar_movimientos(limite=1)[0]
        self.assertEqual(ultimo["tipo"], "entrada")
        self.assertEqual(ultimo["cantidad"], 7)
        self.assertEqual(ultimo["resultante"], self.existencia())

    def test_el_movimiento_guarda_quien_lo_hizo(self):
        self.mover(tipo="entrada", cantidad=3)
        self.assertEqual(db.listar_movimientos(limite=1)[0]["responsable"], "Carlos Restrepo")

    def test_la_salida_que_cruza_el_minimo_genera_alerta(self):
        producto = db.obtener_producto("P001")
        cantidad = producto["existencia"] - producto["minimo"]

        respuesta = self.mover(tipo="salida", cantidad=cantidad, motivo="Venta")

        self.assertIn("Hay que reponer", respuesta.get_data(as_text=True))

    def test_la_entrada_que_pasa_el_maximo_genera_alerta(self):
        producto = db.obtener_producto("P001")
        cantidad = producto["maximo"] - producto["existencia"] + 1

        respuesta = self.mover(tipo="entrada", cantidad=cantidad)

        self.assertIn("sobre stock", respuesta.get_data(as_text=True).lower())

    def test_los_datos_sobreviven_a_reiniciar_la_aplicacion(self):
        """Lo que se registra queda en disco, que es el punto de usar SQLite."""
        self.mover(tipo="entrada", cantidad=11)
        esperado = self.existencia()

        nuevo_cliente = aplicacion.app.test_client()
        nuevo_cliente.post("/login", data={"usuario": "admin", "clave": "1234"})

        self.assertEqual(db.obtener_producto("P001")["existencia"], esperado)


class TestValidaciones(PruebaConBaseTemporal):

    def test_no_permite_sacar_mas_de_lo_disponible(self):
        antes = self.existencia()
        respuesta = self.mover(tipo="salida", cantidad=antes + 1, motivo="Venta")

        self.assertIn("Solo hay", respuesta.get_data(as_text=True))
        self.assertEqual(self.existencia(), antes)

    def test_rechaza_cantidad_cero_o_negativa(self):
        antes = self.existencia()
        for cantidad in (0, -5):
            with self.subTest(cantidad=cantidad):
                respuesta = self.mover(tipo="entrada", cantidad=cantidad)
                self.assertIn("mayor que cero", respuesta.get_data(as_text=True))
        self.assertEqual(self.existencia(), antes)

    def test_rechaza_cantidad_no_numerica(self):
        antes = self.existencia()
        self.mover(tipo="entrada", cantidad="muchas")
        self.assertEqual(self.existencia(), antes)

    def test_rechaza_producto_inexistente(self):
        respuesta = self.mover(producto="NOEXISTE", tipo="entrada", cantidad=5)
        self.assertIn("no existe", respuesta.get_data(as_text=True))

    def test_rechaza_tipo_de_movimiento_invalido(self):
        antes = self.existencia()
        self.mover(tipo="regalo", cantidad=5)
        self.assertEqual(self.existencia(), antes)

    def test_la_entrada_exige_proveedor(self):
        antes = self.existencia()
        respuesta = self.mover(tipo="entrada", cantidad=5, proveedor="")

        self.assertIn("proveedor", respuesta.get_data(as_text=True).lower())
        self.assertEqual(self.existencia(), antes)

    def test_no_se_puede_mover_un_producto_desactivado(self):
        self.cliente.post("/productos/P001/estado")
        respuesta = self.mover(tipo="entrada", cantidad=5)
        self.assertIn("desactivado", respuesta.get_data(as_text=True))


class TestCatalogo(PruebaConBaseTemporal):

    def test_crear_producto(self):
        self.cliente.post("/productos/nuevo", data={
            "codigo": "P900", "nombre": "Producto nuevo", "categoria": "Pruebas",
            "unidad": "Unidad", "precio": "1500", "existencia": "20",
            "minimo": "5", "maximo": "40",
        })
        creado = db.obtener_producto("P900")
        self.assertIsNotNone(creado)
        self.assertEqual(creado["nombre"], "Producto nuevo")

    def test_no_permite_codigo_repetido(self):
        respuesta = self.cliente.post("/productos/nuevo", data={
            "codigo": "P001", "nombre": "Duplicado", "categoria": "Pruebas",
            "unidad": "Unidad", "precio": "1", "existencia": "1",
            "minimo": "1", "maximo": "9",
        }, follow_redirects=True)
        self.assertIn("Ya existe", respuesta.get_data(as_text=True))

    def test_rechaza_maximo_menor_que_minimo(self):
        respuesta = self.cliente.post("/productos/nuevo", data={
            "codigo": "P901", "nombre": "Mal configurado", "categoria": "Pruebas",
            "unidad": "Unidad", "precio": "1", "existencia": "1",
            "minimo": "50", "maximo": "10",
        }, follow_redirects=True)

        self.assertIn("mayor que el mínimo", respuesta.get_data(as_text=True))
        self.assertIsNone(db.obtener_producto("P901"))

    def test_editar_producto_no_cambia_la_existencia(self):
        antes = self.existencia()
        self.cliente.post("/productos/P001/editar", data={
            "nombre": "Arroz renombrado", "categoria": "Granos", "unidad": "Unidad",
            "precio": "3000", "minimo": "15", "maximo": "80",
        })
        producto = db.obtener_producto("P001")

        self.assertEqual(producto["nombre"], "Arroz renombrado")
        self.assertEqual(producto["existencia"], antes)

    def test_activar_y_desactivar(self):
        self.cliente.post("/productos/P001/estado")
        self.assertEqual(db.obtener_producto("P001")["activo"], 0)

        self.cliente.post("/productos/P001/estado")
        self.assertEqual(db.obtener_producto("P001")["activo"], 1)

    def test_el_codigo_sugerido_no_choca(self):
        self.assertIsNone(db.obtener_producto(db.siguiente_codigo()))


class TestPermisos(PruebaConBaseTemporal):

    usuario = "laura"

    def test_la_encargada_puede_registrar_movimientos(self):
        antes = self.existencia()
        self.mover(tipo="entrada", cantidad=4)
        self.assertEqual(self.existencia(), antes + 4)

    def test_la_encargada_no_puede_crear_productos(self):
        self.cliente.post("/productos/nuevo", data={
            "codigo": "P950", "nombre": "No debería existir", "categoria": "X",
            "unidad": "Unidad", "precio": "1", "existencia": "1",
            "minimo": "1", "maximo": "9",
        })
        self.assertIsNone(db.obtener_producto("P950"))

    def test_la_encargada_no_puede_reiniciar_los_datos(self):
        self.mover(tipo="entrada", cantidad=6)
        esperado = self.existencia()

        self.cliente.post("/reiniciar")

        self.assertEqual(self.existencia(), esperado)


class TestReinicio(PruebaConBaseTemporal):

    def test_reiniciar_restaura_el_inventario(self):
        self.mover(tipo="entrada", cantidad=25)
        self.assertNotEqual(self.existencia(), 45)

        self.cliente.post("/reiniciar")

        self.assertEqual(self.existencia(), 45)
        self.assertEqual(len(db.listar_movimientos()), len(db.MOVIMIENTOS_INICIALES))


if __name__ == "__main__":
    unittest.main()
