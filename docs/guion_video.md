# Guion del video (objetivo: 4 min 30 s · máximo 5 min)

Preparación antes de grabar: `docker compose up -d`, `python etl/run_pipeline.py` ya ejecutado,
Adminer abierto en <http://localhost:8080>, la app abierta con `streamlit run app/Inicio.py`
y los filtros en “Todas”.

| Tiempo | Pantalla | Qué decir (resumen) | Requisito cubierto |
|---|---|---|---|
| 0:00–0:30 | Portada / README en GitHub | “Analizo el marketplace brasileño Olist: ≈ 100 000 pedidos reales entre enero 2017 y agosto 2018, 9 tablas de Kaggle. El problema: entender cuánto se vende, qué tan puntuales son las entregas y cómo afectan los retrasos a la satisfacción.” | Problema y dataset |
| 0:30–1:10 | `docs/img/diagrama_estrella.png` | “El modelo estrella tiene una tabla de hechos, `fact_ventas`, y seis dimensiones: tiempo, cliente, producto, vendedor, estado del pedido y pago. **Una fila de la tabla de hechos representa un ítem de producto vendido dentro de un pedido.** Las medidas son precio, flete, valor total, días de entrega, días de retraso, la bandera a tiempo y la reseña.” | Modelo, hechos, dimensiones, granularidad |
| 1:10–1:50 | Adminer → esquema `dw` → `fact_ventas` (estructura con claves) → “Comando SQL” | Mostrar las tablas y sus filas (112 279 en hechos). Ejecutar en vivo: `SELECT * FROM dw.fn_kpis();` y explicar que es la misma función que usa la app. | Demostración PostgreSQL, tablas cargadas, función |
| 1:50–2:40 | App · Inicio | Recorrer las 8 tarjetas KPI, el gráfico de líneas (pico de noviembre 2017 por Black Friday) y el de satisfacción a tiempo vs. con retraso. Abrir “Ver consulta SQL”. | KPI, gráficos |
| 2:40–3:20 | App · barra lateral | **Cambiar un filtro**: Región = Nordeste. Señalar cómo bajan el OTD y el CSAT y sube el tiempo de entrega. Ir a “Logística y satisfacción” y mostrar que el filtro se mantiene; luego “Vendedores” → ordenar por % con retraso. | Interacción, filtros, tabla de detalle |
| 3:20–4:05 | App · Logística y satisfacción | **Resultado relevante:** “Hasta la fecha estimada el CSAT se mantiene sobre 4; con 4 a 7 días de retraso cae a ≈ 2 y con más de una semana casi 8 de cada 10 reseñas son negativas. Río de Janeiro concentra el 23 % de los pedidos retrasados con solo el 13 % de los pedidos. **Decisión:** priorizar la renegociación logística en RJ y el Nordeste, y activar contacto proactivo y cupones cuando un pedido supera la fecha estimada.” | Explicación de resultado y decisión |
| 4:05–4:30 | `docs/uso_ia.md` | “La IA me ayudó a explicar por qué el % a tiempo daba 91,9 % en pandas y 93,2 % en SQL: la fecha estimada no tiene hora. Lo validé calculando ambas versiones: la diferencia son exactamente 1 291 pedidos entregados el mismo día estimado.” | Uso de IA, qué se validó |

Consejos: grabar a 1080p con la ventana del navegador maximizada; ampliar el zoom de Adminer al
125 %; ensayar una vez con cronómetro. Si se excede de 5 min, acortar el bloque de Adminer.
