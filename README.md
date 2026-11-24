# Sistema de control de inventario

Aplicación web para el control de existencias de un supermercado de barrio en
Medellín. Hecha con Flask y Bootstrap, guarda los datos en SQLite y aplica el
**patrón Observer** para avisar cuando un producto se sale de sus niveles.

## Requisitos

- Python 3.10 o superior (probado con 3.12)
- Opcional: Visual Studio Code con la extensión **Python**

## Cómo ejecutarlo

Hay tres caminos; todos abren la aplicación en <http://127.0.0.1:5000>.

### 1. Un solo clic (Windows)

Doble clic en **`iniciar.bat`**. El script crea el entorno virtual si no
existe, instala las dependencias, arranca el servidor y abre el navegador.
Para detenerlo, `Ctrl+C` en la ventana negra.

Desde PowerShell el equivalente es:

```powershell
.\iniciar.ps1
```

En Linux o macOS:

```bash
./iniciar.sh
```

### 2. Desde Visual Studio Code

1. Abre la carpeta del proyecto en VS Code.
2. Acepta las extensiones recomendadas (Python, Debugpy, Live Server).
3. Pulsa **F5** y elige **Flask: Sistema de inventario**.

| Configuración                  | Qué hace                                                   |
| ------------------------------ | ---------------------------------------------------------- |
| `Flask: Sistema de inventario` | Arranca el servidor en modo depuración y abre el navegador |
| `Pruebas (unittest)`           | Ejecuta la batería de pruebas con depurador                |

También están disponibles desde **Terminal → Ejecutar tarea**: instalar
dependencias, ejecutar el servidor, servir el prototipo y ejecutar las pruebas.

> Si VS Code no detecta el intérprete, elígelo con `Ctrl+Shift+P` →
> *Python: Select Interpreter* → `.venv\Scripts\python.exe`.

### 3. A mano, desde la terminal

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

