# Integración de ingeniería inversa y refactorización — plan de implementación

> **Cómo se ejecuta:** tarea a tarea y en orden, marcando cada paso (`- [ ]` → `- [x]`) al terminarlo. Cada fase va en
> su rama y llega a `main` con sus pruebas en verde y la revisión de un agente que no ha visto el trabajo.

**Objetivo:** que el plugin tenga seis skills sin solapes —ingeniería inversa solo documenta lo que hay, refactorización
propone cómo debería estar hecho, el analista acuerda y especifica— y que cualquiera del equipo pueda instalarlo.

**Arquitectura:** una carpeta por aplicación o proyecto (`<p>`) en la que cada skill escribe solo en lo suyo
(`as-is/`, `refactorizacion/`, `analisis/`, `prototipo/`…) y lee lo de las demás por ficheros de formato fijo
(`as-is/datos/*.json`, `refactorizacion/propuesta.md`). `pruebas/comprobar_plugin.py` comprueba en cada cambio que
nadie escribe en lo de otra skill y que cada capacidad (pintar, exportar BPMN, reglas de prosa) vive en un solo sitio.

**Tecnologías:** Python 3.9+ con la biblioteca estándar en los scripts; Playwright y un navegador para pintar (skill de
diagramas y prototipos); `mcp` (vía `uv`) solo en el extractor; Node con `docx` para el Word; pytest para ingeniería
inversa y `selftest.py` en el resto; GitHub Actions en Windows, macOS y Linux.

**Diseño aprobado:** `docs/diseno/2026-10-07-integracion-ingenieria-inversa.md` (copia del doc
«Plan: integrar la ingeniería inversa en el plugin»). Se leen los dos.

## Restricciones globales

- **Plugin y proyecto, separados.** Este repositorio es el código del plugin y sus pruebas. Todo lo que el plugin genera
  al trabajar, también en los proyectos de prueba de las evaluaciones, va a la carpeta de ese proyecto (`<p>`), fuera
  del repositorio; el plugin no escribe nada fuera de `<p>`, salvo la marca de aviso de la Tarea 24, que no es trabajo
  de un proyecto.
- **Las skills, sin proyectos ni clientes dentro.** Una skill solo lleva lo que usa al trabajar; ninguna lleva un
  proyecto, tampoco de ejemplo, ni la marca de un cliente. Las pruebas de cada skill y sus datos ficticios están en
  `pruebas/<skill>/` (Tarea 0), fuera del paquete, y la marca del cliente va en `prototipo/` de su proyecto (Tarea 0b).
- Todo en español: documentos, mensajes de los scripts, commits y nombres de los objetos de los ejemplos.
- Ejemplos y aplicaciones de prueba ficticios. Nada del cliente en el repositorio. Nada sale del equipo para pintar o convertir.
- Ingeniería inversa usa solo los MCP de Appian (Dev MCP, Appian MCP Server y MCP de documentación) y en solo lectura.
- Ingeniería inversa no da nada por inexistente sin decir dónde lo buscó, no toma la definición por la ejecución y
  registra lo que no pudo verificar, con lo que hace falta para resolverlo (Tarea 8b).
- La extracción vive en el proyecto, en `as-is/extraccion/` (D4), tal cual la devuelve el Dev MCP. Se trabaja en
  entornos controlados y no se oculta nada: ni usuarios, ni datos de la app, ni secretos (Raúl, 8 de octubre; Tarea 2b).
  Un secreto escrito en la app sigue siendo un hallazgo de seguridad. Las demás skills leen
  `as-is/datos/`, nunca la extracción.
- Los proyectos de prueba de las evaluaciones se crean en `$PROYECTOS_PRUEBA` (por defecto `proyectos-prueba/`, al
  lado de la carpeta principal del repositorio, también si se trabaja desde un worktree). En el repositorio quedan las
  preguntas, lo esperado y los scripts que puntúan (`pruebas/evaluaciones/`), y los resultados en `docs/evaluaciones.md`.
- Los IDs de otra skill se citan dentro de su fuente: «[FU-07 PAN-03]», «[FU-08 REF-02]» (D1). Nunca en el texto del DF.
- Scripts con `pathlib`, `encoding="utf-8"` y rutas con espacios; en Windows el comando es `python`. Rutas de prueba
  neutras («Carpeta con espacios/Gestión app»).
- Una rama por fase (`f2-…`, `f3-…`); a `main` llega con las pruebas en verde y la revisión independiente de la fase.
  Al cerrarla, el resumen de cambios y las lecciones aprendidas van a `docs/evaluaciones.md`.
- Antes de cada commit: `python3 pruebas/comprobar_plugin.py --completo`, que desde la Tarea 0 incluye las pruebas de
  ingeniería inversa (solas: `python3 -m pytest -q pruebas/appian-reverse-engineering`).
- Commits terminados en `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` y
  `Claude-Session: https://claude.ai/code/session_01DozooebTcuXCNifwmTZUN5`.
- Lo de desarrollo (`docs/`, `CLAUDE.md`, `pruebas/`, `.github/`) no va en el paquete. Versión al cerrar: `0.7.0-beta.1`.
- Las baterías de evaluación (preguntas, malas prácticas, incoherencias, peticiones de enrutado) tienen un tercio
  escrito por un agente aparte y guardado en `ocultas/`, que no lee quien ajusta plantillas ni descripciones hasta medir.

## Riesgos para quien lo use (Review Focus)

Lo que el diseño implica y ninguna prueba de tarea cubriría sola. Cada línea tiene su prueba en la tarea indicada.

1. **Proyecto en una carpeta sincronizada con SharePoint u OneDrive.** Las rutas son cortas. Prueba `test_rutas_cortas`
   (Tarea 2).
2. **Windows.** Rutas con espacios y largas, `python` en vez de `python3`, consola sin UTF-8. Pruebas
   `test_ruta_con_espacios` (Tareas 2 y 6) y la matriz de GitHub Actions (Tarea 26).
3. **Repetir la ingeniería inversa o retomarla en otra sesión o en otro equipo.** Como la extracción está en el
   proyecto, se retoma sin volver a extraer lo que ya está. Prueba `test_retomar` (Tarea 2).
4. **Proyecto sin aplicación existente.** Las comprobaciones nuevas del analista no saltan sin `as-is/`. Prueba: la del
   analista con `datos/autorizaciones` da lo mismo que antes (Tarea 19).
5. **Compañero sin Playwright o sin Node.** Se dibuja el `.drawio` y se exporta el BPMN sin navegador (sin PNG), y se
   dice qué falta. Pruebas `DIAGRAMAS_SIN_NAVEGADOR=1` (Tarea 12) y `REQUISITOS_SIN=playwright,docx` (Tarea 23).
6. **Lo que no se pudo verificar se pierde por el camino.** Llega como NV a refactorización y al analista, que lo
   tratan como pendiente y no como hecho. Pruebas `test_evidencia.py` (Tarea 8b) y las de las Tareas 14, 19 y 20.

---

## F2 · Ingeniería inversa en el plugin, solo con el bloque A

### Tarea 0: Las skills, solo con lo que usan al trabajar

**Ficheros:**
- Mover con `git mv`:
  - `skills/{appian-functional-analyst,appian-diagramas-bpmn,appian-prototipos-aena}/scripts/selftest.py` →
    `pruebas/<skill>/selftest.py`;
  - `skills/appian-reverse-engineering/tests/` → `pruebas/appian-reverse-engineering/`, con `fixtures/` → `datos/`;
  - `skills/appian-functional-analyst/ejemplos/autorizaciones/` → `pruebas/appian-functional-analyst/datos/autorizaciones/`;
  - `skills/appian-diagramas-bpmn/ejemplos/{solicitud,pedido}.json` → `pruebas/appian-diagramas-bpmn/datos/`;
  - `skills/appian-reverse-engineering/docs/{SPEC-v2-devmcp,CHANGELOG}.md` → `docs/ingenieria-inversa/`, y
    `docs/PRIMERA-EJECUCION.md` → `references/primera-ejecucion.md` de la skill, porque es para quien la usa (la cita
    su SKILL.md);
  - `skills/appian-prototipos-aena/examples/{bloques,ia,componentes,README.md}` → `skills/appian-prototipos-aena/galerias/`:
    son el catálogo del kit y se quedan.
- Borrar: `skills/appian-prototipos-aena/examples/casos/` (un proyecto entero dentro de la skill).
- Crear: `pruebas/appian-prototipos-aena/datos/autorizaciones/generar_app.py`, con dos pantallas de
  `pruebas/appian-functional-analyst/datos/autorizaciones/` leídas con `modelo.py` del analista, como hacía el caso borrado.
- Modificar:
  - los `selftest.py` y las pruebas de ingeniería inversa: la skill se toma de `$PLUGIN_A_PROBAR/skills/<skill>` (por
    defecto, la raíz del repositorio) y los datos, de `pruebas/<skill>/datos/`. En ingeniería inversa, `conftest.py`
    define `SKILL` y las pruebas lo usan en lugar de `Path(__file__).parents[1]`;
  - `pruebas/comprobar_plugin.py`: `--completo` ejecuta `pruebas/*/selftest.py` y
    `python -m pytest -q pruebas/appian-reverse-engineering` con `PYTHONUTF8=1` (si faltan `pytest` o `mcp` y hay `uv`,
    con `uv run --no-project --with pytest --with "mcp>=1.2,<2"`; si no, aviso de requisito, como el código 2 de hoy);
    `--plugin <carpeta>` pasa las pruebas del repositorio a otra copia del plugin (la del paquete); `CARPETAS` con
    `galerias`; y errores nuevos: una skill con `tests/`, `ejemplos/`, `examples/` o un `selftest.py`, o con una carpeta
    que tiene forma de proyecto (`proyecto.md`, `fuentes/`, `analisis/`, `as-is/`, `refactorizacion/` o `prototipo/`);
  - lo que citaba los ejemplos. Analista: `SKILL.md` y `references/{funcional,tecnico}-plantilla.md`, donde «Ejemplo
    completo» pasa a fragmentos de pocas líneas dentro de la plantilla (una historia con su criterio, una ficha de
    pantalla, una fila de pendientes y una DT). Diagramas: `SKILL.md` («Ejemplos completos en `ejemplos/`» sobra; basta
    el bloque del formato). Prototipos: `SKILL.md` (sin `examples/casos/`; «En un equipo nuevo» dice que validar y
    construir no necesitan nada más y que las capturas piden Playwright y un navegador, hasta que la Tarea 24 ponga
    `requisitos.py`), `galerias/README.md` (qué es cada galería y que ahí no hay proyectos; sin «Añadir un caso»),
    `references/{bloques,componentes,design-rules}.md`, `schemas/catalogo-appian.json`, `scripts/sail_helpers.py` y los
    `generar_app.py` de las galerías. Y `README.md`;
  - `docs/ingenieria-inversa/SPEC-v2-devmcp.md`: las dos líneas que citan una aplicación del cliente, sin su nombre.

- [x] **Paso 1: pruebas que fallan.** En `comprobar_plugin.py`, con copias temporales del plugin: una skill con
  `ejemplos/x/proyecto.md` da error, y otra con `tests/` también; `--completo --plugin <copia sin pruebas/>` pasa las
  pruebas del repositorio a esa copia. → FALLA.
- [x] **Paso 2:** mover, borrar y ajustar.
- [x] **Paso 3:** `python3 pruebas/comprobar_plugin.py --completo` en verde, con las mismas pruebas que antes salvo las
  del caso borrado, que sustituye el prototipo de `autorizaciones`. `CLAUDE.md`, con los comandos nuevos. Commit
  «F2: las skills, sin proyectos ni pruebas dentro».

### Tarea 0b: Prototipos sin la marca de un cliente

Por defecto, el aspecto estándar de Appian; la marca del cliente es un fichero de su proyecto, como las fuentes.

**Ficheros:**
- Mover con `git mv`: `skills/appian-prototipos-aena/` → `skills/appian-prototipos/` y `pruebas/appian-prototipos-aena/`
  → `pruebas/appian-prototipos/`, y cambiar la ruta de la skill dentro de esas pruebas (`selftest.py` y
  `datos/autorizaciones/generar_app.py`) y la de `galerias/README.md` en el `README.md`.
- Crear en la skill: `assets/brand-appian.json` (la marca por defecto, sin logo, con los valores por defecto del objeto
  Site que da la documentación de Appian, consultada con el MCP de documentación) y `references/marca.md` (formato de
  `brand-<id>.json`, que va en `<p>/prototipo/`, y cómo se saca la marca de un cliente de su guía de marca o de su web
  pública, con la auditoría de contraste de `validate.py`).
