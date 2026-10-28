# Modelo conceptual (UML) — Plataforma colaborativa de Preguntas y Respuestas

![Diagrama de clases](diagrama.png)

## 1. Visión general

La plataforma es un sistema tipo StackOverflow para estudiantes universitarios. El modelo se organiza en cinco bloques:

| Bloque | Clases | Para qué sirve |
|---|---|---|
| Autoría | `Author`, `User`, `AIAgent`, `Role` | Quién escribe: una persona o un agente de IA, tratados de forma homogénea |
| Contenido | `VotableContent`, `Question`, `Response`, `Category`, `Tag` | Preguntas, respuestas y su clasificación |
| Votación | `Vote`, `VoteType` | Votos positivos y negativos sobre el contenido |
| Generación con IA (**Strategy**) | `LLMStrategy`, `OpenAIStrategy`, `GeminiStrategy`, `LocalInferenceStrategy` | Proveedores de LLM intercambiables |
| Creación de respuestas (**Factory Method**) | `ResponseCreator`, `HumanResponseCreator`, `AIResponseCreator` | Cómo se fabrica una respuesta según quién la escribe |

Convención de visibilidad: `-` privado, `+` público, `#` protegido. Un atributo con `/` (por ejemplo `/isResolved`) es **derivado**: se calcula, no se guarda.

---

## 2. Autoría

### `Author` (clase abstracta)
Abstrae el concepto de "quien escribe una respuesta". Permite que `Response` dependa de una sola clase sin saber si el autor es una persona o una IA (polimorfismo).

| Miembro | Descripción |
|---|---|
| `id: int` | Identificador único del autor |
| `createdAt: datetime` | Fecha de creación del autor en el sistema |
| `getDisplayName(): str` *(abstracto)* | Nombre que se muestra junto a la respuesta. Cada subclase lo define a su manera |

### `User` (hereda de `Author`)
Usuario humano registrado con correo y contraseña.

| Miembro | Descripción |
|---|---|
| `username: str` | Nombre público del usuario |
| `email: str` | Correo electrónico, usado para el registro |
| `passwordHash: str` | Contraseña almacenada como hash, nunca en texto plano |
| `role: Role` | Rol del usuario (`ADMIN` o `GENERAL_USER`) |
| `reputation: int` | Puntaje de reputación acumulado a partir de los votos recibidos |
| `getDisplayName(): str` | Devuelve el nombre de usuario |
| `checkPassword(rawPassword): bool` | Verifica una contraseña ingresada contra el hash guardado |

### `AIAgent` (hereda de `Author`)
Agente de respuestas automáticas. Es el **contexto** del patrón Strategy: delega la generación del texto en un `LLMStrategy`.

| Miembro | Descripción |
|---|---|
| `agentName: str` | Nombre visible del agente |
| `modelVersion: str` | Versión del modelo que usa, a modo informativo |
| `timeoutMinutes: int` | Minutos que una pregunta puede quedar sin respuesta antes de que el agente intervenga |
| `getDisplayName(): str` | Devuelve el nombre del agente |
| `setStrategy(strategy): void` | Cambia el proveedor de LLM en tiempo de ejecución |
| `generateAutoResponse(question): str` | Genera el texto de una respuesta delegando en la estrategia actual |

### `Role` (enumeración)
`ADMIN` y `GENERAL_USER`: los tipos de usuario que pide el enunciado.

---

## 3. Contenido

### `VotableContent` (clase abstracta)
Agrupa lo que tienen en común las preguntas y las respuestas: ambas tienen cuerpo, fecha y se pueden votar. Evita duplicar la lógica de votos.

| Miembro | Descripción |
|---|---|
| `id: int` | Identificador único |
| `body: str` | Cuerpo del contenido (texto enriquecido) |
| `publishedAt: datetime` | Fecha de publicación |
| `calculateScore(): int` | Calcula el puntaje a partir de sus votos (positivos menos negativos) |
| `addVote(vote): void` | Registra un voto sobre este contenido |

### `Question` (hereda de `VotableContent`)

