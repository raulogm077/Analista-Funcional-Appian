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
  del repositorio; el plugin no escribe nada fuera de `<p>`. Dentro de las skills solo hay ejemplos mínimos y ficticios
  que enseñan el formato y usan los selftest (como hoy `ejemplos/autorizaciones`).
- Todo en español: documentos, mensajes de los scripts, commits y nombres de los objetos de los ejemplos.
- Ejemplos y aplicaciones de prueba ficticios. Nada del cliente en el repositorio. Nada sale del equipo para pintar o convertir.
- Ingeniería inversa usa solo los MCP de Appian (Dev MCP, Appian MCP Server y MCP de documentación) y en solo lectura.
- La extracción vive en el proyecto, en `as-is/extraccion/` (D4), y se escribe ya saneada: sin credenciales, secretos,
  nombres de usuario (van seudónimos), rutas locales ni la lista de aplicaciones del entorno. Las demás skills leen
  `as-is/datos/`, nunca la extracción.
- Los proyectos de prueba de las evaluaciones se crean en `$PROYECTOS_PRUEBA` (por defecto `../proyectos-prueba/`, al
  lado del repositorio). En el repositorio quedan las preguntas, lo esperado y los scripts que puntúan
  (`pruebas/evaluaciones/`), y los resultados en `docs/evaluaciones.md`.
- Los IDs de otra skill se citan dentro de su fuente: «[FU-07 PAN-03]», «[FU-08 REF-02]» (D1). Nunca en el texto del DF.
- Scripts con `pathlib`, `encoding="utf-8"` y rutas con espacios; en Windows el comando es `python`. Rutas de prueba
  neutras («Carpeta con espacios/Gestión app»).
- Una rama por fase (`f2-…`, `f3-…`); a `main` llega con las pruebas en verde y la revisión independiente de la fase.
- Antes de cada commit: `python3 pruebas/comprobar_plugin.py --completo` y, si se toca ingeniería inversa,
  `python3 -m pytest -q` en `skills/appian-reverse-engineering`.
- Commits terminados en `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` y
  `Claude-Session: https://claude.ai/code/session_01DozooebTcuXCNifwmTZUN5`.
- Lo de desarrollo (`docs/`, `CLAUDE.md`, `pruebas/evaluaciones/`, `.github/`) no va en el paquete. Versión al cerrar: `0.7.0-beta.1`.
- Las baterías de evaluación (preguntas, malas prácticas, incoherencias, peticiones de enrutado) tienen un tercio
  escrito por un agente aparte y guardado en `ocultas/`, que no lee quien ajusta plantillas ni descripciones hasta medir.

## Riesgos para quien lo use (Review Focus)

Lo que el diseño implica y ninguna prueba de tarea cubriría sola. Cada línea tiene su prueba en la tarea indicada.

1. **Proyecto en una carpeta sincronizada con SharePoint u OneDrive.** Lo que llega a `<p>` ya está saneado al
   escribirse, y las rutas son cortas. Pruebas `test_sin_usuarios_ni_secretos` y `test_rutas_cortas` (Tarea 2).
2. **Windows.** Rutas con espacios y largas, `python` en vez de `python3`, consola sin UTF-8. Pruebas
   `test_ruta_con_espacios` (Tareas 2 y 6) y la matriz de GitHub Actions (Tarea 26).
3. **Repetir la ingeniería inversa o retomarla en otra sesión o en otro equipo.** Como la extracción está en el
   proyecto, se retoma sin volver a extraer lo que ya está. Prueba `test_retomar` (Tarea 2).
4. **Proyecto sin aplicación existente.** Las comprobaciones nuevas del analista no saltan sin `as-is/`. Prueba: el
   selftest del ejemplo `autorizaciones` da lo mismo que antes (Tarea 19).
5. **Compañero sin Playwright o sin Node.** Se dibuja el `.drawio` y se exporta el BPMN sin navegador (sin PNG), y se
   dice qué falta. Pruebas `DIAGRAMAS_SIN_NAVEGADOR=1` (Tarea 12) y `REQUISITOS_SIN=playwright,docx` (Tarea 23).

---

## F2 · Ingeniería inversa en el plugin, solo con el bloque A

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
  `scripts/build_summary.py`, `tests/test_registry.py`.
- Modificar: `pruebas/comprobar_plugin.py` (`EXTERNAS["appian-refactorizacion"] = "se crea en F5"`).
- Crear: `skills/appian-reverse-engineering/tests/test_sin_bloque_b.py`.

**Interfaces:**
- Produce: `registro.json` con las claves exactas `{"hallazgos", "porSeveridad", "porCerteza"}`; `summary.json` sin
  `modernization`; la tabla del registro en 09 queda `ID · Hallazgo · Área · Severidad · Certeza · Dónde`.

- [ ] **Paso 1: prueba que falla**

```python
PROHIBIDO = re.compile(
    r"12-especificacion|13-modernizacion|14-diseno|rebuild-architect|target-designer|modernizacion\.json|"
    r"moderniz|reconstru|[Vv]eredicto|\b(MOD|PQ|DEC|RF|RNF)-|17 documentos|00.{1,3}14\b|"
    r"tratamiento (de|en) 13|\"tratamiento\"|tratamiento\[|\| Tratamiento \|")

def test_ingenieria_inversa_no_menciona_el_bloque_b():
    malos = [f"{p.relative_to(ROOT)}:{n}" for p in ROOT.rglob("*") if p.suffix in (".md", ".py", ".json")
             and p.name != "test_sin_bloque_b.py" and "docs" not in p.parts
             for n, l in enumerate(p.read_text(encoding="utf-8").splitlines(), 1) if PROHIBIDO.search(l)]
    assert malos == []
```

  Y en `test_registry.py`: `assert set(reg) == {"hallazgos", "porSeveridad", "porCerteza"}`.