- Borrar de la skill: `assets/brand-aena.json` y `assets/{logo-aena-on-light,logo-aena-on-dark,symbol-aena}.svg`. Raúl
  los recibe en un zip, fuera del repositorio, para la carpeta `prototipo/` de sus proyectos de AENA.
- Modificar:
  - en la skill: `SKILL.md` (nombre, título y descripción sin «con la marca AENA»; si el proyecto no tiene
    `prototipo/brand-<id>.json`, se pregunta por la marca y, sin respuesta, se usa `appian` con un `$assumption`),
    `scripts/{build,validate,sail_helpers}.py` (marca por defecto `appian`; con `--brand x` y sin `brand-x.json` junto al
    `app.json`, error que dice dónde ponerla), `references/design-rules.md` (las reglas valen para cualquier marca; la
    paleta de estados sale de `brand-<id>.json → states`), `references/{componentes,bloques}.md`, y `templates/` y
    `galerias/`, que se regeneran con la marca neutra y con constantes de prefijo ficticio en lugar de `AENA_…`;
  - fuera de ella: `skills/appian-functional-analyst/{SKILL.md,references/actualizacion.md}`, `README.md` (mapa de
    skills; las filas de versiones anteriores no se tocan), `.claude-plugin/{plugin.json,marketplace.json}` (sin «aena»
    en descripción ni palabras clave) y `pruebas/comprobar_plugin.py` (`REGLA_DOCS` y la comprobación nueva).

- [x] **Paso 1: pruebas que fallan.** En `pruebas/appian-prototipos/selftest.py`: sin `--brand`, `build.py` usa `appian`;
  con `--brand x` y un `brand-x.json` de prueba junto al `app.json`, usa esa; con `--brand aena` sin su fichero, sale
  con error y dice dónde ponerlo. En `comprobar_plugin.py`: error si una skill lleva un `brand-*.json` que no sea
  `brand-appian.json`, o un logo. → FALLA.
- [x] **Paso 2:** mover, crear y ajustar; regenerar plantillas y galerías.
- [x] **Paso 3:** `comprobar_plugin.py --completo` en verde y `git grep -i -w aena -- skills .claude-plugin` vacío. La
  galería de componentes de antes del cambio, construida con el kit nuevo y `--brand aena` (los ficheros de AENA,
  sacados del historial, junto a su `app.json`), da el mismo HTML que con el kit de antes: así lo verán los proyectos de
  AENA. Commit «F2: prototipos sin la marca de un cliente».

### Tarea 0c: La configuración de marca de cualquier cliente, a partir de su nombre

Con decir para qué empresa se trabaja, la skill saca su configuración de marca completa, como la que había de AENA, y la
deja en `prototipo/` del proyecto: el objeto Site con su logo, el perfil CSS de Appian, la paleta, las convenciones de
botones y tarjetas, los estados, los colores de gráfico y la tipografía, todo con el contraste comprobado. Así el
prototipo es fiel a su marca y el equipo sabe cómo configurar Appian y cómo diseñar cada pantalla que construya. Sirve
para cualquier cliente. (Añadida el 7 de octubre a petición de Raúl.)

**Ficheros:**
- Crear: `skills/appian-prototipos/scripts/marca.py` y `pruebas/appian-prototipos/datos/web-ficticia/{index.html,estilos.css,logo.svg}`
  (la web de una empresa ficticia: dos colores de marca en variables CSS y en reglas, grises de texto y bordes, un logo
  SVG en la cabecera, un icono del sitio y una tipografía).
- Modificar en `skills/appian-prototipos/`: `SKILL.md` (paso 1, «Marca», y paso 5, «Entregar»), `references/marca.md`
  (qué lleva la configuración y cómo se saca con `marca.py`) y `references/design-rules.md` (con la marca de un cliente,
  sus valores están en `marca-<id>.md` del proyecto). Fuera: `pruebas/appian-prototipos/selftest.py` y `README.md` (fila
  de prototipos en el mapa de skills).

**Interfaces:**
- `marca.py web <url> [--max-css 10] [--timeout 10]`: descarga la página y las hojas de estilo que enlaza del mismo
  sitio (como mucho `--max-css`, 2 MB cada una) y escribe en la salida estándar un JSON `{"url", "colores": [{"hex",
  "veces", "variables", "contraste": {"blanco", "negro"}}], "themeColor", "logos": [{"url", "pista"}], "tipografias"}`.
  `colores` va de más a menos usado, sin blancos, negros ni grises (saturación por debajo del 10 %); `variables`, las
  propiedades CSS que definen ese color. `logos`: SVG en línea o imágenes de la cabecera con «logo» en `src`, `alt`,
  `class` o `id`, primero; el icono del sitio, al final. Un SVG en línea lleva como `url` la de la página con
  `#svg-<n>` y, además, `svg` con su código. Sin red o sin respuesta, sale con 2 y lo dice.
- `marca.py crear --id <id> --nombre <nombre> --fuente <de dónde sale y fecha> --oscuro <hex> --realce <hex>
  --acento <hex> [--principal <hex>] [--secundarios <hex,hex…>] [--logo <svg>] [--logo-claro <svg>]
  [--formas SQUARED|SEMI_ROUNDED|ROUNDED] [--mayusculas si|no] [--tipografia <nombre>] [--sin-perfil-css] <carpeta>`
  escribe en `<carpeta>`:
  - `brand-<id>.json`, con las mismas secciones que la de AENA: `site` (el objeto Site con su logo), `typeface`,
    `palette`, `components` (botones principal, secundario, destructivo y de barra, tarjeta de contenido, fondo de página
    y `chartColorScheme`), `appianSemanticApprox`, `states` y, salvo con `--sin-perfil-css`, `cssProfile`. El perfil
    lleva solo lo que cambia respecto a Appian, con propiedades de `schemas/css-profile-properties.json`, en seis grupos:
    colores semánticos (texto e iconos de estado con 4,5:1 sobre blanco y sobre su fondo, y sus fondos), textos de los
    campos (etiqueta, instrucciones, marcador de posición y asterisco, con 4,5:1), campos (borde con 3:1 y radios de la
    forma), botones (radios), tarjetas, cajas y etiquetas (sombra teñida del oscuro y radios) y tooltips (fondo del oscuro);
  - el logo junto al JSON: `logo-<id>-on-dark.svg` y, con `--logo-claro`, `logo-<id>-on-light.svg`;
  - `perfil-css-<id>.txt`, el perfil para pegar en Admin Console › Branding › CSS Profiles (el mismo texto que escribe
    `build.py`);
  - `marca-<id>.md`, la guía de marca del proyecto para quien construye: la configuración del Site para copiarla tal
    cual, dónde va el perfil CSS y qué capacidades pide, la paleta con el contraste de cada color, botones, tarjetas,
    estados, gráficos, tipografía y logo, las fuentes con su fecha, los ajustes de contraste hechos y lo que tiene que
    confirmar el cliente.

  Lo que no llega a WCAG 2.2 AA lo ajusta cambiando solo la luminosidad (matiz y saturación se quedan) y lo dice en la
  salida y en la guía (`acento #5DA9E9 → #1971BA: 5,1:1 sobre blanco`): el acento se oscurece hasta 4,5:1 sobre blanco y
  sobre el gris de página (`#F4F5F7`); el oscuro, hasta 4,5:1 con texto blanco; el realce se aclara hasta 3:1 sobre el
  oscuro; los colores de estado del perfil, hasta 4,5:1 sobre blanco y sobre su fondo. `palette.navy` es el oscuro;
  `chartColorScheme` pone primero los colores de la marca que llegan a 3:1 sobre blanco y después los de la estándar,
  sin repetir y como mucho 8; `components.primaryButton.color` es `--principal` o `ACCENT`. Avisa si el logo no llega a
  3:1 sobre el oscuro (hace falta su versión en negativo). Error (2) si un color no es `#RRGGBB`, si falta un logo, si
  el `id` no es `[a-z0-9-]` o si `<carpeta>` está dentro del plugin.
- `SKILL.md`, paso 1: si el proyecto no tiene `prototipo/brand-<id>.json` y se sabe para qué empresa es (lo dice el
  usuario o `proyecto.md`), la skill saca su configuración de marca. Busca su guía de marca (manual de identidad) o su
  sala de prensa y, si no las publica, su web oficial: solo fuentes de la propia empresa. Con red en el terminal,
  `marca.py web`; si no, WebFetch pidiendo los colores en hex, la tipografía y la URL del logo. Decide qué color hace
  cada papel (oscuro, realce, acento y botón principal) y ejecuta `marca.py crear` en `<p>/prototipo/`. Después valida y
  construye con `--brand <id>`, pasa la auditoría de contraste, enseña al usuario la cabecera con su logo y el resumen de
  `marca-<id>.md`, y anota en el `$assumption` de `app` «Marca de <empresa> sacada de <fuente> el <fecha>; falta que la
  confirme el cliente». Si no encuentra nada fiable, pide su guía de marca; sin respuesta, `appian`. Paso 5: con el
  prototipo se entregan `marca-<id>.md` y `perfil-css-<id>.txt`.

- [x] **Paso 1: pruebas que fallan.** En el selftest de prototipos, con la marca de una empresa ficticia:
  - `crear` con el acento `#5DA9E9` da un `brand-x.json` con todas las secciones de `brand-appian.json` más `cssProfile`;
    el acento a 4,5:1 o más sobre blanco y sobre `#F4F5F7` y a menos de 10° de su matiz; `palette.navy` igual al
    oscuro; un perfil CSS sin errores de `validate.py`, con los colores de estado a 4,5:1 sobre blanco y sobre su fondo y
    el borde de campo a 3:1; el logo copiado; `perfil-css-x.txt` y `marca-x.md` escritos, y la guía con la configuración
    del Site y cada ajuste hecho. Con `--sin-perfil-css`, sin `cssProfile` ni `perfil-css-x.txt`. `build.py --brand x`
    construye con ella el catálogo de patrones, que pasa la auditoría de contraste si hay navegador. Con un color mal
    escrito, o con la carpeta del plugin como destino, sale con 2;
  - `web` contra `datos/web-ficticia/`, servida en `127.0.0.1` por la propia prueba, da sus dos colores de marca entre
    los tres primeros, el logo de la cabecera el primero de `logos` y su tipografía; contra un puerto cerrado, sale con 2.
  → FALLA.
- [x] **Paso 2:** implementar `marca.py` y escribir los pasos de la marca en `SKILL.md`, `references/marca.md` y
  `references/design-rules.md`.
- [x] **Paso 3:** `comprobar_plugin.py --completo` en verde. Commit «F2: la configuración de marca de cualquier cliente».

### Tarea 1: Apartar el bloque B

**Ficheros:**
- Mover con `git mv` a `docs/bloque-b/` (fuera del paquete y del análisis de skills hasta F5):
  `assets/markdown-templates/{12-especificacion-reconstruccion,13-modernizacion-refactor,14-diseno-objetivo}.md`,
  `agents/{rebuild-architect,target-designer}.md` y `references/modernization-guide.md` de `skills/appian-reverse-engineering/`.
- Modificar en `skills/appian-reverse-engineering/` todo lo que señale la prueba, como mínimo: `SKILL.md` (descripción,
  párrafo inicial, pregunta del objetivo, pasos 4.4 y 4.5, «tratamiento de 13», alta de PQ, entregables, «17 documentos»,
  validación final), `assets/markdown-templates/{00-resumen-ejecutivo,LEEME,11-reglas-negocio}.md`,
  `agents/{pdf-publisher,dashboard-publisher}.md` (sin `modernization` ni `tratamiento[]`; «17 documentos» → la lista
  real), `references/{analysis-workflow,execution-principles,response-format}.md`, `scripts/build_registry.py`,
  `scripts/build_summary.py`, `pruebas/appian-reverse-engineering/test_registry.py`.
- Modificar: `pruebas/comprobar_plugin.py` (`EXTERNAS["appian-refactorizacion"] = "se crea en F5"`).
- Crear: `pruebas/appian-reverse-engineering/test_sin_bloque_b.py`.

**Interfaces:**
- Produce: `registro.json` con las claves exactas `{"hallazgos", "porSeveridad", "porCerteza"}`; `summary.json` sin
  `modernization`; la tabla del registro en 09 queda `ID · Hallazgo · Área · Severidad · Certeza · Dónde`.

- [x] **Paso 1: prueba que falla**

