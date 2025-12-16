¡Buena idea para evaluar tu RAG, Thomas! 👍
*A Christmas Carol* es perfecto porque tiene **personajes claros, eventos secuenciales y temas abstractos**, lo que permite probar recuperación **factual, contextual y semántica profunda**.

Te propongo **queries organizadas por nivel de dificultad y tipo de señal semántica**, así puedes ver **qué chunks recupera** y **por qué**.

---

## 1️⃣ Queries muy específicas (factuales, alta precisión)

Estas prueban si el embedding + búsqueda recupera **chunks concretos**.

* **Q1:**

  > ¿Cómo se llama el socio fallecido de Scrooge?

* **Q2:**

  > ¿Qué advertencia le da el fantasma de Jacob Marley a Scrooge?

* **Q3:**

  > ¿Cuántos espíritus visitan a Scrooge y en qué orden aparecen?

* **Q4:**

  > ¿Qué objeto lleva el Fantasma de las Navidades Presentes?

* **Q5:**

  > ¿Qué frase repite Tiny Tim con frecuencia?

📌 **Esperado:**
Chunks con **nombres propios, descripciones literales o diálogos**.

---

## 2️⃣ Queries específicas pero parafraseadas (sin palabras exactas)

Evalúan si tu RAG **entiende el significado**, no solo coincidencias léxicas.

* **Q6:**

  > ¿Por qué el antiguo compañero de negocios de Scrooge está condenado a vagar como espíritu?

* **Q7:**

  > ¿Qué ejemplos muestran que Scrooge fue un niño solitario?

* **Q8:**

  > ¿Cómo se manifiesta la pobreza en la familia Cratchit?

📌 **Esperado:**
Chunks donde **no aparece la pregunta literal**, pero sí **la escena o idea**.

---

## 3️⃣ Queries de eventos narrativos (dependencia temporal)

Muy útiles para ver si los chunks mantienen **coherencia narrativa**.

* **Q9:**

  > ¿Qué aprende Scrooge durante su visita a las Navidades Pasadas?

* **Q10:**

  > Describe una escena importante mostrada por el Fantasma de las Navidades Presentes.

* **Q11:**

  > ¿Qué futuro aterrador ve Scrooge en la última visita?

📌 **Esperado:**
Chunks largos o múltiples chunks relacionados al **mismo espíritu**.

---

## 4️⃣ Queries temáticas / abstractas (semántica profunda)

Estas son claves para evaluar **embeddings de calidad**.

* **Q12:**

  > ¿Qué representa la avaricia en el cuento?

* **Q13:**

  > ¿Cómo se relaciona la historia con la idea de redención?

* **Q14:**

  > ¿Qué crítica social hace Dickens sobre la pobreza?

* **Q15:**

  > ¿Cuál es el mensaje moral principal del cuento?

📌 **Esperado:**
Chunks distribuidos por todo el texto, no un solo párrafo.

---

## 5️⃣ Queries comparativas / de contraste

Evalúan **relaciones entre chunks distantes**.

* **Q16:**

  > ¿Cómo cambia la actitud de Scrooge desde el inicio hasta el final del cuento?

* **Q17:**

  > Compara a Scrooge con Bob Cratchit en términos de valores humanos.

* **Q18:**

  > ¿En qué se diferencian los Fantasmas de las Navidades Pasadas y Futuras?

📌 **Esperado:**
Recuperación de **chunks de diferentes partes del cuento**.

---

## 6️⃣ Queries “engañosas” (para detectar falsos positivos)

Sirven para ver si tu RAG **recupera mal**.

* **Q19:**

  > ¿Qué papel juega Londres durante la Segunda Guerra Mundial en la historia?

* **Q20:**

  > ¿Cómo influyen los avances tecnológicos en la transformación de Scrooge?

📌 **Esperado:**

* Recuperación irrelevante **mínima**
* O fallback tipo: *“No se encuentra información en el texto”*

---

## 7️⃣ Queries ideales para evaluar ranking (top-k)

Usa estas para inspeccionar **orden de chunks recuperados**.

* **Q21:**

  > Explica quién es Jacob Marley y por qué es importante.

* **Q22:**

  > Describe el destino de Tiny Tim.

Aquí el **primer chunk** debería ser muy relevante, no solo “algo parecido”.

---

## 🧪 Métricas cualitativas que puedes observar

Cuando pruebes estas queries, fíjate en:

* ¿El **top-1** chunk responde directamente?
* ¿Los **top-k** son coherentes entre sí?
* ¿Recupera escenas correctas pero del espíritu equivocado?
* ¿Las queries abstractas traen solo escenas o también reflexión?

---

Si quieres, en el siguiente mensaje puedo:

* Diseñarte un **script de evaluación automática** (precision@k, recall@k)
* Ajustar queries según **tamaño de chunk y overlap**
* Ayudarte a **debuggear embeddings** (por ejemplo con bge-m3 u otro modelo)

¿Con qué modelo de embeddings estás probando el RAG?
