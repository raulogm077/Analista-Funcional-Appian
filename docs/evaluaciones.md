# Evaluaciones y cierre de fases

Resultados de las evaluaciones del plan `docs/plan/2026-10-07-integracion-ingenieria-inversa.md` y, al cerrar cada
fase, el resumen de cambios, lo aprendido y lo que queda aplazado, con la tarea que lo recoge. Los proyectos de prueba
están en `$PROYECTOS_PRUEBA`, fuera del repositorio; aquí solo los resultados.

## F2 · Ingeniería inversa en el plugin (8 de octubre de 2026)

Rama `f2-ingenieria-inversa`, de `main` 4938606 al merge. Versión 0.7.0-alpha.1.

### Qué cambia

- **Skills solo con lo que usan al trabajar (Tareas 0 y 0b).** Las pruebas y sus datos ficticios pasan a
  `pruebas/<skill>/` y el caso de ejemplo de prototipos sale del plugin. `comprobar_plugin.py` da error si una skill
  lleva pruebas, ejemplos, un proyecto o la marca de un cliente, y `--completo --plugin` pasa las mismas pruebas sobre
  la copia del paquete.
- **La marca de cualquier cliente (Tareas 0b y 0c).** `appian-prototipos-aena` pasa a `appian-prototipos`, con la
  marca estándar de Appian por defecto; la de un cliente va en `<p>/prototipo/`. `marca.py web` saca de su web los
  colores, el logo y la tipografía, y `marca.py crear`, la configuración completa (Site, perfil CSS, paleta, estados,
  gráficos y `marca-<id>.md` para quien construye) con el contraste AA ya ajustado.
- **Ingeniería inversa, solo el bloque A (Tarea 1).** Documenta sin juzgar ni rehacer. El bloque B espera a F5 en
  `docs/bloque-b/`.
- **La extracción, en el proyecto y tal cual (Tareas 2 y 2b).** `as-is/extraccion/` con rutas cortas; al repetir o
  retomar no se vuelve a pedir lo descargado. Nada se oculta (Raúl, 8 de octubre): la detección de secretos sigue,
  también en cabeceras y literales SAIL, porque un secreto escrito en la app es un hallazgo.
- **Alta en el plugin (Tarea 3).** Ingeniería inversa entra en la prueba completa y en la regla común de dudas de
  Appian, igual en las tres skills que la llevan y válida con el plugin instalado. El comprobador exige `appian-docs`
  en `.mcp.json`.
- **Revisión de la fase.** Una carpeta es de una aplicación y un entorno: con otro entorno, el extractor sale con 15
  salvo con `extract --refresh`, y avisa cuando reutiliza respuestas de otra ejecución. La orden zip del README deja
  fuera lo de desarrollo (lo comprueba `comprobar_plugin.py`) y el paso 5 de prototipos entrega el perfil CSS que
  escribe `build.py`, también con una marca hecha a mano.

### Pruebas

- `comprobar_plugin.py --completo`: 5 skills, 0 errores y 0 avisos, en el repositorio y en la copia del paquete.
- Ingeniería inversa: 89 pruebas en verde, entre ellas retomar en otra ruta, con espacios y en otro entorno.
- Scripts de `skills/` y `pruebas/`: se analizan e importan con Python 3.9.
- Galerías y plantillas: se regeneran idénticas, byte a byte. La galería de antes, construida con el kit nuevo y la
  marca de AENA del historial, solo cambia el gris del pie del visor de documentos.

### Lo aprendido

- La revisión por tarea, con agentes y varias rondas, alargó la fase. Desde F3: una revisión independiente por fase y
  las tareas pequeñas en línea (Raúl, 8 de octubre).
- La decisión de no ocultar nada llegó a mitad de fase y dejó sin objeto el saneado de la Tarea 2 y una ronda de
  correcciones. Las decisiones de datos y privacidad se toman antes de empezar una fase. Desde ahora, el alcance está
  congelado hasta F9 y lo nuevo va a `docs/siguiente-version.md`.
- La revisión de la fase vio lo que no ven las de tarea: el entorno al retomar (cruza las Tareas 2 y 3), la versión
  sin subir y la orden zip del README. Se revisa la rama entera y también la copia del paquete.
- Claude Code no actualiza un plugin mientras su versión no cambia. Cada fase que llega a `main` sube la versión
  (0.7.0-alpha.N) y F9 cierra con la 0.7.0-beta.1.
- Con el plugin instalado, las herramientas MCP se llaman `mcp__plugin_<plugin>_<servidor>__…`: los textos de las
  skills nombran el servidor, no el prefijo.
- Las restricciones globales (rutas cortas, nada fuera de `<p>`, nada oculto) se prueban ejecutando y mirando el
  disco, no buscando frases en los textos.

### Aplazado

| Dónde | Qué | Tarea |
|---|---|---|
| `references/presentation-rules.md` | «códigos internos de patrones (DAT-02)», resto del bloque B. En el plan, «… y usuarios» ya sobra | 4 |
| `scripts/detect_secrets.py` | Falso positivo con `headers: {Authorization: "Bearer " & cons!X}` en un mapa SAIL, con su prueba | 6 u 8b |
| `assets/markdown-templates/LEEME.md`, `agents/pdf-publisher.md`, `references/response-format.md` | «reingeniería» → «ingeniería inversa», y `reingenier` en `PROHIBIDO` de `test_sin_bloque_b.py` | 8 |
| `agents/ui-rules-analyzer.md` | «independientes de la tecnología… sin abrir el código original» (enfoque de reconstrucción) | 8 |
| `agents/data-modeler.md`, `agents/interface-analyzer.md` | Punteros viejos a `docs-mcp-usage.md` y caché de consultas web | 8 |
| `SKILL.md` de ingeniería inversa | El último punto de la regla común («qué conviene hacer») llega a los subagentes | 8 |
| `scripts/build_model.py` | `slugify` sin tope nombra `extraccion/procesos/`, `anexo/<tipo>/` y `08-procesos-bpmn/`: el recorte de `safe_name` y una prueba con un nombre de 150 caracteres | 8b o 12 |
| `scripts/detect_secrets.py`, `references/response-format.md` | La ubicación de un secreto en un `.json` lleva el prefijo `response.`; «(detalle en el registro de 09)» | 8b |
| `README.md` | Quien solo tiene el paquete no puede comprobar su equipo: la comprobación pide el repositorio | 23 |
| `SKILL.md` de ingeniería inversa | Usa `python3` sin «en Windows, `python`» | 24 |
| `README.md` | Requisitos de ingeniería inversa (`uv`, Dev MCP 26.5+ con rol Designer, solo en el equipo); retirar también la `appian-reverse-engineering` suelta; en «Confidencialidad», que `as-is/` lleva la extracción tal cual y se sincroniza | 25 |
| `skills/appian-functional-analyst/SKILL.md` | La descripción dice «no audita aplicaciones existentes»: «no documenta…» | 28 |
| `.claude-plugin/plugin.json`, `marketplace.json` | La ingeniería inversa, en la descripción y en las keywords | 28 o 31 |

Sin tarea en este plan, en `docs/siguiente-version.md`: lo pendiente de `marca.py` y las copias de conflicto de
OneDrive en la extracción.
