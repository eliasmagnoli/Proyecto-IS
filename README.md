# Proyecto-IS

## Modelo UML

![Diagrama de clases](docs/diagrama.png)

Explicación completa: [docs/explicacion_uml.md](docs/explicacion_uml.md)

## Justificación de patrones

### Abstracción de autoría y Factory Method

`Response` depende de la clase abstracta `Author` y no de `User` ni de `AIAgent`. Gracias al polimorfismo, una respuesta se atribuye de la misma forma a una persona o a un agente de IA, sin duplicar lógica ni acoplar la entidad a un tipo concreto.

Lo que cambia entre ambos casos no es la clase `Response`, sino cómo se construye: de dónde sale el contenido y qué autor se asigna. Esa variación se encapsula con Factory Method: `ResponseCreator` define un único flujo de publicación y delega en `HumanResponseCreator` y `AIResponseCreator` los pasos que difieren. Agregar un nuevo tipo de autor implica agregar una subclase de `Author` y una de `ResponseCreator`, sin modificar el código existente.

#### Dónde está en el código

Los creadores están en `app/patterns/factory/`:

- `ResponseCreator`: clase abstracta con el método plantilla `publish_response(question, raw_content)`. Obtiene el texto, valida que no esté vacío, crea la respuesta y la guarda.
- `HumanResponseCreator(user)`: usa el texto que escribió la persona y asigna al `User` como autor.
- `AIResponseCreator(agent)`: ignora `raw_content`, pide el texto al agente (que lo genera con su estrategia de LLM) y asigna al `AIAgent` como autor.

Toda respuesta debe publicarse con `publish_response`, y no creando `Response` directamente. Así el flujo es el mismo para humanos y para la IA:

```python
HumanResponseCreator(user).publish_response(question, "Mi respuesta")
AIResponseCreator(agent).publish_response(question)
```

Si el texto queda vacío, lanza `ValueError` y no guarda nada. Si el LLM falla, `AIResponseCreator` deja pasar el `LLMError` para que lo maneje quien lo llama.

### Strategy

`AIAgent` genera respuestas automáticas con un LLM, pero el proveedor puede variar (OpenAI, Gemini, un modelo local). Con Strategy, `AIAgent` depende solo de la interfaz `LLMStrategy`, y cada proveedor es una estrategia concreta que la implementa y encapsula sus propios detalles (credenciales, modelo, parámetros).

Cambiar de proveedor es llamar a `setStrategy(...)`, incluso en tiempo de ejecución, y sumar uno nuevo es crear una clase más. Así, la integración con los LLM queda intercambiable y desacoplada del dominio: `AIAgent`, `Response`, `Question` y el resto del sistema no se enteran del cambio.

## Estructura del proyecto

```
app/
├── __init__.py       # create_app(): fábrica de la aplicación Flask
├── config.py         # configuración por entorno
├── extensions.py     # extensiones compartidas (db, migraciones)
├── cli.py            # comandos de Flask
├── models/           # una clase del diagrama por archivo
├── blueprints/       # rutas HTTP, un módulo por área (users, questions, responses, votes)
├── services/         # lógica compartida entre módulos (disparo de agentes de IA)
└── patterns/
    ├── factory/      # Factory Method: ResponseCreator y creadores concretos
    └── strategy/     # Strategy: LLMStrategy y proveedores de LLM
migrations/           # historial de migraciones de la base (Alembic)
tests/                # tests con pytest (unit/ y functional/)
docs/                 # diagrama UML, su explicación y decisiones de diseño
```

## Cómo ejecutarlo

Requisitos: uv y Python 3.12+

```bash
uv sync
uv run flask --app app db upgrade
uv run flask --app app run --debug
```

Para que las sesiones sean seguras fuera de desarrollo, definí una clave secreta propia:

```bash
export SECRET_KEY="una-clave-larga-y-aleatoria"
```

## Endpoints

### POST /users/register

