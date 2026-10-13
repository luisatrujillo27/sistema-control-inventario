"""Pruebas de la aplicación completa: rutas, movimientos y validaciones."""

import unittest

import app as aplicacion


class PruebaBase(unittest.TestCase):
    """Deja el inventario en su estado inicial antes de cada prueba."""

    def setUp(self):
        aplicacion.app.config["TESTING"] = True
        self.client = aplicacion.app.test_client()
        # Reinicia el estado y consume los mensajes pendientes.
        self.client.post("/reiniciar", follow_redirects=True)

    def existencias(self, producto_id):
        return aplicacion.buscar_producto(producto_id)["cantidad"]

    def mover(self, producto_id, tipo, cantidad):
        """Registra un movimiento y devuelve los mensajes que generó.

        Los mensajes se acumulan en la sesión hasta que una página los
        muestra, así que se limpian antes para leer solo los de este
        movimiento.
        """
        with self.client.session_transaction() as sesion:
            sesion.pop("_flashes", None)

        self.client.post(
            "/movimiento",
            data={"producto_id": producto_id, "tipo": tipo, "cantidad": cantidad},
        )

        with self.client.session_transaction() as sesion:
            return sesion.get("_flashes", [])

    def categorias(self, mensajes):
        return [categoria for categoria, _ in mensajes]


class TestInicio(PruebaBase):

    def test_la_pagina_responde_y_lista_los_productos(self):
        respuesta = self.client.get("/")
        html = respuesta.get_data(as_text=True)

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(html.count('data-estado="'), len(aplicacion.productos))
        self.assertIn("Arroz Diana (1 kg)", html)

    def test_cada_producto_tiene_estado_calculado(self):
        for producto in aplicacion.productos:
            self.assertIn(producto["nivel"], ("optimo", "regular", "critico"))


class TestMovimientos(PruebaBase):

    def test_la_entrada_aumenta_las_existencias(self):
        antes = self.existencias("001")
        mensajes = self.mover("001", "entrada", 20)

        self.assertEqual(self.existencias("001"), antes + 20)
        self.assertIn("exito", self.categorias(mensajes))

    def test_la_salida_descuenta_las_existencias(self):
        antes = self.existencias("001")
        mensajes = self.mover("001", "salida", 20)

        self.assertEqual(self.existencias("001"), antes - 20)
        self.assertIn("exito", self.categorias(mensajes))

    def test_la_salida_que_cruza_el_minimo_genera_alerta(self):
        # Huevos AA: 14 unidades, minimo 10. Salir 5 lo deja en 9.
        mensajes = self.mover("009", "salida", 5)

        self.assertEqual(self.existencias("009"), 9)
        self.assertIn("alerta", self.categorias(mensajes))

    def test_la_alerta_no_se_repite_mientras_siga_bajo(self):
        self.mover("009", "salida", 5)
        mensajes = self.mover("009", "salida", 1)

        self.assertNotIn("alerta", self.categorias(mensajes))

    def test_reponer_y_volver_a_bajar_alerta_de_nuevo(self):
        self.mover("009", "salida", 5)
        self.mover("009", "entrada", 50)
        mensajes = self.mover("009", "salida", 50)

        self.assertIn("alerta", self.categorias(mensajes))


class TestValidaciones(PruebaBase):

    def test_no_permite_sacar_mas_de_lo_disponible(self):
        antes = self.existencias("001")
        mensajes = self.mover("001", "salida", antes + 1)

        self.assertEqual(self.existencias("001"), antes)
        self.assertIn("error", self.categorias(mensajes))

    def test_rechaza_cantidad_cero_o_negativa(self):
        antes = self.existencias("001")

        for cantidad in (0, -5):
            with self.subTest(cantidad=cantidad):
                mensajes = self.mover("001", "salida", cantidad)
                self.assertEqual(self.existencias("001"), antes)
                self.assertIn("error", self.categorias(mensajes))

    def test_rechaza_cantidad_no_numerica(self):
        antes = self.existencias("001")
        mensajes = self.mover("001", "salida", "mucho")

        self.assertEqual(self.existencias("001"), antes)
        self.assertIn("error", self.categorias(mensajes))

    def test_rechaza_producto_inexistente(self):
        mensajes = self.mover("999", "salida", 1)
        self.assertIn("error", self.categorias(mensajes))

    def test_rechaza_tipo_de_movimiento_invalido(self):
        antes = self.existencias("001")
        mensajes = self.mover("001", "regalo", 5)

        self.assertEqual(self.existencias("001"), antes)
        self.assertIn("error", self.categorias(mensajes))


class TestReinicio(PruebaBase):

    def test_reiniciar_restaura_el_inventario(self):
        self.mover("001", "salida", 100)
        self.assertNotEqual(self.existencias("001"), 150)

        self.client.post("/reiniciar", follow_redirects=True)

        self.assertEqual(self.existencias("001"), 150)

    def test_reiniciar_no_deja_alertas_pendientes(self):
        self.mover("009", "salida", 5)
        self.client.post("/reiniciar", follow_redirects=True)

        mensajes = self.mover("001", "entrada", 1)
        self.assertNotIn("alerta", self.categorias(mensajes))


if __name__ == "__main__":
    unittest.main(verbosity=2)
