# Especificación técnica (`analisis/tecnico.md`)

Es lo que se construye. Con ella, las historias del funcional y el prototipo, quien construye con el
MCP de desarrollo de Appian no tiene que preguntar ni suponer nada. Es interna: no va al cliente.
Ejemplo completo: `ejemplos/autorizaciones/analisis/tecnico.md`.

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
- **Evolutivo:** cada objeto lleva Nuevo, Modifica o Existe, con el nombre real que da `as-is/`.

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
| 13. Plan de construcción | 08 §3 |
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
Tabla `Dato · Valor · Fuente`: versión de Appian en cada entorno, tier y complementos, base de datos,
inicio de sesión, idioma y zona horaria, calendario laboral, volumen, usuarios y concurrencia, tiempo de
recuperación, accesibilidad, móvil y usuarios externos, licencias. Sale de funcional §10 y de lo que diga
el equipo. Lo que no se sabe es un PT. El prototipo toma de aquí la versión de Appian.

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

### 3. Modelo de datos
Por record type, `### 3.n <Record type>`:
- Tabla `Origen · Acceso · Volumen · Eventos · Seguridad`.
- Tabla de campos `Campo · Tipo · Long. · Clave · Único · Oblig. · Por defecto · Uso`. «Uso» es
  `Funcional: <Dato del funcional §6>` (varios separados por comas) o `Técnico: <para qué>`. Todo dato del
  funcional tiene su campo y todo campo tiene su uso.
- Los estados y las listas de valores son record types de referencia, no texto.

Al final: referencias y carga inicial (`Record type · Valores iniciales · Quién lo mantiene`).

### 4. Grupos y seguridad
- Tabla `Perfil · Grupo · Constante`, con todos los perfiles del funcional.
- Matriz de qué ve y qué hace cada grupo (registros, campos, vistas, acciones).
- Cada «solo lo ve…» o «solo puede…» del funcional, con la capa de Appian que lo aplica (seguridad de
  registro, de campo, de vista, de acción o de la interfaz). Si es una decisión, su DT.

### 5. Estados y transiciones
Qué hace cada transición del funcional (acción, nodo del proceso, regla). Ninguna interfaz cambia el
estado por su cuenta.

### 6. Lógica
Tabla de reglas de expresión y decisiones `Regla · Entradas · Devuelve · Lógica · Pruebas`, y tabla de
constantes `Constante · Valor · Cambia por entorno`.

### 7. Interfaces y acciones
Tabla `Pantalla · Qué es en Appian · Guarda con · Notas`, una fila por PAN: página de site (y de qué tipo),
vista de registro, acción de registro, formulario de tarea o de inicio. Filtros de usuario, búsqueda,
exportación y acciones de registro con quién las ve. Los filtros por defecto y los contadores trabajan sobre
conjuntos acotados (BP 05 §2–3). La composición: «ver prototipo, pantalla <id>».

### 8. Procesos
Por process model, la tabla de nodos `Nodo · Qué hace · Asignado a · Plazo y escalado · Escribe · Evento`,
con el `ACT-nn` del paso en el nodo que lo hace, y después la cancelación y el archivado. Todo paso que ocurre
en la aplicación tiene su nodo o dice qué lo hace. Cómo se parte el proceso en modelos y subprocesos es una DT.

### 9. Avisos
Tabla `Aviso · Cómo se hace · Remitente y respuesta · Plantilla`. Un aviso que no se puede perder es una
tarea más un correo, no solo un correo.

### 10. Integraciones, documentos e IA
Por INT: sistema conectado, autenticación, operación, entradas, salidas, errores, reintentos e
idempotencia. Documentos: dónde se guardan, carpetas, tipos y tamaño, y cómo se generan. IA solo si el
funcional la pide.

### 11. Site e informes
Páginas en orden y quién ve cada una; informes y cuadros de mando con su origen de datos. Los indicadores
que el cliente no ha validado no se construyen: son un PC en el funcional.

### 12. Volumen y operación
Volúmenes frente a los límites, índices, tareas programadas, configuración que cambia por entorno y lo que
hay que vigilar en producción.

### 13. Plan de construcción
Lista numerada en orden de dependencias: grupos y constantes, datos, seguridad, lógica, interfaces,
procesos, site. Los pasos manuales, marcados.

### 14. Pruebas y trazabilidad
Tabla `Criterio · Cómo se prueba` con todos los criterios `HU-nn.m` (se pueden agrupar por historia) y los
escenarios `ESC-nn` como pruebas de extremo a extremo. Cada acción protegida, con un perfil que puede y
otro que no.

### 15. Pendientes técnicos
Tabla `ID · Duda · Bloquea · Quién la resuelve` con los `PT-nn`. Lo que hay que preguntar al cliente no
va aquí: es un PC del funcional.
