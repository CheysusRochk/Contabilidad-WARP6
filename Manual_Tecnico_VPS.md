# Manual Técnico de Implementación en VPS
## contabilidad.warp6.com.bo

Este documento detalla la arquitectura técnica y el funcionamiento del despliegue del Sistema Contable WARP6 en su servidor VPS (Virtual Private Server).

> [!NOTE]
> Dado que el repositorio no incluye archivos de configuración de Docker (Dockerfile, docker-compose.yml), la implementación en el VPS se ha realizado de forma **nativa** (Bare Metal / Entorno Virtual de Python) utilizando servicios del sistema Linux.

---

## 1. Arquitectura del Despliegue

El sistema web `contabilidad.warp6.com.bo` funciona gracias a la interacción de tres componentes principales en su VPS:

### A. La Aplicación (Streamlit / Python)
- **Qué es:** Es el código fuente que tienes en este repositorio (`app.py`, `logic.py`, etc.).
- **Cómo funciona:** Se ejecuta mediante un entorno de Python. Streamlit levanta un servidor web interno que, por defecto, escucha en el puerto `8501`.
- **Base de datos:** Utiliza SQLite (`contabilidad_warp6.db`). Todo se guarda en este archivo físico local dentro del VPS.

### B. El Gestor de Procesos (PM2)
- **Qué es:** PM2 es el administrador de procesos en producción para Node.js y Python.
- **Cómo funciona:** Mantiene vivo el proceso de Streamlit en segundo plano, lo reinicia si falla o si el VPS se reinicia (mediante el servicio de sistema `pm2-root.service`).
- **Nombre del Proceso:** `warp6-conta` (ID: 2).
- **Entorno Virtual:** `/var/www/Contabilidad-WARP6/venv/bin/python`
- **Comando de Ejecución:**
  ```bash
  /var/www/Contabilidad-WARP6/venv/bin/python -m streamlit run accounting_app/app.py --server.port 8501 --server.address 127.0.0.1
  ```

### C. El Servidor Web Inverso (Nginx)
- **Qué es:** El software que recibe las peticiones de los usuarios cuando entran a `https://contabilidad.warp6.com.bo` (puerto 443 con SSL).
- **Cómo funciona:** Como Streamlit corre internamente en `127.0.0.1:8501`, Nginx actúa como un "Reverse Proxy" (Proxy Inverso). Recibe la petición del dominio y la redirige internamente a Streamlit mediante WebSockets y HTTP.

---

## 2. Flujo de Funcionamiento

1. Un usuario entra a `https://contabilidad.warp6.com.bo` en su navegador.
2. El DNS apunta esa dirección IP al VPS.
3. Nginx recibe la petición web segura (HTTPS).
4. Nginx enruta el tráfico internamente a `http://127.0.0.1:8501`.
5. El servicio de Streamlit (mantenido vivo por PM2 bajo `warp6-conta`) procesa la vista, consulta la base de datos `contabilidad_warp6.db` y devuelve la interfaz.

---

## 3. ¿Cómo realizar actualizaciones? (Flujo de Producción)

Actualmente te encuentras en la rama de git `deploy-vps`. Dado que esta rama está sincronizada con GitHub, el proceso de actualización es:

### Pasos para actualizar el servidor:

1. **Subir los cambios (Local):**
   ```bash
   git commit -m "Tus mejoras"
   git push origin deploy-vps
   ```

2. **Entrar al VPS por SSH:**
   ```bash
   ssh root@test1
   ```

3. **Descargar los cambios (En el VPS):**
   ```bash
   cd /var/www/Contabilidad-WARP6
   git pull origin deploy-vps
   ```

4. **Reiniciar el Proceso con PM2:**
   ```bash
   pm2 restart warp6-conta
   ```

---

## 4. Comandos Útiles de Mantenimiento (En el VPS)

**Ver el estado de los procesos:**
```bash
pm2 status
```

**Reiniciar la contabilidad:**
```bash
pm2 restart warp6-conta
```

**Ver los logs en tiempo real (errores y accesos):**
```bash
pm2 logs warp6-conta --lines 50
```

**Guardar el estado actual de PM2 para autoarranque:**
```bash
pm2 save
```

**Reiniciar Nginx (si cambias dominios o certificados SSL):**
```bash
sudo nginx -t
sudo systemctl restart nginx
```
