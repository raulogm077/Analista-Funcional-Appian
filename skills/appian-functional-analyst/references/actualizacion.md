# Incorporar una fuente nueva

Cuándo: ya hay análisis y llega algo nuevo: la reunión de la semana, un correo, los comentarios del cliente
al DF, un documento. Cada fuente se encaja en lo que hay, el analista decide qué entra y el análisis queda
coherente.

- `funcional.md` y `tecnico.md` son el **estado actual**. «Lo validado» es lo marcado 🔒.
- `decisiones.md` es el **historial**: qué cambió, cuándo y qué había antes.
- El **informe de impacto** es la revisión antes de tocar nada.
- El análisis **no se lee entero**: se consulta con `indice.py`.

Una fuente cada vez, en orden de fecha. Cada fuente es un informe de impacto y una versión (+0.1). En los
ejemplos, la fuente nueva es FU-04 y la versión vigente la 1.1. `<p>` es la carpeta del proyecto.

## 0. Antes de empezar
```bash
python3 <skill>/scripts/proyecto.py copia <p>          # guarda la versión vigente en versiones/v1.1/
python3 <skill>/scripts/indice.py resumen <p>
```

## 1. Catalogar
```bash
python3 <skill>/scripts/leer_fuentes.py <fichero nuevo> -o <p>/fuentes/   # sigue la numeración: FU-04
```
El DF devuelto con comentarios o con cambios marcados se cataloga igual: `leer_fuentes.py` saca cada
comentario y cada cambio con el texto al que se refiere y la historia o el apartado donde está.

## 2. Nota de la fuente
`notas/FU-04.md` con las secciones de `volumen-grande.md` §1. Aplica `ingesta-fuentes.md`: separa la
decisión de la conversación; una reunión interna (sin cliente) solo produce propuestas ⚠️; un correo del
cliente que confirma o cambia algo pesa más que la reunión.
- Transcripción automática: si una palabra mal reconocida cambia dónde encaja el punto, toma la lectura
  más probable, márcala 🔶 y dilo. Si quien decide aparece como «Desconocido», atribúyelo por el contexto;
  si no se puede asegurar que es alguien del cliente con autoridad sobre el tema, lo que dice no sube de
  estado (lo nuevo entra como ⚠️).
- Si la fuente remite a algo que no está catalogado (otro documento, otra sesión), lo que dependa de ello
  queda 🔶 o ❓ y se pide ese material.

## 3. Puntos, encaje y dependencias
Convierte la nota en **puntos**: uno por decisión, cambio, dato nuevo, respuesta o idea. Para cada punto:

1. **Dónde encaja.** Busca con dos o tres términos concretos y cortos (pantalla, dato, estado, botón,
   perfil) y lee solo las candidatas. Lo que no tiene ID (datos, alcance, condiciones de uso, apartados
   del técnico) se ve con `seccion`:
   ```bash
   python3 <skill>/scripts/indice.py buscar <p> "fecha límite" aviso
   python3 <skill>/scripts/indice.py ficha <p> HU-07 PAN-04
   python3 <skill>/scripts/indice.py seccion <p> F6 --con "tipo de documento"
   python3 <skill>/scripts/indice.py seccion <p> T3 --con fechaLimite
   ```