- [ ] **Paso 2:** `python3 -m pytest -q tests/test_sin_bloque_b.py tests/test_registry.py` → FALLA con la lista de ficheros y líneas.
- [ ] **Paso 3:** quitar el bloque B de cada fichero de la lista. El `docs/` de la skill se mueve en la Tarea 3; hasta
  entonces la prueba lo excluye con `"docs" not in p.parts`, y esa tarea quita la excepción.
- [ ] **Paso 4:** descripción nueva del SKILL.md (se afina en la Tarea 28):
  «Ingeniería inversa de aplicaciones Appian: lee la aplicación en vivo por el Dev MCP, en solo lectura, y documenta
  cómo está hecha para que el equipo la entienda: funcional, arquitectura, datos, seguridad, integraciones, APIs,
  batches, procesos, pantallas, reglas de negocio, inventario y anexo con las definiciones, cada dato con su evidencia.
  Úsala para entender, documentar o hacer el onboarding de una aplicación Appian existente, o cuando se pida su modelo
  de datos, sus integraciones, procesos, pantallas o reglas, aunque no se diga «ingeniería inversa». No juzga ni
  propone cómo rehacerla (appian-refactorizacion), no escribe requisitos ni especificaciones (appian-functional-analyst),
  no dibuja (appian-diagramas-bpmn) y no crea ni modifica objetos.»
- [ ] **Paso 5:** `python3 -m pytest -q` en verde y `python3 pruebas/comprobar_plugin.py` con 0 errores.
- [ ] **Paso 6:** commit «F2: el bloque B sale de ingeniería inversa».

### Tarea 2: Salida y extracción dentro del proyecto (D4)

**Ficheros:**
- Modificar: `scripts/rutas.py`, `scripts/privacidad.py` (recibe de `build_annex.py` `USER_KEY`, `EMAIL`, `users_seen`,
  `users_in`, `user_labels`, `scrub` y `scrub_text`), `scripts/build_annex.py` (los importa), `scripts/devmcp_extract.py`
  (escribe ya saneado y con rutas cortas), `scripts/build_model.py` (misma ruta corta), `tests/conftest.py`,
  `tests/test_build_model.py:93-95`, `tests/test_extract.py:255`, `tests/test_registry.py:17`, `SKILL.md`
  («Argumentos», «Dos carpetas» pasa a una, y puntos 6 y 11 de la validación final), `references/response-format.md:50`
  y las menciones a `_trabajo` de `references/` y `agents/`.
- Crear: `tests/test_extraccion_en_proyecto.py`.

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

- [ ] **Paso 1: pruebas que fallan.** `interm()` de `conftest.py` usa `rutas.work_dir(self.out)`. En
  `tests/test_extraccion_en_proyecto.py`:
  - `test_extraccion_dentro_del_proyecto`: tras `extract`, existe `<out>/extraccion/mcp_raw` y no hay nada fuera de `<out>`
    (la carpeta temporal de la prueba solo tiene el proyecto, su `.mcp.json` y el registro de llamadas del simulador).
  - `test_sin_usuarios_ni_secretos`: ningún fichero de `<out>` contiene los usuarios de `fixture.GROUP_USERS`, `sk_live_`,
    un correo, la ruta de la carpeta de la prueba ni otra aplicación del entorno; aparece `‹usuario-`; y un mismo usuario
    tiene el mismo seudónimo en los miembros del grupo y en el historial.
  - `test_barrido_final`: con una respuesta preparada que cita «ana.garcia» en una expresión, escrita antes de conocer el
    grupo, tras `barrido_final` ya no aparece.
  - `test_rutas_cortas`: ninguna ruta relativa dentro de `<out>/extraccion` pasa de 100 caracteres.
  - `test_retomar`: una segunda `extract` no vuelve a pedir lo que ya está (registro de llamadas del simulador) y
    `build_model.py` funciona igual.
  - `test_ruta_con_espacios`: lo anterior con `out = tmp / "Carpeta con espacios" / "Gestión app" / "as-is"`.
- [ ] **Paso 2:** `python3 -m pytest -q tests/test_extraccion_en_proyecto.py` → FALLA.
- [ ] **Paso 3:** implementar y ajustar las pruebas existentes de la lista de ficheros.
- [ ] **Paso 4:** `SKILL.md`: salida por defecto `<p>/as-is/` (si la carpeta tiene `proyecto.md` o la da el usuario) o
  `./<PREFIJO>/as-is/`; una sola carpeta, con la extracción en `as-is/extraccion/`, ya saneada; los puntos 6 y 11 de la
  validación final y `response-format.md` lo dicen así.
- [ ] **Paso 5:** `python3 -m pytest -q` en verde. Commit «F2: salida y extracción saneada dentro del proyecto».

### Tarea 3: Alta de ingeniería inversa en el plugin

**Ficheros:**
- Crear: `skills/appian-reverse-engineering/scripts/selftest.py`.
- Mover: `skills/appian-reverse-engineering/docs/` → `docs/ingenieria-inversa/`.
- Modificar: `README.md` (mapa de skills); `skills/appian-reverse-engineering/SKILL.md` (apartado «## Dudas de Appian»
  con el bloque común del analista); `references/docs-mcp-usage.md` (solo lo propio: tope de 30 consultas y caché);
  `tests/test_scripts.py` (las pruebas de `detect_secrets.sh` se saltan si no hay `bash`; `encoding="utf-8"` en toda
  lectura, también en `test_registry.py:50-51`); `tests/test_sin_bloque_b.py` (sin la excepción de `docs`);
  `pruebas/comprobar_plugin.py` (`REGLA_DOCS` incluye `appian-reverse-engineering`).

