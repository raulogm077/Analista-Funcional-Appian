# Incorporar información nueva a un análisis existente

Cuándo: ya hay un `ddf.md` y llega algo nuevo: la reunión de la semana, un correo, los comentarios del
cliente al DDF, un documento. En discovery la información es acumulativa y cambia de rumbo: cada fuente se
encaja en lo que hay, se decide qué entra y el análisis queda coherente.

- El `ddf.md` es el **estado actual** (una sola verdad; «lo validado» es un filtro por estado, 🔒).
- El **Registro de decisiones** (Sec 17) es el **historial**: qué cambió, cuándo, qué había antes.
- El **informe de impacto** es la **revisión** antes de tocar nada: el analista decide qué entra.
- El `ddf.md` **no se lee entero**: se consulta con `ddf_indice.py` (índice, búsqueda, fichas, dependencias).

Una fuente cada vez, en orden de fecha. Cada fuente = un informe de impacto = una versión (+0.1). En los
ejemplos, la fuente nueva es FU-26 y el análisis vigente la v1.3.

## 0. Antes de empezar
```bash
cp ddf.md ddf-v1.3.md          # copia con el número de la versión vigente (la de «Versión:»), para comprobar al final
python3 <skill>/scripts/ddf_indice.py resumen ddf.md
```

## 1. Catalogar
```bash
python3 <skill>/scripts/leer_fuentes.py <fichero nuevo> -o fuentes/     # continúa la numeración: FU-26
```

## 2. Nota de la fuente
`notas/FU-26.md` con las secciones de `volumen-grande.md` §1 (resumen, hablantes → rol, decisiones con
cita y rol que decide, pantallas, datos, reglas, cambios de criterio, pendientes, fuera de alcance). Aplica
`ingesta-fuentes.md`: separar decisión de conversación; una reunión interna (sin cliente) solo produce
propuestas ⚠️; un correo del cliente que confirma o cambia algo pesa más que la reunión.
- Transcripción automática: si una palabra mal reconocida («estalizador») cambia dónde encaja el punto,
  toma la lectura más probable, márcala 🔶 y dilo. Si quien decide aparece como «Desconocido», atribúyelo
  por el contexto (quién pregunta, quién responde, de qué rol se habla); si no se puede asegurar que es
  alguien del cliente con autoridad sobre el tema, lo que dice no sube de estado (lo nuevo entra como ⚠️;
  lo que ya estaba se queda como estaba).
- Si la fuente remite a algo que no está catalogado (el DF v2 «página 192», un correo, otra sesión), lo
  que dependa de ello queda 🔶 o ❓ y se pide ese material (en el informe y, si bloquea, como P-xxx).

## 3. Puntos, encaje y dependencias
Convierte la nota en **puntos**: uno por decisión, cambio, dato nuevo, respuesta o idea. Para cada punto:

1. **Dónde encaja**: busca con 2–3 términos concretos del punto (pantalla, campo, estado, botón, rol;
   cortos, de una o dos palabras; si uno es muy común, como «título», busca los demás por separado) y lee
   solo las candidatas. Lo que no tiene ID (modelo de datos, alcance, descripción de procesos) se ve con
   `seccion`:
   ```bash
   python3 <skill>/scripts/ddf_indice.py buscar ddf.md "fecha límite" alerta
   python3 <skill>/scripts/ddf_indice.py ficha ddf.md PAN-47 RB-162
   python3 <skill>/scripts/ddf_indice.py seccion ddf.md 10 --modulo M2 --con "tipo de documento"
   ```
