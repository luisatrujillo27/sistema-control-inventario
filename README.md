# Sistema de control de inventario

Mock-up funcional del control de existencias de un supermercado de Medellín.
Hecho con Flask, aplica el **patrón Observer** para avisar cuando un producto
queda por debajo de su stock mínimo.

## Requisitos

- Python 3.10 o superior

## Instalación y ejecución

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
python app.py
```

Luego abre <http://localhost:5000>.

## Pruebas

```bash
python -m unittest discover -v
```

## Estructura

| Archivo                | Contenido                                           |
| ---------------------- | --------------------------------------------------- |
| `app.py`               | Aplicación Flask: inventario y rutas                |
| `observer.py`          | Patrón Observer: `Subject`, `Observer`, observadores |
| `templates/index.html` | Interfaz web                                         |
| `test_observer.py`     | Pruebas del patrón y de las alertas                  |
| `test_app.py`          | Pruebas de las rutas, movimientos y validaciones     |

## Cómo funciona el patrón Observer

El inventario no sabe qué hacer cuando cambia una cantidad: solo avisa.
Quien decide si hay que alertar es el observador.

```
Entrada / Salida registrada en app.py
              │
              ▼
      Subject.notify(producto)
              │
              ├──> StockObserver.update()    clasifica el stock y guarda la alerta
              └──> ConsolaObserver.update()  deja constancia en la consola
```

**Piezas**

- `Subject` — mantiene la lista de observadores (`attach`, `detach`) y les avisa
  de cada cambio (`notify`).
- `Observer` — clase abstracta: todo observador debe implementar `update()`.
- `StockObserver` — clasifica cada producto y acumula las alertas.
- `ConsolaObserver` — segundo observador, registra los productos bajos en consola.

**Clasificación del stock**

| Nivel        | Condición                           | Badge      |
| ------------ | ----------------------------------- | ---------- |
| `critico`    | existencias **≤** stock mínimo      | Bajo Stock |
| `regular`    | existencias ≤ stock mínimo × 1.5    | Regular    |
| `optimo`     | por encima de lo anterior           | Óptimo     |

**La alerta es un evento, no un estado.** `StockObserver` solo genera la alerta
cuando el producto *entra* en nivel crítico, no cada vez que se le notifica un
cambio. Para eso lleva su propia memoria de qué productos ya estaban críticos,
en vez de deducirlo del producto: así dos observadores no se pisan entre sí.
`app.py` recoge esas alertas con `recoger_alertas()` y la interfaz las muestra
como un aviso deslizante.

## Notas

- Los datos viven en memoria: al reiniciar el servidor vuelven a su estado
  inicial. Es un mock-up de demostración, no usa base de datos.
- El botón **Reiniciar Datos** restaura el inventario sin reiniciar el servidor.

## Reparto del trabajo

| Integrante | Responsabilidad                                            |
| ---------- | ---------------------------------------------------------- |
| 1          | Gestión del inventario: productos, cantidades y stock mínimo |
| 2          | Interfaz web                                                |
| 3          | Patrón Observer y alertas de stock                          |
| 4          | Integración, pruebas y documentación                        |
