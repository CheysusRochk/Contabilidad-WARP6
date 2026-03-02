# Manual de Usuario - Sistema Contable WARP6

## 1. Introducción
El Sistema Contable WARP6 es una aplicación web diseñada para llevar el control financiero y tributario de la empresa, adaptada a la normativa boliviana (Ley 843 y DS 24051). Permite gestionar ingresos, gastos, impuestos (IVA, IT, IUE, Retenciones), activos fijos y generar reportes tanto para fines legales (SIN) como para la toma de decisiones gerenciales.

## 2. Flujo de la Aplicación y Cómo Usarla

La aplicación está dividida en 5 secciones principales accesibles desde el menú lateral:

### A. Dashboard Ejecutivo
- **Propósito:** Ofrece un vistazo rápido de la salud financiera de la empresa.
- **Funciones:**
  - Muestra KPIs clave: Ventas operativas, gastos totales, gastos no deducibles y crédito fiscal perdido.
  - Alerta sobre la "Eficiencia Fiscal", mostrando qué porcentaje de los gastos no tienen factura, lo cual incrementa el IUE anual.
  - Presenta gráficos visuales con la distribución de gastos por categoría.

### B. Registro de Transacciones
- **Propósito:** Ingresar el día a día operativo (Ingresos y Gastos).
- **Cómo usarlo:**
  - **Fecha y Tipo:** Define si el dinero entra o sale en una fecha específica.
  - **Categoría:** Es vital clasificar correctamente (Ej. "Aporte de Capital", "Sueldos", "Servicios Técnicos") ya que el sistema usa esto para armar el balance y estado de resultados.
  - **Facturas y Retenciones:** Si es un gasto sin factura, puedes marcar aplicar "Retención (Grossing Up)" para asumir el impuesto del proveedor (13% RC-IVA + 3% IT) y hacerlo un gasto deducible.
  - **Bancarización:** Si el monto supera los 50.000 Bs, el sistema generará una alerta recordando la obligatoriedad de usar medios fehacientes de pago (comprobante bancario).

### C. Reportes y Estados Financieros
- **Propósito:** Generar los documentos finales y auditar la realidad contra lo legal.
- **Funciones:**
  - **Fecha de Corte:** Permite sacar balances, filtrando las transacciones estrictamente hasta un día específico.
  - **Reportes Legales (SIN):** Excluyen los gastos sin factura (si no tienen retención) para adherirse estrictamente a la normativa en el Balance General y el Estado de Resultados.
  - **Reportes Gerenciales (Reales):** Muestran la cruda realidad de la caja, incluyendo gastos no deducibles, revelando la *Caja Líquida Real* tras reservar utilidades para el IUE.
  - **Exportación RCV:** Descarga un archivo Excel estructurado para la presentación de los Registros de Compras y Ventas en el SIAT.

### D. Activos Fijos
- **Propósito:** Gestión, registro y depreciación del equipamiento de la empresa.
- **Cómo usarlo:** Permite registrar equipos computacionales y otros activos fijos indicando su valor inicial y fecha de compra. El sistema calcula automáticamente la depreciación acumulada y mensual basada en la vida útil normativa (Ej. 4 años para computadoras).

### E. Importar Data
- **Propósito:** Cargar transacciones masivamente desde Excel, útil para historiales largos.
- **Cómo usarlo:** Descarga la "Plantilla de Importación", complétala respetando estrictamente las columnas (incluyendo las validaciones en "Tiene_Factura" y "Aplica_Retencion"), y sube el archivo. El importador validará tipo, montos y formato antes de guardarlos.

---

## 3. Arquitectura y Usos Técnicos

El sistema está construido como una aplicación web moderna orientada a la eficiencia y el uso de Data Science para los cálculos y reportes.

- **Stack Tecnológico:**
  - **Frontend / Interfaz:** `Streamlit` (Framework de Python) param generar una interfaz web interactiva sin necesidad de HTML/CSS complejo.
  - **Manipulación de Datos:** `Pandas`, utilizado extensivamente para cálculos rápidos, filtrado de DataFrames, agrupaciones tributarias y exportación a .xlsx.
  - **Base de Datos:** `SQLite` (vía `sqlite3`), almacenada en formato local en el archivo `contabilidad_warp6.db`. Permite tener transaccionalidad segura sin configurar un servicio externo robusto tradicional.

