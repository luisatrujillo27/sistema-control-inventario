"""Pruebas del patrón Observer y de las alertas de stock."""

import unittest

from observer import ConsolaObserver, Observer, StockObserver, Subject


def producto(cantidad, minimo=10, nombre="Arroz Diana (1 kg)"):
    return {"id": "001", "nombre": nombre, "cantidad": cantidad, "minimo": minimo}


class TestClasificacionDeStock(unittest.TestCase):
    """El observador debe clasificar correctamente cada producto."""

    def setUp(self):
        self.inventario = Subject()
        self.observador = StockObserver()
        self.inventario.attach(self.observador)

    def test_cantidad_inferior_al_minimo_es_critico(self):
        p = producto(cantidad=4, minimo=10)
        self.inventario.notify(p)
        self.assertEqual(p["nivel"], "critico")
        self.assertTrue(p["alerta"])

    def test_cantidad_igual_al_minimo_es_critico(self):
        """El enunciado pide detectar existencia *igual o inferior* al mínimo."""
        p = producto(cantidad=10, minimo=10)
        self.inventario.notify(p)
        self.assertEqual(p["nivel"], "critico")
        self.assertTrue(p["alerta"])

    def test_cantidad_justo_encima_del_minimo_es_regular(self):
        p = producto(cantidad=12, minimo=10)
        self.inventario.notify(p)
        self.assertEqual(p["nivel"], "regular")
        self.assertFalse(p["alerta"])

    def test_cantidad_holgada_es_optimo(self):
        p = producto(cantidad=90, minimo=10)
        self.inventario.notify(p)
        self.assertEqual(p["nivel"], "optimo")
        self.assertFalse(p["alerta"])


class TestAlertas(unittest.TestCase):
    """La alerta es un evento: solo al *entrar* en estado crítico."""

    def setUp(self):
        self.inventario = Subject()
        self.observador = StockObserver()
        self.inventario.attach(self.observador)

    def test_se_genera_alerta_al_caer_bajo_el_minimo(self):
        p = producto(cantidad=12, minimo=10)
        self.inventario.notify(p)
        self.observador.recoger_alertas()

        p["cantidad"] = 3
        self.inventario.notify(p)

        alertas = self.observador.recoger_alertas()
        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["nombre"], p["nombre"])
        self.assertEqual(alertas[0]["cantidad"], 3)

    def test_la_alerta_no_se_repite_si_sigue_critico(self):
        p = producto(cantidad=2, minimo=10)
        self.inventario.notify(p)
        self.observador.recoger_alertas()

        self.inventario.notify(p)
        self.inventario.notify(p)

        self.assertEqual(self.observador.recoger_alertas(), [])

    def test_vuelve_a_alertar_despues_de_reponer_y_bajar_otra_vez(self):
        p = producto(cantidad=2, minimo=10)
        self.inventario.notify(p)
        self.observador.recoger_alertas()

        p["cantidad"] = 50          # entrada: sale del estado crítico
        self.inventario.notify(p)
        p["cantidad"] = 1           # salida: vuelve a caer
        self.inventario.notify(p)

        self.assertEqual(len(self.observador.recoger_alertas()), 1)

    def test_recoger_alertas_vacia_la_lista(self):
        p = producto(cantidad=1, minimo=10)
        self.inventario.notify(p)

        self.assertEqual(len(self.observador.recoger_alertas()), 1)
        self.assertEqual(self.observador.recoger_alertas(), [])


class TestSubject(unittest.TestCase):
    """Registro y baja de observadores."""

    def test_notifica_a_varios_observadores(self):
        inventario = Subject()
        uno, dos = StockObserver(), StockObserver()
        inventario.attach(uno)
        inventario.attach(dos)

        inventario.notify(producto(cantidad=1, minimo=10))

        self.assertEqual(len(uno.recoger_alertas()), 1)
        self.assertEqual(len(dos.recoger_alertas()), 1)

    def test_detach_deja_de_notificar(self):
        inventario = Subject()
        observador = StockObserver()
        inventario.attach(observador)
        inventario.detach(observador)

        p = producto(cantidad=1, minimo=10)
        inventario.notify(p)

        self.assertNotIn("estado", p)
        self.assertEqual(observador.recoger_alertas(), [])

    def test_no_registra_dos_veces_el_mismo_observador(self):
        inventario = Subject()
        observador = StockObserver()
        inventario.attach(observador)
        inventario.attach(observador)

        inventario.notify(producto(cantidad=1, minimo=10))

        self.assertEqual(len(observador.recoger_alertas()), 1)

    def test_los_observadores_cumplen_el_contrato(self):
        self.assertIsInstance(StockObserver(), Observer)
        self.assertIsInstance(ConsolaObserver(), Observer)


if __name__ == "__main__":
    unittest.main(verbosity=2)