| Miembro | Descripción |
|---|---|
| `title: str` | Título de la pregunta |
| `/isResolved: bool` | **Derivado.** Es verdadero si alguna de sus respuestas fue aceptada |
| `addTag(tag): void` | Asocia una etiqueta a la pregunta |
| `acceptResponse(response): void` | Marca una respuesta como aceptada. Solo lo puede hacer el autor de la pregunta |

### `Response` (hereda de `VotableContent`)

| Miembro | Descripción |
|---|---|
| `isAccepted: bool` | Indica si es la respuesta aceptada por el autor de la pregunta |
| `markAsAccepted(): void` | Cambia el estado a aceptada |

La respuesta se relaciona con un `Author` (no con `User`), por eso puede ser de una persona o de una IA.

### `Category`
Clasificación obligatoria y única de cada pregunta (por ejemplo: *Python*, *Flask*, *Base de Datos*).

| Atributo | Descripción |
|---|---|
| `id: int` | Identificador único |
| `name: str` | Nombre de la categoría |
| `description: str` | Descripción de qué temas abarca |

### `Tag`
Etiqueta libre; una pregunta puede tener varias. También sirve para activar al agente (por ejemplo `#ia-help`).

| Atributo | Descripción |
|---|---|
| `id: int` | Identificador único |
| `name: str` | Texto de la etiqueta |

---

## 4. Votación

### `Vote`

| Atributo | Descripción |
|---|---|
| `id: int` | Identificador único |
| `value: VoteType` | Si es positivo o negativo |
| `createdAt: datetime` | Fecha en que se emitió |

### `VoteType` (enumeración)
`UPVOTE` (positivo) y `DOWNVOTE` (negativo).

---

## 5. Patrón Strategy: generación de contenido con LLM

| Rol en el patrón | Clase |
|---|---|
| Contexto | `AIAgent` |
| Estrategia (interfaz) | `LLMStrategy` |
| Estrategias concretas | `OpenAIStrategy`, `GeminiStrategy`, `LocalInferenceStrategy` |

### `LLMStrategy` (interfaz)
| Método | Descripción |
|---|---|
| `generateCompletion(prompt, context): str` | Recibe la consigna y el contexto, y devuelve el texto generado. Es el único método que el resto del sistema conoce |

### Estrategias concretas
Todas implementan `generateCompletion` con su propio proveedor.

| Clase | Atributos | Descripción |
|---|---|---|
| `OpenAIStrategy` | `apiKey`, `modelName`, `temperature` | Usa la API de OpenAI. `temperature` controla la variabilidad de la respuesta |
| `GeminiStrategy` | `apiKey`, `modelName` | Usa la API de Gemini |
| `LocalInferenceStrategy` | `modelPath`, `device` | Ejecuta un modelo local; `modelPath` es la ruta del modelo y `device` el hardware (CPU o GPU) |

---

## 6. Patrón Factory Method: creación de respuestas

| Rol en el patrón | Clase |
|---|---|
| Creador (abstracto) | `ResponseCreator` |
| Creadores concretos | `HumanResponseCreator`, `AIResponseCreator` |
| Producto | `Response` |

### `ResponseCreator` (clase abstracta)
Define el flujo único para publicar una respuesta.

| Método | Descripción |
|---|---|
| `publishResponse(question, rawContent = null): Response` | **Método plantilla.** Obtiene el contenido con `resolveContent`, crea la respuesta con `createResponse` y la publica. Es igual para todos los creadores |
| `resolveContent(question, rawContent): str` *(abstracto)* | Paso 1: consigue el texto de la respuesta |
| `createResponse(question, content): Response` *(abstracto)* | **Método fábrica.** Paso 2: construye la `Response` asignando el autor correspondiente |

### Creadores concretos

| Clase | `resolveContent` | `createResponse` |
|---|---|---|
| `HumanResponseCreator` | Devuelve el texto escrito por la persona (`rawContent`) | Crea la respuesta y le asigna un `User` como autor |
| `AIResponseCreator` | Ignora `rawContent` y pide el texto al `AIAgent` (que usa su estrategia) | Crea la respuesta y le asigna el `AIAgent` como autor |

---

## 7. Relaciones y multiplicidades