Registra un usuario nuevo con el rol `GENERAL_USER`. Recibe un JSON con `username` (3 a 50 caracteres), `email` y `password` (mínimo 8 caracteres). El email se guarda en minúsculas y tanto el email como el nombre de usuario deben ser únicos. La contraseña se guarda solo como hash.

```bash
curl -X POST localhost:5000/users/register \
  -H "Content-Type: application/json" \
  -d '{"username":"ana","email":"ana@example.com","password":"secreto123"}'
```

Respuestas:

- `201`: usuario creado. Devuelve `id`, `username`, `email` y `role`.
- `400`: datos inválidos. Devuelve `{"errors": {...}}` con un mensaje por cada campo con problema.

### POST /users/login

Inicia sesión con `email` y `password` en un JSON. Si son correctos, el servidor guarda el usuario en la sesión (una cookie firmada de Flask) y devuelve sus datos. El email no distingue mayúsculas de minúsculas. Si el email no existe o la contraseña es incorrecta, devuelve el mismo error, para no revelar qué emails están registrados.

```bash
curl -i -c cookies.txt -X POST localhost:5000/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"ana@example.com","password":"secreto123"}'
```

Respuestas:

- `200`: sesión iniciada. Devuelve `id`, `username`, `email` y `role`.
- `401`: credenciales incorrectas.

### POST /users/logout

Cierra la sesión borrando la cookie. Responde `204`.

### GET /users/me

Devuelve el usuario con la sesión iniciada. Es un ejemplo de ruta protegida con `@login_required`. Para probarlo con curl hay que reenviar la cookie con `-b cookies.txt`.

- `200`: datos del usuario.
- `401`: no hay sesión iniciada.

### Permisos por rol

Para restringir una ruta a un rol se usa el decorador `role_required`:

```python
from app.blueprints.users.auth import role_required
from app.models import Role


@bp.post("/algo")
@role_required(Role.ADMIN)
def algo(): ...
```

Sin sesión devuelve `401`; con sesión pero sin el rol necesario, `403`. Acepta varios roles: `@role_required(Role.ADMIN, Role.GENERAL_USER)`.

### Limitaciones conocidas

- Las sesiones viven en una cookie firmada y el servidor no guarda nada. Por eso el logout solo borra la cookie del navegador: una cookie copiada antes de cerrar sesión sigue siendo válida hasta que vence (31 días por defecto).
- No hay límite de intentos de login.
- La validación del email solo comprueba el formato, no que la casilla exista.
- La respuesta automática se genera dentro del mismo pedido HTTP, así que publicar una pregunta etiquetada puede tardar lo que tarde el LLM.

## Agente de IA

El agente (`AIAgent`) genera respuestas con un LLM a través de la interfaz `LLMStrategy` (patrón Strategy). Por ahora hay tres estrategias:

- `GeminiStrategy`: usa la API de Gemini.
- `LocalInferenceStrategy`: usa un modelo que corre en tu propia máquina a través de Ollama.
- `FakeStrategy`: respuestas simuladas, para tests. No llama a ningún proveedor.

### Configurar Gemini