2. **Tipo:**

   | Tipo | Cuándo | Qué se hace | Fila en decisiones.md |
   |---|---|---|---|
   | NUEVO | No hay pieza para ello | Pieza nueva con el siguiente ID (`indice.py siguientes`) | No |
   | COMPLETA | Añade detalle sin contradecir | Se añade a la pieza con su cita | No |
   | CONFIRMA | Ratifica algo ⚠️, 🔶 o ❓ | Pasa a ✅ y suma la cita | No |
   | VALIDA | El cliente lo aprueba por escrito o en la revisión del DF | Pasa a 🔒 | Sí (una por bloque) |
   | CAMBIA | Contradice una decisión anterior | Se reescribe la pieza; lo anterior va a «Antes» | Sí |
   | ANULA | Deja de hacerse algo que tiene ID | Se tacha: `Anulada por D-nn` | Sí |
   | RESPONDE | Contesta un PC entero | Se aplica; el PC se tacha: `Respondida por D-nn` | Sí |
   | ALCANCE+ / ALCANCE− | Entra o sale funcionalidad | Funcional §1 y piezas nuevas o anuladas | Sí |
   | PREGUNTA | Surge una duda o algo queda abierto | PC nuevo (o PT si es técnica) | No |
   | SIN IMPACTO | Contexto, conversación o repite lo que hay | Nada | No |

   Los plazos, hitos y dependencias del proyecto no son SIN IMPACTO: van a `proyecto.md` o, si condicionan
   la construcción, al técnico (§12 o un PT).

   Casos frontera:
   - Si lo que se quita es **parte** de una pieza (una columna, un dato de un aviso), es CAMBIA de esa
     pieza, no ANULA.
   - **Respuesta parcial**: se aplica lo contestado y el PC se reescribe con lo que queda. Antes, busca otros
     del mismo tema (`buscar … --tipo PC`): suele haber duplicados.
   - **Validación condicionada** («lo apruebo cuando lo reenvíes con el filtro»): nada pasa a 🔒 hasta que
     llegue esa confirmación.
   - **Comentario del cliente al DF**: cada comentario es un punto. Un «de acuerdo» sobre una historia o una
     pantalla es VALIDA de esa pieza.
   - Llevar a otra pantalla algo que ya está en otras iguales es COMPLETA; ALCANCE+ es una capacidad que no
     está en ninguna parte.

3. **Dependencias**: lo que hay que revisar si cambian esas piezas, también en el técnico.
   ```bash
   python3 <skill>/scripts/indice.py impacto <p> HU-07 PAN-04
   python3 <skill>/scripts/indice.py impacto <p> PAN-01 --con "responsable"     # pieza muy citada
   ```
   «Dependen de ellas» y «texto sin ID que las menciona» se revisan siempre; «remiten a», solo si el cambio
   afecta a su contenido. La salida dice también las pantallas y los apartados del técnico afectados.

4. **Requiere aprobación** si: CAMBIA o ANULA algo 🔒; es ALCANCE+ o ALCANCE−; una fuente interna cambia
   algo decidido con el cliente; dos personas del cliente dicen cosas distintas; o el cambio obliga a
   rediseñar una pantalla confirmada (`proyecto.md`) o construida. Los retoques (un texto, una columna, el
   orden) no la requieren.

## 4. Informe de impacto: `impacto/FU-04.md`
```markdown
# Impacto de FU-04 · Seguimiento con la unidad gestora · 2026-10-01
Análisis base: versión 1.1 · Estado: pendiente de aprobación

## Resumen
- 9 puntos: 2 NUEVO · 3 COMPLETA · 1 CAMBIA · 1 RESPONDE · 2 SIN IMPACTO
- Requieren aprobación: punto 4 (cambia HU-07, 🔒)
- Pendientes que se cierran: PC-02 · nuevos: 1 · alcance: sin cambios
- Pantallas afectadas: PAN-02 · Técnico: DT-03, §8

## Puntos
| # | Tipo | Qué se dice | Encaja en | Cambio propuesto | Revisar también | Requiere | Decisión |
|---|---|---|---|---|---|---|---|
| 1 | RESPONDE | Si no subsana en 10 días hábiles, se archiva [FU-04 00:12:30] | PC-02, ACT-06 | ACT-06 con el archivo; HU-03.3 nueva; se cierra PC-02 | HU-03, T §8 | — | ✔ |

## Revisión de dependencias
| Pieza | Punto | Resultado |
|---|---|---|
| HU-03 | 1 | Modificada: criterio HU-03.3 |

## Aplicado
Versión 1.2: ACT-06 y HU-03 modificadas · ~~PC-02~~ respondida (D-03) · nuevas: HU-03.3
```
- «Qué se dice» lleva la cita. «Encaja en» son IDs existentes o «nuevo en funcional §4».
- «Decisión»: en lo que no requiere aprobación propones ✔ (o ⚠️, ❓, ✗); en lo que la requiere pones
  «Pendiente» y la fija el analista: ✔ aplicar · ⚠️ aplicar como pendiente · ❓ preguntar al cliente (PC) ·
  ✗ descartar.
- Lo SIN IMPACTO se agrupa en una fila. En «Revisión de dependencias» se pueden agrupar piezas con el mismo
  resultado.

