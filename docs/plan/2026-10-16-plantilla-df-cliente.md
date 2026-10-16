# Plan: el DF del cliente sobre una plantilla universal

Fecha: 16 de octubre de 2026. Parte de `main` (`2f9151d`, 0.8.0-beta.1). Rama `yaroslav/plantilla-DF-cliente`. Registro
de cada cambio, para adjuntar al PR: `docs/plan/2026-10-16-plantilla-df-cliente-registro.md`.

**Objetivo.** Que `appian-functional-analyst` entregue, además del análisis funcional, el **DF del cliente**: el
documento que el cliente revisa y valida, con la estructura de la plantilla de Word que ya usa el equipo (sale del
PowerPoint de revisión de requisitos), sin la marca de ningún cliente. Cada sección lleva su descripción y su tono, y
las pantallas se describen con una guía de requerimientos universal que pasa a formar parte del plugin.

**Cómo se trabaja.** Como piden `CLAUDE.md` y `.github/CONTRIBUTING.md`: solo en esta rama, sin tocar la versión, la
rama se sube como copia de seguridad cuando convenga y el PR se abre al terminar, con auto-merge, y entra con la
aprobación de Raúl. Antes de cada commit, `comprobar_plugin.py`; si cambia un script o una plantilla, el selftest de la
skill. Las pruebas se hacen con el plugin cargado desde esta carpeta (`claude --plugin-dir`) en un proyecto fuera del
repositorio.

**Material de partida (fuera del repositorio).**
- La plantilla de Word del equipo, con la marca de un cliente: portada, control de cambios, 1. Introducción (descripción,
  integraciones, alcance), 2. Diseño de la solución (flujo y reglas comunes, ficha de 10 campos por actividad, pantallas,
  roles y matriz de permisos, notificaciones, métricas y KPIs).
- El PowerPoint con ejemplos reales del tono de varias secciones (reglas comunes, actividades, roles, matriz,
  notificaciones). Tiene datos del cliente: **no entra en el repositorio**; de él solo salen ejemplos reescritos con un
  caso ficticio.
- La skill suelta `requerimientos-pantallas` (Lógica General, Filtros, Ordenación, Reglas de Validación), hoy fuera del
  plugin y con un ejemplo de un proyecto concreto.
- Un primer intento ya hecho sobre la 0.7.0-beta.4 en el plugin «appian-analyst-plantilla-actualizada» (instalado en la
  cuenta, no en el repositorio): `assets/plantillas/df-cliente.docx` (la misma plantilla sin logos),
  `assets/plantillas/df-cliente.md`, `references/df-cliente-plantilla.md`, `references/requerimientos-pantallas.md` y
  `scripts/df_cliente_docx.py` (906 líneas, python-docx). Se parte de él en vez de empezar de cero.

## 1. Decisiones

Confirmadas por Yaroslav el 16 de octubre de 2026, salvo las marcadas «propuesta».

- **D0. Se parte de la variante, pero como borrador.** Se aprovecha lo que sirva de la 0.7.0-beta.4, revisado con lo
  de este plan; la base es siempre la última versión del plugin (`main`), no la variante.
- **D1. El DF del cliente es un documento propio, escrito desde las fuentes.** No se deriva del análisis funcional
  (`analisis/funcional.md`) ni hay una tabla que ate sus secciones a las del funcional. Se escribe analizando una a una
  las fuentes del proyecto (transcripciones, correos, documentos, capturas, diagramas y lo que se pase como contexto).
  Si el proyecto ya tiene funcional, es una fuente más, no el origen. Vive en `analisis/df-cliente.md`.
- **D2. Trabajo iterativo: la última fuente manda.** Cada fuente nueva se lee contra el DF tal como está y, si
  contradice lo que se acordó antes (también lo aceptado en la reunión anterior), se reescribe con la decisión nueva.
  Nada se cambia en silencio: cada cambio dice qué fuente lo trae y qué decisión anterior sustituye, y la entrega
  siguiente lo recoge en el control de cambios. Se apoya en lo que el plugin ya hace con las fuentes (`leer_fuentes.py`,
  notas, informe de impacto, `decisiones.md`).
- **D3. La plantilla neutra es la del equipo sin marca**: sin logos, con colores neutros y textos de ejemplo
  genéricos, y con el apartado **2.6 Periodo de estabilización**, que la plantilla de Word aún no tiene. La de un
  cliente vive en su proyecto (`<p>/plantillas/df-cliente.docx`), nunca en el plugin.
