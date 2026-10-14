# appian-analisis-funcional

Plugin de Claude para equipos que analizan, documentan, rehacen, construyen y prueban aplicaciones Appian: del material
del cliente al diseño funcional que valida (DF en Word) y a lo que se construye, se prueba y pasa a producción. Sirve
para cualquier proceso y cualquier cliente: el dominio sale siempre de las fuentes del proyecto. Las plantillas y las
galerías del plugin enseñan técnica, no un dominio (`skills/appian-prototipos/galerias/README.md`), y el plugin no lleva
ningún proyecto, tampoco de ejemplo.

<img src=".github/assets/como-trabaja.svg" alt="Las fuentes del cliente entran al analista funcional con su informe de impacto; una aplicación existente pasa antes por ingeniería inversa y, si se rehace, por refactorización. El analista escribe el funcional, el técnico y las unidades de cambio; de ahí salen el prototipo, el DF en Word y los diagramas BPMN. Al aprobar una unidad se escriben sus issues, que se construyen y verifican en desarrollo; el QA recorre la unidad con SAIL CLI y un fallo devuelve su issue. Desde el paquete no actúa la IA: una persona lo revisa y hace el pase." width="100%">

## Cómo trabaja

Cada fuente nueva (una reunión, un correo, un acta, una demo o los comentarios del cliente al DF) entra con un informe
de impacto que aprueba el analista: solo cambia lo afectado, en el funcional, el técnico, los diagramas y las pantallas.

Cada proyecto es un repositorio git que crea `proyecto.py iniciar`, siempre con la misma forma: `fuentes/`, `notas/` e
`impacto/` (lo que entra y cómo encaja), `analisis/` (funcional, técnico, decisiones y unidades de cambio),
`prototipo/`, `entregables/` y `versiones/`, y, cuando hacen falta, `construccion/<U>/`, `qa/<U>/`, `as-is/` y
`refactorizacion/`. El código vive en Appian y el repositorio guarda todo lo demás, sobre `main` y sin ramas. Lleva un
`AGENTS.md` generado (dónde está cada cosa, las reglas y los flujos), un `CLAUDE.md` que lo importa y, en
`.agents/workflows/`, los nueve flujos del método: F1 aplicación nueva, F2 incorporar una fuente, F3 evolutivo, F4
defecto, F5 urgente, F6 ingeniería inversa, F7 refactorización, F8 construir y verificar y F9 pase a producción. Cada
flujo dice quién hace cada paso y con qué skill, y cita el detalle sin repetirlo. Su única fuente es
`skills/appian-functional-analyst/assets/flujos/`: volver a lanzar `iniciar` pone al día `AGENTS.md` y los flujos con la
versión del plugin, sin tocar lo demás.

Cada cambio es una unidad (`EV-nn`, `URG-nn`) en `analisis/cambios.md`. Al aprobarla el jefe de proyecto, un script
escribe en `construccion/<U>/` una issue por requisito, con lo que necesita quien la construye y nada más (qué se pide,
sus escenarios en Gherkin, sus objetos y lo que dice de ellos el técnico), en orden y diciendo cuáles pueden ir a la
vez. Quien construye, persona o agente, pide la siguiente (`indice.py issues <p> <U> --siguiente`), que queda reservada
con un commit para que nadie más se la lleve, y la construye solo en desarrollo. La issue está hecha cuando pasa su
verificación: sus objetos, como dice el técnico, y sus pruebas, los casos de prueba guardados de sus reglas e interfaces
y de lo que las usa; un retoque que no cambia criterios ni reglas no ejecuta ninguno. Con todas hechas, el QA recorre la
unidad con SAIL CLI como cada rol, en otra sesión y solo con sus escenarios, y deja cada recorrido como guion en
`qa/<U>/`. Un fallo devuelve su issue a pendiente, salvo que una persona marque esa prueba como no necesaria, con motivo
(`skills/appian-functional-analyst/references/cambios.md` §6). Después, la unidad se marca construida.