Antes de presentarlo:
```bash
python3 <skill>/scripts/comprobar.py <p> --impacto <p>/impacto/FU-04.md --fuentes <p>/fuentes/
```
Comprueba que los IDs existen, que las citas son reales y que ningún tramo de 10 minutos de la reunión se
ha quedado sin cita (señal de que se ha leído entera).

## 5. Aprobación
Presenta el **Resumen** y **solo los puntos que requieren aprobación**, cada uno con tu recomendación, y
pregunta «¿Aplico el informe con estas decisiones?». Con cualquier confirmación, aplica. Lo que decide el
analista manda: si al aplicar ves un motivo para no seguirlo, pregúntale.

Sin respuesta o en una sesión desatendida: aplica lo que no requiere aprobación; lo demás entra como ⚠️
«pendiente de aprobación del analista» y el informe lo dice en su cabecera. Una decisión explícita del
cliente no se le vuelve a preguntar.

## 6. Aplicar
- Solo se tocan las piezas del informe. `ficha --lineas` da las líneas exactas: lee solo ese tramo y edita
  en sitio. Las líneas marcadas ⟂ están iguales en otro sitio: incluye la de al lado para que sea única.
- Lo que cambia cita la fuente nueva en su comentario y actualiza el estado (✅, 🔒, ⚠️…).
- **CAMBIA**: la pieza queda con lo nuevo; lo anterior y su cita van a «Antes» de la fila D.
- **Texto que queda viejo**: tras un CAMBIA, un ANULA o un RESPONDE, busca el criterio viejo con sus
  propias palabras (`buscar` con las palabras del «Antes», también en el técnico) y corrige cada sitio que
  lo siga diciendo. Es el error más frecuente y ningún script lo detecta.
- **ANULA**: se tacha el ID y las piezas que lo citaban se corrigen o dicen que ya no aplica.
- **Criterios**: si cambia el comportamiento, se reescribe el criterio (mismo ID) o se añade el siguiente.
- **Técnico**: los campos, decisiones, nodos, pruebas y apartados afectados. Si un cambio del cliente choca
  con una buena práctica o con la plataforma, se le explica en un PC con la alternativa.
- **Diagramas**: si cambia el proceso, se pasan solo los cambios a `diagrama.py actualizar` (skill
  `appian-diagramas-bpmn`). Si se niega, alguien editó el `.drawio`: primero `diagrama.py comparar`. Los
  diagramas de estados se editan en su `.mmd` y se vuelven a pintar con `render_mermaid.py`.
- **decisiones.md**: fila de la versión nueva y filas D nuevas al final.
- **Versión**: sube 0.1 en funcional y técnico.
- **Anexo**: `indice.py derivadas <p> --escribir`.
- **proyecto.md**: la fuente en «Fuentes procesadas» y el siguiente paso.
- En el informe: completa «Revisión de dependencias» y «Aplicado», y pon «Estado: aplicado en 1.2».

## 7. Verificar
```bash
python3 <skill>/scripts/comprobar.py <p> --fuentes <p>/fuentes/ --anterior <p>/versiones/v1.1 --impacto <p>/impacto/FU-04.md
```
Tiene que salir sin errores: ningún ID desaparecido, la versión sube y tiene su fila, cada dependencia con
resultado, cada cambio declarado en el informe, nada marcado «sin cambios» que haya cambiado y nada 🔒
cambiado sin un punto aprobado. Después:
- el Word, si ya se había entregado un DF (`df_docx.js`);
- el prototipo: solo las pantallas afectadas, con `appian-prototipos-aena`. Las confirmadas en
  `proyecto.md` no se tocan sin el visto bueno del analista.

## 8. Entregar
En pocas líneas: versión, puntos por tipo, lo que cambió de verdad (CAMBIA, ANULA, alcance), pendientes
cerrados y nuevos, lo que quedó pendiente de aprobación y las pantallas a actualizar.

## Varias fuentes juntas
En orden de fecha y en un solo informe si tratan lo mismo (la reunión y el correo que la confirma); si no,
un informe por fuente. Para arrancar un análisis con muchas reuniones ya acumuladas, `volumen-grande.md`.
