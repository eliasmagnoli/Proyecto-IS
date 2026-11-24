# Proyecto-IS

## Modelo UML

![Diagrama de clases](docs/diagrama.png)

Explicación completa: [docs/explicacion_uml.md](docs/explicacion_uml.md)

## Justificación de patrones

### Abstracción de autoría y Factory Method

`Response` depende de la clase abstracta `Author` y no de `User` ni de `AIAgent`. Gracias al polimorfismo, una respuesta se atribuye de la misma forma a una persona o a un agente de IA, sin duplicar lógica ni acoplar la entidad a un tipo concreto.

Lo que cambia entre ambos casos no es la clase `Response`, sino cómo se construye: de dónde sale el contenido y qué autor se asigna. Esa variación se encapsula con Factory Method: `ResponseCreator` define un único flujo de publicación y delega en `HumanResponseCreator` y `AIResponseCreator` los pasos que difieren. Agregar un nuevo tipo de autor implica agregar una subclase de `Author` y una de `ResponseCreator`, sin modificar el código existente.

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

### Limitaciones conocidas

- Las sesiones viven en una cookie firmada y el servidor no guarda nada. Por eso el logout solo borra la cookie del navegador: una cookie copiada antes de cerrar sesión sigue siendo válida hasta que vence (31 días por defecto).
- No hay límite de intentos de login.
- La validación del email solo comprueba el formato, no que la casilla exista.

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