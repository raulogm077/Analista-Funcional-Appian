# Plan: método L.U.C.I.A. en el plugin

Fecha: 14 de octubre de 2026. Parte de `main` (`d6126a8`, 0.7.0-beta.4). Rama `metodo-lucia`. Análisis y diseño: `docs/diseno/2026-10-14-metodo-lucia.md`.

**Objetivo.** Adoptar de L.U.C.I.A. lo que encaja en Appian, sin burocracia nueva: la frontera en el paquete, el contexto bajo demanda, un repositorio git por proyecto, flujos con una sola fuente, criterios en Gherkin, issues repartidas por un script y QA con SAIL CLI.

**Cómo se trabaja.** Una rama local y la PR cuando Raúl lo diga, como pide el `CLAUDE.md`. Las fases 1, 3 y 4 no necesitan Appian; las demás usan el Dev MCP de Indra-spain y SAIL CLI desde Claude Code. Las pruebas con reuniones reales se hacen en una carpeta fuera de este repositorio; aquí solo llegan las lecciones, sin datos del cliente. Antes de cerrar cada fase, `python3 pruebas/comprobar_plugin.py` y, si cambia un script o una plantilla, el selftest de su skill. Antes de empezar, el anexo «Hechos comprobados» del diseño: lo que ya se comprobó, lo que se descartó y lo que falta comprobar. Si algo no está en estos dos ficheros, se pregunta a Raúl en vez de suponerlo.

## 1. Decisiones

Todas confirmadas por Raúl el 14 de octubre de 2026.

- **B1. QA incluido; F10, aparcado en lo demás.** Del F10 entran las issues, los flujos y el QA. Qué agente hace cada papel lo decide cada equipo; el tablero sigue fuera.
- **B2. La IA solo escribe en desarrollo** y, en una urgencia, en el entorno de corrección. A pruebas y producción llegan paquetes cuyos objetos ha revisado una persona. Una persona puede marcar una prueba como «no necesaria para avanzar», con motivo.
- **B3. Solo dos bloqueos nuevos:** escribir fuera de desarrollo (salvo el entorno de corrección en una urgencia) y un fallo en las pruebas de la propia issue, también las de QA, que nadie ha marcado como no necesario.
- **B4. Retoque cosmético construido:** el coste medido en T6 decide si se hace a mano en Designer.
- **B5. Requisitos en Gherkin.** Siguen fuera rama y Merge Request en Appian, cobertura, issues por repositorio, cerebro por MCP y aduana de modelos.
- **B6. La issue es un fichero** en `construccion/<U>/`, sin GitHub Issues: ataría el método a una plataforma, duplicaría la fuente y añadiría llamadas en cada paso. Reservar una issue es un commit. Si alguien necesita un tablero, un script lo publicará en un solo sentido.
- **B7. Los flujos viven en el plugin.** `AGENTS.md` y `.agents/workflows/` se generan enteros en cada proyecto y no se editan; sin `.agents/skills/`.
- **B8. QA con SAIL CLI**, como en el diseño («QA con SAIL CLI»): casos de prueba guardados en la sesión de construir; escenarios en otra sesión, solo con los `.feature` y por unidad completa, con guiones que se repiten sin IA.
- **B9. Un repositorio git por proyecto**, alojado donde diga cada proyecto, con todo lo del proyecto (también las fuentes; las grabaciones no, porque git no está pensado para vídeos grandes) y trabajado sobre main.

## 2. Tareas

### Fase 1 · Contexto bajo demanda

