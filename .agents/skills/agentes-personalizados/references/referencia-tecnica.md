# Referencia Técnica: Agentes Personalizados en Google Antigravity

Documento de especificación exhaustiva sobre la configuración, tipos de datos, valores permitidos y comportamientos en tiempo de ejecución de los Custom Agents.

---

## 1. Especificación del YAML Frontmatter

```yaml
---
name: string                   # [Requerido] Identificador kebab-case único
description: string            # [Requerido] Descripción para el planner/orquestador
tools: string[]                # [Opcional] Herramientas permitidas (default: todas)
mainAgent: boolean             # [Opcional] Habilitar como Agente Principal (default: true)
subagent: boolean              # [Opcional] Habilitar como Subagente (default: true)
model: inherit | flash | pro   # [Opcional] Nivel de modelo (default: inherit)
commandExecutionPolicy: off | auto | eager | sandbox # [Opcional] (default: sandbox)
permissionMode: string         # [Opcional] Modo de permisos (ej: acceptEdits)
skills: string[]               # [Opcional] Lista de rutas a skills permitidas
mcpServers: object[]           # [Opcional] Servidores MCP específicos
---
```

---

## 2. Detalle de Parámetros

### `name` (String, Requerido)
* Define el identificador con el que el sistema registra el agente.
* **Convención**: Usar minúsculas separadas por guiones (kebab-case), por ejemplo `code-auditor`, `dependency-modernizer`, `tester-qa`.

### `description` (String, Requerido)
* Este texto es fundamental para la orquestación multi-agente.
* El modelo coordinador utiliza este campo para decidir automáticamente cuándo delegar un subobjetivo a este subagente.
* **Buena práctica**: Describir tanto las capacidades clave como las situaciones ideales de activación (ej: *"Especialista en auditoría estática de código, detección de vulnerabilidades OWASP y análisis de memory leaks. Usar para revisar PRs y cambios de seguridad"*).

### `tools` (Array de Strings, Opcional)
* Limita el conjunto de herramientas disponibles para el agente.
* Si se omite o está vacío, hereda las herramientas del entorno.
* **Herramientas estándar soportadas en Antigravity**:
  * Lectura de código y archivos: `view_file`, `grep_search`, `list_dir`
  * Edición y creación: `replace_file_content`, `multi_replace_file_content`, `write_to_file`
  * Ejecución y terminal: `run_command`, `manage_task`
  * Navegación web y búsqueda: `search_web`, `read_url_content`
  * Control de navegador: `browser_subagent`
  * Generación de medios: `generate_image`
* **Precaución**: Nombres no válidos o con errores tipográficos pueden provocar bloqueo en tiempo de ejecución.

### `mainAgent` vs `subagent` (Booleans, Opcionales - True Symmetry)
* `mainAgent: true`: Permite que el usuario inicie una sesión directamente con este agente en la UI de Antigravity 2.0 o mediante `agy --agent <name>`. Sus instrucciones se convierten en el system prompt principal.
* `subagent: true`: Permite que otros agentes llamen a este agente mediante `invoke_subagent`.
* Si un agente solo debe ser convocado como trabajador en segundo plano, define `mainAgent: false, subagent: true`.
* Si un agente está pensado únicamente para interacción directa humana, define `mainAgent: true, subagent: false`.

### `model` (String, Opcional)
* Selecciona la capacidad del modelo para este agente:
  * `inherit` (default): Usa el mismo modelo seleccionado en la sesión activa.
  * `flash`: Optimizado para velocidad, tareas de búsqueda rápida, formato o comprobaciones ligeras.
  * `pro`: Para tareas complejas de razonamiento profundo, arquitectura o auditorías críticas.

### `commandExecutionPolicy` (String, Opcional)
Controla el grado de autonomía y confirmación requerido para comandos de shell/terminal:
* `sandbox` (default): Ejecuta comandos en un entorno aislado con restricciones estrictas.
* `auto`: **Recomendado para agentes de testing/build.** Ejecuta automáticamente comandos de lectura, compilación y pruebas en segundo plano; pide confirmación para comandos de alto riesgo (borrado de archivos, operaciones destructivas).
* `eager`: Ejecuta comandos de forma permisiva sin solicitar confirmación a menos que haya alertas críticas de seguridad.
* `off`: Desactiva la ejecución de comandos.

### `skills` (Array de Strings, Opcional)
* Lista de habilidades específicas que se inyectan a la vista del agente.
* Formato: rutas relativas como `skills/nombre-de-la-skill` (por ejemplo `skills/seguridad-owasp`).
* Esto evita la saturación de contexto con decenas de skills globales del workspace.

---

## 3. Ciclo de Vida y Estados del Subagente

Cuando un Custom Agent es invocado como subagente:

1. **Running (En ejecución)**:
   * Ejecuta herramientas de forma autónoma.
   * La ventana de contexto del agente padre permanece limpia.
   * El usuario puede inspeccionar la consola en tiempo real (panel de subagentes o `Alt+J` en CLI).

2. **Idle (Inactivo / En espera)**:
   * Finaliza su turno y reporta un resumen al agente padre.
   * Conserva toda su memoria y contexto interno.
   * Si el padre o el usuario le envía un nuevo mensaje, se reactiva inmediatamente sin perder el hilo de trabajo anterior.

3. **Killed (Terminado)**:
   * Terminado manualmente por el usuario (`Stop Subagent` / tecla `k` en CLI) o por el padre.
   * Se limpian los worktrees temporales de Git asociados.
   * Las transcripciones se conservan en `.system_generated/logs/transcript.jsonl`.

### Límite de Profundidad (Nesting Limit)
* Antigravity impone un límite estricto de **10 niveles de anidamiento** para subagentes (agente padre -> subagente -> subagente hijo...) para prevenir recursiones infinitas y consumo desmedido de recursos.