2. **Tipo**:

   | Tipo | Cuándo | Qué se hace | Fila D |
   |---|---|---|---|
   | NUEVO | No hay pieza para ello | Pieza nueva con el siguiente ID (`siguientes --modulo Mx`) | No |
   | COMPLETA | Añade detalle sin contradecir (un campo, un texto literal, un valor por defecto, un caso) | Se añade a la pieza con su cita | No |
   | CONFIRMA | Ratifica algo ⚠️, 🔶 o ❓ | Pasa a ✅ y suma la cita | No |
   | VALIDA | El cliente lo valida por escrito o en la revisión del DDF | Pasa a 🔒 | Sí (una por bloque) |
   | CAMBIA | Contradice una decisión anterior | Se reescribe la pieza; lo anterior va a «Antes» | Sí |
   | ANULA | Deja de hacerse algo que tiene ID propio | `~~ID~~ … Anulado por D-xxx` | Sí |
   | RESPONDE | Contesta una P-xxx entera | Se aplica la respuesta; `~~P-xxx~~ … Respondida por D-xxx` | Sí |
   | ALCANCE+ / ALCANCE− | Entra o sale funcionalidad | Sec 3 y piezas nuevas o anuladas | Sí |
   | PREGUNTA | Surge una duda o algo queda abierto | P-xxx nueva | No |
   | SIN IMPACTO | Contexto, conversación, repite lo que ya está | Nada (se agrupan con su cita) | No |

   Los plazos, hitos y dependencias del proyecto («desarrollo y pruebas hasta el 17/12», «los permisos se
   harán al final») no son SIN IMPACTO: son COMPLETA de la Sec 4 (restricciones) o de la Sec 17
   (dependencias).

   Casos frontera:
   - Lo que se quita es **parte** de una pieza (una variable de un mensaje, una columna): es CAMBIA de esa
     pieza, no ANULA.
   - **Respuesta parcial** a una pregunta: se aplica lo contestado (COMPLETA o CAMBIA), la pregunta se
     reescribe con lo que queda, cita la fuente y sigue abierta. Antes de cerrar o abrir preguntas, busca
     otras del mismo tema (`buscar … --tipo P`): suele haber duplicadas.
   - **Validación condicionada** («lo apruebo cuando me lo reenvíes con el filtro»): no se pasa nada a 🔒
     hasta que llegue esa confirmación (será otra fuente); el punto queda ✗ con el motivo.
   - Una decisión anterior que queda sin efecto **en parte**: su «Vigente» pasa a «En parte: D-xxx cambia …».
   - **Confirmación parcial** (se ve construida una parte de una pantalla): CONFIRMA de esa parte; el resto
     se queda con su estado.
   - **COMPLETA o ALCANCE+**: llevar a otra pantalla algo que el análisis ya tiene en otras iguales (el mismo
     botón en otro listado) es COMPLETA; ALCANCE+ es una capacidad que no está en ninguna parte.

3. **Dependencias**: lo que hay que revisar si cambian esas piezas.
   ```bash
   python3 <skill>/scripts/ddf_indice.py impacto ddf.md RB-162 PAN-47
   python3 <skill>/scripts/ddf_indice.py impacto ddf.md PAN-01 --con "responsable del paso"   # pantalla muy citada
   ```
   «Dependen de ellas» (las citan) y «texto sin ID que las menciona» se revisan siempre; «remiten a», solo
   si el cambio afecta a su contenido. Cuando el cambio es una parte concreta (una columna, un filtro, un
   aviso) de una pieza muy citada, filtra con `--con` y los términos de esa parte: las piezas que solo
   enlazan la pantalla no hace falta revisarlas una a una; `--con` conserva siempre los RF que se verifican
   con los criterios de la pieza (si añades o cambias criterios, su «Se verifica en» cambia) y además
   saca las preguntas abiertas del mismo tema, por si el punto las contesta. El texto sin ID se cita por
   su sección («Sec 10 M1 · 10.3 Informe»), no por número de línea, que cambia al editar. Avisa si alguna
   es 🔒.

4. **Requiere aprobación** si: CAMBIA o ANULA algo 🔒; ALCANCE+ o ALCANCE−; una fuente interna cambia algo
   decidido con el cliente; dos personas del cliente dicen cosas distintas; o el cambio obliga a
   **rediseñar** una pantalla ya prototipada (su ficha tiene «Capturas») o construida, o a cambiar su
   comportamiento. Los retoques (un texto, una columna, el orden, un formato) no requieren aprobación,
   aunque estén construidos: son decisiones normales del cliente. Si no sabes si algo está construido y el
   cambio es de fondo, márcalo para aprobación y pregúntalo.

