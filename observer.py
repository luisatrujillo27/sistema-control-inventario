"""Patrón Observer aplicado al control de existencias.

Subject  -> mantiene la lista de observadores y les avisa de cada cambio.
Observer -> contrato que debe cumplir cualquier observador.
StockObserver / ConsolaObserver -> observadores concretos.

El inventario no decide qué hacer cuando cambia una cantidad: solo avisa.
Quien clasifica el stock y levanta la alerta es el observador.
"""

from abc import ABC, abstractmethod

# Niveles posibles de un producto.
NIVEL_BAJO = "bajo"
NIVEL_NORMAL = "normal"
NIVEL_EXCESO = "exceso"

# Cómo se muestra cada nivel en la interfaz: etiqueta y color de Bootstrap.
PRESENTACION = {
    NIVEL_BAJO: ("Stock bajo", "danger"),
    NIVEL_NORMAL: ("Normal", "success"),
    NIVEL_EXCESO: ("Sobre stock", "warning"),
}


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


def clasificar(producto):
    """Devuelve el nivel de stock de un producto, sin tocarlo.

    Es una función aparte para poder usarla al pintar las tablas, donde
    solo se necesita el nivel y no hay ningún cambio que notificar.
    """
    existencia = producto["existencia"]
    maximo = producto.get("maximo") or 0

    if existencia <= producto["minimo"]:
        return NIVEL_BAJO
    if maximo and existencia > maximo:
        return NIVEL_EXCESO
    return NIVEL_NORMAL


def describir(producto):
    """Añade al producto su nivel, su etiqueta y su color, y lo devuelve."""
    nivel = clasificar(producto)
    etiqueta, color = PRESENTACION[nivel]
    producto["nivel"] = nivel
    producto["estado"] = etiqueta
    producto["color"] = color
    return producto


class StockObserver(Observer):
    """Clasifica el stock y acumula las alertas de los productos fuera de rango.

    Solo genera una alerta cuando el producto *entra* en un nivel que no es
    normal, no cada vez que se le notifica un cambio: la alerta es un evento,
    no un estado.
    """

    def __init__(self):
        self._alertas = []
        # Nivel que tenía cada producto en la notificación anterior. Es
        # memoria propia del observador: si se dedujera del diccionario del
        # producto, dos observadores se pisarían entre sí.
        self._niveles = {}

    def update(self, producto):
        describir(producto)
        nivel = producto["nivel"]
        anterior = self._niveles.get(producto["codigo"])

        if nivel != NIVEL_NORMAL and nivel != anterior:
            self._alertas.append({
                "tipo": nivel,
                "codigo": producto["codigo"],
                "nombre": producto["nombre"],
                "existencia": producto["existencia"],
                "minimo": producto["minimo"],
                "maximo": producto.get("maximo") or 0,
            })

        self._niveles[producto["codigo"]] = nivel

    def recoger_alertas(self):
        """Devuelve las alertas pendientes y limpia la lista."""
        alertas = self._alertas
        self._alertas = []
        return alertas

    def olvidar(self):
        """Borra la memoria de niveles. Se usa al reiniciar los datos."""
        self._alertas = []
        self._niveles = {}


class ConsolaObserver(Observer):
    """Observador secundario: deja constancia de los cambios en la consola."""

    def update(self, producto):
        nivel = clasificar(producto)
        if nivel == NIVEL_BAJO:
            print(
                f"[ALERTA] {producto['nombre']}: {producto['existencia']} "
                f"(minimo {producto['minimo']})"
            )
        elif nivel == NIVEL_EXCESO:
            print(
                f"[AVISO] {producto['nombre']}: {producto['existencia']} "
                f"(maximo {producto['maximo']})"
            )
