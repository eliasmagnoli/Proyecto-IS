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
tests/                # tests con pytest
docs/                 # diagrama UML y su explicación
```

## Cómo ejecutarlo

Requisitos: uv y Python 3.12+

```bash
uv sync
uv run flask --app app run --debug
```

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