pip install -r requirements.txt
python app.py
```

## Acceso

Usuarios de demostración. Son credenciales fijas de un proyecto académico:
no hay registro, no son datos reales y por eso no se cifran.

| Usuario | Contraseña | Rol           | Qué puede hacer                                  |
| ------- | ---------- | ------------- | ------------------------------------------------ |
| `laura` | `1234`     | Encargada     | Consultar y registrar entradas y salidas         |
| `admin` | `1234`     | Administrador | Lo anterior, más gestionar el catálogo y reiniciar |

## Módulos

| Módulo                 | Contenido                                                          |
| ---------------------- | ------------------------------------------------------------------ |
| **Resumen**            | Indicadores, movimientos del día, reparto por categoría y últimos movimientos |
| **Productos**          | Catálogo con búsqueda, alta, edición y activación/desactivación     |
| **Entradas y salidas** | Registro de mercancía recibida y de salidas, con validaciones       |
| **Historial**          | Todos los movimientos, filtrables por tipo, producto y rango de fechas |
| **Alertas**            | Productos bajo el mínimo, sobre el máximo y en nivel normal         |

## La interfaz

Tema claro sobre Bootstrap 5. El menú lateral es una franja estrecha de iconos
que se despliega al pasar el ratón o al llegar con el tabulador; flota sobre el
contenido, así la página no se mueve al abrirlo. Cuando hay productos fuera de
rango aparece un punto rojo sobre el icono de alertas.

En pantallas de menos de 768 px la franja pasa a ser una fila de iconos bajo la
cabecera.

> Las plantillas de `templates/` se ven **solo** a través del servidor, en
> <http://127.0.0.1:5000>. Abiertas con doble clic son Jinja sin procesar: se
> ven sin estilos.

## Los datos se guardan

El inventario vive en **`inventario.db`**, un archivo SQLite que se crea solo
la primera vez que arranca la aplicación. Lo que registres en el navegador
sigue ahí después de cerrar el servidor.

- El archivo está en `.gitignore`: cada quien trabaja con su propia copia.
- Para volver al estado inicial, entra como `admin` y usa **Reiniciar datos**
  en el resumen. También basta con borrar `inventario.db`: se regenera sola.
- No hacen falta dependencias extra: `sqlite3` viene con Python.

## Pruebas

```bash
python -m unittest discover -v
```

Desde VS Code también aparecen en la pestaña **Testing**.

Cubren el patrón Observer, la clasificación de niveles, el acceso y los roles,
los movimientos, las validaciones, el catálogo y la persistencia. Cada prueba
corre contra una base de datos temporal propia, así que no tocan tu
`inventario.db`.

## Prototipo navegable

El prototipo de `prototipo/` es HTML estático y no depende de Flask. Es el
diseño previo de navegación, anterior a esta aplicación.

Lo más directo es abrir `prototipo/index.html` con doble clic: en Chrome o
Firefox carga bien. Aun así conviene servirlo por HTTP, porque algunas vistas
previas integradas muestran los archivos locales sin estilos:

- Doble clic en **`iniciar-prototipo.bat`** (puerto 5500).
- En VS Code: clic derecho sobre `prototipo/index.html` → **Open with Live Server**.

## Estructura

| Archivo                        | Contenido                                               |
| ------------------------------ | ------------------------------------------------------- |
| `app.py`                       | Aplicación Flask: sesión, roles y rutas de los módulos  |
| `db.py`                        | Capa de persistencia en SQLite y datos de arranque      |
| `observer.py`                  | Patrón Observer: `Subject`, `Observer`, observadores     |
| `templates/`                   | Plantillas Jinja: `base.html` y una por módulo           |
| `static/css/estilos.css`       | Ajustes propios sobre Bootstrap                          |
| `test_observer.py`             | Pruebas del patrón y de la clasificación de niveles      |
| `test_app.py`                  | Pruebas de rutas, roles, movimientos y validaciones      |
| `iniciar.bat` / `.ps1` / `.sh` | Lanzadores: preparan el entorno y arrancan Flask         |
| `iniciar-prototipo.bat`        | Sirve el prototipo estático en el puerto 5500            |
| `.vscode/`                     | Configuración de ejecución, depuración y pruebas         |
| `prototipo/`                   | Prototipo navegable estático (sin Flask)                 |

## Cómo funciona el patrón Observer

El inventario no sabe qué hacer cuando cambia una cantidad: solo avisa.
Quien decide si hay que alertar es el observador.

```
Entrada / Salida registrada en app.py
              │
              ▼
      Subject.notify(producto)
              │
              ├──> StockObserver.update()    clasifica el nivel y guarda la alerta
              └──> ConsolaObserver.update()  deja constancia en la consola
```

**Piezas**

- `Subject` — mantiene la lista de observadores (`attach`, `detach`) y les avisa
  de cada cambio (`notify`).
- `Observer` — clase abstracta: todo observador debe implementar `update()`.
- `StockObserver` — clasifica cada producto y acumula las alertas.
- `ConsolaObserver` — segundo observador, registra en consola.

**Clasificación del stock**

| Nivel    | Condición                        | Etiqueta    |
| -------- | -------------------------------- | ----------- |
| `bajo`   | existencia **≤** nivel mínimo    | Stock bajo  |
| `normal` | entre el mínimo y el máximo      | Normal      |
| `exceso` | existencia **>** nivel máximo    | Sobre stock |

**La alerta es un evento, no un estado.** `StockObserver` solo genera la alerta
cuando el producto *entra* en un nivel que no es normal, no cada vez que se le
notifica un cambio. Para eso lleva su propia memoria del nivel anterior de cada
producto, en vez de deducirlo del producto: así dos observadores no se pisan
entre sí. `app.py` recoge esas alertas con `recoger_alertas()` y la interfaz las
muestra como avisos en la parte superior.

## Notas

- La existencia de un producto **solo** cambia registrando entradas o salidas.
  El formulario de edición no la toca, para que el historial siempre cuadre.
- No se permite sacar más de lo disponible ni mover productos desactivados.
- La clave de sesión y las contraseñas son fijas porque es una demostración
  académica. Un sistema real usaría contraseñas cifradas y una clave secreta
  fuera del código.

## Reparto del trabajo

| Integrante | Responsabilidad                                              |
| ---------- | ------------------------------------------------------------ |
| 1          | Gestión del inventario: productos, cantidades y niveles       |
| 2          | Interfaz web                                                  |
| 3          | Patrón Observer y alertas de stock                            |
| 4          | Integración, pruebas y documentación                          |
