
class Subject:
    """Objeto que notifica cuando cambia el inventario."""

    def __init__(self):
        self._observers = []

    def attach(self, observer):
        """Registra un observador."""
        self._observers.append(observer)

    def detach(self, observer):
        """Retira un observador."""
        if observer in self._observers:
            self._observers.remove(observer)

    def notify(self, producto):
        """Notifica el cambio a todos los observadores."""
        for observer in self._observers:
            observer.update(producto)



class StockObserver:
    """Observador que detecta productos con stock bajo."""

    def update(self, producto):
        if producto["cantidad"] <= producto["minimo"]:
            producto["estado"] = "Stock bajo"
            producto["alerta"] = True
            print(
                f"ALERTA: {producto['nombre']} tiene "
                f"{producto['cantidad']} unidades."
            )
        else:
            producto["estado"] = "Stock suficiente"
            producto["alerta"] = False