**Interfaces:**
- `selftest.py`: ejecuta `python -m pytest -q <skill>/tests` con `PYTHONUTF8=1`. Si faltan `pytest` o `mcp` y hay `uv`,
  lo repite con `uv run --no-project --with pytest --with "mcp>=1.2,<2"`. Sale 0, 1 (falla) o 2 (falta un requisito).

- [ ] **Paso 1:** añadir `appian-reverse-engineering` a `REGLA_DOCS` y ejecutar `python3 pruebas/comprobar_plugin.py --completo`
  → FALLA («falta el apartado Dudas de Appian») y no aparece «Prueba de appian-reverse-engineering».
- [ ] **Paso 2:** hacer los cambios de la lista.
- [ ] **Paso 3:** `python3 pruebas/comprobar_plugin.py --completo` → «Prueba de appian-reverse-engineering: bien», 0 errores.
- [ ] **Paso 4:** commit «F2: ingeniería inversa en la prueba completa del plugin». Cierre de fase: revisión
  independiente de la rama y merge a `main`.

---

## F3 · Precisa y sin relleno

### Tarea 4: Reglas de prosa en un solo sitio

**Ficheros:**
- Crear: `skills/appian-functional-analyst/scripts/redaccion.py`.
- Modificar: `skills/appian-functional-analyst/scripts/comprobar.py` (usa `redaccion.py`; mismo comportamiento) y
  `scripts/selftest.py`; `skills/appian-reverse-engineering/references/presentation-rules.md`: se quedan el esqueleto
  de documento (TL;DR, Vista, Detalle, Hallazgos, Cobertura) y las reglas de evidencia, marcas de certeza y usuarios;
  las de prosa remiten a `appian-functional-analyst/references/redaccion.md`.

**Interfaces:**
- `redaccion.muletillas(ruta=None) -> list[str]` (líneas `- «x» →` de `references/redaccion.md`, normalizadas),
  `redaccion.frases(texto) -> list[str]`, `redaccion.MAX_PALABRAS = 35`,
  `redaccion.parrafos_repetidos(textos: dict[str, str], minimo=20) -> list[tuple[str, list[str]]]`.

- [ ] **Paso 1:** en el selftest del analista: con un `redaccion.md` temporal de dos muletillas, `muletillas(ruta)` las
  devuelve normalizadas; `parrafos_repetidos` encuentra un párrafo de 25 palabras que está en dos textos y no uno de 15.
  → FALLA (no existe el módulo).
- [ ] **Paso 2:** crear `redaccion.py` moviendo `muletillas()` y `frases()` de `comprobar.py`.
- [ ] **Paso 3:** selftest del analista sin fallos y con los mismos avisos que antes en `autorizaciones`. Recortar
  `presentation-rules.md`. Commit «F3: reglas de prosa en un solo sitio».

### Tarea 5: `as-is/datos/`, el contrato con las demás skills

**Ficheros:**
- Crear: `skills/appian-reverse-engineering/scripts/build_datos.py`, `references/datos.md`, `tests/test_datos.py`.
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
- Lo usan las Tareas 6, 14, 19 y 20.

- [ ] **Paso 1:** `test_datos.py::test_datos_formato`: tras el flujo del simulador con un `hallazgos/prueba.json` de un
  hallazgo sobre `DEM_ERP_API_TOKEN`, existen los cuatro ficheros con sus claves, cada objeto de cada hallazgo está en
  el inventario, la tabla `DEM_SOLICITUD` y la vista «Resumen» están en `tambien` de `DEM Solicitud`, y ningún fichero
  contiene un usuario del simulador. → FALLA.
- [ ] **Paso 2:** implementar y documentar el formato en `references/datos.md`. **Paso 3:** pytest en verde. Commit.

### Tarea 6: `comprobar_asis.py`

**Ficheros:**
- Crear: `scripts/comprobar_asis.py`, `tests/test_comprobar_asis.py`, `assets/presupuesto-palabras.json`.
- Modificar: `SKILL.md` (fase 8: sin errores de `comprobar_asis.py` antes de responder).

**Interfaces:**
- `comprobar(salida: Path) -> tuple[list[str], list[str]]` (errores, avisos). CLI: 0 sin errores, 1 con errores.
- Errores:
  - un nombre entre comillas invertidas que empieza por el prefijo de la app (seguido de `_` o espacio, cortado en `.`
    o `#`) y no está ni en `objetos[].nombre`, ni en `objetos[].tambien`, ni es `aplicacion.nombre`;
  - una tabla con columna «Certeza» sin columna «Evidencia», o una fila cuya evidencia no enlaza a un fichero existente
    de `anexo/`, o una certeza fuera de ✅ 🔵 ❓;
  - cifras de `00` («N objetos», «N process models», «N interfaces», «N record types») distintas de las de
    `as-is/extraccion/summary.json`;
  - `{{` sin sustituir, un enlace relativo a un fichero que no existe, o lo que detecte `detect_secrets.py`.
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
- Crear: `tests/mock_devmcp/fixture_mal_hecha.py`, `tests/test_fixture_mal_hecha.py`,
  `pruebas/evaluaciones/aplicacion-ficticia/{malas-practicas.json,preguntas.json,ocultas/}`.
