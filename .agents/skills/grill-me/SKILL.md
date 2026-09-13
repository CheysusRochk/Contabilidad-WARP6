---
name: grill-me
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases or /grill-me.
---

# Grill-Me (Entrevista implacable de diseño)

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Format a round like so:

```markdown
? **Q1** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

?? <your recommended answer>

---

? **Q2** - **<question title>**: <question body, might be multiple paragraphs, including multiple choices>

?? <your recommended answer>
```

### Reglas Clave de Ejecución:

1. **Recomputar la Frontera:**
   Cada ronda de respuestas del usuario remodela el árbol: las decisiones resueltas expanden la frontera y desbloquean preguntas que dependían de ellas. Recomputa la frontera y formula la siguiente ronda. Una pregunta que dependa de otra pregunta aún abierta en esta ronda pertenece a una ronda *posterior*.

2. **Hechos vs. Decisiones:**
   Encontrar **hechos** es tu trabajo, nunca del usuario. Cuando una pregunta requiera un dato del entorno (código, archivos, herramientas, dependencias), explóralo tú mismo o delega en un subagente; nunca preguntes al usuario cosas que tú puedes verificar en el proyecto. Las **decisiones** son del usuario: preséntalas con tu recomendación (`??`) y espera.

3. **Criterio de Finalización:**
   La sesión termina cuando la frontera está vacía: cada rama del árbol de diseño ha sido visitada y no queda nada asumido en silencio. **No actúes ni generes código/plan definitivo** hasta que el usuario confirme explícitamente que se ha alcanzado un entendimiento mutuo.
