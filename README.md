En el contenedor de docker creado por:

```yaml
version: "3.9"

services:
  pgvector:
    image: pgvector/pgvector:pg16
    container_name: test-pgvector-db
    environment:
      POSTGRES_USER: langchain
      POSTGRES_PASSWORD: langchain
      POSTGRES_DB: langchain
    ports:
      - "5432:5432"
    volumes:
      - ./data:/var/lib/postgresql/data

```
- Entramos al bash del contenedor:

```bash
docker exec -it test-pgvector-db bash
```

- Entramos al usuario langchain de postgres a la base de datos langchain del usuario langchain:

```bash
psql -U langchain -d langchain
```


y luego ejecutamos:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Esto instala la extension vector necesaria para manejar vectores.


---

.

.

.

.

.

.

.

.

---

Claro. Ese comando es **clave** cuando trabajas con embeddings en PostgreSQL + pgvector. Vamos por partes y con intuición matemática 👇

---

## 🔹 El comando completo

```sql
CREATE INDEX ON chunks
USING ivfflat (chunk_embedding vector_cosine_ops)
WITH (lists = 100);
```

Este comando crea un **índice vectorial aproximado** para hacer **búsquedas por similitud** de forma eficiente.

---

## 1️⃣ ¿Qué problema resuelve?

Sin índice, una consulta como:

```sql
SELECT *
FROM chunks
ORDER BY chunk_embedding <=> :query_embedding
LIMIT 5;
```

hace:

❌ **Búsqueda exhaustiva (full scan)**
→ compara tu vector contra **todos los embeddings**
→ complejidad ( O(N \cdot d) )

Con miles o millones de chunks → **muy lento**

---

## 2️⃣ ¿Qué es `ivfflat`?

`ivfflat` = **Inverted File Flat Index**

Es un algoritmo de **búsqueda aproximada de vecinos más cercanos (ANN)**:

### Idea intuitiva:

1. Agrupa los vectores en **clusters** (listas)
2. En una consulta:

   * No revisa todos los vectores
   * Solo revisa los clusters más cercanos al vector de consulta

📌 Sacrifica un poco de exactitud
📌 Gana **muchísima velocidad**

---

## 3️⃣ `vector_cosine_ops` — la métrica

```sql
(chunk_embedding vector_cosine_ops)
```

Indica **cómo medir similitud** entre vectores.

### Cosine similarity

Mide el **ángulo** entre vectores:

[
\cos(\theta) = \frac{v \cdot w}{|v| |w|}
]

✔️ Ideal para embeddings semánticos
✔️ Invariante a la magnitud
✔️ Es lo estándar para modelos como BGE, SBERT, OpenAI, etc.

En SQL usarás:

```sql
chunk_embedding <=> query_embedding
```

que internamente aplica coseno.

---

## 4️⃣ `lists = 100` — el parámetro clave

```sql
WITH (lists = 100);
```

Define **cuántos clusters** crea el índice.

### Intuición:

* Más `lists` → más clusters pequeños
* Menos `lists` → clusters grandes

### Trade-off:

| lists       | Precisión | Velocidad  | Memoria |
| ----------- | --------- | ---------- | ------- |
| bajo (10)   | baja      | muy rápida | baja    |
| medio (100) | buena     | rápida     | media   |
| alto (1000) | muy alta  | más lenta  | alta    |

📌 Regla práctica:

```
lists ≈ sqrt(N)
```

Ejemplo:

* 10k vectores → ~100 lists
* 1M vectores → ~1000 lists

---

## 5️⃣ ⚠️ Importante: no es automático

Para que PostgreSQL use el índice **DEBES** decirle cuántas listas explorar:

```sql
SET ivfflat.probes = 10;
```

* `probes` = número de clusters que se inspeccionan
* Más probes → más precisión, menos velocidad

📌 Típico:

```sql
SET ivfflat.probes = 5;   -- rápido
SET ivfflat.probes = 10;  -- balance
SET ivfflat.probes = 20;  -- más preciso
```

---
