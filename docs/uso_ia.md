# Evidencias de uso de Inteligencia Artificial Generativa

Herramienta utilizada: asistente de IA generativa (Claude, Anthropic), como apoyo para
diseñar consultas SQL, depurar código, interpretar resultados y redactar documentación.
Criterio aplicado en todos los casos: **ninguna propuesta se aceptó sin ejecutarla contra los
datos y contrastarla con un resultado independiente**. La estudiante es responsable del
contenido final y puede explicar, ejecutar y modificar cada componente.

---

## Uso 1 · Discrepancia del KPI de entregas a tiempo (91,9 % vs. 93,2 %)

| Aspecto | Detalle |
|---|---|
| **Problema** | En el Entregable 1 el % de entregas a tiempo fue ≈ 91,9 %, pero la función `fn_kpis()` del Entregable 2 devolvía 93,2 %. Era necesario saber cuál era correcto antes de presentarlo. |
| **Prompt** | *“Mi KPI de entregas a tiempo da 91,9 % en el perfilado con pandas y 93,2 % en PostgreSQL. En pandas comparo `order_delivered_customer_date <= order_estimated_delivery_date` y en SQL convierto ambas a DATE. ¿Por qué difieren y cuál debo usar?”* |
| **Propuesta de la IA** | La fecha estimada no tiene hora (siempre `00:00:00`). Al comparar timestamps, un pedido entregado el mismo día estimado a las 15:00 se marca como retrasado, aunque llegó en la fecha prometida. Propuso comparar fechas de calendario. |
| **Qué se utilizó / modificó** | Se adoptó la comparación por fecha (`f_entrega <= f_estimada` sobre `::date`) en `04_fact_ventas.sql`. Se añadió además la regla de calcular las medidas de entrega solo para pedidos `delivered`. |
| **Comprobación** | Se calcularon ambas versiones sobre los mismos pedidos: 91,9 % (timestamp) y 93,2 % (fecha). La diferencia corresponde exactamente a los **1 291 pedidos** entregados el mismo día de la fecha estimada. La regla “solo `delivered`” se validó con `05_validaciones.sql` (3 y 3a): 2 407 ítems sin medidas de entrega, todos explicados por su estado. |

## Uso 2 · Sobreconteo de la satisfacción en pedidos con varios ítems

| Aspecto | Detalle |
|---|---|
| **Problema** | La tabla de hechos tiene grano de ítem, pero la reseña es por pedido. Un pedido con 3 ítems repetía su reseña 3 veces y pesaba el triple en el promedio. |
| **Prompt** | *“Tengo `fact_ventas` a nivel de ítem y `review_score` se repite en cada ítem del pedido. ¿Cómo calculo el promedio de satisfacción sin contar dos veces los pedidos con varios ítems, pero manteniendo los filtros por categoría?”* |
| **Propuesta de la IA** | Usar una CTE con `SELECT DISTINCT ON (order_id) … ORDER BY order_id` para obtener una fila por pedido después de aplicar los filtros, y promediar sobre esa CTE. |
| **Qué se utilizó / modificó** | Se aplicó en `fn_kpis`, `fn_csat_por_puntualidad`, `fn_csat_por_retraso` y `fn_ventas_por_estado`; en `fn_ranking_vendedores` se adaptó a `DISTINCT ON (seller_id, order_id)` porque un pedido puede tener varios vendedores. |
| **Comprobación** | **9 767 pedidos** tienen más de un ítem. El CSAT promedio calculado por ítem es ≈ 0,07 puntos menor que el calculado por pedido: los pedidos con varios ítems tienen peores reseñas y quedaban sobrerrepresentados. La consulta 4c de validación recalcula el KPI directamente sobre la tabla de hechos y coincide con `fn_kpis()`. |

## Uso 3 · Normalización de ciudades e imputación desde geolocalización