- [x] **T1. Medir y clasificar.** Repetir con la versión actual el caso de «Agilidad» (fuente corta y retoque de prototipo) con una reunión de `Cerebro_Corporativo_Transcripciones` y el plugin cargado desde la carpeta (`claude --plugin-dir`, pendiente en `siguiente-version.md`). Por paso: minutos, llamadas, qué se leyó y de qué color es.
- [x] **T2. Corregir los cuatro puntos de «Agilidad»** de `docs/siguiente-version.md`, según T1: qué se lee en un retoque de prototipo; el analista consulta con `indice.py` en vez de leer funcional y técnico enteros; la nota de la fuente, proporcional al original; el DF sin esperar al prototipo, con las capturas después.
- [x] **T3. Volver a medir** el mismo caso y anotarlo en `docs/evaluaciones.md`, sin datos del cliente.
- [x] **T4. Tres líneas en el `CLAUDE.md`:** antes de añadir algo, «¿de qué color es este paso?» y «¿seguiría funcionando sin IA?»; y, tras cada prueba con reuniones reales, la lección que pide un cambio va a `siguiente-version.md`, sin datos del cliente.

### Fase 2 · El Dev MCP y SAIL CLI en Indra-spain

- [x] **T5. Mirar el Dev MCP y SAIL CLI reales**, como pide el `CLAUDE.md`: qué herramientas crean y ejecutan casos de prueba, si lanza las pruebas en bloque, si da los dependientes de un objeto y qué quita `LCP_TOOL_MODE=readonly`. Con SAIL CLI: entrar con una cuenta local por rol, cada una en su `--data-dir`, recorrer un escenario y leer su `--json`. `verificar` reconocerá las herramientas por su firma, como ya hace `devmcp_extract.py`, sin fijar nombres.
- [x] **T6. Línea base del retoque construido**, a ciegas ×3 y antes de tocar nada: el texto de un botón ya construido (encargo, Dev MCP, `verificar` y `construida`). Decide B4.

### Fase 3 · Repositorio, flujos y estructura

- [x] **T7. Catálogo de flujos F1 a F9:** un fichero corto por flujo en el plugin, con pasos, quién y qué skill; enlaza el detalle de cada skill sin repetirlo.
- [x] **T8. `proyecto.py iniciar`** deja el proyecto como repositorio git: lo crea si no lo es, con su `.gitignore`, y añade `AGENTS.md` (generado entero; lo propio del proyecto sigue en `proyecto.md`), `CLAUDE.md` con «@AGENTS.md», `.agents/workflows/` y `qa/`. Si se vuelve a lanzar, pone al día `AGENTS.md` y los flujos y no toca lo demás. `proyecto.py estado` avisa si hay cambios sin subir, si el proyecto va por detrás del remoto, si `AGENTS.md` o los flujos son de otra versión o si el `CLAUDE.md` no importa `AGENTS.md`. *Hecho con dos diferencias: `qa/` y `construccion/<U>/` no se crean vacías (git no las guarda; las crea el script que escribe en ellas, como dice el diseño) y se añade un `.gitattributes` para que git no cambie los finales de línea.*

### Fase 4 · Requisitos en Gherkin

- [x] **T9. Criterios de una línea** con dado, cuando y entonces, y su ID, en las plantillas y las instrucciones del funcional y del DF. Con `--anterior`, `comprobar.py` avisa del criterio nuevo o cambiado que no lo cumple; los viejos se reescriben cuando se cambian.

### Fase 5 · Issues y construcción