- **Estructura Interna (Archivos Principales):**
  - `app.py`: Orquesta la interfaz de usuario, las vistas (menús laterales) y el renderizado de gráficos y métricas métricas llamando a los paquetes visuales de Streamlit.
  - `logic.py`: Contiene el "Cerebro" matemático. Posee las funciones atómicas que calculan impuestos (IVA, IT, IUE), aplican acrecentamientos (Grossing up) y realizan las sumatorias complejas tanto para saldos contables fiscales como reales.
  - `database.py`: Gestiona las consultas SQL directas. Inicializa las tablas si no existen e inserta los registros y activos previniendo problemas de inyección y formato.
  - `importer.py`: Lee, parsea y estandariza los archivos de Excel suministrados por el usuario durante la migración masiva.
  - `reports.py`: Toma los diccionarios generados por el archivo lógico y diagrama / "dibuja" los reportes en formatos PDF listos para impresión contable.

---

## 4. Mejores Prácticas de Uso Contable y Técnico

1. **Clasificación Cuidada de Categorías:**
   - Asegúrate de diferenciar bien un "Aporte de Capital" de un ingreso por ventas/servicios. Los aportes no generan ni IVA ni IT, lo que protege tus márgenes, mientras que un ingreso sí.
   - Marca los "Pagos de Impuestos" cuidadosamente para evitar doble conteo pasando por encima de las obligaciones fiscales mensuales previamente generadas.
   - **Tabla de Clasificación Automática de Categorías:** El sistema inteligente analiza las palabras dentro del nombre de la **Categoría** para clasificar la transacción y generar los reportes de forma automática. Es vital usar estas palabras clave al crear nuevas categorías o importar:

| Clasificación en Reporte | Palabras Clave Detectadas (Automático) | Comportamiento Contable en el Sistema |
| :--- | :--- | :--- |
| **Aportes de Capital** | `aporte` y `capital` | Aumenta el patrimonio y la caja. No genera IVA, IT ni se toma como venta. No paga IUE. |
| **Costo de Ventas** | `material`, `equipo`, `mercaderia`, `costo`, `compra` | Se resta de las Ventas para calcular el **Margen Bruto** directo. |
| **Gastos de Personal** | `sueldo`, `salario`, `personal`, `afp`, `patronal`, `planila` | Se agrupa en Estado de Resultados debajo del margen bruto. |
| **Gastos Financieros** | `interes`, `banco`, `comision`, `financiero` | Se envía al final del Estado de Resultados (antes de impuestos). |
| **Gasto por Impuestos** | `impuesto`, `it`, `tasa`, `patente` *(sin decir pago)* | Gasto tributario incurrido en el mes. Deducible o no según la factura. |
| **Pago de Pasivos** | `pago` y (`impuesto`, `iva`, `it`, `tributo`) | Reduce la caja y la deuda pendiente de impuestos. **No entra al Estado de Resultados** como gasto (evita duplicar el gasto que ya generaste el mes anterior). |
| **Activos Fijos (CAPEX)**| `equipos de computación`, `vehículos`, `muebles y enseres`, etc. | No entran directamente al gasto P&L. El sistema los extrae y envía el impacto al P&L mediante la depreciación (25% anual, etc.). |
| **Gastos Operativos Fijos**| *(Cualquier otra categoría no listada arriba)* | Entran en la bolsa de "Gastos Operativos" regulares (Ej. `Servicios Básicos`, `Alquiler`). |

2. **Gestión Proactiva de Gastos sin Factura:**
   - Esfuérzate por obtener facturas para salvaguardar tu Crédito Fiscal. Utiliza la herramienta del Dashboard "Eficiencia Fiscal" y el reporte "Tax Shield" para saber cuánto dinero se pierde mes a mes.
   - Si debes registrar un gasto grande no facturado que sea completamente indispensable para la compañía, marca la opción **Aplica Retención (Grossing Up)**. Esto aumentará artificialmente el impacto del gasto, pero lo asegurará 100% como deducible del IUE al final de la gestión.

3. **Separación de Realidades para Reportes:**
   - Al presentar resultados al directorio o dueños, usa siemrpe los **Reportes Gerenciales**. Muestran la "Caja Real" disponible en billetera o banco.
   - Para las declaraciones juradas y presentaciones anuales de estados financieros, usa únicamente los **Reportes Legales (SIN)**.

4. **Resguardo Frecuente (Backups):**
   - Técnicamente toda la historia, la lógica y los datos contables viven en un solo archivo físico: `contabilidad_warp6.db`. Haz copias periódicas de este archivo.

5. **Cierres Mensuales con RCV:**
   - Aprovecha el sistema en modalidad de Cierre Mensual. Usa los informes de "Calendario Fiscal Mensual" y la exportación de RCV antes del vencimiento del NIT, cuadrando a centavos los montos adeudados con los montos pagados.
