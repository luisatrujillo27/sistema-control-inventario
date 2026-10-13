"""Patrón Observer aplicado al control de existencias.

Subject  -> mantiene la lista de observadores y les avisa de cada cambio.
Observer -> contrato que debe cumplir cualquier observador.
StockObserver / ConsolaObserver -> observadores concretos.
"""

from abc import ABC, abstractmethod

# Margen sobre el stock mínimo para considerar que un producto está "regular".
MARGEN_REGULAR = 1.5


class Observer(ABC):
    """Contrato que debe cumplir todo observador del inventario."""

    @abstractmethod
    def update(self, producto):
        """Reacciona al cambio de un producto."""


class Subject:
    """Objeto observado: notifica cuando cambia el inventario."""

    def __init__(self):
        self._observers = []

    def attach(self, observer):
        """Registra un observador."""
        if observer not in self._observers:
            self._observers.append(observer)

    def detach(self, observer):
        """Retira un observador."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, producto):
        """Notifica el cambio a todos los observadores registrados."""
        for observer in self._observers:
            observer.update(producto)


class StockObserver(Observer):
    """Clasifica el stock y acumula las alertas de productos críticos.

    Solo genera una alerta cuando el producto *entra* en estado crítico,
    no cada vez que se le notifica un cambio.
    """

    def __init__(self):
        self._alertas = []
        # Ids de los productos que ya estaban críticos en la notificación
        # anterior. Es memoria propia del observador: si se dedujera del
        # diccionario del producto, dos observadores se pisarían entre sí.
        self._criticos = set()

    def update(self, producto):
        estaba_critico = producto["id"] in self._criticos

        if producto["cantidad"] <= producto["minimo"]:
            producto["nivel"] = "critico"
            producto["estado"] = "Bajo Stock"
            producto["alerta"] = True
        elif producto["cantidad"] <= producto["minimo"] * MARGEN_REGULAR:
            producto["nivel"] = "regular"
            producto["estado"] = "Regular"
            producto["alerta"] = False
        else:
            producto["nivel"] = "optimo"
            producto["estado"] = "Óptimo"
            producto["alerta"] = False

        if producto["alerta"]:
            if not estaba_critico:
                self._alertas.append({
                    "nombre": producto["nombre"],
                    "cantidad": producto["cantidad"],
                    "minimo": producto["minimo"],
                })
            self._criticos.add(producto["id"])
        else:
            self._criticos.discard(producto["id"])

    def recoger_alertas(self):
        """Devuelve las alertas pendientes y limpia la lista."""
        alertas = self._alertas
        self._alertas = []
        return alertas


class ConsolaObserver(Observer):
    """Observador secundario: deja constancia de los cambios en consola."""

    def update(self, producto):
        if producto["cantidad"] <= producto["minimo"]:
            print(
                f"[ALERTA] {producto['nombre']}: {producto['cantidad']} "
                f"unidades (mínimo {producto['minimo']})"
            )