```python
import re

from conftest import SKILL  # carpeta de la skill (Tarea 0)

PROHIBIDO = re.compile(
    r"12-especificacion|13-modernizacion|14-diseno|rebuild-architect|target-designer|modernizacion\.json|"
    r"moderniz|reconstru|[Vv]eredicto|\b(MOD|PQ|DEC|RF|RNF)-|17 documentos|00.{1,3}14\b|"
    r"tratamiento (de|en) 13|\"tratamiento\"|tratamiento\[|\| Tratamiento \|"
    r"|`1[234]`|(?i:moderniz|reconstru)|\b(MOD|PQ)\b|(?:\b(?:de|en|y)|→) 1[234]\b(?![\w ]*(referencias|interfaces|constantes|tareas))|\| (\d\d, )*1[234] [|(]")

def test_ingenieria_inversa_no_menciona_el_bloque_b():
    malos = [f"{p.relative_to(SKILL)}:{n}" for p in SKILL.rglob("*") if p.suffix in (".md", ".py", ".json")
             for n, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if PROHIBIDO.search(l)]
    assert malos == []
```

  Y en `test_registry.py`: `assert set(reg) == {"hallazgos", "porSeveridad", "porCerteza"}`.
- [x] **Paso 2:** en `pruebas/appian-reverse-engineering/`, `python3 -m pytest -q test_sin_bloque_b.py test_registry.py`
  → FALLA con la lista de ficheros y líneas.
- [x] **Paso 3:** quitar el bloque B de cada fichero de la lista. La prueba no necesita excepciones: el `docs/` de la
  skill y sus pruebas ya salieron de ella en la Tarea 0.
- [x] **Paso 4:** descripción nueva del SKILL.md (se afina en la Tarea 28):
  «Ingeniería inversa de aplicaciones Appian: lee la aplicación en vivo por el Dev MCP, en solo lectura, y documenta
  cómo está hecha para que el equipo la entienda: funcional, arquitectura, datos, seguridad, integraciones, APIs,
  batches, procesos, pantallas, reglas de negocio, inventario y anexo con las definiciones, cada dato con su evidencia.
  Úsala para entender, documentar o hacer el onboarding de una aplicación Appian existente, o cuando se pida su modelo
  de datos, sus integraciones, procesos, pantallas o reglas, aunque no se diga «ingeniería inversa». No juzga ni
  propone cómo rehacerla (appian-refactorizacion), no escribe requisitos ni especificaciones (appian-functional-analyst),
  no dibuja (appian-diagramas-bpmn) y no crea ni modifica objetos.»
- [x] **Paso 5:** `python3 -m pytest -q` en verde y `python3 pruebas/comprobar_plugin.py` con 0 errores.
- [x] **Paso 6:** commit «F2: el bloque B sale de ingeniería inversa».

### Tarea 2: Salida y extracción dentro del proyecto (D4)

**Ficheros:**
- Modificar: `scripts/rutas.py`, `scripts/privacidad.py` (recibe de `build_annex.py` `USER_KEY`, `EMAIL`, `users_seen`,
  `users_in`, `user_labels`, `scrub` y `scrub_text`, y también `sensitive()` y lo que usan: `URL_CREDS`, `MASKED`,
  `URL_HOST`, `INTERNAL_HOST`, `USER_PH` y `load`, para que no haya importación circular), `scripts/build_annex.py` (los
  importa), `scripts/devmcp_extract.py` (escribe ya saneado y con rutas cortas), `scripts/build_model.py` (misma ruta
  corta), `SKILL.md` («Argumentos», «Dos carpetas» pasa a una, y puntos 6 y 11 de la validación final), la nota sobre
  `appian-docs/_trabajo/<PREFIJO>/` de `references/response-format.md` y las menciones a `_trabajo` de `references/` y
  `agents/`.
- Modificar también lo que aún dice que la extracción va aparte: `assets/markdown-templates/LEEME.md`,
  `references/security-rules.md`, `references/presentation-rules.md` y, en `SKILL.md`, la fase 3.3 y el punto 4 de la
  validación final.
- Modificar en `pruebas/appian-reverse-engineering/`: `conftest.py` y lo que da por hecho `_trabajo` (la prueba de
  `_trabajo` de `test_build_model.py`, `test_work_data_outside_deliverables`, entera; el `.gitignore` de
  `test_extract.py:255` y la ruta de `test_registry.py:17`, con los números de línea de antes de la Tarea 0). También
  la aserción de `lastModifiedBy` de `test_build_model.py`, que pasa a `privacidad.seudonimo(…)`, y lo que usa
  `dx.safe_name(uuid)` en `test_extract.py`, que pasa a `rutas.carpeta_objeto`.
- Crear: `pruebas/appian-reverse-engineering/test_extraccion_en_proyecto.py`.

**Interfaces:**
- `rutas.work_dir(out, crear=False) -> Path`: `<out>/extraccion`, dentro del proyecto. Ya no hay `_trabajo` ni `.gitignore`.
- `rutas.carpeta_objeto(raw: Path, tipo: str, uuid: str) -> Path`: `<raw>/<tipo>/<12 hex del sha1 del uuid>`; la usan
  `devmcp_extract.py` al escribir y `build_model.py` al leer. `mcp_raw/_objects.json` sigue guardando el uuid de cada objeto.
- `privacidad.seudonimo(usuario: str) -> str`: `‹usuario-xxxxxx›`, con los 6 primeros hex del sha256 del usuario en
  minúsculas. El mismo usuario da siempre el mismo seudónimo, así que se puede retomar y `user_labels` sigue agrupando por grupos.
- `privacidad.sanea(data, usuarios: set[str]) -> Any`: después de `mask_secrets`, cambia por su seudónimo los usuarios
  de los campos de `USER_KEY`, de los objetos de tipo usuario y de las constantes de tipo usuario, y los usuarios ya
  conocidos que aparezcan en cualquier texto; los correos pasan a `‹correo›`. `devmcp_extract.py` lo aplica a cada
  respuesta antes de escribirla.
- `devmcp_extract.barrido_final(raw: Path) -> int`: al terminar la extracción, repasa todos los ficheros con la lista
  completa de usuarios (por si un texto se escribió antes de conocer a su usuario) y devuelve cuántos cambió.
- `preflight.json` y `extraction_report.json` guardan del fichero de configuración solo su nombre, no su ruta, y de las
  aplicaciones del entorno solo cuántas hay.
- De la lista de aplicaciones, `mcp_raw/_env/` guarda solo la aplicación elegida (nada si no hay ninguna).
  `datafabric.json` guarda del fichero de configuración solo su nombre.

- [x] **Paso 1: pruebas que fallan.** `interm()` de `conftest.py` usa `rutas.work_dir(self.out)`. En
  `pruebas/appian-reverse-engineering/test_extraccion_en_proyecto.py`:
  - `test_extraccion_dentro_del_proyecto`: tras `extract`, existe `<out>/extraccion/mcp_raw` y no hay nada fuera de `<out>`
    (la carpeta temporal de la prueba solo tiene el proyecto, su `.mcp.json`, el registro de llamadas del simulador y la
    carpeta `home/` del conftest).
  - `test_sin_usuarios_ni_secretos`: ningún fichero de `<out>` contiene los usuarios de `fixture.GROUP_USERS`, `sk_live_`,
    un correo, la ruta de la carpeta de la prueba ni otra aplicación del entorno; aparece `‹usuario-`; y un mismo usuario
    tiene el mismo seudónimo en los miembros del grupo y en el historial.
  - `test_barrido_final`: con una respuesta preparada que cita «ana.garcia» en una expresión, escrita antes de conocer el
    grupo, tras `barrido_final` ya no aparece.
  - `test_rutas_cortas`: ninguna ruta relativa dentro de `<out>/extraccion` pasa de 100 caracteres.
  - `test_retomar`: una segunda `extract` no vuelve a pedir lo que ya está (registro de llamadas del simulador) y
    `build_model.py` funciona igual.
  - `test_ruta_con_espacios`: lo anterior con `out = tmp / "Carpeta con espacios" / "Gestión app" / "as-is"`.
- [x] **Paso 2:** `python3 -m pytest -q pruebas/appian-reverse-engineering/test_extraccion_en_proyecto.py` → FALLA.
- [x] **Paso 3:** implementar y ajustar las pruebas existentes de la lista de ficheros.
- [x] **Paso 4:** `SKILL.md`: salida por defecto `<p>/as-is/` (si la carpeta tiene `proyecto.md` o la da el usuario) o
  `./<PREFIJO>/as-is/`; una sola carpeta, con la extracción en `as-is/extraccion/`, ya saneada; los puntos 6 y 11 de la
  validación final y `response-format.md` lo dicen así.
- [x] **Paso 5:** `python3 -m pytest -q` en verde. Commit «F2: salida y extracción saneada dentro del proyecto».

### Tarea 2b: Nada se oculta

Raúl decidió el 8 de octubre que no se oculte nada: se trabaja en entornos controlados donde toda la información se
puede consumir. La extracción y los documentos llevan los usuarios, los datos de la app y los secretos tal cual. Un
secreto escrito en una constante o en una conexión sigue siendo un hallazgo de seguridad: lo que se va es ocultarlo.

**Ficheros:**
- Borrar `skills/appian-reverse-engineering/scripts/privacidad.py` y lo que añadió la Tarea 2 para sanear: seudónimos,
  huellas (`_huellas.json`), barrido final, `preflight.json` y `datafabric.json` sin rutas, y `_env/` sin la lista de
  aplicaciones. Se queda lo demás de la Tarea 2: la extracción en `<salida>/extraccion`, `rutas.carpeta_objeto` con su
  tope de longitud y lo que arregló al retomar.
- Modificar en `skills/appian-reverse-engineering/`:
  - `scripts/build_annex.py`, sin saneado: ni `‹usuario›`, ni `‹correo›`, ni `‹secreto›`, ni `‹host interno›`;
  - `scripts/devmcp_extract.py` y `scripts/build_model.py`, que escriben y leen tal cual;
  - `references/presentation-rules.md`: la Regla 8 pierde los usuarios, el correo y el render sin valores;
  - `references/execution-principles.md`: el principio 11 pasa a «un secreto escrito en la app es un hallazgo»;
  - `references/security-rules.md`: cómo se detecta y se registra un secreto, sin ocultarlo;
  - `SKILL.md`, `references/{lectura-mcp-raw,analysis-workflow,response-format}.md`, los agentes y las plantillas:
    todo lo que manda ocultar o comprobar que no haya usuarios, valores o secretos.
- Modificar en `pruebas/appian-reverse-engineering/` las pruebas que exigían el saneado.

- [x] **Paso 1: pruebas que fallan.** `test_tal_cual`: tras `extract` y `build_annex.py`, los usuarios de
  `fixture.GROUP_USERS`, un correo y el valor de la constante con la clave de API aparecen como los devuelve el
  simulador, en la extracción y en el anexo; y `test_sin_ocultar`: ningún texto de la skill pide seudónimos, `‹usuario›`,
  `‹correo›`, `‹secreto›` ni «sin usuarios». Siguen `test_extraccion_dentro_del_proyecto`, `test_rutas_cortas`,
  `test_retomar` y `test_ruta_con_espacios`. → FALLA.
- [x] **Paso 2:** quitar el saneado y reescribir los textos de la lista.
- [x] **Paso 3:** `python3 -m pytest -q pruebas/appian-reverse-engineering` y `comprobar_plugin.py --completo` en verde.
  Commit «F2: nada se oculta en ingeniería inversa».

### Tarea 3: Alta de ingeniería inversa en el plugin

Sus pruebas ya las ejecuta `comprobar_plugin.py --completo` desde la Tarea 0; aquí entra en las reglas comunes.

**Ficheros:** Modificar `README.md` (mapa de skills); `skills/appian-reverse-engineering/SKILL.md` (apartado «## Dudas
de Appian» con el bloque común del analista); `references/docs-mcp-usage.md` (solo lo propio: tope de 30 consultas y
caché); `pruebas/appian-reverse-engineering/test_scripts.py` (las pruebas de `detect_secrets.sh` se saltan si no hay
`bash`; `encoding="utf-8"` en toda lectura, también en cada `read_text()` sin `encoding` de `test_registry.py`);
`pruebas/comprobar_plugin.py` (`REGLA_DOCS` incluye `appian-reverse-engineering`).

- [x] **Paso 1:** añadir `appian-reverse-engineering` a `REGLA_DOCS` y ejecutar `python3 pruebas/comprobar_plugin.py --completo`
  → FALLA («falta el apartado Dudas de Appian»).