## 4. Informe de impacto: `impacto/FU-26.md`
```markdown
# Impacto de FU-26 · Seguimiento del desarrollo · 2026-09-24
Análisis base: ddf.md v1.3 · Estado: pendiente de aprobación

## Resumen
- 12 puntos: 2 NUEVO · 4 COMPLETA · 2 CONFIRMA · 2 CAMBIA · 1 RESPONDE · 1 SIN IMPACTO
- Requieren aprobación: puntos 4 y 9 (cambian piezas 🔒)
- Preguntas que se cierran: P-020 · nuevas: 1 · alcance: sin cambios
- Pantallas afectadas: PAN-07, PAN-47

## Puntos
| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | RESPONDE | El umbral de la alerta media es el 10 % del presupuesto del expediente [FU-26 00:12:30] | P-020, RB-162 | RB-162 pasa a 10 %; CA-PAN-47.2 con 10 %; se cierra P-020 | PAN-47, RF-160 | — | ✔ |

## Revisión de dependencias
| Pieza | Punto | Resultado |
|---|---|---|
| PAN-47 | 1 | Modificada: texto de la alerta media |
| RF-160 | 1 | Revisada, sin cambios |

## Aplicado
v1.4: RB-162 y CA-PAN-47.2 modificadas · ~~P-020~~ respondida (D-087) · nuevas: RF-432, CA-PAN-07.12
```
- «Qué se dice» lleva la cita. «Encaja en» son los IDs existentes (o «nuevo en Sec 12 M2»).
- «Decisión»: en los puntos que no requieren aprobación propones ✔ (o ⚠️, ❓, ✗); en los que la requieren
  pones «Pendiente» y la fija el analista: ✔ aplicar · ⚠️ aplicar como pendiente · ❓ preguntar al cliente
  (P-xxx) · ✗ descartar.
- «Revisión de dependencias» se escribe en el paso 4 con resultado «pendiente» y se completa al aplicar.
- Los SIN IMPACTO se agrupan en una sola fila (en el resumen se cuenta cada uno). En «Revisión de
  dependencias» se pueden agrupar varias piezas en una fila si tienen el mismo resultado («Revisadas, sin
  cambios: solo enlazan la pantalla»).

Antes de presentarlo, comprueba que los IDs existen, que las citas del informe y de la nota son reales, que
cada pieza de «Revisar también» tiene su fila de revisión y que ningún tramo de 10 minutos de la reunión se
ha quedado sin cita (señal de que se ha leído entera):
```bash
python3 <skill>/scripts/comprobar_ddf.py ddf.md --impacto impacto/FU-26.md --fuentes fuentes/
```

## 5. Aprobación
Presenta al usuario el **Resumen** y **solo los puntos que requieren aprobación**, cada uno con tu
recomendación, y pregunta «¿Aplico el informe con estas decisiones?». Con cualquier confirmación, aplica.
Lo que decide el analista manda: si al aplicar ves un motivo para no seguirlo (una regla, una duda nueva),
no lo cambies por tu cuenta: pregúntale.
Sin respuesta o en una sesión desatendida: aplica lo que no requiere aprobación; lo que la requiere entra
como ⚠️ con una pregunta 🔴 («FU-26 propone X frente a lo validado en FU-20; ¿se confirma?»), y el informe
lo dice en su cabecera.

## 6. Aplicar
- Solo se tocan las piezas del informe. `ficha --lineas` da las líneas exactas: lee solo ese tramo
  (Read con offset y limit) y edita en sitio. Las líneas marcadas ⟂ existen igual en otro sitio (una
  «Fuente» repetida): incluye la línea de al lado para que el texto a sustituir sea único. Una actividad
  tiene ficha y fila en la tabla de actividades de la Sec 6 (`ficha` enseña las dos): cambia ambas.