- Modificar: `tests/mock_devmcp/lcp_mcp_server_mock.py` (módulo de `$MOCK_APP`, por defecto `fixture`; el prefijo sale
  del objeto aplicación del fixture y no de `"DEM"` fijo en las líneas 170 y 239; tipo `DATA_STORE` en `_app_objects`;
  definición para `DATA_TYPE` y `DATA_STORE`) y `tests/mock_devmcp/appian_mcp_server_mock.py` (también `$MOCK_APP`).

**Interfaces:**
- `fixture_mal_hecha` expone lo mismo que `fixture`: `APP_KEY`, `REFS`, `DEPENDENTS_SUPPORTED`, `GROUP_USERS`,
  `PM_HISTORY`, `VALIDATION_ISSUES` y `build()`.
- Aplicación «MNT Mantenimiento de Instalaciones», prefijo `MNT`, unos 45 objetos, con estas 10 malas prácticas
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
- Lo que pregunta un recién llegado: CDT `MNT_OrdenDTO` con su data store, record types `MNT Orden`, `MNT Técnico` y
  `MNT Estado`, grupos `MNT Administradores`, `MNT Técnicos` y `MNT Supervisores`, un site de tres páginas, un proceso
  sin ejecuciones `MNT_PM_Antiguo` y usuarios ficticios en los grupos, en una constante y como asignados.
- `preguntas.json`: 20 preguntas `{"id": "Q-01", "pregunta", "respuestas": [formas aceptadas], "tipo": "objeto|numero|si-no|lista"}`,
  al menos una por documento 01–11. Por ejemplo: «¿Qué proceso lanza la acción "Nueva orden"?» → `MNT_PM_GestionOrden`;
  «¿Cada cuánto se ejecuta el recordatorio?» → «5 minutos»; «¿Qué constante cambia por entorno?» → `MNT_URL_ERP_PRE`;
  «¿Qué proceso no se ha ejecutado nunca?» → `MNT_PM_Antiguo`; «¿Qué grupos ven la página Administración?» → `MNT Administradores`.
- `ocultas/`: 7 preguntas y 3 malas prácticas más, escritas por un agente aparte con solo el fixture delante.

- [ ] **Paso 1:** `test_fixture_mal_hecha.py`: con `MOCK_APP=fixture_mal_hecha`, `extract` + `build_model.py` dan al
  menos 40 objetos y prefijo `MNT`; el CDT y el data store tienen `detail: "full"`; cada objeto de `malas-practicas.json`
  y cada respuesta de tipo `objeto` de `preguntas.json` está en `inventory.json`; y el simulador DEM da lo mismo que antes. → FALLA.
- [ ] **Paso 2:** escribir la aplicación, los cambios del simulador y los JSON. **Paso 3:** pytest en verde.
- [ ] **Paso 4:** commit «F3: aplicación ficticia mal hecha» y etiqueta `f3-antes` (punto de partida de la Tarea 9).

### Tarea 8: Preguntas primero, hechos y no consejos

**Ficheros:**
- Modificar: `assets/markdown-templates/**/*.md` (00–11, LEEME, INVENTARIO y `08-procesos-bpmn/pm-template.md`), los
  cinco agentes de análisis, `references/{execution-principles,security-rules}.md`, `scripts/build_registry.py`
  (aviso si un hallazgo trae `recomendacion`) y `tests/test_registry.py`.
- Crear: `tests/test_plantillas.py`.

- [ ] **Paso 1: pruebas que fallan.** `test_plantillas.py`:
  - `test_cada_plantilla_empieza_por_sus_preguntas`: tras el título, una línea `> **Responde a:**` con 2 a 5 preguntas.
  - `test_toda_tabla_con_certeza_tiene_evidencia`.
  - `test_sin_recomendaciones`: ni plantillas, ni agentes, ni `references/` dicen «recomendaci» o «recomienda».
  - En `test_registry.py`, `test_recomendacion_es_aviso`.
- [ ] **Paso 2:** reescribir: las preguntas que responde cada documento, tablas antes que prosa, columna «Evidencia»
  donde hay «Certeza», sin explicar conceptos de Appian (se enlaza la documentación), sin repetir datos de otro
  documento y sin consejos (la frase de 09 «Appian recomienda dividir…» se va; el dato «procesos de más de 50 nodos» se queda).
- [ ] **Paso 3:** pytest en verde. Commit «F3: plantillas que responden preguntas».

### Tarea 9: Evaluación del recién llegado (antes y después)

**Ficheros:**
- Crear: `pruebas/evaluaciones/recien-llegado/{README.md,puntuar.py,palabras.py}` y, en `docs/evaluaciones.md`, sus
  resultados. El proyecto de prueba `MNT` se crea en `$PROYECTOS_PRUEBA/MNT/`, fuera del repositorio; las Tareas 15 y
  22 trabajan sobre él.

**Interfaces:**
- `puntuar.py <respuestas.json> <as-is> [--ocultas]`: `respuestas.json` = `[{"id": "Q-01", "respuesta", "evidencia": "ruta#ancla"}]`.
  Acierta si la respuesta normalizada está entre las aceptadas y el fichero de la evidencia existe. Imprime aciertos y
  sale 0 con el 90 % o más.
- `palabras.py <as-is>`: palabras por documento y total.

- [ ] **Paso 1:** «antes»: desde `f3-antes`, un agente genera `as-is/` de la aplicación ficticia siguiendo el SKILL.md
  contra el simulador, en `$PROYECTOS_PRUEBA/MNT-antes/`; otro, que solo lee su `as-is/`, responde las 20 preguntas y las 7
  ocultas. Aciertos y palabras a `docs/evaluaciones.md`.