- [x] **Paso 2:** hacer los cambios de la lista.
- [x] **Paso 3:** `python3 pruebas/comprobar_plugin.py --completo` → «Prueba de appian-reverse-engineering: bien», 0 errores.
- [x] **Paso 4:** commit «F2: ingeniería inversa en la prueba completa del plugin». Cierre de fase: revisión
  independiente de la rama y merge a `main`.

---

## F3 · Precisa y sin relleno

### Tarea 4: Reglas de prosa en un solo sitio

**Ficheros:**
- Crear: `skills/appian-functional-analyst/scripts/redaccion.py`.
- Modificar: `skills/appian-functional-analyst/scripts/comprobar.py` (usa `redaccion.py`; mismo comportamiento) y
  `pruebas/appian-functional-analyst/selftest.py`; `skills/appian-reverse-engineering/references/presentation-rules.md`: se quedan el esqueleto
  de documento (TL;DR, Vista, Detalle, Hallazgos, Cobertura) y las reglas de evidencia y marcas de certeza;
  las de prosa remiten a `appian-functional-analyst/references/redaccion.md`.

**Interfaces:**
- `redaccion.muletillas(ruta=None) -> list[str]` (líneas `- «x» →` de `references/redaccion.md`, normalizadas),
  `redaccion.frases(texto) -> list[str]`, `redaccion.MAX_PALABRAS = 35`,
  `redaccion.parrafos_repetidos(textos: dict[str, str], minimo=20) -> list[tuple[str, list[str]]]`.

- [x] **Paso 1:** en el selftest del analista: con un `redaccion.md` temporal de dos muletillas, `muletillas(ruta)` las
  devuelve normalizadas; `parrafos_repetidos` encuentra un párrafo de 25 palabras que está en dos textos y no uno de 15.
  → FALLA (no existe el módulo).
- [x] **Paso 2:** crear `redaccion.py` moviendo `muletillas()` y `frases()` de `comprobar.py`.
- [x] **Paso 3:** selftest del analista sin fallos y con los mismos avisos que antes en `autorizaciones`. Recortar
  `presentation-rules.md`. Commit «F3: reglas de prosa en un solo sitio».

### Tarea 5: `as-is/datos/`, el contrato con las demás skills

**Ficheros:**
- Crear: `skills/appian-reverse-engineering/scripts/build_datos.py`, `references/datos.md`, `pruebas/appian-reverse-engineering/test_datos.py`.
- Modificar: `SKILL.md` (fase 6: `build_datos.py <salida>` después de `build_summary.py`).

**Interfaces:**
- `build_datos.construir(salida: Path) -> dict` escribe en `<salida>/datos/`:
  - `inventario.json`: `{"aplicacion": {"nombre", "prefijo", "uuid"}, "objetos": [{"nombre", "tipo", "uuid", "anexo",
    "tambien"}]}`; `anexo` es la ruta de su ficha relativa a `<salida>` y `tambien` los nombres que no son objetos pero
    se citan con él (tabla, vistas, campos, acciones de un record type).
  - `dependencias.json`: `{"aristas": [{"de", "a", "donde"}]}` con nombres de objeto (de `graph.json`).
  - `hallazgos.json`: `{"hallazgos": [{"id", "titulo", "area", "severidad", "certeza", "objetos", "documento", "evidencia"}]}`
    (de `registro.json`, sin duplicados).
  - `procesos.json`: `{"procesos": [{"nombre", "json", "nodos", "ejecuciones"}]}`, con `json` = ruta del JSON de
    diagrama en `08-procesos-bpmn/`.
- Lo usan las Tareas 6, 14, 19 y 20. La Tarea 8b añade `sin-verificar.json` y dos campos, sin cambiar nada de lo de aquí.

- [ ] **Paso 1:** `test_datos.py::test_datos_formato`: tras el flujo del simulador con un `hallazgos/prueba.json` de un
  hallazgo sobre `DEM_ERP_API_TOKEN`, existen los cuatro ficheros con sus claves, cada objeto de cada hallazgo está en
  el inventario, y la tabla `DEM_SOLICITUD` y la vista «Resumen» están en `tambien` de `DEM Solicitud`. → FALLA.
- [ ] **Paso 2:** implementar y documentar el formato en `references/datos.md`. **Paso 3:** pytest en verde. Commit.

### Tarea 6: `comprobar_asis.py`

**Ficheros:**
- Crear: `scripts/comprobar_asis.py`, `pruebas/appian-reverse-engineering/test_comprobar_asis.py`, `assets/presupuesto-palabras.json`.
- Modificar: `SKILL.md` (fase 8: sin errores de `comprobar_asis.py` antes de responder).

**Interfaces:**
- `comprobar(salida: Path) -> tuple[list[str], list[str]]` (errores, avisos). CLI: 0 sin errores, 1 con errores.
- Errores (los de tablas y de `{{` no se miran en `anexo/` ni en `extraccion/`: una lista anidada de SAIL lleva `{{`):
  - un nombre entre comillas invertidas que empieza por el prefijo de la app (seguido de `_` o espacio, cortado en `.`
    o `#`) y no está ni en `objetos[].nombre`, ni en `objetos[].tambien`, ni es `aplicacion.nombre`;
  - una tabla con columna «Certeza» sin columna «Evidencia», salvo la del registro de 09, entre `<!-- registro:inicio -->`
    y `<!-- registro:fin -->`, cuyas filas enlazan en «Dónde» al documento que tiene la evidencia; o una fila cuya
    evidencia no enlaza a un fichero existente de `anexo/`, o una certeza fuera de ✅ 🔵 ❓;
  - cifras de `00` («N objetos», «N process models», «N interfaces», «N record types») distintas de las de
    `as-is/extraccion/summary.json`;
  - `{{` sin sustituir o un enlace relativo a un fichero que no existe.
- Avisos (con `redaccion.py` del analista, importado desde `<skill>/../appian-functional-analyst/scripts`): muletillas,
  frases de más de 35 palabras, párrafos de 20 palabras o más repetidos en dos documentos y documentos por encima de su
  presupuesto (`presupuesto-palabras.json`: palabras base más palabras por objeto de su tipo).

- [ ] **Paso 1: pruebas que fallan**, con una carpeta `as-is` mínima creada en la prueba: `test_objeto_inventado`,
  `test_tabla_y_vista_no_son_inventadas`, `test_certeza_sin_evidencia`, `test_evidencia_rota`, `test_cifra_distinta`,
  `test_marcador_y_enlace_roto`, `test_muletilla_es_aviso` (sale 0), `test_documento_correcto` (0 errores y 0 avisos) y
  `test_ruta_con_espacios`.
- [ ] **Paso 2:** implementar. **Paso 3:** pytest en verde. Commit «F3: comprobar_asis.py».

### Tarea 7: Aplicación ficticia mal hecha a propósito

**Ficheros:**
- Crear: `pruebas/appian-reverse-engineering/mock_devmcp/fixture_mal_hecha.py`, `pruebas/appian-reverse-engineering/test_fixture_mal_hecha.py`,
  `pruebas/evaluaciones/aplicacion-ficticia/{malas-practicas.json,preguntas.json,ocultas/}`.
- Modificar: `pruebas/appian-reverse-engineering/mock_devmcp/lcp_mcp_server_mock.py` (módulo de `$MOCK_APP`, por defecto `fixture`; el prefijo sale
  del objeto aplicación del fixture y no de `"DEM"` fijo en las líneas 170 y 239; tipo `DATA_STORE` en `_app_objects`;
  definición para `DATA_TYPE` y `DATA_STORE`) y `pruebas/appian-reverse-engineering/mock_devmcp/appian_mcp_server_mock.py`
  (también `$MOCK_APP`, y toma `COUNTS` de ese módulo: los de DEM pasan a `fixture.py`).

**Interfaces:**
- `fixture_mal_hecha` expone lo mismo que `fixture`: `APP_KEY`, `REFS`, `DEPENDENTS_SUPPORTED`, `GROUP_USERS`,
  `PM_HISTORY`, `VALIDATION_ISSUES`, `COUNTS` y `build()`. Usa las claves `G_ADM` y `G_USR`, que el simulador pide para
  los grupos por defecto de la aplicación.
- Aplicación «MNT Mantenimiento de Instalaciones», prefijo `MNT`, unos 45 objetos, con estas 11 malas prácticas
  (`malas-practicas.json`: `id`, `descripcion`, `objetos`, `capa`, `bp` = «doc §sección», fijada consultando
  `appian-best-practices/scripts/seccion.py`):
  1. `MNT_IF_ListadoOrdenes`: `a!queryEntity` sin filtros ni paginación.
  2. `MNT_IF_FormularioOrden`: más de 3.000 líneas que repiten la misma lógica.
  3. `MNT_IF_Panel`: seguridad solo con `showWhen` por grupo; `MNT Orden` sin seguridad de registro.
  4. `MNT_PM_GestionOrden`: 130 nodos sin subprocesos.
  5. `MNT_PM_Recordatorio`: temporizador cada 5 minutos que busca órdenes pendientes.
  6. `MNT_URL_ERP_PRE`: URL de un entorno escrita en una constante.
  7. `MNT_ERP_API_TOKEN`: clave de API en una constante.
  8. `MNT_INT_ConsultarERP`: integración sin tratamiento de errores ni reintentos.
  9. `ReglaCalculoPlazo` y `calcFecha`: sin prefijo ni convención de nombres.
  10. `MNT_IF_Tecnicos`: una consulta dentro de `a!forEach` por cada fila.
  11. `MNT_CS_Proveedores`: connected system con `authType` explícito sin autenticación y la URL de un entorno de
      desarrollo, en un entorno que no es de desarrollo.
- Lo que no se puede verificar (Tarea 8b): las definiciones de `MNT_IF_FormularioOrden`, `MNT_PM_GestionOrden` y
  `MNT_IF_Panel` llaman a `rule!CMN_FormatearFecha`, `rule!CMN_UsuarioActual` y `rule!CMN_IF_Cabecera`, de otra
  aplicación ficticia (un marco común con prefijo `CMN`) que no está en la extracción. No hace falta una herramienta de
  dependencias salientes: la del Dev MCP que se conoce da quién usa un objeto, y si el real trae otra, está sin verificar.
- Con `MOCK_APP=fixture_mal_hecha`, el entorno simulado es de preproducción (`LCP_URL` = `https://pre.mnt.example.org`,
  que pasa `test_fixture_mal_hecha.py` a `add_devmcp` y pone el `.mcp.json` del proyecto de prueba de la Tarea 9); la
  URL de `MNT_CS_Proveedores` es de desarrollo (`https://proveedores-dev.example.org`). Las dos, en un dominio de
  ejemplo público, como el fixture DEM: un `.local` se publica como host interno.
- Lo que pregunta un recién llegado: CDT `MNT_OrdenDTO` con su data store, record types `MNT Orden`, `MNT Técnico` y
  `MNT Estado`, grupos `MNT Administradores`, `MNT Técnicos` y `MNT Supervisores`, un site de tres páginas, un proceso
  sin ejecuciones `MNT_PM_Antiguo` y usuarios ficticios en los grupos, en una constante y como asignados.
- `preguntas.json`: 22 preguntas `{"id": "Q-01", "pregunta", "respuestas": [formas aceptadas], "tipo": "objeto|numero|si-no|lista"}`,
  al menos una por documento 01–11. Por ejemplo: «¿Qué proceso lanza la acción "Nueva orden"?» → `MNT_PM_GestionOrden`;
  «¿Cada cuánto está programado el recordatorio?» → «5 minutos»; «¿Qué constante cambia por entorno?» → `MNT_URL_ERP_PRE`;
  «¿Qué proceso no se ha ejecutado nunca?» → `MNT_PM_Antiguo`; «¿Qué grupos ven la página Administración?» → `MNT Administradores`.
  Q-21 mide la Tarea 8b: «¿Qué no se pudo verificar y qué hace falta para hacerlo?» → `lista` con
  `respuestas` = `["CMN_FormatearFecha", "CMN_UsuarioActual", "CMN_IF_Cabecera", ["export", "acceso"]]` (un elemento que
  es una lista son formas alternativas). Q-22: «¿Qué connected system no tiene autenticación?» → `MNT_CS_Proveedores`.
- `ocultas/`: 7 preguntas y 3 malas prácticas más, escritas por un agente aparte con solo el fixture delante.

