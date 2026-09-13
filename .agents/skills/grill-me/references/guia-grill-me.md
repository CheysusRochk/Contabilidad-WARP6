# Guía de Uso de Grill-Me y Grilling

Documentación de referencia extraída del repositorio oficial `mattpocock/skills`.

## ¿Qué hace Grill-Me?

`grill-me` toma una **idea inicial o boceto** y te entrevista implacablemente hasta llegar a un compromiso y claridad de diseño total. No necesitas un plan cerrado para comenzar: producirlo es el objetivo de la sesión. Realiza preguntas organizadas en **rondas**, donde cada ronda representa la **frontera** actual (todas las decisiones cuyos prerrequisitos ya han sido resueltos).

Es **sin estado (stateless)**: no escribe archivos a menos que se solicite explícitamente, su objetivo es pulir la idea en la cabeza del desarrollador.

---

## Conceptos Clave

1. **El Árbol de Diseño (Design Tree):**
   Cada decisión ramifica en decisiones subsiguientes que dependen de ella.

2. **La Frontera (The Frontier):**
   El conjunto de preguntas que pueden formularse *ahora*, sin tener que adivinar respuestas futuras pendientes.

3. **Rondas (Rounds):**
   Todas las preguntas de la frontera actual se formulan juntas en una sola ronda con su respuesta sugerida (`??`), permitiendo responder rápidamente por número: *"1 sí, 2 la segunda opción, 3 no por esto..."*.

4. **Hechos vs. Decisiones:**
   - **Hechos:** Responsabilidad del agente (leer código, revisar dependencias, buscar en el proyecto).
   - **Decisiones:** Responsabilidad del usuario. El agente propone una recomendación fundamentada y espera.

---

## Formato Estándar de Pregunta

```markdown
? **Q1** - **<Título de la Pregunta>**: <Cuerpo descriptivo y opciones>

?? <Respuesta o recomendación sugerida por el agente>

---

? **Q2** - **<Título de la Pregunta>**: <Cuerpo descriptivo y opciones>

?? <Respuesta o recomendación sugerida por el agente>
```

---

## Criterios de Éxito

- Surgen discrepancias productivas: una sesión donde el usuario simplemente dice "sí a todo" no aportó valor real.
- Las preguntas llegan en pocas rondas densas y estructuradas, no en un goteo interminable de preguntas sueltas.
- El agente investiga el entorno antes de preguntar cosas obvias.
- La sesión concluye pidiendo confirmación de entendimiento mutuo antes de escribir código.