- [x] **T10. Columna «Para» en técnico §13:** el requisito (HU, PAN o ACT) de cada objeto, o «Base». `comprobar.py` avisa del objeto que no la tiene.
- [x] **T11. `indice.py issues <p> <U>`** sustituye a `indice.py encargo`: escribe en `construccion/<U>/` el índice y, por issue, `ISS-nn.md`, `ISS-nn.feature` y lo esperado. `--siguiente` da la próxima y la reserva con un commit y un push; si el push falla porque otro la reservó antes, da la siguiente. Un criterio que aún no está en Gherkin pasa tal cual, con aviso. Se prueba con datos ficticios.
- [x] **T12. Solo se escribe en desarrollo.** En `devmcp-setup.md` y el README: fuera de desarrollo y del entorno de corrección, el Dev MCP va con `LCP_TOOL_MODE=readonly` y, donde se pueda, con un usuario que solo ve la aplicación. SAIL CLI, igual: en desarrollo y, en una urgencia, en el entorno de corrección. Técnico §0 lleva la URL de cada entorno, y `proyecto.py estado` avisa si el Dev MCP de otro entorno no está en solo lectura (`requisitos.py` ya sabe leer su host). *Hecho con la decisión de Raúl del 14 de octubre: `LCP_TOOL_MODE` no hace nada en el Dev MCP 26.6.110 y no se añade maquinaria; fuera de desarrollo, una cuenta que solo ve la aplicación, la misma por entorno; sin aviso en `estado`.*
- [x] **T13. Pruebas de la issue.** Técnico §14 dice cómo se comprueba cada criterio: caso de prueba guardado (regla: salida esperada; interfaz: sin errores) o SAIL CLI, que es del QA (T15). Al terminar la issue se ejecutan solo los casos de sus reglas e interfaces y de lo que las usa; un retoque que no cambia criterios ni reglas no ejecuta nada. Bloquea un fallo en lo de la issue, salvo que una persona lo marque con `--sin-prueba <caso> --motivo «…»`, que se niega con `--desatendida`, como ya hacen `aprobada` y `produccion`; un fallo fuera de la issue es un aviso. `verificar` lee el resultado de cada prueba. La regresión, siempre: los casos de toda la aplicación, en bloque en Appian, antes de preparar el paquete; si el Dev MCP no puede ejecutar casos, los de la issue esperan a ella. *Hecho: el Dev MCP no ejecuta casos en bloque (T5), así que la regresión la pasa un script objeto a objeto (`devmcp_extract.py regresion`), como decidió Raúl.*
- [x] **T14. Aviso de revisión.** Si la unidad cambia datos, seguridad, integraciones o procesos en curso (las filas de «Cambio sobre lo construido»), o usa IA, al aprobarla (`proyecto.py cambio … aprobada`) y en la issue sale «que una persona revise DT-nn antes de construir». Es un aviso, no una puerta.

### Fase 6 · QA con SAIL CLI

- [x] **T15. Skill appian-qa**, con el método de «QA con SAIL CLI»: por unidad completa y en otra sesión, solo con sus `.feature`; cada rol con su cuenta y su `--data-dir`; el «entonces» se comprueba en el `--json`; cada recorrido que pasa queda como guion en `qa/<U>/`, y un script del plugin los repite sin IA antes de cada paquete. Un fallo devuelve su issue a pendiente. El flujo va también a `.agents/workflows/`, para cualquier agente.
- [x] **T16. Ensayo de QA en Indra-spain.** Una unidad de prueba con defectos sembrados: una regla que rompe otra, una transición de estado mal, un rol que ve de más y un fallo visual. Se prueba de tres formas: quien construye en su misma sesión, QA en otra sesión con el mismo modelo y QA con otro modelo (Sonnet 5.5, decidido por Raúl); y SAIL CLI frente a Playwright CLI en los mismos escenarios. Por forma: defectos encontrados, tokens y minutos. Decide el modelo del QA y si entra Playwright.

### Fase 7 · Medir y pasar a producción

- [x] **T17. Volver a medir** el retoque construido como en T6: no debe costar más.
- [x] **T18. Revisión humana y trazabilidad.** Una línea en `cambios.md` §6 y en `urgentes.md`: quien prepara el paquete revisa en Compare and Deploy la comparación de los objetos, como en un Merge Request, junto con los fallos de la regresión (casos de prueba y guiones de QA) y las pruebas marcadas como no necesarias; se promueve el mismo paquete con un ICF por entorno; y, si el despliegue es directo o por API, se activa «Require review». `produccion --ref` lleva la referencia del pase en el cliente. Sin script nuevo.

## 3. Más adelante, solo si pasa

- Un tablero que publique las issues en un solo sentido, si alguien lo necesita para seguir el proyecto.
- Playwright CLI para lo que SAIL CLI no ve, si T16 lo justifica.
- Contexto común del cliente (convenciones, sistemas, decisiones transversales), cuando dos o más proyectos del mismo cliente usen el plugin, junto al cerebro corporativo.
- Desplegar con la API o el MCP de despliegues, si un cliente lo usa.
- Flujos de mantenimiento de plataforma (subida de versión, plug-ins, Health Check) y de prueba de concepto técnica.

