# Especificación técnica (`analisis/tecnico.md`)

Es lo que se construye. Con ella, las historias del funcional y el prototipo, quien construye con el
MCP de desarrollo de Appian no tiene que preguntar ni suponer nada. Es interna: no va al cliente.
Los fragmentos de los apartados 2, 13 y 14 son de un caso ficticio (solicitudes de autorización) y tienen el formato
exacto que leen los scripts.

## Cómo se escribe

- Cabecera `# <Proyecto> — Especificación técnica` y `Versión: x.y · Estado: en curso`, con la misma versión
  que el funcional. Pasa a `Estado: completo` cuando se entrega para construir: desde entonces, `comprobar.py`
  trata como error lo que falte (una pantalla sin su interfaz, un paso sin su nodo, un criterio sin prueba).
- Apartados `## N. Título` con los números de abajo; si uno no aplica, «No aplica: <motivo>». Los
  nombres de los objetos, en español y con las convenciones del apartado 1. Las fuentes se citan a la vista (`FU-03 00:14:32`).
- **Cada cosa en un sitio.** El comportamiento y los criterios están en las historias; la composición de
  cada pantalla, en el prototipo. Aquí se remite a ellos.
- **Fuera:** lo que la skill oficial de Appian resuelve siempre igual (UUID, nombre de columna desde el
  campo, la relación inversa).
- **Aplicación existente** (`as-is/`): los nombres son los de `as-is/datos/inventario.json` y de sus objetos de fuera
  de la aplicación (`dependencias.json`); los hallazgos, NV y REF se citan dentro de su fuente («[FU-01 NV-ARQ-01]»).
  Cambian §2, §3, §13 y §15, como se dice en cada uno. Sin `as-is/`, nada de eso.
- **Unidades de cambio** (`analisis/cambios.md`): lo que cambia en el técnico, en `cambios.md` §4.

## Buenas prácticas al diseñar

La especificación aplica `appian-best-practices` en su modo de orientar. No se carga su SKILL.md: antes de
escribir un apartado se abre solo la sección que dice la tabla, con
`python3 <skill>/../appian-best-practices/scripts/seccion.py <doc> <sección>` (sin número de sección,
lista los títulos del doc).

| Apartado | Abre en appian-best-practices |
|---|---|
| 0. Entorno | 00 «Before recommending: tier and version» |
| 1. Convenciones | 08 §1 y §2 |
| 2. Decisiones técnicas | 00, el bloque de la capa (Data, Security, Logic, Process, Interfaces, Navigation, Integrations, AI) |
| 3. Modelo de datos | 01 §1, §2, §4, §8 y §11; 05 §5 si hay volumen |
| 4. Grupos y seguridad | 06 §1 y §5 |
| 5. Estados y transiciones | 01 §1.1 |
| 6. Lógica | 04 §1, §5 y §9 |
| 7. Interfaces y acciones | 02 (la sección del componente); 01 §9; 09 §1 |
| 8. Procesos | 03 §1, §2, §6 y §7; 11 §1 y §2 |
| 9. Avisos | 03 §10 |
| 10. Integraciones, documentos e IA | 07; 01 §8.bis; 12 si hay IA |
| 11. Site e informes | 09; 05 §4 |
| 12. Volumen y operación | 05 §8; 11 §5 y §7; 13 |
| 13. Plan de construcción | Nada: el orden está en el propio apartado |
| 14. Pruebas y trazabilidad | 10; 11 §6 |

**Qué fuente manda** (BP 10 «Hierarchy when requirements conflict»): la seguridad y la validez de la
plataforma según la documentación de la versión del entorno; después, lo que el cliente ha aprobado en el
funcional; después, las decisiones `DT-nn` y las convenciones; después, las buenas prácticas; y al final,
las preferencias. Si algo aprobado choca con lo primero, no se reinterpreta: se explica al cliente en el
funcional con una alternativa (un PC) y se registra la decisión.

**Dudas de Appian:** lo que no se sabe con certeza (si existe algo, desde qué versión, en qué tier, sus
límites) se consulta en el MCP de documentación como dice el SKILL.md, y la URL va en el «Por qué» o en
«Verificado».

## Apartados