- [ ] **Paso 1:** `test_fixture_mal_hecha.py`: con `MOCK_APP=fixture_mal_hecha`, `extract` + `build_model.py` dan al
  menos 40 objetos y prefijo `MNT`; el CDT y el data store tienen `detail: "full"`; cada objeto de `malas-practicas.json`
  y cada respuesta de tipo `objeto` de `preguntas.json` está en `inventory.json`; los tres objetos `CMN` están en la
  definición de quien los usa y no en `inventory.json`; `MNT_CS_Proveedores` llega con su `authType` y su URL; la URL
  del entorno no es de desarrollo; y el simulador DEM da lo mismo que antes. → FALLA.
- [ ] **Paso 2:** escribir la aplicación, los cambios del simulador y los JSON. **Paso 3:** pytest en verde.
- [ ] **Paso 4:** commit «F3: aplicación ficticia mal hecha» y etiqueta `f3-antes` (punto de partida de la Tarea 9).

### Tarea 8: Preguntas primero, hechos y no consejos

**Ficheros:**
- Modificar: `assets/markdown-templates/**/*.md` (00–11, LEEME, INVENTARIO y `08-procesos-bpmn/pm-template.md`), los
  cinco agentes de análisis, `references/{execution-principles,security-rules,appian-objects-guide}.md` (en la guía de
  objetos, el dato de los 50 nodos se queda), `scripts/build_registry.py` (aviso si un hallazgo trae `recomendacion`) y
  `pruebas/appian-reverse-engineering/test_registry.py`.
- Crear: `pruebas/appian-reverse-engineering/test_plantillas.py`.

- [ ] **Paso 1: pruebas que fallan.** `test_plantillas.py`:
  - `test_cada_plantilla_empieza_por_sus_preguntas`: tras el título, una línea `> **Responde a:**` con 2 a 5 preguntas.
  - `test_toda_tabla_con_certeza_tiene_evidencia`.
  - `test_sin_recomendaciones`: ni plantillas, ni agentes, ni `references/` dicen «recomendaci» o «recomienda».
  - En `test_registry.py`, `test_recomendacion_es_aviso`.
- [ ] **Paso 2:** reescribir: las preguntas que responde cada documento, tablas antes que prosa, columna «Evidencia»
  donde hay «Certeza», sin explicar conceptos de Appian (se enlaza la documentación), sin repetir datos de otro
  documento y sin consejos (la frase de 09 «Appian recomienda dividir…» se va; el dato «procesos de más de 50 nodos» se queda).
- [ ] **Paso 3:** pytest en verde. Commit «F3: plantillas que responden preguntas».

### Tarea 8b: Disciplina de evidencia

Lo aprobado en la evaluación de encaje del 7 de octubre, adaptado a lo que la skill ya hace (✅/🔵/❓, evidencia
enlazada al anexo, «dato ausente no es defecto»). Lo que no se pudo verificar queda registrado con lo que hace falta para
resolverlo; nada se da por inexistente sin decir dónde se buscó; la definición no se toma por la ejecución; y cada
revisión cierra las preguntas con las que empezó. Solo añade: ningún fichero ni campo de `as-is/datos/` (Tarea 5) cambia
de nombre. Lo único que cambia es la marca de inferido, que pasa de 🔵 a 🔶, la del analista; el JSON sigue diciendo `inferido`.

**Ficheros:**
- Modificar en `skills/appian-reverse-engineering/`:
  - `references/execution-principles.md`:
    - el principio 3 vale también para objetos y dependencias: «no encontrado en <ámbito consultado>» (aplicación,
      entorno o herramienta), nunca «no existe»;
    - el principio 4 admite «según su nombre» solo cuando ni la definición ni otra respuesta dicen lo que se afirma
      (sigue valiendo, por ejemplo, para el actor que se deduce del nombre de un grupo);
    - principio nuevo, «Diseño no es ejecución»: frecuencia, fallos, tiempos y volúmenes solo con evidencia de ejecución
      (`@history`, recuentos del data fabric, Appian MCP Server); si no, «configurado para…» ✅ y lo de la ejecución ❓;
    - §3, «Registro de hallazgos»: `base` (las evidencias de las que sale) es obligatorio con `certeza: inferido`;
    - sección nueva «Sin verificar»: qué es un NV; lo registra el propietario del área y el orquestador une los
      duplicados en la pasada de coherencia (`duplicadoDe`), como con los hallazgos; una limitación global va en «Qué
      no incluye» de LEEME, no como NV;
    - una regla de trabajo: una llamada fuera del script de extracción —al Dev MCP, con las herramientas que permite
      `scripts/devmcp_policy.json`, o al Appian MCP Server, solo con lo que permite `references/data-fabric.md`
      (metadatos y recuentos)— responde a una pregunta de la revisión o a un NV. El
      MCP de documentación sigue con sus reglas («Dudas de Appian»);
  - `references/presentation-rules.md` (Regla 7 y checklist con ✅ 🔶 ❓; un ❓ cita su NV cuando lo tiene),
    `references/analysis-workflow.md` y `references/datos.md` (los campos nuevos);
  - lo que remitía a las preguntas abiertas de `12`, que se va en la Tarea 1 (`references/response-format.md` y
    `agents/pdf-publisher.md`), remite a «Sin verificar»;
  - `SKILL.md`: la pregunta única del paso 5 de la fase 0 pide también qué necesita saber el equipo (sin respuesta: qué
    hace, cómo está hecha y qué riesgos tiene), que se guarda en `preguntas` de `output_preferences.json`
    (`{pdf, dashboard, preguntas}`); la fase 6 ejecuta `build_datos.py` después de escribir LEEME, para que rellene su
    tabla «Sin verificar»; la fase 8 cierra cada pregunta, vuelve a ejecutar `build_datos.py` si ha creado un NV y la
    respuesta al usuario dice qué preguntas quedan abiertas;
  - plantillas: `LEEME.md` («Preguntas de esta revisión» tras el TL;DR; «Sin verificar», generada; `NV-<ÁREA>-NN` en
    «Identificadores»; leyenda con 🔶) e `INVENTARIO.md` («Para qué» de un objeto sin descripción: una frase sacada de
    su definición, 🔶, y «🔶 según su nombre» solo si no la tiene; «Cobertura de la extracción» suma las herramientas
    usadas y omitidas, con el motivo, de `extraction_plan.json` y `extraction_report.json`);
  - los agentes de análisis (registran sus NV y el `base` de sus hallazgos inferidos);
  - `scripts/build_model.py`: un `rule!` o `cons!` cuyo nombre no está en la aplicación crea un nodo externo sin uuid,
    con su nombre y su tipo («llamado con rule!», porque puede ser regla, interfaz, integración o decisión, o
    constante); si una herramienta de dependencias ya trajo ese objeto con uuid, se une por nombre en un solo nodo; el
    tipo de todos los nodos externos pasa por `canon_ext`;
  - `scripts/build_registry.py` (🔶; error si un hallazgo `inferido` no trae `base`), `scripts/build_datos.py` y
    `scripts/comprobar_asis.py`;
  - 🔵 → 🔶 en toda la skill (plantillas, agentes, referencias y scripts) y en sus pruebas.
- Modificar `pruebas/comprobar_plugin.py`: error si una skill usa 🔵 como marca.
- Modificar `pruebas/appian-reverse-engineering/{test_datos.py,test_registry.py}` (cinco ficheros en `datos/`; `base`).
- Crear: `pruebas/appian-reverse-engineering/test_evidencia.py`.

**Interfaces:**
- `<trabajo>/sin-verificar/<agente>.json`: `[{"id": "NV-ARQ-01", "pregunta", "porQue", "queHaceFalta", "aQuien",
  "dondeSeBusco", "objetos": [], "indicios", "estado", "documento", "duplicadoDe"}]`:
  - `id` cumple `^NV-[A-Z]{2,4}-\d{2,3}$`, con el prefijo de área de los hallazgos (no «PV»: en Appian son las
    variables de proceso);
  - `queHaceFalta` empieza por acceso, export, permiso, entorno o negocio; `estado` es abierto, parcial o resuelto;
  - `objetos`: los de la aplicación afectados y los de fuera; `duplicadoDe` solo lo pone el orquestador.
- `build_datos.construir()` valida los NV como `build_registry.py` valida los hallazgos (error con un `id`, un `estado` o
  un `queHaceFalta` fuera de formato), y además escribe:
  - `datos/sin-verificar.json`: `{"sinVerificar": [...]}`, sin duplicados;
  - en `datos/dependencias.json`, `fueraDeLaAplicacion: [{"nombre", "tipo", "usadoPor": [], "usa": [], "nv"}]`, de los
    nodos externos del grafo: `usadoPor` son los objetos de la aplicación que lo llaman y `usa`, los que él llama; `nv`,
    el NV que lo tiene en `objetos`. No se llama `externos` porque en la skill de diagramas son los participantes externos;
  - en `datos/hallazgos.json`, `base` en los de certeza `inferido`;
  - en LEEME, entre `<!-- sin-verificar:inicio -->` y `<!-- sin-verificar:fin -->`, la tabla
    `ID · Pregunta · Qué hace falta · A quién · Estado`.
- LEEME, «Preguntas de esta revisión»: `Pregunta · Estado · Dónde se responde`. Estado = Respondida, Parcial o Sin
  resolver. Dónde = un enlace a un documento, el ID de un NV o, si lo impide una limitación global, un enlace a «Qué no
  incluye».
- `comprobar_asis.py`:
  - errores: un `NV-…` citado que no está en `sin-verificar.json`; una pregunta de `preguntas` que no está en la tabla,
    o está sin estado, o Parcial o Sin resolver sin NV ni enlace a «Qué no incluye»; una certeza fuera de ✅ 🔶 ❓;
  - avisos: «no existe», «no existen» o «no hay ningún» en un entregable (no en `anexo/` ni en `extraccion/`); «según su
    nombre» en una fila de INVENTARIO cuyo objeto tiene `detail: "full"` en `extraccion/inventory.json`; un hallazgo
    `inferido` de severidad Alta con menos de dos evidencias en `base`; un objeto de `fueraDeLaAplicacion` con
    `usadoPor` y sin NV (los que solo usan la aplicación no son nada sin verificar).

- [ ] **Paso 1: pruebas que fallan.** `test_evidencia.py`, con el simulador (variante A, y `MOCK_APP=fixture_mal_hecha`
  donde se dice):
  - `test_sin_verificar_formato`: un `sin-verificar/prueba.json` llega validado a `datos/` y a la tabla de
    LEEME; con un `id` o un `estado` fuera de formato, error;
  - `test_nv_inexistente`, `test_pregunta_sin_cerrar` y `test_pregunta_que_falta`: errores; una pregunta Parcial con
    enlace a «Qué no incluye» no da error;
  - `test_negativo_sin_ambito`: aviso en un entregable y nada en `anexo/`;
  - `test_segun_su_nombre_con_definicion`: aviso solo en la fila de un objeto con `detail: "full"`;
  - `test_fuera_de_la_aplicacion` (`fixture_mal_hecha`): los tres objetos `CMN` de la Tarea 7 salen en
    `fueraDeLaAplicacion` con su `usadoPor`, y sin NV dan aviso;
  - `test_base_en_inferidos`: un `inferido` sin `base` da error en `build_registry.py`; uno Alta con una evidencia,
    aviso; con dos, nada;
  - `test_marca_de_inferido`: ningún 🔵 en la skill (la prueba lo escribe como `"\U0001F535"`) y los JSON siguen
    diciendo `inferido`. → FALLA.
- [ ] **Paso 2:** implementar y reescribir reglas, plantillas y agentes.
- [ ] **Paso 3:** pytest y `comprobar_plugin.py --completo` en verde. Commit «F3: disciplina de evidencia».

### Tarea 9: Evaluación del recién llegado (antes y después)

**Ficheros:**
- Crear: `pruebas/evaluaciones/recien-llegado/{README.md,puntuar.py,palabras.py,evidencia.py}` y, en
  `docs/evaluaciones.md`, sus resultados. El proyecto de prueba `MNT` se crea en `$PROYECTOS_PRUEBA/MNT/`, fuera del repositorio; las Tareas 15 y
  22 trabajan sobre él.

**Interfaces:**
- `puntuar.py <respuestas.json> <as-is> [--ocultas] [--minimo N] [--obligatorias Q-21,…]`: `respuestas.json` =
  `[{"id": "Q-01", "respuesta", "evidencia": "ruta#ancla"}]`. Acierta si la respuesta normalizada está entre las
  aceptadas y el fichero de la evidencia existe y no está en `extraccion/`; una de tipo `lista`, si están todos sus
  elementos (de un elemento que es una lista de formas, basta una). Imprime aciertos y
  sale 0 con `--minimo` aciertos o más (por defecto, el 90 %) y todas las obligatorias bien.