Desde el paquete no actúa la IA. Antes de prepararlo, la regresión ejecuta todos los casos de prueba de la aplicación y
`qa.py` repite sin IA los guiones del QA; quien lo prepara revisa en Compare and Deploy la comparación de sus objetos
con esos fallos, y `proyecto.py cambio <p> <U> produccion --ref` registra el pase.

## Qué hace cada skill

Cada petición entra por una sola skill. Las demás se usan desde ella, y se pasan el trabajo en ficheros con un formato
fijo.

| Skill | Se ocupa de | No hace | Usa |
|---|---|---|---|
| `appian-functional-analyst` | Leer las fuentes del proyecto y escribir el análisis funcional (`analisis/funcional.md`), del que sale el DF en Word para el cliente, y la especificación técnica (`analisis/tecnico.md`). Encajar cada reunión, correo o comentario nuevo en lo que ya hay. Llevar cada cambio como unidad, repartir lo que se construye en issues y registrar una urgencia | Dibujar procesos, hacer prototipos, construir o revisar objetos de Appian, documentar una aplicación existente | La skill de diagramas para los procesos; buenas prácticas para orientar la solución (`00` y la sección que decide); el MCP de documentación; git |
| `appian-diagramas-bpmn` | Dibujar los procesos en draw.io con notación BPMN y un carril por perfil: `.drawio` editable, PNG para el documento y BPMN 2.0. Decir qué se cambió a mano en una reunión | Decidir qué pasos tiene un proceso | Ninguna otra skill |
| `appian-prototipos` | Las pantallas: patrón, componentes de Appian, marca, navegación, validaciones, capturas para el documento y trazabilidad con los requisitos. La marca es la estándar de Appian o la del cliente: con su nombre, saca de su guía de marca o de su web su configuración completa (el Site con su logo, el perfil CSS, la paleta, los estados, los gráficos y una guía para quien construye), con el contraste comprobado, y la deja en `prototipo/` de su proyecto | Redactar requisitos, decidir el modelo de datos o la seguridad, construir en Appian | El análisis como entrada; buenas prácticas para las reglas de pantalla (`02` y `09`); el MCP de documentación |
| `appian-best-practices` | Cómo se hace bien en Appian: decisiones de solución, reglas por dominio, quality gates y runbooks de mantenimiento. Es la entrada para construir cada issue en desarrollo, revisar o diagnosticar objetos | Análisis funcional, diagramas y prototipos | El MCP de documentación; la skill oficial `appian` ([appian/dev-mcp-skills](https://github.com/appian/dev-mcp-skills/)) para escribir en un entorno |
| `appian-reverse-engineering` | Documentar cómo está hecha una aplicación Appian que ya existe, para que el equipo la entienda: la lee en vivo por el Dev MCP, en solo lectura, y deja en `as-is/` su funcional, arquitectura, datos, seguridad, integraciones, APIs, batches, procesos, pantallas y reglas de negocio, con el inventario y el anexo de definiciones; cada dato, con su evidencia. Con el mismo extractor, verificar cada issue contra el técnico (`verificar`), pasar la regresión antes del paquete (`regresion`) y detectar lo cambiado fuera (`deriva`) | Proponer cómo debería estar hecha o rehacerla, escribir requisitos o especificaciones, crear o modificar objetos | El Dev MCP (obligatorio), el Appian MCP Server del mismo entorno (volúmenes) y el MCP de documentación; la skill de diagramas para dibujar los procesos en draw.io |
| `appian-refactorizacion` | Plantear cómo debería estar hecha una aplicación existente, entera o una parte, con buenas prácticas y eficiencia. A partir de `as-is/`, escribe `refactorizacion/propuesta.md`: cada problema con su evidencia y la regla de buenas prácticas que incumple, la solución por capas, la migración y la convivencia con lo actual, la hoja de ruta y lo que falta por decidir. El técnico del analista baja a objetos cada decisión | Documentar la aplicación, escribir requisitos o la especificación objeto a objeto, revisar un objeto suelto, crear o modificar objetos | `as-is/` de ingeniería inversa (sus datos y su anexo, nunca la extracción en bruto); buenas prácticas para cada regla y decisión; el MCP de documentación |
| `appian-qa` | El QA de una unidad construida: en otra sesión y solo con sus escenarios (`construccion/<U>/*.feature`), recorre cada uno con SAIL CLI como lo haría cada rol, con su cuenta, y comprueba el «entonces» en lo que devuelve Appian. Cada recorrido queda como guion en `qa/<U>/`, que `qa.py` repite sin IA antes de cada paquete; un escenario que falla devuelve su issue a pendiente | Construir o corregir objetos, escribir criterios, verificar los objetos contra el técnico, mirar la maquetación o los estilos | SAIL CLI, solo en desarrollo (en una urgencia, en el entorno de corrección), y una cuenta local de Appian por rol |

**MCP `appian-docs`**: la documentación oficial de Appian (servidor público de Appian alojado en Kapa). Lo que una skill
no sepa con certeza de Appian se le pregunta antes de escribirlo, y lo que se escribe lleva la URL. Qué conviene hacer
no es una duda de documentación: eso es de buenas prácticas.

## Requisitos

En Claude (web o escritorio, sesiones en la nube) ya está todo, salvo ingeniería inversa y el QA, que necesitan el Dev
MCP o SAIL CLI en el equipo. En el equipo, con Claude Code, hace falta lo de esta tabla; en negrita, lo imprescindible:

<!-- requisitos:inicio -->
| Requisito | Lo usa | Para qué | Si falta | Cómo se instala |
|---|---|---|---|---|
| **Python 3.9 o superior** | Todas las skills | Todos los scripts; el extractor de ingeniería inversa usa 3.10 o superior, que trae uv | No funciona nada | Windows: `winget install Python.Python.3.12` (el comando es `python`)<br>macOS: `brew install python`<br>Linux: `sudo apt install python3` |
| Playwright para Python | `appian-diagramas-bpmn`, `appian-functional-analyst`, `appian-prototipos`, `appian-reverse-engineering` | Imagen de los diagramas; prueba de humo, contraste y capturas del prototipo | Diagramas sin imagen (el .drawio y el BPMN, sí) y prototipo sin capturas (se valida y se construye) | Windows: `python -m pip install playwright`<br>macOS y Linux: `python3 -m pip install playwright` |
| Un navegador: el Chromium de Playwright, Chrome o Edge | `appian-diagramas-bpmn`, `appian-functional-analyst`, `appian-prototipos`, `appian-reverse-engineering` | Lo usa Playwright para pintar sin conexión | Lo mismo que sin Playwright | Windows: `python -m playwright install chromium`, o Chrome o Edge ya instalados<br>macOS y Linux: `python3 -m playwright install chromium`, o Chrome o Edge ya instalados |
| Node.js | `appian-functional-analyst` | DF en Word, con el paquete docx | Se entrega el funcional.md | Windows: `winget install OpenJS.NodeJS.LTS`<br>macOS: `brew install node`<br>Linux: `sudo apt install nodejs npm` |
| Paquete docx de Node | `appian-functional-analyst` | DF en Word | Se entrega el funcional.md | `npm install docx` en la carpeta de trabajo, o `npm install -g docx` |
| LibreOffice | `appian-functional-analyst` | Revisar el DF en Word como PDF y ver las diapositivas de un DF del cliente | Se revisa a mano | Windows: `winget install TheDocumentFoundation.LibreOffice`<br>macOS: `brew install --cask libreoffice`<br>Linux: `sudo apt install libreoffice` |
| pdftotext o pypdf | `appian-functional-analyst` | Leer fuentes en PDF | Claude lee el PDF directamente, más despacio | Windows: `python -m pip install pypdf`<br>macOS: `brew install poppler` o `python3 -m pip install pypdf`<br>Linux: `sudo apt install poppler-utils` o `python3 -m pip install pypdf` |
| git | `appian-functional-analyst` | El repositorio de cada proyecto (`proyecto.py iniciar` y `estado`) y la reserva de las issues de construcción (`indice.py issues --siguiente`) | El proyecto se crea sin repositorio, `estado` no sabe qué está subido y las issues se dan sin reservar: dos personas pueden llevarse la misma | Windows: `winget install Git.Git`<br>macOS: `brew install git`, o las herramientas de línea de comandos de Xcode<br>Linux: `sudo apt install git` |
| uv | `appian-reverse-engineering` | Arrancar el Dev MCP y el extractor, con Python 3.10 o superior y el SDK mcp | No se puede usar ingeniería inversa | Windows: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"`<br>macOS y Linux: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Appian Dev MCP configurado | `appian-reverse-engineering` | Leer la aplicación en solo lectura (entorno 26.5 o superior, usuario con rol Designer) | No se puede usar ingeniería inversa | Lo instala cada persona y lo configura en el `.mcp.json` de su carpeta: `skills/appian-reverse-engineering/references/devmcp-setup.md` |
| Appian MCP Server del mismo entorno | `appian-reverse-engineering` | Volúmenes del data fabric | La documentación sale sin volúmenes | Lo activa un administrador del entorno; se añade a la configuración MCP como `<URL del entorno>/mcp` (misma guía) |
| SAIL CLI | `appian-qa` | Recorrer los escenarios de una unidad como cada rol y repetir sus guiones (`qa/`) | No se puede usar el QA | Viene en el paquete del Dev MCP (`bin/`): `bin/setup-*` lo deja en el PATH como `sail` |
| Skill de PDF de Claude | `appian-reverse-engineering` | Exportar `as-is/` a PDF | Se entrega en Markdown | En Claude (web o escritorio) ya está; en Claude Code, una skill de PDF instalada, como `pdf` de anthropics/skills |
| pytest | Las pruebas del repositorio | Pruebas de ingeniería inversa en `pruebas/comprobar_plugin.py --completo` | Las trae uv; sin uv, esas pruebas no se completan | Windows: `python -m pip install pytest`<br>macOS y Linux: `python3 -m pip install pytest` |
| SDK mcp de Python (pide Python 3.10 o superior) | Las pruebas del repositorio | Pruebas de ingeniería inversa, con el Dev MCP simulado | Lo mismo que sin pytest | Windows: `python -m pip install "mcp>=1.2,<2"`<br>macOS y Linux: `python3 -m pip install "mcp>=1.2,<2"` |
<!-- requisitos:fin -->

La tabla sale de `requisitos.json` (`python3 requisitos.py --tabla-readme`). `requisitos.py`, en la carpeta del plugin,
dice qué falta en un equipo, qué se pierde y cómo se instala: `python3 requisitos.py` para todo el plugin y
`--skill <nombre>` para una skill (en Windows, `python`). Cada skill lo ejecuta antes de su primera tarea. Con el plugin
instalado, basta pedir a Claude «comprueba qué le falta al plugin en este equipo».

**Aviso al instalar**: al empezar una sesión, el plugin comprueba el equipo (`requisitos.py --breve`, en
`hooks/hooks.json`) y Claude dice lo que falta la primera vez de cada versión. Los hooks de un plugin se cargan en
Claude Code (también en la pestaña Code de la app de escritorio) y en Cowork; en el chat no, y allí lo comprueba cada
skill antes de su primera tarea.

**Correos de Outlook (.msg)**: el paquete `extract-msg` no se instala en muchos equipos. Lo fiable es guardar el correo
como `.eml` (Archivo → Guardar como) o PDF.

## Instalación

- **Claude Code y la app de Claude** (escritorio o web): el repositorio es también un marketplace. Los pasos, y cómo
  llegan las versiones nuevas, están en su portada de GitHub (`.github/README.md`). Una versión llega cuando cambia
  `version` en `.claude-plugin/plugin.json`.
- **Claude, para una organización**: un administrador publica el fichero `appian-analisis-funcional.plugin` para la
  organización y cada persona lo instala desde el catálogo de plugins; también se puede instalar a título personal
  abriendo el `.plugin` en una conversación. El `.plugin` es la carpeta del plugin comprimida en zip, sin lo de
  desarrollo (`docs/`, `pruebas/`, `CLAUDE.md`, `CLAUDE.local.md`, `.github/`, `.claude/`), ni `.git`, cachés u otros
  `.plugin`. Lo hace `python3 pruebas/empaquetar.py`, también en Windows (lo deja junto a la carpeta del repositorio), o
  esta orden:
  `zip -r appian-analisis-funcional.plugin . -x ".git/*" ".github/*" ".claude/*" "docs/*" "pruebas/*" "CLAUDE.md" "CLAUDE.local.md" "*__pycache__*" "*.pytest_cache*" "*.plugin"`

**Retirar las skills sueltas**: si alguien tenía instalada como skill independiente una del plugin
(`appian-functional-analyst`, `appian-best-practices`, `appian-reverse-engineering` o `appian-prototipos-<cliente>`, hoy
`appian-prototipos`), hay que eliminarla: si no, existe dos veces con versiones distintas y no se sabe cuál se activa.
`requisitos.py` avisa si encuentra una en `~/.claude/skills/`.

### MCP de documentación de Appian

Se conecta solo al instalar el plugin. La primera consulta pide iniciar sesión con Google o GitHub (lo exige el
proveedor, Kapa; no guarda datos personales). Límite: 300 consultas al día y 60 por minuto por persona. Es opcional: sin
él, las skills consultan docs.appian.com por la web.

### Dev MCP y SAIL CLI

**No se incluyen.** El Appian Dev MCP (lectura y escritura de objetos de diseño) lo instala cada persona en local
(Python 3.13, `uv`, su ruta y el plug-in instalado en el entorno Appian por un administrador), y SAIL CLI viene en su
paquete. Guía: `skills/appian-reverse-engineering/references/devmcp-setup.md`. Para construir, la entrada es cada issue
de `construccion/<U>/`, que trae lo que hace falta del técnico y del prototipo; buenas prácticas pide además la skill
oficial `appian` antes de escribir en un entorno.

**Solo se escribe en desarrollo.** La IA construye en el entorno de desarrollo y, en una urgencia, en el entorno de
corrección; a pruebas y a producción llega un paquete que ha revisado una persona. En los demás entornos, el Dev MCP
entra con una cuenta que solo lee, la misma para todo el equipo, y SAIL CLI no se usa, porque crea datos y lanza
procesos. `LCP_TOOL_MODE=readonly` no basta: la documentación de Appian la describe, pero el Dev MCP 26.6.110 no la
aplica. Detalle en `skills/appian-reverse-engineering/references/devmcp-setup.md`, «Solo se escribe en desarrollo».

**No se incluye `appian-sail-generator`**, la skill para escribir código SAIL suelto: va aparte.

## Confidencialidad

- La carpeta del proyecto (fuentes, análisis, prototipo, issues y QA) contiene información del cliente: no sale del
  proyecto. Es un repositorio git privado; dónde se aloja lo decide cada proyecto.
- Si ingeniería inversa encuentra secretos escritos en la aplicación, sus valores quedan en claro en `as-is/`: el equipo
  decide antes de subirla.
- Los diagramas se dibujan con el navegador local: Mermaid (licencia MIT) y el visor de draw.io (licencia Apache 2.0)
  van incluidos en el plugin. Para editar un `.drawio` a mano sirven draw.io Desktop, app.diagrams.net (no sube el
  fichero) o la integración de draw.io con SharePoint y OneDrive.
- Un prototipo publicado como artefacto es privado hasta que su autor lo comparte, y usa siempre personas y datos
  ficticios.

## Desarrollo

Cómo se trabaja en este repositorio (la rama, las pruebas, la versión y el PR) está en `CLAUDE.md`. Qué comprueba
`pruebas/comprobar_plugin.py` lo dice su cabecera; las pruebas de cada skill están en `pruebas/<skill>/` y las
evaluaciones, en `pruebas/evaluaciones/`. En `docs/`: el diseño y el plan de la versión en curso (`docs/diseno/` y
`docs/plan/`), los resultados de las evaluaciones (`docs/evaluaciones.md`) y lo pendiente (`docs/siguiente-version.md`).

## Versiones

| Versión | Cambios |
|---|---|
| 0.8.0-beta.1 | **Método L.U.C.I.A.: la IA prepara y, desde el paquete, deciden personas, Appian y scripts.** Cada proyecto es un repositorio git (`proyecto.py iniciar`), sobre main y sin ramas, con un `AGENTS.md` generado y los flujos F1 a F9, de la aplicación nueva al pase a producción, en `.agents/workflows/`, para que cualquier persona o agente trabaje igual. Los criterios de aceptación se escriben en Gherkin de una línea (dado, cuando y entonces) y pasan a `.feature` sin IA. Las issues por requisito sustituyen al encargo: con la columna «Para» de técnico §13, `indice.py issues` escribe en `construccion/<U>/` una por requisito, con solo lo que necesita quien construye, en orden y diciendo cuáles van a la vez; `--siguiente` la reserva con un commit. `verificar` ejecuta las pruebas de la issue (los casos de prueba de sus reglas e interfaces y de lo que las usa) y un fallo propio la deja pendiente salvo que una persona lo marque con `--sin-prueba` y motivo; antes del paquete, la regresión de toda la aplicación. Skill nueva, `appian-qa`: el QA de la unidad con SAIL CLI, en otra sesión y solo con sus escenarios, con guiones que `qa.py` repite sin IA. Quien prepara el paquete revisa en Compare and Deploy la comparación de los objetos con los fallos de la regresión y del QA, y `produccion --ref` guarda la referencia del pase. En un proyecto que ya existe: lanzar `proyecto.py iniciar`, que lo pasa a git y le pone `AGENTS.md` y los flujos sin tocar lo demás; las verificaciones del encargo antiguo (`construccion/verificacion/<U>.json`) no cuentan y una unidad aprobada entonces se verifica de nuevo, issue a issue |
| 0.7.0-beta.4 | **Buenas prácticas, contrastadas con la documentación y con la skill oficial.** Las 37 reglas en las que `appian-best-practices` contradecía a la skill oficial `appian` se han verificado contra docs.appian.com (26.9). Se corrige lo que estaba mal (consulta en `data`, prefijo de los grupos, visibilidad de página, role map del sitio, escribir en línea o con proceso, botón con `a!startProcess`, foco automático, record list en una interfaz) y se precisan alcance, versión y fuente del resto (clave compuesta desde 26.3, `modifiedOn`, `fetchTotalCount`, tamaño de lote). Referencia nueva, `14-official-skill-divergences.md`: 18 puntos en los que la skill oficial no sigue la documentación y qué hacer en cada uno. Las puertas 1 y 4 ya no repiten lo que la skill oficial comprobó al escribir, y `SKILL.md` no exige el MCP de documentación para escribir. A demanda, con red: `pruebas/comprobar_anclas.py` (unas 1.200 citas a la documentación, 0 anclas rotas tras corregir 22) y `pruebas/comprobar_divergencias.py` (qué divergencias ha corregido ya Appian en su skill). Y más ligero: al modificar un objeto se envía el `versionId` leído, para no pisar el cambio de otro; las puertas ya no piden anotar un veredicto con su evidencia (lo que falla se arregla y lo que no se pudo comprobar se dice); la rúbrica UX de prototipos, solo con pantallas nuevas o antes de enseñarlas al cliente |
| 0.7.0-beta.3 | **Retoques ligeros y menores.** Analista: un retoque que nadie tiene que aprobar va por un camino corto (`actualizacion.md`): `proyecto.py version` hace en una orden la copia, la versión de los dos documentos, sus filas en `decisiones.md` (también las D con `--decision`) y la fuente en `proyecto.md`; el informe se escribe ya aplicado y se comprueba una vez; `indice.py impacto --cambio` dice la fila de técnico §13. Medido a ciegas: de 34, 34 y 47 llamadas a 16, 19 y 21. Ingeniería inversa: el informe de extracción lista las herramientas omitidas con su motivo (`toolsOmitted`), también con `--solo`. Diagramas: la etiqueta de cada salida de una puerta, en su propio tramo. `requisitos.py`: un servidor http ajeno (GitHub, Notion) ya no deja el Appian MCP Server sin comprobar |
| 0.7.0-beta.2 | **Evolutivos, construcción y urgencias, y calidad de producción.** Cada cambio sobre una aplicación es una unidad (`EV-nn`, `URG-nn`) en `analisis/cambios.md` con su estado (Abierta, Aprobada, Construida, En producción), que solo mueve `proyecto.py cambio`: el jefe de proyecto aprueba la unidad una vez; lo ya construido se señala como posible petición de cambio sin pedir aprobación punto a punto; dos unidades sobre el mismo objeto necesitan una decisión antes de construir. Por script, sin leer documentos: el DF del cambio (`df_docx.js --cambio`), el encargo de construcción (`indice.py encargo`, que construye `appian-best-practices` en el orden de la skill oficial de Appian), las pruebas que hay que repetir y las colisiones. Ingeniería inversa verifica lo construido contra el técnico (`verificar --esperado`), detecta cambios hechos fuera (`deriva`), reextrae solo unos objetos y mantiene los IDs de los hallazgos. Las urgencias van por un camino corto: ficha, colisión, corrección en desarrollo o en el entorno de corrección, y la tarea de reaplicarla en el evolutivo, que no se construye sin ella. Analista: la versión sube solo si cambia algo y el Word se genera al enviarlo y nunca pisa uno entregado; lo que llega por el chat es una fuente; ficha INT con criterios para los sistemas externos; el Word con el color de la marca del cliente. Prototipos: la marca del cliente con solo su nombre y `capture.py --solo`. Diagramas: temporizador que interrumpe, avisos sin capa y ocho correcciones de dibujo y BPMN. Buenas prácticas: seis prácticas nuevas, cada una con su fuente oficial. Plugin neutral para cualquier equipo y cliente; descripciones de menos de 1.000 bytes probadas también frente a `appian-sail-generator` y la skill de Word; pruebas de las evaluaciones en `--completo` y CI con Node 24 |
| 0.7.0-beta.1 | **Integración de ingeniería inversa, versión para el equipo.** Seis skills que se pasan el trabajo por el proyecto: **ingeniería inversa** documenta una aplicación existente en solo lectura, con cada dato con su evidencia, lo que no se pudo verificar registrado y los procesos grandes en tramos; **refactorización** (nueva) propone cómo rehacerla, entera o un módulo, con su migración y su hoja de ruta; el **analista** parte de un DF ya hecho, de una demo o de una aplicación existente, y prepara el guion de la próxima reunión; **diagramas** dibuja y exporta todos los procesos, también sin navegador; **prototipos** construye con la marca de cualquier cliente o la estándar de Appian y rehace solo lo que cambia tras una demo; **buenas prácticas** revisa objetos sueltos y remite la evaluación de una aplicación entera. `requisitos.py` y el aviso al empezar dicen qué falta en el equipo; el paquete no lleva nada personal ni de un cliente; las pruebas pasan en Windows, macOS y Linux; `pruebas/empaquetar.py` hace el `.plugin` |

Las versiones anteriores, de la 0.1.0 a la 0.7.0-alpha.7, están en el historial de git de este fichero.