### 0. Entorno
Tabla `Dato · Valor · Fuente`: una fila «Aplicación» con su nombre exacto entre comillas invertidas, sin comentarios
ni paréntesis, y otra «Prefijo»; la URL de cada entorno (una fila por entorno:
«URL de desarrollo», «URL de pruebas», «URL de producción» y, si lo hay, «URL del entorno de corrección»), versión de
Appian en cada entorno, tier y complementos, base de datos, inicio de sesión, idioma y zona horaria, calendario
laboral, volumen, usuarios y concurrencia, tiempo de recuperación, accesibilidad, móvil y usuarios externos, licencias.
Sale de funcional §10 y de lo que diga el equipo. Lo que no se sabe es un PT. El prototipo toma de aquí la versión de
Appian, y la orden de terminar una issue, el Dev MCP de desarrollo de cada equipo (el que apunta a esa URL).
«Site» es el nombre del site en su URL (`/suite/sites/<site>`), y «Cuentas de prueba en desarrollo», el usuario de la
cuenta de cada rol (`Gestor: qa.gestor`), nunca su contraseña: de aquí los toma el QA (`appian-qa`).

### 1. Convenciones
Tabla `Qué · Convención · Por qué`: prefijo, idioma de los nombres, mayúsculas por tipo de objeto, nombre
de la clave, campos de auditoría, borrado, carpetas.

### 2. Decisiones técnicas
Una ficha `**DT-nn — Título**` por cada decisión que no sea obvia: cómo se modela algo, qué capa aplica una
regla de seguridad, cómo se parte un proceso en modelos, dónde se guardan los documentos, cómo se integra
un sistema. Tabla vertical:

| Campo | Contenido |
|---|---|
| **Capa** | Datos, Seguridad, Lógica, Proceso, Interfaz, Navegación, Integración, IA u Operación |
| **Necesidad** | Las HU, PAN, ACT o RB que la piden |
| **Decisión** | Qué se hace, con los nombres de los objetos |
| **Por qué** | En una frase, con `BP nn §x` y la URL de la documentación |
| **Descartada** | La alternativa y por qué no |
| **Riesgo** | Qué puede salir mal, o «Ninguno relevante» |
| **Depende de** | Versión o tier (ⓥ, ⓣ de buenas prácticas), u otra cosa; «—» si nada |
| **Verificar** | Qué hay que comprobar en el entorno; «—» si nada |
| **Verificado** | Dónde se comprobó (documentación de la versión, prueba) o «pendiente» |

```markdown
**DT-01 — Estados como record type de referencia**

| Campo | Contenido |
|---|---|
| **Capa** | Datos |
| **Necesidad** | funcional 3.2 y HU-03 |
| **Decisión** | `AUT Estado`, record type de referencia relacionado con `AUT Solicitud` |
| **Por qué** | Un estado escrito como texto en cada fila no se puede renombrar ni filtrar bien (BP 01 §1.1 · https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#store-lookup-data-in-a-separate-record-type) |
| **Descartada** | Texto con los valores en una constante: cambiar un estado obliga a desplegar |
| **Riesgo** | Ninguno relevante |
| **Depende de** | — |
| **Verificar** | — |
| **Verificado** | No hace falta |
```

Con propuesta de refactorización (`refactorizacion/propuesta.md`), cada REF de su «3. Solución» se baja a objetos en
una DT que la cita en «Necesidad»: «[FU-02 REF-01], HU-02». Una REF que el cliente rechaza se cierra igual, con una DT
que la cita: «Decisión: No se hace: <lo que decide el cliente> (FU-nn)», en «Por qué» la BP que queda sin aplicar y en
«Riesgo», el hallazgo que sigue. Con el técnico «en curso», una REF sin DT es aviso; con «completo», error.

### 3. Modelo de datos
Por record type, `### 3.n <Record type>`:
- Tabla `Origen · Acceso · Volumen · Eventos · Seguridad`.
- Tabla de campos `Campo · Tipo · Long. · Clave · Único · Oblig. · Por defecto · Uso`. «Uso» es
  `Funcional: <Dato del funcional §6>` (varios separados por comas) o `Técnico: <para qué>`. Todo dato del
  funcional tiene su campo y todo campo tiene su uso.
- Los estados y las listas de valores son record types de referencia, no texto.
- Cada tabla lleva los campos de auditoría definidos en §1. Un texto de más de 255 caracteres se diseña como Long Text.

Al final: referencias y carga inicial (`Record type · Valores iniciales · Quién lo mantiene`).

