# Sistema de Control de Inventario — Prototipo navegable

## Cómo abrir
1. Descomprime el ZIP.
2. Abre la carpeta `prototipo_inventario_corregido` desde Visual Studio Code.
3. Abre `index.html` con Open in Integrated Browser o con Live Server.

## Archivos
- `index.html`: estructura de las seis pantallas.
- `css/estilos.css`: diseño visual, responsive y estados de interacción.
- `js/navegacion.js`: navegación, filtros, tarjetas clicables, modal y vista previa.

## Funcionalidades del prototipo
- Las tarjetas del Dashboard abren Inventario con el filtro correspondiente.
- Las tarjetas de resumen en Alertas hacen lo mismo.
- La búsqueda por nombre o código funciona junto con los filtros.
- Se muestra un mensaje cuando no hay resultados.
- Los botones de detalle muestran datos del producto seleccionado.
- La navegación conserva la ruta en el hash y admite Atrás/Adelante.
- Los controles de navegación de tarjetas funcionan con mouse y teclado.
- El formulario de movimientos muestra una vista previa, sin guardar datos.

## Alcance
Es un prototipo académico de navegación. No se conecta a Flask ni a una base de datos y no cambia las existencias reales.

## Nota sobre la clasificación
Se ajustó el ejemplo de Huevos AA a estado Óptimo para que la tabla coincida con los indicadores presentados: 11 óptimos, 3 regulares y 4 críticos. Esta es una clasificación ilustrativa del prototipo y debe contrastarse con las reglas reales del proyecto si se integra posteriormente.