## 4. Pasos de Raúl

- Cuentas locales de prueba en Indra-spain, una por rol, para SAIL CLI (T5 y T16).
- Mirar el resultado de T1 antes de T2.
- Decir cuándo se abre la PR.

## 5. Criterios

- **Fase 1:** la IA no lee entero un documento que `indice.py` o `seccion.py` pueden consultar por partes; la sesión de T3 baja en minutos y llamadas frente a T1; el retoque de análisis sigue en 25 llamadas o menos.
- **Fase 2:** se sabe qué puede probar el Dev MCP y cómo entra SAIL CLI con cada rol, sin fijar nombres de herramientas, y hay línea base del retoque construido.
- **Fase 3:** dos proyectos nuevos tienen la misma estructura y son repositorios git; tras cambiar de versión, `AGENTS.md` y los flujos se ponen al día sin tocar `proyecto.md`; `estado` avisa de lo que no está subido.
- **Fase 4:** cada criterio nuevo tiene dado, cuando y entonces, y su `.feature` sale sin IA.
- **Fase 5:** con los mismos datos, `indice.py issues` da las mismas issues, con el mismo número; dos agentes que piden `--siguiente` a la vez no se llevan la misma; ninguna pide leer un documento entero; fuera de desarrollo, el Dev MCP no ofrece herramientas que escriban (no se cumple tal cual: decisión de Raúl en T12); un cambio en una regla que rompe otra que la usa se detecta antes de dar la issue por hecha; un retoque que no cambia criterios ni reglas no ejecuta pruebas.
- **Fase 6:** el QA encuentra los defectos sembrados que le tocan, sus guiones se repiten sin IA con el mismo resultado y un retoque no lanza QA.
- **Fase 7:** el retoque de T17 no cuesta más que el de T6, y quien prepara el paquete sabe qué revisar sin preguntar.
- **Siempre:** ningún paso obligatorio nuevo en un retoque cosmético y ningún documento nuevo escrito a mano por cambio.

## 6. Estado al terminar (14 de octubre de 2026)

Hechas T1 a T18 en la rama `metodo-lucia` (en GitHub, sin PR); lo medido, lo revisado y lo que no se cumple tal cual, en
`docs/evaluaciones.md` («Método L.U.C.I.A.»); lo que surgió y no entra, en `docs/siguiente-version.md`. Las pruebas con
datos reales y con el entorno de desarrollo, fuera del repositorio, en `Proyectos IA/Pruebas-plugin/` del equipo de Raúl;
la aplicación ficticia DEM del entorno de desarrollo queda sin defectos y con la acción «Nueva solicitud».

Lo que decide Raúl antes de la PR:
1. **B4**: con las cifras de T6 y T17 (unos 4 minutos y 2 USD por retoque construido), si un retoque cosmético se hace a
   mano en Designer.
2. **El modelo del QA y Playwright** (T16): la recomendación es Sonnet 5.5 y Playwright solo para lo que solo se ve en
   pantalla; está escrito así en `appian-qa` y en F8.
3. **«El Word no espera al prototipo»** (T2): sin efecto medido en cuatro sesiones; quitarlo o dejarlo.
4. **Los minutos de más de T17**: +1,2 por retoque tras optimizar `verificar` (4,1 frente a 2,9), con un 30 % menos de llamadas y un 18 % menos de coste; el resto es el arranque del Dev MCP y el recorrido de la issue.
5. **La versión del plugin** (sigue en 0.7.0-beta.4) y su fila en el README.
6. **El diseño y su anexo**: lo que ya no es verdad (`LCP_TOOL_MODE`, la regresión «en bloque», las 5.600 líneas, la ruta
   de verificación, el cierre de las sesiones de SAIL CLI); el texto que propone la revisión final está en el historial de
   este plan (commit `b8d12c8`, apartado 6 de entonces).