- [ ] **Paso 2:** «después», igual con la Tarea 8 hecha, en `$PROYECTOS_PRUEBA/MNT/`. Criterio: 18 de 20 y 6 de 7
  ocultas, con evidencia; 0 errores de `comprobar_asis.py`; menos palabras que «antes».
- [ ] **Paso 3:** si dos documentos se responden el uno al otro (LEEME con 00, 05 con 06), se unen —plantillas,
  entregables del SKILL.md, publicadores y pruebas de la Tarea 8— y se repite el Paso 2.
- [ ] **Paso 4:** commit. Cierre de fase: revisión y merge.

---

## F4 · Un solo exportador BPMN y un solo pintor

### Tarea 10: Datos de Appian en el diagrama y en el BPMN

**Ficheros:**
- Modificar en `skills/appian-diagramas-bpmn/scripts/`: `drawio_modelo.py`, `diagrama.py` (`_limpio` conserva las
  claves nuevas), `bpmn_export.py`, `selftest.py`; y `SKILL.md`.
- Crear: `ejemplos/semantico.json` (el proceso de `proceso_semantico.bpmn` de ingeniería inversa).

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
  en el analista, `SKILL.md`, `references/mermaid-diagrams.md`, `references/actualizacion.md` y `scripts/selftest.py`.

**Interfaces:**
- `mermaid.py <ficheros .mmd> [-o carpeta] [--check] [--svg] [--width N] [--md fichero.md …]`: con `--md` valida cada
  bloque ```mermaid y dice en qué línea empieza el que falla. Sale 0 bien, 1 sintaxis, 2 falta un requisito.

- [ ] **Paso 1:** selftest de diagramas: `--check` de un `.mmd` válido → 0 y de uno inválido → 1; `--md` de un
  Markdown con dos bloques, uno roto en la línea 12 → 1 y «línea 12» en la salida. → FALLA.
- [ ] **Paso 2:** mover, añadir `--md` y cambiar las rutas del analista. **Paso 3:** los dos selftest en verde. Commit.

### Tarea 12: Ingeniería inversa dibuja con la skill de diagramas, también sin navegador

**Ficheros:**
- Modificar en diagramas: `scripts/colocacion.py` (colocación de reserva sin navegador: capas de izquierda a derecha y
  un carril por perfil, la de `bpmn_layout.py`), `scripts/diagrama.py` (`crear` sin navegador escribe el `.drawio`, avisa
  «sin PNG» y sale con 2 solo por la imagen), `scripts/navegador.py` (`DIAGRAMAS_SIN_NAVEGADOR=1` simula que no hay), `selftest.py`.
- Modificar en ingeniería inversa: `agents/process-modeler.md` (escribe `08-procesos-bpmn/<slug>.json` con `nodo`,
  `temporizador`, `proceso_llamado` y `condicion`; después `diagrama.py crear` y `diagrama.py bpmn`),
  `references/bpmn-mapping.md` (nodo de Appian → tipo de paso y claves), `references/mermaid-rules.md` (qué se dibuja;
  sin las reglas del validador), `SKILL.md` (fase 5: `mermaid.py --md` en cada documento con Mermaid; sin navegador se
  dice y se sigue), `agents/{pdf-publisher,dashboard-publisher}.md` (imágenes de `mermaid.py --svg` y de los `.png`),
  `tests/test_scripts.py` (quedan las pruebas de `detect_secrets`).
- Borrar: `scripts/bpmn_layout.py`, `scripts/validate_mermaid.py`, `scripts/render_diagrams.sh`,
  `tests/test_bpmn_layout.py`, `tests/fixtures/proceso_semantico.bpmn`.
- Crear: `tests/test_una_pieza.py`.

- [ ] **Paso 1: pruebas que fallan.** Selftest de diagramas con `DIAGRAMAS_SIN_NAVEGADOR=1`: `crear` de
  `semantico.json` escribe un `.drawio` sin pasos solapados, sale con 2 y dice «sin PNG»; `bpmn` de ese `.drawio` da un
  BPMN válido. `test_una_pieza.py` (excluyéndose a sí mismo): ningún fichero de la skill de ingeniería inversa menciona
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
- Borrar: `docs/bloque-b/`.
- Modificar: `pruebas/comprobar_plugin.py` (fuera de `EXTERNAS`, dentro de `REGLA_DOCS`; error si refactorización o el
  analista citan `as-is/extraccion` o `mcp_raw`) y `README.md`.

**Interfaces:**
- `propuesta.md`: `## 1. Alcance` (qué se rehace, qué se queda y los límites del equipo: plazo y lo que no se puede
  tocar) · `## 2. Diagnóstico` (fichas `**REF-nn — Problema**` con `Evidencia · Regla · Efecto · Prioridad · Esfuerzo`;
  Evidencia enlaza a `../as-is/…`; Regla = «BP nn §x») · `## 3. Solución` (por capa: `Capa · Qué se hace · Por qué ·
  Se descarta`, cada fila con sus REF) · `## 4. Migración y convivencia` · `## 5. Hoja de ruta` (`Fase · Qué · Depende de`) ·
  `## 6. Pendientes`.
- SKILL.md: «Qué hace y qué no», entradas (`as-is/`, alcance y límites), flujo, «Dudas de Appian» (bloque común) y
  `## Qué escribe` con `refactorizacion/propuesta.md`.