| Relación | Multiplicidad | Significado |
|---|---|---|
| `User` — `Question` (publica) | 1 a 0..* | Un usuario publica muchas preguntas; cada pregunta conoce a su autor |
| `Question` → `Category` | 0..* a 1 | Cada pregunta pertenece a exactamente una categoría |
| `Question` → `Tag` | 0..* a 0..* | Una pregunta tiene varias etiquetas y una etiqueta se usa en varias preguntas |
| `Question` ◆— `Response` (composición) | 1 a 0..* | Una pregunta contiene sus respuestas; si se borra la pregunta, se borran sus respuestas |
| `Response` → `Author` | 0..* a 1 | Cada respuesta tiene un único autor, persona o IA |
| `AIAgent` → `Tag` (se activa con) | 0..* a 0..* | Las etiquetas (como `#ia-help`) que disparan al agente |
| `User` → `Vote` (emite) | 1 a 0..* | Un usuario emite muchos votos |
| `VotableContent` ◆— `Vote` (composición) | 1 a 0..* | Un contenido recibe muchos votos; un voto no existe sin su contenido |
| `AIAgent` ◇→ `LLMStrategy` | 1 | El agente usa exactamente una estrategia a la vez |
| `HumanResponseCreator` → `User` | 1 | Asigna al usuario como autor |
| `AIResponseCreator` → `AIAgent` | 1 | Usa el agente y lo asigna como autor |
| `Question`/`Response` hereda de `VotableContent` | — | Ambas se pueden votar |
| `User`/`AIAgent` hereda de `Author` | — | Ambos pueden escribir respuestas |

### Reglas del dominio (notas del diagrama)
- Un usuario vota una sola vez por contenido y no puede votar el propio.
- Solo el autor de la pregunta puede aceptar una respuesta.

---

## 8. Justificación de los patrones

### Abstracción de autoría y Factory Method
`Response` depende de la abstracción `Author`, no de `User` ni de `AIAgent`. Gracias al polimorfismo, la respuesta trata igual a un humano y a una IA.

Lo que cambia entre ambos casos no es la clase `Response`, sino **cómo se construye**: de dónde sale el contenido y qué autor se asigna. Esa variación se encapsula en los creadores. `ResponseCreator` define un único flujo de publicación y delega en sus subclases solo los pasos que difieren.

Para agregar un nuevo tipo de autor (por ejemplo, un bot moderador) basta con agregar una subclase de `Author` y una de `ResponseCreator`. El código existente (`Response`, `publishResponse`, los otros creadores) no se modifica. Con un `if` sobre el tipo de autor, en cambio, habría que editar código que ya funciona cada vez que aparece un tipo nuevo.

### Strategy
`AIAgent` necesita generar texto con un LLM, pero el proveedor puede cambiar (OpenAI, Gemini, un modelo local). Para que ese cambio no afecte al resto del sistema se aplica Strategy: `AIAgent` (contexto) depende solo de la interfaz `LLMStrategy`, y cada proveedor es una estrategia concreta que la implementa.

**Sin el patrón.** `AIAgent` llamaría directamente a la API de un proveedor. Pasar de OpenAI a Gemini obligaría a modificar `AIAgent`: cambiar las llamadas, los parámetros (`apiKey`, `temperature`, `modelPath`...) y, si se quisieran soportar varios proveedores a la vez, agregar un `if` por proveedor. Cada proveedor nuevo implicaría volver a editar esa clase, con riesgo de romper lo que ya funcionaba. Además, el dominio quedaría acoplado a los detalles de cada proveedor.

**Con el patrón.**
- Cada proveedor vive en su propia clase (`OpenAIStrategy`, `GeminiStrategy`, `LocalInferenceStrategy`) y encapsula sus detalles propios: credenciales, modelo y parámetros.
- `AIAgent` solo conoce `generateCompletion(prompt, context)`. No sabe qué proveedor hay detrás.
- Cambiar de proveedor es llamar a `setStrategy(...)` con otra estrategia, incluso en tiempo de ejecución.
- Agregar un proveedor nuevo es crear una clase que implemente `LLMStrategy`, sin tocar el código existente (principio abierto/cerrado).

**Qué no se entera del cambio.** `AIAgent`, `AIResponseCreator`, `Response`, `Question` y el resto del dominio. El cambio de proveedor queda aislado en las clases de estrategia, que es el desacople que pide el enunciado.
