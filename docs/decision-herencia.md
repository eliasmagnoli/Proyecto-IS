# Decisión: mapeo de herencia en SQLAlchemy

## Contexto

El diagrama de clases tiene dos jerarquías que hay que guardar en la base de datos:

- `Author`, con las subclases `User` y `AIAgent`.
- `VotableContent`, con las subclases `Question` y `Response`.

Las tablas relacionales no tienen herencia, así que hay que elegir cómo representarla. La decisión condiciona el resto de los modelos:

- `Response` se relaciona con un `Author` (persona o IA).
- `Vote` se relaciona con un `VotableContent` (pregunta o respuesta).
- `Response` también se relaciona con su `Question`.

## Opciones evaluadas

| Opción | Cómo funciona | A favor | En contra |
|---|---|---|---|
| Tabla única (single table) | Una sola tabla con las columnas de todas las subclases | Sin JOINs, es la más simple | Muchas columnas en NULL; se pierden los `NOT NULL` de las columnas de cada subclase |
| Tablas unidas (joined) | Una tabla para la clase padre y una por subclase, unidas por la clave primaria | Sin NULL innecesarios, mantiene las restricciones de cada subclase, permite FK hacia el padre | Cada consulta polimórfica hace un JOIN |
| Tablas concretas (concrete) | Una tabla completa por subclase, sin tabla padre | Sin JOINs | No existe una tabla padre, así que no se puede hacer una FK a `Author` ni a `VotableContent` |

## Decisión

Usamos herencia **joined** en las dos jerarquías.

Razones:

1. **Integridad de datos.** `User` necesita `username`, `email` y `password_hash` obligatorios y únicos. En tabla única esas columnas quedarían nulables, porque las filas de `AIAgent` no las tienen, y la base ya no podría garantizarlas.
2. **Claves foráneas.** `Response` necesita una FK a `author.id` para que su autor pueda ser un `User` o un `AIAgent`. `Vote` necesita una FK a `votable_content.id` para votar preguntas y respuestas. Con tablas concretas no habría tabla padre a la que apuntar.
3. **El costo del JOIN es aceptable.** Es un JOIN por clave primaria entre dos tablas, que está indexada. Para el tamaño de este proyecto no es un cuello de botella.

Se descartó la tabla única para `VotableContent`, aunque era una opción razonable, porque `Response` necesita una FK a `Question` y en una tabla única esa FK apuntaría a la misma tabla. Además se perderían los `NOT NULL` de `title` y `question_id`.

## Consecuencias

- Cada subclase declara su `id` como `ForeignKey` a la tabla padre y como clave primaria.
- Las clases padre tienen una columna `type` que indica la subclase (`polymorphic_on`), y se marcan como abstractas (`polymorphic_abstract`) para que no se puedan instanciar directamente.
- Consultar `Author` devuelve objetos `User` o `AIAgent` según corresponda.
- Los modelos de los demás integrantes (`Question`, `Response`, `Vote`) deben seguir este mismo patrón.
- Se usa la tabla `users` y no `user`, porque `user` es palabra reservada en PostgreSQL.