- **D4. La guía de pantallas va dentro de la skill del analista** (`references/requerimientos-pantallas.md`), que es la
  que escribe el DF. La usan el apartado 2.3 y el modo «Pantalla suelta». La skill suelta se retira cuando esto esté en
  `main`.
- **D5. El Word se genera con Python** (`df_cliente_docx.py`, python-docx), porque rellena la plantilla en vez de
  dibujarla desde cero. python-docx entra en `requisitos.json`. (Propuesta.)
- **D6. Antes del PR, pruebas con casos reales** que pasa Yaroslav (transcripciones de un proyecto), fuera del
  repositorio: se prueba, se revisa el resultado, se corrige el plugin y se repite hasta que el DF salga bien. Al
  repositorio solo llegan los cambios del plugin y las lecciones, sin datos del cliente.

## 2. Tareas

### Fase 0 · Preparación

- [ ] **T0. Equipo y punto de partida.** Python (aquí solo existe `py`: ver «Aprendizajes»), python-docx, Node y
  LibreOffice; `comprobar_plugin.py` y el selftest del analista en verde antes de tocar nada. Comparar la variante con
  la 0.8.0-beta.1 fichero a fichero y decidir qué se trae y qué se rehace.

### Fase 1 · Plantilla universal

- [ ] **T1. `assets/plantillas/df-cliente.docx` neutro**, a partir de la plantilla del equipo: sin las tres imágenes de
  marca, colores y tipos de letra neutros, encabezado y pie genéricos, textos de ejemplo entre corchetes que el script
  reconoce. Comprobar que no queda nada de ningún cliente (`pruebas/clientes.txt`, también dentro del `.docx`).
- [ ] **T2. Plantilla de un cliente.** Cómo se crea en un proyecto (copia de la neutra cambiando solo logos, colores,
  letra y pie) y que el script la usa si existe; si no, la neutra con el color de `prototipo/brand-<id>.json`.
- [ ] **T3. Añadir «2.6 Periodo de estabilización»** a la plantilla neutra, con sus textos de ejemplo. Su contenido se
  acuerda con Yaroslav (ver «Abierto»).

### Fase 2 · El DF del cliente como entregable

- [ ] **T4. `references/df-cliente-plantilla.md`**: para cada sección, qué es, para qué la lee el cliente, qué se
  escribe, de qué tipo de fuente suele salir y el formato exacto que lee el script, con un caso ficticio.
- [ ] **T5. `assets/plantillas/df-cliente.md`**: el esqueleto que copia `proyecto.py iniciar`.
- [ ] **T6. Del material al DF.** Cómo se construye el DF desde cero con todas las fuentes: leerlas todas antes de
  escribir, en orden de fecha; qué sale de cada tipo (una transcripción, un correo, un documento del cliente, una
  captura, un diagrama, un funcional que ya exista) y qué se pregunta en vez de inventarse.
- [ ] **T7. Iteración: una fuente nueva sobre un DF que ya existe.** La fuente se lee contra el DF; lo que cambia se
  reescribe con la decisión nueva, aunque se hubiera aceptado antes; el informe de impacto dice qué cambia, de qué
  fuente sale y qué sustituye; la entrega siguiente sube la versión y añade su fila al control de cambios. Reutiliza
  `actualizacion.md` donde encaje, sin atar el DF al funcional.
- [ ] **T8. `SKILL.md` del analista**: el DF del cliente en «Qué escribe», en los modos, en los pasos y en la tabla de
  referencias; los flujos que lo nombran; `proyecto.py` (iniciar, estado, entregar) y `comprobar.py` si tienen que
  conocerlo.

### Fase 3 · Tono y descripción de cada sección

- [ ] **T9. Guía de tono por sección**, a partir de los ejemplos del PowerPoint reescritos con un caso ficticio: regla
  común (título en mayúsculas, cuándo aplica, qué pasa, excepciones), ficha de actividad (entrada y salida con sus IDs,
  estados por acción «Acción "X" → Estado / Subestado», «N/A» cuando no aplica), roles («Dónde se define»), matriz
  (agrupada por pantalla o sección, con notas con asterisco) y notificaciones (asunto con variables, cuerpo literal).
- [ ] **T10. Revisar la guía con Yaroslav** con una sección de cada tipo escrita con ella.

### Fase 4 · Descripción de pantallas universal

- [ ] **T11. Revisar las instrucciones generales** de la skill suelta y de la variante: qué sirve, qué sobra y qué está
  pensado para un proyecto concreto.