Con `as-is/`, §3 termina con `### 3.n Carga inicial y migración`: tabla `Origen en la app actual · Destino ·
Transformación · Volumen · Cómo se verifica`, una fila por lo que se carga o se mueve («—» en el origen si el dato es
nuevo), también el valor que toman los registros que ya hay en un estado que la aplicación actual no guarda (§5). Con
propuesta de refactorización es obligatoria.

### 4. Grupos y seguridad
- Tabla `Perfil · Grupo · Constante`, con todos los perfiles del funcional.
- Matriz de qué ve y qué hace cada grupo (registros, campos, vistas, acciones).
- Cada «solo lo ve…» o «solo puede…» del funcional, con la capa de Appian que lo aplica (seguridad de
  registro, de campo, de vista, de acción o de la interfaz). Si es una decisión, su DT.
- La cuenta del sistema que llama a una Web API expuesta (§10), con su grupo: va aquí y solo aquí.

### 5. Estados y transiciones
Qué hace cada transición del funcional (acción, nodo del proceso, regla). Ninguna interfaz cambia el
estado por su cuenta. Un estado que la aplicación actual no guarda lleva una DT (cómo se guarda o se calcula) y su
carga inicial en §3.

### 6. Lógica
Tabla de reglas de expresión y decisiones `Regla · Entradas · Devuelve · Lógica · Pruebas`, y tabla de
constantes `Constante · Valor · Cambia por entorno`.

### 7. Interfaces y acciones
Tabla `Pantalla · Qué es en Appian · Guarda con · Notas`, una fila por PAN: página de site (y de qué tipo),
vista de registro, acción de registro, formulario de tarea o de inicio. Filtros de usuario, búsqueda,
exportación y acciones de registro con quién las ve. Los filtros por defecto y los contadores trabajan sobre
conjuntos acotados (BP 05 §2–3). La composición: «ver prototipo, pantalla <id>».
Cada acción que lanza un proceso desde una pantalla dice qué es y de qué record type: acción de lista de registros
(crea) o acción relacionada (sobre un registro), puesta con el componente de acciones de registro; nunca un enlace de
inicio de proceso en la interfaz (BP 00 «Process», 01 §9.2, 02 §5.4, 03 §8, 06 §5.3). Las de cada record type, en una
tabla `Acción · Tipo · Proceso · Quién la ve` bajo «Acciones de registro de `<record type>`», con el nombre entre
comillas latinas y el tipo «De lista» o «Relacionada»: de ahí sale lo que `verificar` comprueba de una acción que se
construye o cambia (su nombre y su tipo), también si se renombra.

### 8. Procesos
Por process model, la tabla de nodos `Nodo · Qué hace · Asignado a · Plazo y escalado · Escribe · Evento`,
con el `ACT-nn` del paso en el nodo que lo hace, y después la cancelación y el archivado. Todo paso que ocurre
en la aplicación tiene su nodo o dice qué lo hace. Cómo se parte el proceso en modelos y subprocesos es una DT.

### 9. Avisos
Tabla `Aviso · Cómo se hace · Remitente y respuesta · Plantilla`. Un aviso que no se puede perder es una
tarea más un correo, no solo un correo.

### 10. Integraciones, documentos e IA
Por INT: sistema conectado, autenticación, operación, entradas, salidas, errores, reintentos e
idempotencia; los criterios `INT-nn.m` de su ficha, en §14. Si el otro sistema nos llama, el bloque «Expuesta»:
método, ruta, grupo que la llama, entradas, salidas, errores y versión (BP 07 §6); la cuenta que llama, solo en §4.
Documentos: dónde se guardan, carpetas, tipos y tamaño, y cómo se generan. IA solo si el funcional la pide.

### 11. Site e informes
Páginas en orden y quién ve cada una; informes y cuadros de mando con su origen de datos. Los indicadores
que el cliente no ha validado no se construyen: son un PC en el funcional.

### 12. Volumen y operación
Volúmenes frente a los límites, índices, tareas programadas, configuración que cambia por entorno y lo que
hay que vigilar en producción.

### 13. Plan de construcción
Lista numerada en orden de dependencias: grupos y constantes, datos, seguridad, lógica, interfaces,
procesos, site. Los pasos manuales, marcados.