1. Sacá una clave de API en [Google AI Studio](https://aistudio.google.com/).
2. Definila como variable de entorno. La app no lee el archivo `.env` sola, así que hay que exportarla:

```bash
export GEMINI_API_KEY="tu-clave"
export GEMINI_MODEL="gemini-3.8-flash"   # opcional
```

`GEMINI_MODEL` es opcional; si no se define, se usa `gemini-3.8-flash`. Las variables disponibles están en `.env.example`. La clave nunca debe commitearse: `.env` está en `.gitignore`.

### Probar Gemini a mano

```bash
uv run python -c "from app.patterns.strategy.gemini_strategy import GeminiStrategy; print(GeminiStrategy.from_env().generate_completion('Respondé en una frase.', '¿Qué es Flask?'))"
```

### Configurar el modelo local

Usa [Ollama](https://ollama.com/) para correr un modelo en tu propia máquina, sin clave ni costo:

```bash
ollama pull llama3.2
```

Por defecto la estrategia se conecta a `http://localhost:11434` y usa el modelo `llama3.2`. Se pueden cambiar con las variables `LOCAL_LLM_URL` y `LOCAL_LLM_MODEL` (están en `.env.example`). Un modelo local puede tardar bastante en responder, sobre todo sin GPU.

A diferencia del diagrama UML, donde `LocalInferenceStrategy` tenía `modelPath` y `device`, acá el modelo corre en un servidor aparte (Ollama) y la clase solo necesita el nombre del modelo y la dirección. El patrón no cambia: sigue siendo una estrategia concreta que implementa `LLMStrategy`.

### Probar el modelo local a mano

```bash
uv run python -c "from app.patterns.strategy.local_inference_strategy import LocalInferenceStrategy; print(LocalInferenceStrategy.from_env().generate_completion('Respondé en una frase.', '¿Qué es Flask?'))"
```

### Uso en el código

```python
agent.set_strategy(GeminiStrategy.from_env())
texto = agent.generate_auto_response(question)
```

Para cambiar de proveedor, incluso en tiempo de ejecución, alcanza con asignar otra estrategia. `AIAgent` no cambia:

```python
agent.set_strategy(LocalInferenceStrategy.from_env())
```

La estrategia no se guarda en la base de datos: hay que asignarla cada vez que se carga el agente. Si el proveedor falla, la estrategia lanza `LLMError`.

### Respuesta automática por etiqueta

Un agente se asocia a una o más etiquetas (por ejemplo `ia-help`). Cuando se publica una pregunta con alguna de ellas, hay que llamar a:

```python
from app.services.ai_agent_triggers import trigger_agents

trigger_agents(question)
```

Cada agente asociado responde a través de `AIResponseCreator`. Si la pregunta no tiene etiquetas de agente, no pasa nada. Si el LLM falla, la pregunta queda publicada y el error se registra en el log. Un agente no responde dos veces a la misma pregunta.

El proveedor se elige con la variable `LLM_PROVIDER` (`gemini` por defecto, o `local`).

### Proceso periódico

Además de responder al publicar (por etiqueta), un proceso periódico hace que el agente
responda las preguntas que **nadie contestó** dentro de su `timeout_minutes`:

```bash
uv run flask --app app respond-unanswered
```

Para que corra solo, se programa con cron (por ejemplo, cada 5 minutos):

```cron
*/5 * * * * cd /ruta/al/proyecto && uv run flask --app app respond-unanswered
```

Reglas:

- Solo se consideran preguntas **sin ninguna respuesta**.
- Si hay varios agentes, se revisan del timeout más corto al más largo y responde **uno solo**.
- Si el LLM falla, el error se registra y la pregunta se reintenta en la próxima ejecución.

### Comandos de administración

```bash
uv run flask --app app create-agent --name helper --timeout 30 --tag ia-help
uv run flask --app app create-admin --username root --email root@example.com
```

`create-agent` crea (si no existen) las etiquetas que activan al agente.
`create-admin` pide la contraseña por consola.

## Base de datos y migraciones

Por defecto se usa SQLite (`instance/proyecto.db`). Para usar otra base, definí la variable de entorno `DATABASE_URL`. Por ejemplo, para PostgreSQL hace falta el driver y la URL de conexión:

```bash
uv add "psycopg[binary]"
export DATABASE_URL="postgresql+psycopg://usuario:clave@localhost:5432/proyecto"
```

### Tener la base al día

Después de clonar el repo o de traer cambios de `main`:

```bash
uv run flask --app app db upgrade
```

### Cambiar el esquema

Cuando modifiques un modelo:

```bash
uv run flask --app app db migrate -m "descripción del cambio"
```

Esto genera un archivo en `migrations/versions/`. Revisalo antes de seguir, porque Alembic no siempre detecta todo correctamente. Después aplicalo:

```bash
uv run flask --app app db upgrade
```

Los archivos de `migrations/` se commitean junto con el cambio del modelo.

## Tests y estilo de código

```bash
uv run pytest                # corre los tests y muestra la cobertura
uv run ruff check            # revisa errores y orden de imports
uv run ruff format           # formatea el código
```