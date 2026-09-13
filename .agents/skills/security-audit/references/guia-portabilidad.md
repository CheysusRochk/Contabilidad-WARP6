# Guía de Portabilidad y Uso en Otros Proyectos

Esta guía detalla cómo utilizar este flujo de auditoría de seguridad en cualquier otra aplicación web o de sistema que tengas en tu equipo.

---

## 🚀 Método 1: Uso Global Directo (Sin configurar nada)

Dado que la habilidad ha sido instalada en la configuración global de Antigravity (`~/.gemini/config/skills/security-audit/`):

1. Abre cualquier proyecto o carpeta en Antigravity IDE.
2. Escribe en el chat:
   ```text
   /security-audit
   ```
   o simplemente:
   ```text
   Audita la seguridad de este proyecto, mapea vulnerabilidades y prepara el reporte SECURITY_AUDIT.md
   ```
3. El asistente activará automáticamente el protocolo de 4 fases y generará `SECURITY_AUDIT.md` en esa carpeta.

---

## 📦 Método 2: Instalar la Plantilla Completa en un Proyecto Específico

Si deseas que un proyecto tenga sus propios subagentes dedicados (`security-scout`, `vuln-auditor`, `leak-secrets-detector`, `patch-crafter`) y personalizaciones locales:

### En Windows PowerShell:
Ejecuta este comando desde la terminal reemplazando `C:\Ruta\A\Tu\OtroProyecto`:

```powershell
Copy-Item -Path "c:\Users\cheysus\Documents\github\FLUJO DE DESAROLLO CONFIGURACION Y PRUEBAS\.agents" -Destination "C:\Ruta\A\Tu\OtroProyecto\.agents" -Recurse -Force
```

Esto copiará:
- `.agents/agents/security-scout.md`
- `.agents/agents/vuln-auditor.md`
- `.agents/agents/leak-secrets-detector.md`
- `.agents/agents/patch-crafter.md`
- `.agents/skills/security-audit/`

---

## 🛡️ Flujo de Trabajo Recomendado para Apps en Producción (VPS)

1. **Trabajar en la copia local:**
   Asegúrate de estar en una rama de trabajo local (ej. `git checkout -b security-audit-fixes`).
2. **Ejecutar la Auditoría:**
   Invoca `/security-audit`. Se generará el archivo `SECURITY_AUDIT.md`.
3. **Revisar las PoCs y Diffs:**
   Examina los escenarios de ataque descritos en el reporte y la matriz de riesgo de regresión.
4. **Aprobar y Aplicar Parches en Local:**
   Pídele al agente: *"Aplica el parche de VULN-001 y VULN-002"*. El subagente `patch-crafter` editará los archivos locales.
5. **Prueba y Validación Local:**
   Levanta la app en local (`npm run dev` o `python main.py`) y verifica que los flujos legítimos sigan funcionando sin regresiones.
6. **Deploy Seguro al VPS:**
   Haz commit de los parches y sube los cambios al VPS con confianza.