- `evidencia.py <as-is>`: en `datos/`, `MNT_CS_Proveedores` tiene un hallazgo `verificado` con evidencia a su ficha del
  anexo (la evidencia `mcp:<tipo>/<nombre>#…` de `hallazgos.json` se pasa a su ficha con `inventario.json → anexo`), y
  los tres `CMN` están en `fueraDeLaAplicacion` con un NV cuyo `queHaceFalta` empieza por export o acceso; y ningún
  entregable dice «no existe». Sale 0 si se cumple todo.
- `palabras.py <as-is>`: palabras por documento y total.

- [ ] **Paso 1:** «antes»: desde `f3-antes`, un agente genera `as-is/` de la aplicación ficticia siguiendo el SKILL.md
  contra el simulador, en `$PROYECTOS_PRUEBA/MNT-antes/`, y pasa `comprobar_asis.py` solo como informe, sin exigir 0
  errores (la columna «Evidencia» llega con la Tarea 8); otro, que solo lee su `as-is/` sin `extraccion/`, responde las
  22 preguntas y las 7 ocultas. Aciertos y palabras a `docs/evaluaciones.md`.
- [ ] **Paso 2:** «después», igual con las Tareas 8 y 8b hechas, en `$PROYECTOS_PRUEBA/MNT/`. Criterio:
  `puntuar.py --minimo 20 --obligatorias Q-21` y, con las ocultas, `--minimo 6`; `evidencia.py` sale 0; 0 errores de
  `comprobar_asis.py`; menos palabras que «antes».
- [ ] **Paso 3:** si dos documentos se responden el uno al otro (LEEME con 00, 05 con 06), se unen —plantillas,
  entregables del SKILL.md, publicadores y pruebas de las Tareas 8 y 8b— y se repite el Paso 2. Las secciones de la
  Tarea 8b van al documento que quede, y `build_datos.py` escribe en él. Si se unen LEEME y 00, cambian también
  `scripts/comprobar_asis.py` y `test_comprobar_asis.py::test_cifra_distinta`, que buscan las cifras en `00`.
- [ ] **Paso 4:** commit. Cierre de fase: revisión y merge.

---

## F4 · Un solo exportador BPMN y un solo pintor

### Tarea 10: Datos de Appian en el diagrama y en el BPMN

**Ficheros:**
- Modificar en `skills/appian-diagramas-bpmn/scripts/`: `drawio_modelo.py`, `diagrama.py` (`_limpio` conserva las
  claves nuevas) y `bpmn_export.py`; `SKILL.md` y `pruebas/appian-diagramas-bpmn/selftest.py`.
- Crear: `pruebas/appian-diagramas-bpmn/datos/semantico.json` (el proceso de `proceso_semantico.bpmn` de ingeniería inversa).

**Interfaces:**
- JSON del proceso, claves opcionales: en un paso `nodo` (id del nodo en Appian), `temporizador` (expresión) y
  `proceso_llamado` (nombre); en un flujo `condicion` (expresión). Tipo nuevo de paso `error` (sobre el borde de su
  tarea con un flujo discontinuo, como `temporizador`).
- `.drawio`: esas claves van como atributos de un `<object>` que envuelve la celda (en draw.io, «Editar datos») y
  `drawio_modelo.leer()` las devuelve.
- BPMN: `nodo` → `<bpmn:documentation>nodo N</bpmn:documentation>`; `temporizador` →
  `<bpmn:timeCycle xsi:type="bpmn:tFormalExpression">`; `proceso_llamado` → `calledElement`; `condicion` →
  `<bpmn:conditionExpression xsi:type="bpmn:tFormalExpression">`; `error` → `<bpmn:errorEventDefinition/>` con
  `cancelActivity="true"` (el temporizador y el mensaje de borde siguen sin interrumpir).

- [ ] **Paso 1:** en el selftest de diagramas, `crear` + `bpmn` de `semantico.json`: documentación «nodo 1» en el
  inicio; `conditionExpression` «pv!ok» con su `xsi:type` en el flujo «Sí»; `default` en la puerta; evento de error que
  interrumpe, con `attachedToRef` a «Guardar»; un `BPMNShape` por nodo y carril y un `BPMNEdge` con dos o más puntos por
  flujo; los hijos del inicio en orden (`documentation`, `outgoing`); dos exportaciones iguales; `leer()` devuelve
  `nodo` y `condicion`; `comparar --aceptar` no las pierde. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** selftest de diagramas en verde. Commit «F4: datos de Appian en el diagrama y en el BPMN».

### Tarea 11: Un solo pintor Mermaid

**Ficheros:**
- Mover: `skills/appian-functional-analyst/scripts/render_mermaid.py` → `skills/appian-diagramas-bpmn/scripts/mermaid.py`.
- Modificar: `mermaid.py` (`MERMAID_JS` = su propia `assets/mermaid.min.js`; opción `--md`), el selftest de diagramas y,
  en el analista, `SKILL.md`, `references/mermaid-diagrams.md`, `references/actualizacion.md` y `pruebas/appian-functional-analyst/selftest.py`.

**Interfaces:**
- `mermaid.py <ficheros .mmd> [-o carpeta] [--check] [--svg] [--width N] [--md fichero.md …]`: con `--md` valida cada
  bloque ```mermaid y dice en qué línea empieza el que falla; con solo `--md`, los `.mmd` son opcionales. Sale 0 bien,
  1 sintaxis, 2 falta un requisito.

- [ ] **Paso 1:** selftest de diagramas: `--check` de un `.mmd` válido → 0 y de uno inválido → 1; `--md` de un
  Markdown con dos bloques, uno roto en la línea 12 → 1 y «línea 12» en la salida. → FALLA.
- [ ] **Paso 2:** mover, añadir `--md` y cambiar las rutas del analista. **Paso 3:** los dos selftest en verde. Commit.

### Tarea 12: Ingeniería inversa dibuja con la skill de diagramas, también sin navegador

**Ficheros:**
- Modificar en diagramas: `scripts/colocacion.py` (colocación de reserva sin navegador: capas de izquierda a derecha y
  un carril por perfil, la de `bpmn_layout.py`), `scripts/diagrama.py` (`crear` sin navegador escribe el `.drawio`, avisa
  «sin PNG» y sale con 2 solo por la imagen), `scripts/navegador.py` (`DIAGRAMAS_SIN_NAVEGADOR=1` simula que no hay)
  y `pruebas/appian-diagramas-bpmn/selftest.py`.
- Modificar en ingeniería inversa: `agents/process-modeler.md` (escribe `08-procesos-bpmn/<slug>.json` con `nodo`,
  `temporizador`, `proceso_llamado` y `condicion`; después `diagrama.py crear` y `diagrama.py bpmn`),
  `references/bpmn-mapping.md` (nodo de Appian → tipo de paso y claves), `references/mermaid-rules.md` (qué se dibuja;
  sin las reglas del validador), `SKILL.md` (fase 5: `mermaid.py --md` en cada documento con Mermaid; sin navegador se
  dice y se sigue), `agents/{pdf-publisher,dashboard-publisher}.md` (imágenes de `mermaid.py --svg` y de los `.png`),
  `pruebas/appian-reverse-engineering/test_scripts.py` (quedan las pruebas de `detect_secrets`).
- Borrar: `scripts/bpmn_layout.py`, `scripts/validate_mermaid.py`, `scripts/render_diagrams.sh`,
  `pruebas/appian-reverse-engineering/test_bpmn_layout.py`, `pruebas/appian-reverse-engineering/datos/proceso_semantico.bpmn`.
- Crear: `pruebas/appian-reverse-engineering/test_una_pieza.py`.

- [ ] **Paso 1: pruebas que fallan.** Selftest de diagramas con `DIAGRAMAS_SIN_NAVEGADOR=1`: `crear` de
  `semantico.json` escribe un `.drawio` sin pasos solapados, sale con 2 y dice «sin PNG»; `bpmn` de ese `.drawio` da un
  BPMN válido. `test_una_pieza.py`: ningún fichero de la skill de ingeniería inversa menciona
  `bpmn_layout`, `validate_mermaid`, `render_diagrams`, `mmdc` ni la vía «.bpmn + Mermaid».
- [ ] **Paso 2:** hacer los cambios. **Paso 3:** pytest y `comprobar_plugin.py --completo` en verde.
- [ ] **Paso 4:** commit «F4: ingeniería inversa dibuja con la skill de diagramas». Cierre de fase: revisión y merge.

---

## F5 · Refactorización

### Tarea 13: La skill

**Ficheros:**
- Crear desde `docs/bloque-b/`: `skills/appian-refactorizacion/SKILL.md`, `assets/plantillas/propuesta.md`,
  `agents/arquitecto-refactorizacion.md` (rebuild-architect sin el 12 ni el detalle objeto a objeto del 14) y
  `references/senales.md` (de `modernization-guide.md`: `Señal · Dónde se ve en as-is/ · Problema · BP nn §x`, sin copiar doctrina).
  Donde el bloque B decía 🔵, 🔶 (Tarea 8b).
- Borrar: `docs/bloque-b/`.
- Modificar: `pruebas/comprobar_plugin.py` (fuera de `EXTERNAS`, dentro de `REGLA_DOCS`; error si refactorización o el
  analista citan `as-is/extraccion` o `mcp_raw`) y `README.md`.

**Interfaces:**
- `propuesta.md`: `## 1. Alcance` (qué se rehace, qué se queda y los límites del equipo: plazo y lo que no se puede
  tocar) · `## 2. Diagnóstico` (fichas `**REF-nn — Problema**` con `Evidencia · Regla · Efecto · Prioridad · Esfuerzo`;
  Evidencia enlaza a `../as-is/…` y cita el `H-…` si sale de un hallazgo; Regla = «BP nn §x») · `## 3. Solución` (por capa: `Capa · Qué se hace · Por qué ·
  Se descarta`, cada fila con sus REF) · `## 4. Migración y convivencia` · `## 5. Hoja de ruta` (`Fase · Qué · Depende de`) ·
  `## 6. Pendientes` (lo que tiene que decidir el equipo o el cliente, y los NV de `as-is/datos/sin-verificar.json` que
  condicionan la solución, con su ID).
- Si la evidencia de una REF cita un hallazgo `inferido` o `pendiente`, la REF lo dice y la Hoja de ruta pone antes
  «Verificar H-…» (Tarea 8b).
- SKILL.md: «Qué hace y qué no», entradas (`as-is/`, alcance y límites), flujo, «Dudas de Appian» (bloque común) y
  `## Qué escribe` con `refactorizacion/propuesta.md`.

- [ ] **Paso 1:** quitar la skill de `EXTERNAS`: `comprobar_plugin.py` → FALLA (cita una skill que no existe).
- [ ] **Paso 2:** escribir la skill. **Paso 3:** `comprobar_plugin.py` → 6 skills, 0 errores. Commit «F5: skill de refactorización».

### Tarea 14: `comprobar_propuesta.py`, ejemplo y selftest

**Ficheros:**
- Crear: `skills/appian-refactorizacion/scripts/comprobar_propuesta.py`, `pruebas/appian-refactorizacion/selftest.py` y
  `pruebas/appian-refactorizacion/datos/mantenimiento/{as-is/datos/*.json,as-is/anexo/…,refactorizacion/propuesta.md}`
  (ficticio y pequeño).

**Interfaces:**
- `comprobar(p: Path) -> tuple[list[str], list[str]]`. Errores: falta un apartado; una REF sin evidencia o con un enlace
  a `as-is/` que no existe; una «BP nn §x» que `appian-best-practices/scripts/seccion.py nn x` no encuentra; en
  Diagnóstico, un nombre con el prefijo de la app que no está en `as-is/datos/inventario.json`; una
  REF que no aparece en Solución; un NV citado que no está en `as-is/datos/sin-verificar.json`. Avisos: una REF que no
  está en la Hoja de ruta; una REF cuya evidencia cita un hallazgo `inferido` o `pendiente` sin «Verificar H-…» antes en la
  Hoja de ruta.
- Los datos de `datos/mantenimiento` traen un `sin-verificar.json` con un NV y un hallazgo `inferido`.

- [ ] **Paso 1:** selftest: `datos/mantenimiento` pasa (0/0); cinco copias rotas (evidencia rota, «BP 99 §1», objeto
  inventado en Diagnóstico, REF sin Solución, NV inexistente) dan su error, y una REF sobre el hallazgo inferido sin
  «Verificar» da su aviso; un objeto nuevo en Solución no da error. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** `comprobar_plugin.py --completo` en verde. Commit.

