# Sistema Contable WARP6 SOLUTIONS S.R.L.

Aplicación web de gestión contable diseñada para servicios tecnológicos en Bolivia, cumpliendo con la Ley 843 y DS 24051.

## Características

*   **Registro de Transacciones**: Ingresos y Gastos con clasificación automática.
*   **Lógica Tributaria**: Cálculo automático de IVA (13%), IT (3%) e IUE referencial.
*   **Activos Fijos**: Módulo de depreciación para equipos de computación con ajuste UFV.
*   **Importación Masiva**: Carga de datos desde Excel con plantilla estandarizada.
*   **Dashboard Ejecutivo**: Análisis visual de gastos, métricas de crédito fiscal perdido y control de deducibilidad.
*   **Reportes Legales**:
    *   Exportación de RCV (Registro de Compras y Ventas) a Excel (Formato SIAT).
    *   Generación de Estado de Resultados en PDF.
*   **Control de Bancarización**: Alerta para transacciones mayores a 50.000 Bs.

## Categorías Especiales (Importante)

El sistema reconoce automáticamente ciertas palabras clave en la columna **Categoria** para aplicar reglas tributarias específicas:

*   **"Aporte de Capital"** (o similar): Se considera una inyección de dinero que **NO** genera impuestos (IVA/IT).
*   **"Pago de Impuestos"**: Se considera un egreso que **NO** genera crédito fiscal y no es deducible como gasto operativo directo en ciertos reportes.

## Requisitos

*   Python 3.8+
*   Librerías listadas en `requirements.txt`

## Instalación y Ejecución

1.  **Instalar dependencias**:
    Abre una terminal en la carpeta del proyecto y ejecuta:
    ```bash
    pip install -r requirements.txt
    ```

2.  **Iniciar la aplicación**:
    ```bash
    python -m streamlit run app.py
    ```

3.  **Usar el Sistema**:
    La aplicación se abrirá en tu navegador predeterminado (usualmente http://localhost:8501).

## Estructura del Proyecto

*   `app.py`: Archivo principal de la interfaz (Streamlit).
*   `database.py`: Manejo de base de datos SQLite (`contabilidad_warp6.db`).
*   `logic.py`: Cálculos de impuestos y depreciación.
*   `reports.py`: Generación de archivos Excel y PDF.