- [ ] **Paso 1:** quitar la skill de `EXTERNAS`: `comprobar_plugin.py` → FALLA (cita una skill que no existe).
- [ ] **Paso 2:** escribir la skill. **Paso 3:** `comprobar_plugin.py` → 6 skills, 0 errores. Commit «F5: skill de refactorización».

### Tarea 14: `comprobar_propuesta.py`, ejemplo y selftest

**Ficheros:**
- Crear: `skills/appian-refactorizacion/scripts/{comprobar_propuesta.py,selftest.py}` y
  `ejemplos/mantenimiento/{as-is/datos/*.json,as-is/anexo/…,refactorizacion/propuesta.md}` (ficticio y pequeño).

**Interfaces:**
- `comprobar(p: Path) -> tuple[list[str], list[str]]`. Errores: falta un apartado; una REF sin evidencia o con un enlace
  a `as-is/` que no existe; una «BP nn §x» que `appian-best-practices/scripts/seccion.py nn x` no encuentra; en
  Diagnóstico o en «Sustituye a», un nombre con el prefijo de la app que no está en `as-is/datos/inventario.json`; una
  REF que no aparece en Solución. Aviso: una REF que no está en la Hoja de ruta.

- [ ] **Paso 1:** selftest: el ejemplo pasa (0/0) y cuatro copias rotas (evidencia rota, «BP 99 §1», objeto inventado en
  Diagnóstico, REF sin Solución) dan su error; un objeto nuevo en Solución no da error. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** `comprobar_plugin.py --completo` en verde. Commit.

### Tarea 15: Evaluación de malas prácticas sembradas

**Ficheros:** Crear `pruebas/evaluaciones/malas-practicas/{README.md,puntuar.py}`; resultados en `docs/evaluaciones.md`.

**Interfaces:**
- `puntuar.py <propuesta.md> [--ocultas]`: una mala práctica cuenta si una REF cita en su evidencia alguno de sus
  objetos, su regla es del documento de BP esperado y la REF tiene alternativa en Solución. Sale 0 con el 90 % o más.

- [ ] **Paso 1:** un agente ejecuta refactorización en el proyecto de prueba `$PROYECTOS_PRUEBA/MNT/` siguiendo el SKILL.md.
- [ ] **Paso 2:** 9 de 10 y 3 de 3 ocultas, y `comprobar_propuesta.py` sin errores. Resultados a `docs/evaluaciones.md`.
- [ ] **Paso 3:** commit. Cierre de fase: revisión y merge.

---

## F6 · Analista

### Tarea 16: Citas de IDs de otras skills

**Ficheros:** Modificar `skills/appian-functional-analyst/scripts/modelo.py` y `scripts/selftest.py`.

**Interfaces:** `modelo.quita_citas(texto) -> str` borra los tramos `[FU-nn …]` antes de buscar IDs; lo usan la búsqueda
de referencias de `modelo.py`, `indice.py` y `comprobar.py`.

- [ ] **Paso 1:** selftest: en una copia del ejemplo, una línea con «[FU-07 PAN-03]» no aparece en `indice.py impacto PAN-03`
  y no cuenta como referencia a la PAN-03 del análisis. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** selftest en verde. Commit.

### Tarea 17: Guion de la próxima reunión

**Ficheros:** Modificar `scripts/indice.py`, `scripts/selftest.py`, `SKILL.md`, `references/actualizacion.md`.

**Interfaces:** `indice.py pendientes <p>`: Markdown con las PC abiertas (sin tachar) agrupadas por «A quién»; cada una
con pregunta, opciones y «Afecta a». Peso = elementos de «Afecta a» separados por comas + líneas fuera del §11 que citan
la PC. Dentro de cada grupo, de más peso a menos y, a igual peso, por ID.

- [ ] **Paso 1:** selftest: en `autorizaciones` salen PC-01 y PC-02 bajo «Responsable de la unidad» y no sale PC-03; en
  una copia con una PC-04 que afecta a cuatro elementos, PC-04 sale la primera. → FALLA.
- [ ] **Paso 2:** implementar `c_pendientes`. **Paso 3:** selftest en verde. Commit.

### Tarea 18: Texto que queda viejo