### Tarea 15: Evaluación de malas prácticas sembradas

**Ficheros:** Crear `pruebas/evaluaciones/malas-practicas/{README.md,puntuar.py}`; resultados en `docs/evaluaciones.md`.

**Interfaces:**
- `puntuar.py <propuesta.md> <as-is> [--ocultas]`: una mala práctica cuenta si una REF cita en su evidencia alguno de
  sus objetos, su regla es del documento de BP esperado y la REF tiene alternativa en Solución. Además, «Pendientes»
  tiene que citar los NV de `as-is/datos/sin-verificar.json` que incluyen los objetos `CMN` (los usan las malas
  prácticas 2, 3 y 4). Sale 0 con el 90 % o más y esa cita.

- [ ] **Paso 1:** un agente ejecuta refactorización en el proyecto de prueba `$PROYECTOS_PRUEBA/MNT/` siguiendo el SKILL.md.
- [ ] **Paso 2:** 10 de 11 y 3 de 3 ocultas, con los NV de `CMN` en «Pendientes» (`puntuar.py` sale 0), y
  `comprobar_propuesta.py` sin errores. Resultados a `docs/evaluaciones.md`.
- [ ] **Paso 3:** commit. Cierre de fase: revisión y merge.

---

## F6 · Analista

### Tarea 16: Citas de IDs de otras skills

**Ficheros:** Modificar `skills/appian-functional-analyst/scripts/modelo.py` y `pruebas/appian-functional-analyst/selftest.py`.

**Interfaces:** `modelo.quita_citas(texto) -> str` borra los tramos `[FU-nn …]` antes de buscar IDs; lo usan la búsqueda
de referencias de `modelo.py`, `indice.py` y `comprobar.py`.

- [ ] **Paso 1:** selftest: en una copia de `datos/autorizaciones`, una línea con «[FU-07 PAN-03]» no aparece en `indice.py impacto PAN-03`
  y no cuenta como referencia a la PAN-03 del análisis. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** selftest en verde. Commit.

### Tarea 17: Guion de la próxima reunión

**Ficheros:** Modificar `scripts/indice.py`, `pruebas/appian-functional-analyst/selftest.py`, `SKILL.md`, `references/actualizacion.md`.

**Interfaces:** `indice.py pendientes <p>`: Markdown con las PC abiertas (sin tachar) agrupadas por «A quién»; cada una
con pregunta, opciones y «Afecta a». Peso = elementos de «Afecta a» separados por comas + líneas fuera del §11 que citan
la PC. Dentro de cada grupo, de más peso a menos y, a igual peso, por ID.

- [ ] **Paso 1:** selftest: en `autorizaciones` salen PC-01 y PC-02 bajo «Responsable de la unidad» y no sale PC-03; en
  una copia con una PC-04 que afecta a cuatro elementos, PC-04 sale la primera. → FALLA.
- [ ] **Paso 2:** implementar `c_pendientes`. **Paso 3:** selftest en verde. Commit.

### Tarea 18: Texto que queda viejo

**Ficheros:** Modificar `scripts/comprobar.py`, `pruebas/appian-functional-analyst/selftest.py` y `references/actualizacion.md` (el paso «Texto que
queda viejo» cita la comprobación).

**Interfaces:** `comprobar.texto_viejo(m, ant, modif) -> list[str]`: para cada pieza modificada, las secuencias de cinco
palabras que tenía antes y ya no tiene; avisa de cada otra línea del funcional o del técnico que aún las contiene
(«HU-07: "…" sigue en PAN-04, l.212»). Solo con `--anterior`. Es aviso, no error.

- [ ] **Paso 1:** selftest: en una copia, cambiar el plazo de una historia y dejar la frase vieja en una pantalla →
  aviso con los dos IDs; sin dejarla → sin aviso. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** selftest en verde. Commit.

### Tarea 19: Aplicación existente en el funcional y el técnico

**Ficheros:**
- Modificar: `references/funcional-plantilla.md` (§4: con `as-is/`, la tabla de cada historia suma «Origen» = «Se
  conserva», «Cambia» o «Nueva»; si corrige un hallazgo, la cita «[FU-nn H-…]» va en la trazabilidad, no en el DF),
  `references/tecnico-plantilla.md` (con `as-is/`: §3 termina con «Carga inicial y migración» `Origen en la app actual ·
  Destino · Transformación · Volumen · Cómo se verifica`; §13 es una tabla `Paso · Objeto · Tipo · Situación · Sustituye
  a`, con Situación = Nuevo, Modifica, Existe o Sustituye; §2: una DT cita «[FU-nn REF-nn]» en «Necesidad»; un NV de
  `as-is/` que condiciona lo que se construye entra como PT, con la cita «[FU-nn NV-…]»; sin `as-is/` todo sigue como
  hoy). En `funcional-plantilla.md`, si el NV lo tiene que resolver negocio, entra además como PC (así llega al guion
  de la Tarea 17), redactada en términos de negocio y sin objetos de Appian, con la cita en el comentario de
  trazabilidad de su fila. `references/ingesta-fuentes.md` y `scripts/leer_fuentes.py` (opción `--una-fuente`: `as-is/`
  entra como una sola FU con el índice de sus documentos; `propuesta.md`, como cualquier fichero), `scripts/comprobar.py`,
  `pruebas/appian-functional-analyst/selftest.py`, `SKILL.md` (modo evolutivo y de refactorización).
- Crear: `pruebas/appian-functional-analyst/datos/evolutivo/` (ficticio: `as-is/datos/` de la app DEM del simulador,
  con un NV y un objeto fuera de la aplicación, una `refactorizacion/propuesta.md` pequeña y un análisis con tres
  historias nuevas).

**Interfaces:** `comprobar.comprobar_as_is(m)`, solo si existe `<p>/as-is/datos/inventario.json`.
- Errores: historia sin «Origen»; «Corrige H-xx» en una tabla del DF; una cita de hallazgo que no está en
  `hallazgos.json`; en §13, «Modifica» o «Existe» con un objeto que no está ni en el inventario ni en
  `fueraDeLaAplicacion`, «Nuevo» con uno que está en cualquiera de los dos, o «Sustituye» sin un objeto del inventario;
  una cita de NV que no está en `sin-verificar.json`; con propuesta, una REF de su Solución sin DT que la cite o un §3
  sin la tabla de migración.
- Un objeto de `fueraDeLaAplicacion` puede ser «Existe» (está en otra aplicación); «Modifica» con él es aviso: «CMN_X es
  de otra aplicación: ¿quién la cambia?».
- Si `as-is/datos/` no trae `sin-verificar.json` ni `fueraDeLaAplicacion` (un `as-is/` anterior a la Tarea 8b), lo que
  depende de ellos no se comprueba.

- [ ] **Paso 1:** selftest: `datos/evolutivo` pasa; siete copias rotas dan su error (dos de ellas, «Nuevo» con el objeto
  de fuera y un NV inexistente); una con «Existe» y el objeto de fuera no da error, y con «Modifica» da su aviso;
  `leer_fuentes.py --una-fuente`
  cataloga `as-is/` como una FU; y `datos/autorizaciones`, sin `as-is/`, da exactamente los mismos errores y avisos
  que antes. → FALLA.
- [ ] **Paso 2:** implementar y escribir `datos/evolutivo`. **Paso 3:** selftest en verde. Commit.

### Tarea 20: Aviso de parte mal hecha

**Ficheros:** Modificar `scripts/comprobar.py`, `pruebas/appian-functional-analyst/selftest.py` y `SKILL.md`.

**Interfaces:** dentro de `comprobar_as_is(m)`, por cada fila de §13 «Modifica» o «Existe»:
- aviso si su objeto tiene un hallazgo de severidad Alta: «DEM_X tiene H-SEG-01 (Alta): ¿pasa antes por refactorización?»;
- aviso si su objeto tiene un NV abierto o parcial: «DEM_X tiene NV-ARQ-01 sin verificar: ¿PC?» si su `queHaceFalta`
  empieza por negocio, y «¿PT?» si no.

- [ ] **Paso 1:** selftest con `datos/evolutivo` (un objeto con un hallazgo Alta y el objeto de fuera, con un NV abierto,
  como «Existe») → cada aviso cita su H o su NV. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** selftest en verde. Commit.

### Tarea 21: DF ya hecho (D2) y ciclo con el prototipo

**Ficheros:** Modificar en el analista `SKILL.md` (modo «DF ya hecho» en lugar de «Fiel»), `references/ingesta-fuentes.md`
y `references/actualizacion.md` (apartado «Feedback de una demo»); en prototipos, `SKILL.md` (paso «Después de una demo»).

- Modo «DF ya hecho»: el DF entra como versión 1.0 en el formato del plugin con sus IDs originales en la trazabilidad, y
  se escriben el funcional, el técnico y el Word. Las reuniones anteriores al DF pasan por el informe de impacto, y todo
  lo que no coincide con el DF requiere aprobación. Las posteriores, como siempre.
- Feedback de una demo: cada comentario es un punto que encaja en su PAN; si la PAN está validada (🔒), requiere
  aprobación; prototipos rehace solo las PAN del informe con `--anterior` y `--confirmadas`.

- [ ] **Paso 1:** `comprobar_plugin.py` y los selftest del analista y de prototipos en verde. **Paso 2:** commit.

### Tarea 22: Evaluaciones del analista

**Ficheros:** Crear `pruebas/evaluaciones/{incoherencias,demo,evolutivo}/` con `README.md`, sus fuentes ficticias,
`esperado.json`, `puntuar.py` y `ocultas/`; la demo trae además su análisis de partida (un funcional ficticio con seis
PAN, dos validadas 🔒) y el `generar_app.py` de su prototipo. Cada caso se copia a su proyecto de `$PROYECTOS_PRUEBA/`,
se ejecuta allí y los resultados van a `docs/evaluaciones.md`.

- Incoherencias: un DF ficticio (1.0) y tres reuniones (`.txt` con marcas de tiempo) con 10 incoherencias sembradas y
  3 más ocultas; `esperado.json` = `[{"fuente", "minuto", "piezas", "tipo"}]`. `puntuar.py` cuenta las que aparecen en
  los informes con su pieza y como «requiere aprobación», y comprueba que no se aplicó ninguna sin ella. Criterio: todas.
- Demo: un comentario de demo por cada una de sus 6 pantallas, dos de ellas validadas; `esperado.json` = PAN que
  cambian. `puntuar.py` compara los `app.json`: cambian las 4 no validadas y las 2 validadas solo con aprobación.
- Evolutivo: tres historias nuevas sobre la aplicación ficticia; `esperado.json` = la Situación de cada objeto de §13.
  `puntuar.py` compara (marcarlo todo «Nuevo» no pasa) y `comprobar.py` sin errores.

- [ ] **Paso 1:** un agente hace cada caso siguiendo los SKILL.md. **Paso 2:** cada `puntuar.py` cumple su criterio.
- [ ] **Paso 3:** commit. Cierre de fase: revisión y merge.

---

## F7 · Cualquiera del equipo puede usarlo

### Tarea 23: `requisitos.py`

**Ficheros:** Crear `requisitos.json`, `requisitos.py` y `pruebas/requisitos-esperado.json` en la raíz (este último se
genera con `requisitos.py --json` y `REQUISITOS_SIN` de todo lo opcional); modificar `pruebas/comprobar_plugin.py`
(`--completo` ejecuta la prueba de requisitos).

**Interfaces:**
- `requisitos.json`: `[{"id", "nombre", "skills", "imprescindible", "solo_pruebas", "para", "sin_el", "instalar": {"windows", "macos", "linux"}}]`
  con `python` (3.9+; ingeniería inversa pide 3.10 o superior, que instala `uv`), `playwright`, `navegador`, `node`,
  `docx`, `libreoffice`, `pdf` (pdftotext o pypdf), `uv`, `devmcp` (configuración encontrada con `config_files`,
  `server_entries` e `is_devmcp` de `devmcp_extract.py`), `appian-mcp-server`, `skill-pdf` (no se detecta: se informa)
  y, con `solo_pruebas`, `pytest` y `mcp`.
- `requisitos.py [--skill NOMBRE] [--json] [--breve] [--tabla-readme]`. Sale 1 si falta algo imprescindible para lo
  pedido. `--json`: `{"python": "3.12.1", "requisitos": [{…, "presente": bool}], "avisos": [...]}`. Navegador: el
  Chromium de Playwright, o Chrome o Edge en sus rutas habituales, sin abrir ninguno. `docx`: se busca en la carpeta
  actual y en la global de npm, como `df_docx.js`. `REQUISITOS_SIN=id,id` fuerza ausencias para las pruebas.
