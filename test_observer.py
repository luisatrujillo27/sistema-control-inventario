"""Pruebas del patrón Observer y de la clasificación de niveles."""

import unittest

from observer import (
    NIVEL_BAJO,
    NIVEL_EXCESO,
    NIVEL_NORMAL,
    ConsolaObserver,
    Observer,
    StockObserver,
    Subject,
    clasificar,
    describir,
)


def producto(existencia, minimo=10, maximo=50, codigo="P001"):
    """Arma un producto de prueba con los campos que usa el observador."""
    return {
        "codigo": codigo,
        "nombre": f"Producto {codigo}",
        "existencia": existencia,
        "minimo": minimo,
        "maximo": maximo,
    }


class ObservadorEspia(Observer):
    """Observador de prueba: solo anota qué le notificaron."""

    def __init__(self):
        self.recibidos = []

    def update(self, producto):
        self.recibidos.append(producto["codigo"])


class TestClasificacionDeStock(unittest.TestCase):

    def test_existencia_igual_al_minimo_es_bajo(self):
        """El enunciado pide detectar existencia *igual o inferior* al mínimo."""
        self.assertEqual(clasificar(producto(10, minimo=10)), NIVEL_BAJO)

    def test_existencia_inferior_al_minimo_es_bajo(self):
        self.assertEqual(clasificar(producto(3, minimo=10)), NIVEL_BAJO)

    def test_existencia_entre_minimo_y_maximo_es_normal(self):
        self.assertEqual(clasificar(producto(25, minimo=10, maximo=50)), NIVEL_NORMAL)

    def test_existencia_igual_al_maximo_sigue_siendo_normal(self):
        self.assertEqual(clasificar(producto(50, minimo=10, maximo=50)), NIVEL_NORMAL)

    def test_existencia_sobre_el_maximo_es_exceso(self):
        self.assertEqual(clasificar(producto(51, minimo=10, maximo=50)), NIVEL_EXCESO)

    def test_sin_maximo_definido_no_hay_exceso(self):
        self.assertEqual(clasificar(producto(900, minimo=10, maximo=0)), NIVEL_NORMAL)

    def test_describir_agrega_etiqueta_y_color(self):
        datos = describir(producto(3, minimo=10))
        self.assertEqual(datos["nivel"], NIVEL_BAJO)
        self.assertEqual(datos["estado"], "Stock bajo")
        self.assertEqual(datos["color"], "danger")


class TestSubject(unittest.TestCase):

    def test_notifica_a_varios_observadores(self):
        sujeto = Subject()
        uno, dos = ObservadorEspia(), ObservadorEspia()
        sujeto.attach(uno)
        sujeto.attach(dos)

        sujeto.notify(producto(20))

        self.assertEqual(uno.recibidos, ["P001"])
        self.assertEqual(dos.recibidos, ["P001"])

    def test_no_registra_dos_veces_el_mismo_observador(self):
        sujeto = Subject()
        espia = ObservadorEspia()
        sujeto.attach(espia)
        sujeto.attach(espia)

        sujeto.notify(producto(20))

        self.assertEqual(espia.recibidos, ["P001"])

    def test_detach_deja_de_notificar(self):
        sujeto = Subject()
        espia = ObservadorEspia()
        sujeto.attach(espia)
        sujeto.detach(espia)

        sujeto.notify(producto(20))

        self.assertEqual(espia.recibidos, [])

    def test_los_observadores_cumplen_el_contrato(self):
        self.assertIsInstance(StockObserver(), Observer)
        self.assertIsInstance(ConsolaObserver(), Observer)


class TestAlertas(unittest.TestCase):

    def setUp(self):
        self.observador = StockObserver()

    def test_se_genera_alerta_al_caer_bajo_el_minimo(self):
        self.observador.update(producto(30))
        self.assertEqual(self.observador.recoger_alertas(), [])

        self.observador.update(producto(8))
        alertas = self.observador.recoger_alertas()

        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["tipo"], NIVEL_BAJO)
        self.assertEqual(alertas[0]["existencia"], 8)

    def test_se_genera_alerta_al_pasar_del_maximo(self):
        self.observador.update(producto(30))
        self.observador.recoger_alertas()

        self.observador.update(producto(80, maximo=50))
        alertas = self.observador.recoger_alertas()

        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["tipo"], NIVEL_EXCESO)

    def test_la_alerta_no_se_repite_si_sigue_en_el_mismo_nivel(self):
        """La alerta es un evento, no un estado: se avisa al entrar, no siempre."""
        self.observador.update(producto(8))
        self.observador.recoger_alertas()

        self.observador.update(producto(5))

        self.assertEqual(self.observador.recoger_alertas(), [])

    def test_vuelve_a_alertar_despues_de_reponer_y_bajar_otra_vez(self):
        self.observador.update(producto(8))
        self.observador.recoger_alertas()

        self.observador.update(producto(40))   # repuesto: vuelve a normal
        self.observador.recoger_alertas()
        self.observador.update(producto(6))    # baja de nuevo

        self.assertEqual(len(self.observador.recoger_alertas()), 1)

    def test_pasar_de_bajo_a_exceso_genera_alerta_nueva(self):
        self.observador.update(producto(5))
        self.observador.recoger_alertas()

        self.observador.update(producto(90, maximo=50))
        alertas = self.observador.recoger_alertas()

        self.assertEqual(len(alertas), 1)
        self.assertEqual(alertas[0]["tipo"], NIVEL_EXCESO)

    def test_recoger_alertas_vacia_la_lista(self):
        self.observador.update(producto(5))

        self.assertEqual(len(self.observador.recoger_alertas()), 1)
        self.assertEqual(self.observador.recoger_alertas(), [])

    def test_olvidar_borra_la_memoria_de_niveles(self):
        self.observador.update(producto(5))
        self.observador.recoger_alertas()

        self.observador.olvidar()
        self.observador.update(producto(5))

        # Sin memoria previa, el producto "entra" de nuevo en nivel bajo.
        self.assertEqual(len(self.observador.recoger_alertas()), 1)

    def test_dos_productos_distintos_no_se_pisan(self):
        self.observador.update(producto(5, codigo="P001"))
        self.observador.update(producto(5, codigo="P002"))

        alertas = self.observador.recoger_alertas()

        self.assertEqual({a["codigo"] for a in alertas}, {"P001", "P002"})


if __name__ == "__main__":
    unittest.main()