**Ficheros:** Modificar `scripts/comprobar.py`, `scripts/selftest.py` y `references/actualizacion.md` (el paso «Texto que
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
  a`, con Situación = Nuevo, Modifica, Existe o Sustituye; §2: una DT cita «[FU-nn REF-nn]» en «Necesidad»; sin `as-is/`
  todo sigue como hoy), `references/ingesta-fuentes.md` y `scripts/leer_fuentes.py` (opción `--una-fuente`: `as-is/`
  entra como una sola FU con el índice de sus documentos; `propuesta.md`, como cualquier fichero), `scripts/comprobar.py`,
  `scripts/selftest.py`, `SKILL.md` (modo evolutivo y de refactorización).
- Crear: `ejemplos/evolutivo/` (ficticio: `as-is/datos/` de la app DEM del simulador, una `refactorizacion/propuesta.md`
  pequeña y un análisis con tres historias nuevas).

**Interfaces:** `comprobar.comprobar_as_is(m)`, solo si existe `<p>/as-is/datos/inventario.json`. Errores: historia sin
«Origen»; «Corrige H-xx» en una tabla del DF; una cita de hallazgo que no está en `hallazgos.json`; en §13, «Modifica» o
«Existe» con un objeto que no está en el inventario, «Nuevo» con uno que sí está, o «Sustituye» sin un objeto del
inventario; con propuesta, una REF de su Solución sin DT que la cite o un §3 sin la tabla de migración.

- [ ] **Paso 1:** selftest: `ejemplos/evolutivo` pasa; cinco copias rotas dan su error; `leer_fuentes.py --una-fuente`
  cataloga `as-is/` como una FU; y `ejemplos/autorizaciones`, sin `as-is/`, da exactamente los mismos errores y avisos
  que antes. → FALLA.
- [ ] **Paso 2:** implementar y escribir el ejemplo. **Paso 3:** selftest en verde. Commit.

### Tarea 20: Aviso de parte mal hecha

**Ficheros:** Modificar `scripts/comprobar.py`, `scripts/selftest.py` y `SKILL.md`.

**Interfaces:** dentro de `comprobar_as_is(m)`: aviso por cada fila de §13 «Modifica» o «Existe» cuyo objeto tiene un
hallazgo de severidad Alta: «DEM_X tiene H-SEG-01 (Alta): ¿pasa antes por refactorización?».

- [ ] **Paso 1:** selftest con `ejemplos/evolutivo` (un objeto con un hallazgo Alta) → el aviso cita su H. → FALLA.
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
`esperado.json`, `puntuar.py` y `ocultas/`; en el ejemplo ATP de prototipos, dos PAN validadas (🔒). Cada caso se
ejecuta en su proyecto de `$PROYECTOS_PRUEBA/` y los resultados van a `docs/evaluaciones.md`.

- Incoherencias: un DF ficticio (1.0) y tres reuniones (`.txt` con marcas de tiempo) con 10 incoherencias sembradas y
  3 más ocultas; `esperado.json` = `[{"fuente", "minuto", "piezas", "tipo"}]`. `puntuar.py` cuenta las que aparecen en
  los informes con su pieza y como «requiere aprobación», y comprueba que no se aplicó ninguna sin ella. Criterio: todas.
- Demo: un comentario de demo por cada una de 6 pantallas del ATP, dos de ellas validadas; `esperado.json` = PAN que
  cambian. `puntuar.py` compara los `app.json`: cambian las 4 no validadas y las 2 validadas solo con aprobación.
- Evolutivo: tres historias nuevas sobre la aplicación ficticia; `esperado.json` = la Situación de cada objeto de §13.
  `puntuar.py` compara (marcarlo todo «Nuevo» no pasa) y `comprobar.py` sin errores.

- [ ] **Paso 1:** un agente hace cada caso siguiendo los SKILL.md. **Paso 2:** cada `puntuar.py` cumple su criterio.
- [ ] **Paso 3:** commit. Cierre de fase: revisión y merge.

---

## F7 · Cualquiera del equipo puede usarlo

### Tarea 23: `requisitos.py`

**Ficheros:** Crear `requisitos.json`, `requisitos.py` y `pruebas/requisitos-esperado.json` en la raíz; modificar
`pruebas/comprobar_plugin.py` (`--completo` ejecuta la prueba de requisitos).

**Interfaces:**
- `requisitos.json`: `[{"id", "nombre", "skills", "imprescindible", "solo_pruebas", "para", "sin_el", "instalar": {"windows", "macos", "linux"}}]`
  con `python` (3.9+), `playwright`, `navegador`, `node`, `docx`, `libreoffice`, `pdf` (pdftotext o pypdf), `uv`,
  `devmcp` (configuración encontrada con `config_files`, `server_entries` e `is_devmcp` de `devmcp_extract.py`),
  `appian-mcp-server`, `skill-pdf` (no se detecta: se informa) y, con `solo_pruebas`, `pytest` y `mcp`.
- `requisitos.py [--skill NOMBRE] [--json] [--breve] [--tabla-readme]`. Sale 1 si falta algo imprescindible para lo
  pedido. `--json`: `{"python": "3.12.1", "requisitos": [{…, "presente": bool}], "avisos": [...]}`. Navegador: el
  Chromium de Playwright, o Chrome o Edge en sus rutas habituales, sin abrir ninguno. `docx`: se busca en la carpeta
  actual y en la global de npm, como `df_docx.js`. `REQUISITOS_SIN=id,id` fuerza ausencias para las pruebas.
- Aviso si existe una copia suelta de una skill del plugin en `~/.claude/skills/` (dos versiones activas a la vez).

- [ ] **Paso 1:** prueba en `comprobar_plugin.py --completo`: con `REQUISITOS_SIN=playwright,docx`, la salida `--json`
  es igual a `pruebas/requisitos-esperado.json` salvo versión y rutas, y sale 0; con `REQUISITOS_SIN=python`, sale 1;
  con un `HOME` temporal que tiene `.claude/skills/appian-reverse-engineering/SKILL.md`, hay aviso. → FALLA.
- [ ] **Paso 2:** implementar. **Paso 3:** en verde. Commit.

### Tarea 24: Aviso al instalar

**Ficheros:** Crear `hooks/hooks.json`; modificar la sección «Requisitos» de cada SKILL.md (una línea:
`python3 <skill>/../../requisitos.py --skill <nombre>` antes de la primera tarea).

- [ ] **Paso 1:** comprobar con la documentación de plugins (agente `claude-code-guide`) cómo se declara un hook
  `SessionStart` de un plugin sin depender del shell (en Windows puede ir por PowerShell 5.1, que no tiene `||`) y cómo
  se cita su carpeta (`${CLAUDE_PLUGIN_ROOT}`).
- [ ] **Paso 2:** `--breve` siempre sale con 0 (si no, Claude no recibe el texto), imprime solo lo que falta y escribe la
  marca `~/.cache/appian-analisis-funcional/avisado-<versión>` después de imprimir. Prueba: con `HOME` temporal y
  `REQUISITOS_SIN=docx`, la primera vez lo dice y la segunda no imprime nada; con `REQUISITOS_SIN=python`, sale 0 y lo dice.
- [ ] **Paso 3:** `hooks.json` en la forma que da el Paso 1.
- [ ] **Paso 4 (Raúl):** instalar el paquete en Claude Code y en la app de escritorio con algo de la tabla sin instalar
  y comprobar que el primer mensaje lo dice. Resultado en `docs/evaluaciones.md`.
- [ ] **Paso 5:** commit.

### Tarea 25: README generado y nada personal

**Ficheros:** Modificar `README.md` (tabla entre `<!-- requisitos:inicio -->` y `<!-- requisitos:fin -->`) y
`pruebas/comprobar_plugin.py`.

**Interfaces:** `comprobar_plugin.py` da error si la tabla del README no es la salida de `requisitos.py --tabla-readme`,
o si un fichero que va al paquete contiene, con límite de palabra y sin distinguir acentos ni mayúsculas, `rgmoya`,
`raulogm`, `C:/Users/` o `C:\Users\` no seguido de `<usuario>`, `/home/claude`, `Proyectos IA` o «Raúl» y «Raul»; salvo
el autor en `.claude-plugin/plugin.json` y en `.claude-plugin/marketplace.json`.

- [ ] **Paso 1:** con un fichero temporal en una skill que diga `C:/Users/rgmoya`, `comprobar_plugin.py` da error, y el
  `HYDRAULIC` de `viewer-static.min.js` no lo da. → FALLA.
- [ ] **Paso 2:** implementar y regenerar la tabla. **Paso 3:** en verde sin el fichero temporal. Commit.

### Tarea 26: Pruebas en Windows, macOS y Linux

**Ficheros:** Crear `.github/workflows/pruebas.yml`.

- Matriz `ubuntu-latest`, `windows-latest` y `macos-latest` con Python 3.9 y 3.12: instala `playwright` (y
  `python -m playwright install chromium`), `pytest`, `mcp` y Node con `docx`; ejecuta `python pruebas/comprobar_plugin.py --completo`
  con `PYTHONUTF8=1`.
- [ ] **Paso 1:** subir la rama y ver la ejecución en las seis combinaciones. **Paso 2:** arreglar lo que falle en
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
  refactorización y se recorta, porque hoy tiene 1021 caracteres; diagramas nombra a refactorización si dibuja procesos objetivo.
- [ ] **Paso 1:** `comprobar_plugin.py` en verde. **Paso 2:** commit.

### Tarea 29: Prueba de enrutado

**Ficheros:** Crear `pruebas/enrutado.json` (`[{"peticion", "skill"}]`: unas 30, al menos 4 por skill y 6 frontera; un
tercio en `ocultas/`) y `pruebas/evaluaciones/enrutado/README.md`; resultados en `docs/evaluaciones.md`.

- Fronteras: «¿la rehacemos o la evolucionamos?» → refactorización; «revisa esta interfaz» → buenas prácticas;
  «documenta la app X» → ingeniería inversa; «añade estas historias a lo que ya hay» → analista; «dibuja el proceso de
  la app existente» → diagramas (con ingeniería inversa si no hay JSON); «enséñale al cliente cómo quedaría» → prototipos.
- [ ] **Paso 1:** comprobar si `claude plugin eval` está disponible (agente `claude-code-guide`) y, si lo está, pasar el caso con él.
- [ ] **Paso 2:** si no, un agente que solo ve las seis descripciones elige la skill de cada petición. Criterio: todas;
  si no, se ajustan las descripciones y se repite con las ocultas sin ver. **Paso 3:** resultados y commit. Cierre de fase: revisión y merge.

---

## F9 · Cierre

### Tarea 30: Punta a punta y revisión independiente

- [ ] **Paso 1:** con la aplicación ficticia: ingeniería inversa → refactorización de un módulo → funcional y técnico
  (con una reunión ficticia que cambia algo) → diagramas → prototipo → DF en Word. Todos los comprobadores sin errores.
- [ ] **Paso 2:** un agente que no ha visto el trabajo revisa la rama entera contra el diseño; se corrige lo que encuentre.
- [ ] **Paso 3:** commit.

### Tarea 31: Paquete, instalación limpia, versión y entrega

**Ficheros:** Crear `pruebas/empaquetar.py` (zip sin `.git`, `__pycache__`, `.pytest_cache`, `.github/`, `docs/`,
`CLAUDE.md`, `pruebas/evaluaciones/` ni `*.plugin`); actualizar el comando de empaquetado del README.

- [ ] **Paso 1:** empaquetar, descomprimir en una carpeta temporal y, desde ella, `requisitos.py --json` con
  `REQUISITOS_SIN` de todo lo opcional: coincide con `pruebas/requisitos-esperado.json`. Después,
  `pruebas/comprobar_plugin.py --completo` en verde desde la copia.
- [ ] **Paso 2:** `0.7.0-beta.1` en `plugin.json` y su fila en el README (qué cambia, una línea por skill);
  `comprobar_plugin.py --completo` en verde; paquete; etiqueta `v0.7.0-beta.1`; entregar el `.plugin`.
- [ ] **Paso 3 (Raúl):** desinstalar de su cuenta la skill suelta de ingeniería inversa (y avisar a quien la tenga) y
  archivar `~/Proyectos IA/appian-reverse-engineering`, que lleva `.git/re-historial.bundle`, la copia usada en F1.