- Aviso si existe una copia suelta de una skill del plugin en `~/.claude/skills/` (dos versiones activas a la vez),
  también con el nombre que tenía antes (`appian-prototipos-aena`, hoy `appian-prototipos`). La carpeta personal (`~`)
  sale de `devmcp_extract.home_dir()`, que respeta `APPIAN_RE_HOME`.

- [ ] **Paso 1:** prueba en `comprobar_plugin.py --completo`: con `REQUISITOS_SIN` de todo lo opcional, la salida
  `--json` es igual a `pruebas/requisitos-esperado.json` salvo versión y rutas, como en la Tarea 31; con
  `REQUISITOS_SIN=playwright,docx`, sale 0 y esos dos van con `presente: false`; con `REQUISITOS_SIN=python`, sale 1;
  con un `APPIAN_RE_HOME` temporal que tiene `.claude/skills/appian-reverse-engineering/SKILL.md`, hay aviso, y también
  con `.claude/skills/appian-prototipos-aena/SKILL.md`. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** en verde. Commit.

### Tarea 24: Aviso al instalar

**Ficheros:** Crear `hooks/hooks.json`; modificar la sección «Requisitos» de cada SKILL.md, que se crea donde no la
haya (una línea: `python3 <skill>/../../requisitos.py --skill <nombre>` antes de la primera tarea).

- [ ] **Paso 1:** comprobar con la documentación de plugins (agente `claude-code-guide`) cómo se declara un hook
  `SessionStart` de un plugin sin depender del shell (en Windows puede ir por PowerShell 5.1, que no tiene `||`) y cómo
  se cita su carpeta (`${CLAUDE_PLUGIN_ROOT}`).
- [ ] **Paso 2:** `--breve` siempre sale con 0 (si no, Claude no recibe el texto), imprime solo lo que falta y escribe la
  marca `~/.cache/appian-analisis-funcional/avisado-<versión>` (`~` sale de `devmcp_extract.home_dir()`) después de
  imprimir. Prueba: con `APPIAN_RE_HOME` temporal y `REQUISITOS_SIN=docx`, la primera vez lo dice y la segunda no
  imprime nada; con `REQUISITOS_SIN=python`, sale 0 y lo dice.
- [ ] **Paso 3:** `hooks.json` en la forma que da el Paso 1.
- [ ] **Paso 4 (Raúl):** instalar el paquete en Claude Code y en la app de escritorio con algo de la tabla sin instalar
  y comprobar que el primer mensaje lo dice. Resultado en `docs/evaluaciones.md`.
- [ ] **Paso 5:** commit.

### Tarea 25: README generado y nada personal

**Ficheros:** Modificar `README.md` (tabla entre `<!-- requisitos:inicio -->` y `<!-- requisitos:fin -->`),
`pruebas/comprobar_plugin.py`, `pruebas/clientes.txt` y, en `skills/appian-prototipos/`, los datos de ejemplo de
`galerias/*/generar_app.py` y `templates/generar_plantillas.py`, con lo que regeneran, y los ejemplos de
`references/{design-rules,ingesta-requisitos,spec-format}.md`, que también pasan al dominio neutro.

**Interfaces:** `comprobar_plugin.py` da error si la tabla del README no es la salida de `requisitos.py --tabla-readme`,
o si un fichero que va al paquete contiene, con límite de palabra y sin distinguir acentos ni mayúsculas, `rgmoya`,
`raulogm`, `C:/Users/` o `C:\Users\` no seguido de `<usuario>`, `/home/claude`, `Proyectos IA` o «Raúl» y «Raul»; salvo
`author.name` de `.claude-plugin/plugin.json` y `owner.name` de `.claude-plugin/marketplace.json`. También, si `skills/` o
`.claude-plugin/` nombran un cliente de `pruebas/clientes.txt` (hoy, AENA): el plugin no lleva clientes (Tarea 0b).
`clientes.txt` lleva también lo que delata a ese cliente en los datos de ejemplo: aeropuerto, Barajas, El Prat, MAD, BCN,
PMI y AGP. Los datos de las galerías y las plantillas de prototipos pasan a un dominio ficticio neutro (por ejemplo,
incidencias y expedientes en las sedes de una empresa ficticia), sin aeropuertos ni lugares o códigos reales de un
cliente, y se regeneran con sus scripts (lo decidió Raúl el 7 de octubre).

- [ ] **Paso 1:** con un fichero temporal en una skill que diga `C:/Users/rgmoya`, `comprobar_plugin.py` da error, y el
  `HYDRAULIC` de `viewer-static.min.js` no lo da; una galería que dice «Barajas» también da error. → FALLA.
- [ ] **Paso 2:** implementar, pasar galerías y plantillas al dominio neutro y regenerar la tabla. **Paso 3:** en verde
  sin el fichero temporal. Commit.

### Tarea 26: Pruebas en Windows, macOS y Linux

**Ficheros:** Crear `.github/workflows/pruebas.yml`.

- Matriz `ubuntu-latest`, `windows-latest` y `macos-latest` con Python 3.9 y 3.12: instala `playwright` (y
  `python -m playwright install chromium`), `pytest`, `mcp` y Node con `docx`; ejecuta `python pruebas/comprobar_plugin.py --completo`
  con `PYTHONUTF8=1`.
- En Python 3.9 no se instala `mcp`, que pide 3.10 o superior: se instala `uv` con `UV_PYTHON=3.12` y
  `comprobar_plugin.py` pasa ingeniería inversa por su vía de uv.
- [ ] **Paso 1:** subir la rama y ver la ejecución en las seis combinaciones. Si el token no deja subir
  `.github/workflows/` (permiso `workflows`), el fichero lo sube Raúl. **Paso 2:** arreglar lo que falle en
  Windows o macOS (codificación, rutas, `python3`/`python`) con su prueba. **Paso 3:** commit. Cierre de fase: revisión y merge.

---

## F8 · Sin solapes

### Tarea 27: Un dueño por salida

**Ficheros:** Crear `pruebas/propietarios.json`; modificar `pruebas/comprobar_plugin.py` y cada SKILL.md (sección
`## Qué escribe` con las rutas entre comillas invertidas, relativas a `<p>`).

**Interfaces:**
- `propietarios.json`: lista de reglas `{"patron", "dueno", "tambien": [...]}`; gana el patrón más específico.
  - `proyecto.md`, `fuentes/`, `notas/`, `impacto/`, `analisis/*.md`, `analisis/diagramas/*.mmd`, `entregables/`, `versiones/` → analista.
  - `as-is/` → ingeniería inversa; `as-is/08-procesos-bpmn/*.{drawio,png,bpmn}` → diagramas.
  - `refactorizacion/` → refactorización; `prototipo/` → prototipos.
  - `analisis/diagramas/*.{drawio,png,bpmn,svg}` → diagramas.
  - `analisis/diagramas/*.json` → analista, `tambien` diagramas; `as-is/08-procesos-bpmn/*.json` → ingeniería inversa,
    `tambien` diagramas (los reescribe al aceptar cambios hechos a mano en draw.io).
- Errores nuevos: una ruta de «Qué escribe» que no es de esa skill ni la tiene en `tambien`; una regla que su dueño no
  declara; un `.py` fuera de diagramas con `mermaid.initialize` o `BPMNDiagram`; una lista de muletillas (`- «…» →`)
  fuera de `redaccion.md`.

- [ ] **Paso 1:** pruebas en `comprobar_plugin.py` con copias temporales: una skill que declara `as-is/` sin serlo y un
  script con `BPMNDiagram` fuera de diagramas dan error; las reglas de `tambien` no. → FALLA.
- [ ] **Paso 2:** implementar y escribir las secciones. **Paso 3:** en verde. Commit.

### Tarea 28: Las seis descripciones

**Ficheros:** el `description` de los seis SKILL.md.

- Cada una: qué hace, cuándo usarla y un «No…» que nombra la skill que lo hace; 1024 caracteres como mucho.
- Cambios: ingeniería inversa (Tarea 1); refactorización nueva («Úsala después de ingeniería inversa cuando se quiera
  plantear cómo debería estar hecha la aplicación, entera o una parte, con buenas prácticas y eficiencia…»); el analista
  remite a refactorización y deja de decir «no audita»; buenas prácticas remite «evaluar una aplicación entera» a
  refactorización y se recorta, porque hoy tiene 1021 caracteres; diagramas nombra a refactorización si dibuja procesos objetivo;
  prototipos, ya `appian-prototipos` y sin marca de cliente (Tarea 0b).
- [ ] **Paso 1:** `comprobar_plugin.py` en verde. **Paso 2:** commit.

### Tarea 29: Prueba de enrutado

**Ficheros:** Crear `pruebas/enrutado.json` (`[{"peticion", "skill"}]`: unas 30, al menos 4 por skill y 6 frontera; un
tercio en `ocultas/`) y `pruebas/evaluaciones/enrutado/README.md`; resultados en `docs/evaluaciones.md`.

- Fronteras: «¿la rehacemos o la evolucionamos?» → refactorización; «revisa esta interfaz» → buenas prácticas;
  «documenta la app X» → ingeniería inversa; «añade estas historias a lo que ya hay» → analista; «dibuja el proceso de
  la app existente» → diagramas (con ingeniería inversa si no hay JSON); «enséñale al cliente cómo quedaría» → prototipos.
- [ ] **Paso 1:** aquí se pasa al Paso 2: `claude plugin eval` espera otro formato de casos y llama a la API. Si Raúl
  quiere `eval`, se convierte `enrutado.json` en casos con el evaluador `tool_used: Skill` y los ejecuta él.
- [ ] **Paso 2:** un agente que solo ve las seis descripciones elige la skill de cada petición. Criterio: todas;
  si no, se ajustan las descripciones y se repite con las ocultas sin ver. **Paso 3:** resultados y commit. Cierre de fase: revisión y merge.

---

## F9 · Cierre

### Tarea 30: Punta a punta y revisión independiente

- [ ] **Paso 1:** con la aplicación ficticia: ingeniería inversa → refactorización de un módulo → funcional y técnico
  (con una reunión ficticia que cambia algo) → diagramas → prototipo → DF en Word. Todos los comprobadores sin errores.
- [ ] **Paso 2:** un agente que no ha visto el trabajo revisa la rama entera contra el diseño; se corrige lo que encuentre.
- [ ] **Paso 3 (Raúl):** con una aplicación real del cliente, en su equipo: ingeniería inversa en la carpeta de su
  proyecto, con extracción nueva (la guardada es del formato anterior a la Tarea 2). Lo que Raúl sabe que no se puede
  verificar sale como NV con lo que hace falta, los hallazgos que ya conoce salen verificados con su evidencia y
  refactorización, sobre ese `as-is/`, recoge esos NV en «Pendientes». El resultado se queda en el proyecto. A
  `docs/evaluaciones.md` va si pasó o no y qué se corrigió, sin nombres ni detalles del cliente; si no pasa, se corrige
  y se repite antes de la Tarea 31.
- [ ] **Paso 4:** commit.

### Tarea 31: Paquete, instalación limpia, versión y entrega

**Ficheros:** Crear `pruebas/empaquetar.py` (zip sin `.git`, `__pycache__`, `.pytest_cache`, `.github/`, `.claude/`,
`docs/`, `CLAUDE.md`, `pruebas/` ni `*.plugin`: reutiliza `NO_VAN_EN_EL_PAQUETE` y `CACHES` de `comprobar_plugin.py`);
actualizar el comando de empaquetado del README.

- [ ] **Paso 1:** empaquetar, descomprimir en una carpeta temporal y, desde ella, `requisitos.py --json` con
  `REQUISITOS_SIN` de todo lo opcional: coincide con `pruebas/requisitos-esperado.json` del repositorio. Después, desde
  el repositorio, `python3 pruebas/comprobar_plugin.py --completo --plugin <copia>` en verde: las pruebas contra lo que
  se instala, que no las lleva.
- [ ] **Paso 2:** `0.7.0-beta.1` en `plugin.json` y su fila en el README (qué cambia, una línea por skill);
  `comprobar_plugin.py --completo` en verde; paquete; etiqueta `v0.7.0-beta.1`; entregar el `.plugin`.
- [ ] **Paso 3 (Raúl):** desinstalar de su cuenta la skill suelta de ingeniería inversa (y avisar a quien la tenga) y
  archivar `~/Proyectos IA/appian-reverse-engineering`, que lleva `.git/re-historial.bundle`, la copia usada en F1.