Con `as-is/`, o cuando se va a construir (una unidad de cambio, `cambios.md`), en lugar de la lista, tabla `Paso ·
Objeto · Tipo · Situación · Sustituye a · Cambio · Para`, una fila por objeto, en el mismo orden, y debajo los pasos
manuales. De ella salen las issues de construcción (`cambios.md` §5). Situación:
- **Nuevo**: no está en el inventario ni es de otra aplicación.
- **Modifica**: está en el inventario y cambia. Un objeto de otra aplicación que cambia lo cambia su equipo: dilo.
- **Existe**: se usa sin cambiarlo; también un objeto de otra aplicación.
- **Sustituye**: un objeto nuevo que reemplaza al del inventario que va en «Sustituye a».

**Cambio** es la unidad de la fila (`cambios.md` §4). **Para** es el requisito al que sirve el objeto: su `HU-nn`, su
`PAN-nn` o su `ACT-nn`; si sirve a varios, todos, separados por comas (van en la misma issue). Lo común (datos, grupos,
constantes, sistemas conectados) dice «Base» y se construye lo primero. En un defecto, el criterio que no se cumple
(`HU-03.2`). Lo que «Existe» no la lleva. Si de un objeto solo cambia una parte, la fila la nombra: `AUT Solicitud —
acción «Nueva solicitud»`.

El site y sus páginas van en la issue de la primera pantalla que publican.

```markdown
| Paso | Objeto | Tipo | Situación | Sustituye a | Cambio | Para |
|---|---|---|---|---|---|---|
| 2 | `AUT_IdEstado` | Regla de expresión | Sustituye | `AUT_ESTADOS_VALIDOS` | EV-02 | Base |
| 2 | `UTL_DiasLaborables` | Regla de otra aplicación | Existe | — | EV-02 | — |
| 5 | `AUT_SubsanarSolicitud` | Interfaz | Nuevo | — | EV-02 | PAN-03 |
| 6 | `AUT Tramitar Solicitud` | Process model | Modifica | — | EV-02 | ACT-02, ACT-06 |
```

Si hay preguntas sin respuesta y se acuerda construir con un supuesto, debajo de la tabla:

#### Supuestos para construir

| Pregunta | Se construye con | Dónde cambia |
|---|---|---|
| PC-nn | Valor o comportamiento acordado mientras llega la respuesta | Nombre exacto del objeto entre comillas invertidas |

Las filas llegan a las issues que citan el PC o construyen el objeto. Las instrucciones generales se escriben bajo
«Reglas para quien construye» y llegan a todas. Al responder el PC se revisa el supuesto con `indice.py impacto`.

### 14. Pruebas y trazabilidad
Tabla `Criterio · Cómo se prueba · Con qué` con todos los criterios `HU-nn.m` e `INT-nn.m` (se pueden agrupar) y los
escenarios `ESC-nn` como pruebas de extremo a extremo. Cada acción protegida, con un perfil que puede y
otro que no. «Con qué» dice cómo se comprueba cada criterio, y la issue lo copia junto a su escenario:
- `Caso de prueba de <regla o interfaz>`, con el objeto entre comillas invertidas: un caso de prueba guardado en él. De
  una regla comprueba la salida esperada; de una interfaz, que no da error.
- `SAIL CLI`: se recorre la pantalla como un usuario. Es del QA de la unidad, no de quien construye.
- `Playwright`: un criterio que solo se ve en pantalla (un color, la maquetación) y no basta con que lo mire una persona.
  También del QA (`appian-qa`).

Cuando un criterio depende de una regla, «Cómo se prueba» fija la entrada y la salida esperadas concretas;
quien construye las copia al caso de prueba, sin decidir el resultado esperado.

```markdown
| Criterio | Cómo se prueba | Con qué |
|---|---|---|
| HU-01.2 | Dos envíos a la vez no repiten número | Caso de prueba de `AUT_GenerarNumero` |
| HU-03.1, HU-03.2 | Subsanar una solicitud devuelta y reenviarla | SAIL CLI |
```

### 15. Pendientes técnicos
Tabla `ID · Duda · Bloquea · Quién la resuelve` con los `PT-nn`. Lo que hay que preguntar al cliente no
va aquí: es un PC del funcional.

Lo que ingeniería inversa no pudo verificar (un NV de `as-is/datos/sin-verificar.json`) y condiciona lo que se
construye es un PT con su cita: «¿Qué devuelve `UTL_DiasLaborables`? [FU-01 NV-ARQ-01]». Si lo resuelve negocio, es
además un PC del funcional.