| Aspecto | Detalle |
|---|---|
| **Problema** | Las ciudades venían escritas de muchas formas (`são paulo`, `sao paulo - sp`, `sao paulo / sao paulo`) y algunos vendedores tenían valores inválidos: un número (`04482255`), un correo electrónico o solo la sigla `sp`. |
| **Prompt** | *“Escribe una función de pandas que normalice nombres de ciudades brasileñas: minúsculas, sin tildes, sin sufijos de estado. ¿Qué hago con valores que no son ciudades, como un correo o un código numérico?”* |
| **Propuesta de la IA** | `unicodedata.normalize('NFKD')` para quitar tildes, una expresión regular para cortar sufijos (`" - "`, `/`, `\`, `,`), y para los valores inválidos, imputar la ciudad más frecuente del mismo prefijo postal usando la tabla de geolocalización deduplicada. |
| **Qué se utilizó / modificó** | Se implementó en `etl/02_limpieza.py`. Se agregó por cuenta propia la eliminación de la sigla del estado al final (`sao paulo sp`) y la conversión del acento agudo `´` a apóstrofo (`santa barbara d´oeste`). |
| **Comprobación** | Se revisaron manualmente los 7 casos imputados de vendedores (p. ej. `04482255` → `rio de janeiro`, `vendas@creditparts.com.br` → `maringa`). Las ciudades distintas de vendedores pasaron de 611 a 581 y la validación 3b reporta **0 vendedores y 0 clientes sin ciudad**. |

## Uso 4 · Filtros que se perdían al cambiar de página en Streamlit

| Aspecto | Detalle |
|---|---|
| **Problema** | Con varias páginas, al pasar de “Inicio” a “Ventas” los filtros volvían a “Todas”, por lo que las páginas mostraban resultados de contextos distintos. |
| **Prompt** | *“En Streamlit multipágina, mis `selectbox` con `key` se reinician al cambiar de página. ¿Cómo conservo los filtros de la barra lateral en todas las páginas?”* |
| **Propuesta de la IA** | Streamlit elimina el estado de un widget cuando su página deja de mostrarse. Propuso guardar los valores en una clave propia de `st.session_state` (no asociada a un widget), restaurarlos antes de dibujar los widgets y actualizarlos con `on_change`. |
| **Qué se utilizó / modificó** | Se implementó en `app/componentes.py` (`filtros_sidebar`, `_persistir`, `_restablecer`) y se añadió el filtro de estado en cascada: si la región cambia y el estado ya no pertenece a ella, se reinicia a “Todas”. |
| **Comprobación** | Prueba manual: se fijó Región = Nordeste, UF = BA, categoría y medio de pago, y se recorrieron las cuatro páginas; los filtros y los KPI se mantuvieron. Se probó además una combinación sin datos para confirmar que cada página muestra un aviso en lugar de fallar. |

## Uso 5 · Error al ejecutar el script de validaciones desde Python

| Aspecto | Detalle |
|---|---|
| **Problema** | `03_carga.py` separaba `05_validaciones.sql` por `;` para ejecutar cada consulta y guardar su resultado, pero fallaba con `syntax error at or near "los"`. |
| **Prompt** | *“Mi script de Python divide un archivo .sql por ';' y ejecuta cada parte con psycopg2, pero da error de sintaxis en una línea que es un comentario. ¿Qué está pasando?”* |
| **Propuesta de la IA** | Un comentario contenía un punto y coma (`…pedidos no entregados; los de review_score…`), así que la división cortaba el comentario por la mitad y la segunda parte quedaba como código. Propuso eliminar los comentarios antes de dividir. |
| **Qué se utilizó / modificó** | Se corrigió `ejecutar_validaciones()` para quitar las líneas que empiezan con `--` antes del `split(';')`. |
| **Comprobación** | El pipeline completo se ejecutó de nuevo sin errores y `reports/validaciones.md` contiene las 14 consultas con sus resultados. |

---

### Lo que **no** se delegó a la IA

- La elección del dataset, las preguntas de negocio y los usuarios destinatarios (Entregable 1).
- La decisión de mantener el grano de ítem y no crear una segunda tabla de hechos.
- La interpretación final de los resultados y las recomendaciones de negocio.