- Todo lo que cambia cita la fuente nueva; el estado de la pieza se actualiza (✅, 🔒, ⚠️…).
- **CAMBIA**: la pieza queda con lo nuevo; lo anterior y su cita van a «Antes» de la fila D. Si una D
  anterior queda sin efecto, su «Vigente» pasa a «No: sustituida por D-xxx».
- **Texto obsoleto**: tras un CAMBIA, un ANULA o un RESPONDE, busca el criterio viejo con sus propios
  términos (`buscar` con las palabras del «Antes», también `--tipo P`) y corrige cada sitio que lo siga
  diciendo: otra ficha que lo repite, una regla de pantalla, una pregunta abierta que ya está contestada.
  Es el error más frecuente de una actualización y ningún script lo detecta.
- **ANULA**: se tacha el ID de la pieza (y de sus criterios si quedan sin sentido); las piezas que la
  citaban se corrigen o dicen explícitamente que ya no aplica.
- **Criterios**: si cambia el comportamiento, se reescribe el criterio (mismo ID) o se añade el siguiente
  `.n`; nunca se deja un criterio que contradiga la pieza.
- **Diagramas**: si cambia un flujo o un estado, se edita su bloque Mermaid; `ddf_indice.py diagramas
  ddf.md -o diagramas` dice cuáles han cambiado (sin escribir nada) y con `--escribir` los guarda; se
  renderizan solo esos con `render_mermaid.py`.
- **Sec 1**: FU-26 en la tabla de fuentes; «Versión:» sube 0.1; fila del control de versiones
  `| v1.4 | fecha | Incorpora FU-26 (impacto/FU-26.md) | FU-26 | IDs afectados |`.
- **Registro de decisiones**: filas D nuevas al final, con el siguiente ID.
- Secciones derivadas (casos de uso y matriz de cobertura): `ddf_indice.py derivadas ddf.md --escribir`.
- En el informe: completa «Revisión de dependencias» (cada pieza de «Revisar también» con su resultado:
  «Modificada: …», «Revisada, sin cambios» o «Sin cambios por este punto (cambia por el punto N)»),
  «Aplicado» y pon «Estado: aplicado en v1.4». Si al aplicar sale algo que el informe no preveía (otra
  pieza que hay que tocar, un dato que va en otro sitio), se añade a «Revisión de dependencias» con su
  resultado y se explica en «Aplicado».
- Un criterio anulado: `` - ~~`CA-PAN-66.6`~~ Anulado por D-086 [FU-22 00:04:44]: ~~**Dado** … **entonces** …~~ ``.

## 7. Verificar
```bash
python3 <skill>/scripts/comprobar_ddf.py ddf.md --fuentes fuentes/ --anterior ddf-v1.3.md --impacto impacto/FU-26.md
```
Tiene que salir sin problemas: ningún ID desaparecido, versión nueva con su fila, ninguna pieza vigente que
remita a una anulada, cada dependencia con resultado, cada cambio declarado en el informe (en «Cambio
propuesto» de un punto, en una fila de revisión con cambios o en «Aplicado»), nada marcado «sin cambios»
que haya cambiado y ninguna pieza 🔒 cambiada sin un punto aprobado. Después, el Word si existía
(`ddf_docx.js`) y, si hay prototipo, regenera **solo** las «Pantallas afectadas» con
`appian-prototipos-aena`.

## 8. Entregar
En pocas líneas: versión, puntos por tipo, lo que cambió de verdad (CAMBIA, ANULA, alcance), preguntas
cerradas y nuevas, lo que quedó como ⚠️ pendiente de aprobación y las pantallas a actualizar.

## Varias fuentes juntas
Si llegan varias a la vez (la reunión y el correo que la confirma), en orden de fecha y en un solo informe
si tratan lo mismo; si no, un informe por fuente. Para arrancar un análisis con muchas reuniones ya
acumuladas, `volumen-grande.md`; después, cada reunión nueva por este procedimiento.
