---
name: agentes-personalizados
description: >-
  Guía completa y flujo de trabajo para crear, configurar e invocar agentes personalizados
  (Custom Agents y Subagents) en Google Antigravity. Utiliza esta habilidad siempre que
  se requiera crear un nuevo agente especializado, configurar archivos de agente en .agents/agents/,
  definir los campos del YAML frontmatter (tools, mainAgent, subagent, model, commandExecutionPolicy, skills),
  establecer el system prompt o configurar la invocación como Agente Principal o Subagente.
---

# Habilidad: Agentes Personalizados (Antigravity Custom Agents)

Esta habilidad proporciona el conocimiento técnico y los procedimientos paso a paso para crear, configurar y ejecutar **Agentes Personalizados (Custom Agents)** en Google Antigravity (Antigravity 2.0 Desktop y Antigravity CLI).

---

## 1. ¿Qué son los Agentes Personalizados?

Un **Custom Agent** es una configuración declarativa basada en un archivo Markdown (`.md`) con un encabezado YAML frontmatter. Define un rol especializado con su propio conjunto acotado de instrucciones, herramientas permitidas, políticas de seguridad y habilidades asociadas.

### Beneficios clave:
* **Especialización sin repetición**: El agente adopta un rol claro (ej. auditor de seguridad, gestor de dependencias, experto en tests) con sus convenciones de proyecto sin tener que explicárselo en cada prompt.
* **Eliminación del *Context Window Bloat***: Solo carga las herramientas y skills necesarias para ese rol, ahorrando tokens y evitando confusiones de herramientas.
* **Simetría Real (*True Symmetry*)**: Puede actuar tanto como **Agente Principal (Main Agent)** en sesiones directas con el usuario, como **Subagente Asíncrono (Subagent)** delegado por un orquestador.

---

## 2. Ubicación y Descubrimiento de Archivos de Agente

Antigravity busca automáticamente archivos de agente en las siguientes rutas (orden jerárquico):

| Ámbito | Ruta | Descripción |
| :--- | :--- | :--- |
| **Workspace (Proyecto)** | `.agents/agents/<nombre>.md`<br>o `.agents/agents/<nombre>/agent.md` | **Recomendado para proyectos.** Se comparte con el equipo vía control de versiones (Git). Disponible al clonar el repo. |
| **Global (Usuario/Máquina)** | `~/.gemini/config/agents/<nombre>.md`<br>o `~/.gemini/config/agents/<nombre>/agent.md` | Disponible en todos los proyectos de tu máquina local. |
| **Plugins** | `plugins/<plugin_name>/agents/` | Agentes empaquetados dentro de un plugin distribuible. |

> [!IMPORTANT]
> Para este proyecto, todos los agentes deben crearse dentro de `.agents/agents/` en la raíz del repositorio.

---

## 3. Estructura y Formato del Archivo (`.md`)

Todo archivo de agente se compone de dos partes fundamentales:
1. **Encabezado YAML Frontmatter** (delimitado por `---` al inicio y final).
2. **Cuerpo Markdown (System Prompt)** (instrucciones compiladas directamente en el rol del agente).

### Esquema del YAML Frontmatter

```yaml
---
name: nombre-del-agente
description: Descripción detallada de qué hace y cuándo debe invocarse.
tools:
  - view_file
  - replace_file_content
  - grep_search
  - run_command
mainAgent: true
subagent: true
model: inherit
commandExecutionPolicy: auto
permissionMode: acceptEdits
skills:
  - skills/mi-skill-especifica
---
```

### Detalle de Campos del Frontmatter

| Campo | Tipo | Requerido | Por defecto | Descripción |
| :--- | :--- | :---: | :---: | :--- |
| **`name`** | `string` | **Sí** | - | Identificador único en minúsculas y con guiones (ej. `dependency-modernizer`). |
| **`description`** | `string` | **Sí** | - | Descripción clara usada por el orquestador/planner para saber cuándo delegarle tareas. |
| **`tools`** | `string[]` | No | `[]` (todas) | Lista explícita de herramientas permitidas (ej. `view_file`, `replace_file_content`, `run_command`, `grep_search`). |
| **`mainAgent`** | `boolean` | No | `true` | Si es `true`, aparece en el dropdown de la GUI de Antigravity y se puede ejecutar con `agy --agent <nombre>`. |
| **`subagent`** | `boolean` | No | `true` | Si es `true`, puede ser invocado en segundo plano por otros agentes mediante `invoke_subagent`. |
| **`model`** | `string` | No | `inherit` | Nivel de modelo: `inherit` (hereda del padre), `flash` (rápido/económico), o `pro` (máximo razonamiento). |
| **`commandExecutionPolicy`** | `string` | No | `sandbox` | Política de ejecución de comandos terminal: `off`, `auto`, `eager`, `sandbox`. Con `auto`, ejecuta tests y builds de forma autónoma pero pide confirmación para comandos destructivos. |
| **`permissionMode`** | `string` | No | - | Modo de permisos (ej. `acceptEdits`, `bypassPermissions`). |
| **`skills`** | `string[]` | No | `[]` | Lista de rutas de habilidades específicas permitidas (ej. `skills/seguridad`). |
| **`mcpServers`** | `object[]` | No | `[]` | Servidores MCP adicionales o dedicados para este agente. |