- [ ] **T12. `references/requerimientos-pantallas.md`**, dentro de la skill del analista. Tiene que decir de forma
  explícita:
  - que **cada funcionalidad de la pantalla se describe, sin saltarse ninguna**: cada campo, columna, botón de cabecera
    y de fila, enlace, icono, pestaña, filtro, orden, tooltip, mensaje, estado vacío y modal que se abre; lo que se ve en
    la captura o el prototipo y nadie explicó también se describe o se pregunta;
  - **el formato**: los apartados de la plantilla en su orden («Ejemplo ilustrativo», «Lógica General», «Búsqueda y
    Filtros», «Ordenación», «Reglas de Validación»), lista numerada con sub-viñetas, una idea por punto;
  - **cómo se describe** cada tipo de elemento (qué es, tipo de control, de dónde sale el valor, valores y por defecto,
    qué pasa al pulsarlo o cambiarlo, qué se ve si está vacío), con un ejemplo ficticio completo en vez del de un
    proyecto real;
  - una **lista de repaso** final para comprobar que no falta nada.
- [ ] **T13. Lo que se añade o cambia respecto a la skill suelta**, con lo que pida Yaroslav. De partida: estado inicial
  y pantalla vacía, paginación, modo lectura y edición con Guardar y Cancelar, tipos de control cerrados, búsqueda
  libre, mensajes de error de validación, navegación entre pantallas y modales; la visibilidad por rol pasa de
  «Reglas de Validación» a la matriz (2.4.1), como dice la plantilla; borrado con confirmación y texto literal; la
  explicación manda sobre la captura.
- [ ] **T14. Modo «Pantalla suelta»** con esta guía: la ficha en el formato del 2.3, en el chat y, si hay proyecto, en
  el DF del cliente.

### Fase 5 · El Word

- [ ] **T15. `scripts/df_cliente_docx.py`** traído de la variante y puesto al día con `main`: lee `df-cliente.md`,
  rellena la plantilla (con el 2.6), no enseña comentarios ni lo tachado, resalta «pendiente de confirmar», avisa de
  textos de ejemplo sin rellenar y de pantallas sin Lógica General; no sobrescribe un Word entregado; PDF con
  LibreOffice.
- [ ] **T16. Selftest** en `pruebas/appian-functional-analyst/` con un proyecto ficticio: genera el Word y comprueba
  secciones, fichas, matriz, notificaciones y avisos.

### Fase 6 · Probar con casos reales e iterar

Fuera del repositorio, con el plugin cargado desde esta carpeta (`claude --plugin-dir`). Cada vuelta, una fila en el
registro y las lecciones en «Aprendizajes».

- [ ] **T17. Primera pasada**: con las transcripciones y artefactos que pase Yaroslav de un proyecto, el DF del cliente
  desde cero y en Word. Revisar el PDF juntos: qué falta, qué sobra, qué está mal contado, qué pantalla no está entera.
- [ ] **T18. Iteración**: pasar las fuentes una a una, como llegarían en el proyecto, y comprobar que cada una reescribe
  lo que cambia (también lo aceptado antes) y que el control de cambios lo recoge.
- [ ] **T19. Corregir y repetir**: cada fallo se corrige en el plugin y se vuelve a probar hasta que Yaroslav dé el DF
  por bueno. Lo que no entre en este trabajo, a `siguiente-version.md`; lo aplicado, a `evaluaciones.md`, sin datos del
  cliente.

### Fase 7 · Cerrar

- [ ] **T20.** `comprobar_plugin.py`, selftests, registro completo, la rama subida y el PR con auto-merge; su
  descripción sale del registro.

## Abierto

- Qué contiene el **2.6 Periodo de estabilización** (por ejemplo: duración, quién da soporte y cómo se piden las
  correcciones, qué cuenta como incidencia y cuándo se da por cerrado).
- La lista de Yaroslav de lo que falta o cambia en la guía de pantallas (T13).

## 3. Aprendizajes

Lo que se aprende mientras se trabaja. Lo que pide un cambio en el plugin que no entra en este trabajo pasa a
`docs/siguiente-version.md`; lo aplicado, a `docs/evaluaciones.md`. Sin datos del cliente.

- (16/10) En este Windows no existen `python` ni `python3`, solo el lanzador `py`. El SKILL.md dice «en Windows,
  `python` en vez de `python3`» y `CLAUDE.md` usa `python3`: aquí fallan los dos. → `siguiente-version.md`.
- (16/10) Ya había un primer intento de este trabajo en un plugin aparte (0.7.0-beta.4) que no llegó al repositorio.
  Lo que se hace fuera del repositorio se pierde o se duplica: es lo que el `CLAUDE.md` quiere evitar.