> [!WARNING]
> **Validación de Herramientas**: Si se escribe mal el nombre de una herramienta en el campo `tools` (por ejemplo `runcommand` en vez de `run_command`), el agente puede colgarse en tiempo de ejecución. Verifica siempre la lista de herramientas válidas en [referencia-tecnica.md](./references/referencia-tecnica.md).

---

## 4. Invocación y Simetría de Ejecución

Antigravity soporta **True Symmetry**: un agente puede configurarse para ser Agente Principal, Subagente, o ambos.

### Modo 1: Como Agente Principal (Main Agent)
* **Requisito**: `mainAgent: true` en el frontmatter.
* **Cómo invocarlo**:
  * **En Antigravity 2.0 Desktop / IDE**: Selecciónalo directamente en el desplegable de agentes en la barra de chat.
  * **En Antigravity CLI**: Ejecuta el comando:
    ```bash
    agy --agent nombre-del-agente
    ```
* **Comportamiento**: La sesión primaria adopta el system prompt, modelo, herramientas y políticas definidas en el archivo `.md`.

### Modo 2: Como Subagente (Subagent Asíncrono)
* **Requisito**: `subagent: true` en el frontmatter.
* **Cómo invocarlo**:
  * El agente coordinador/padre llama a la herramienta `invoke_subagent` indicando el nombre del agente y la tarea:
    ```json
    {
      "SubagentName": "nombre-del-agente",
      "Task": "Instrucciones detalladas de la tarea a realizar...",
      "WorkspaceOption": "inherit"
    }
    ```
  * Opciones de workspace para subagentes:
    * `inherit`: Comparte el workspace actual con el padre.
    * `branch`: Crea un Git worktree aislado para experimentar sin alterar el código principal.
    * `share`: Comparte almacenamiento en un directorio específico.
* **Ciclo de vida**:
  1. `Running`: Ejecuta activamente herramientas y tareas en segundo plano.
  2. `Idle`: Finaliza la tarea, envía el resultado al padre y se pausa. Si recibe otro mensaje, se despierta automáticamente reteniendo su contexto.
  3. `Killed`: Terminado permanentemente.
* **Límite de anidamiento**: Hasta un máximo de 10 niveles de profundidad.

---

## 5. Procedimiento: Cómo Crear un Nuevo Agente en el Proyecto

Sigue estos pasos para crear un agente personalizado en este repositorio:

1. **Crear el directorio si no existe**:
   Asegúrate de que exista la carpeta `.agents/agents/` en la raíz del proyecto.

2. **Crear el archivo del agente**:
   Crea un archivo `.agents/agents/<nombre-del-agente>.md`.

3. **Definir el YAML Frontmatter**:
   Establece nombre, descripción clara, lista de `tools`, si es `mainAgent` y/o `subagent`, el `model` y la política `commandExecutionPolicy`.

4. **Redactar el System Prompt**:
   Debajo del cierre `---`, escribe las instrucciones del agente usando encabezados Markdown (`# Rol`, `# Reglas`, `# Flujo de Trabajo`, etc.).

5. **Verificar**:
   * Revisa que los nombres de las herramientas en `tools` coincidan con herramientas válidas de Antigravity.
   * Si usas CLI, ejecuta `agy --agent <nombre-del-agente>` para validar que sea descubierto.
   * Si usas la GUI, verifica que aparezca en el selector de agentes.

---

## 6. Recursos Adicionales

* [Referencia Técnica Completa de Campos y Políticas](./references/referencia-tecnica.md)
* [Plantillas y Ejemplos Prácticos de Agentes](./examples/plantillas.md)
