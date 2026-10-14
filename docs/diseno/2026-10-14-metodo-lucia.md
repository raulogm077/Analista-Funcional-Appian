# Método L.U.C.I.A. en el plugin: diseño

Análisis del 12 al 14 de octubre de 2026 sobre la 0.7.0-beta.4 (`d6126a8`) y el artículo [L.U.C.I.A. al detalle técnico](https://dev.to/raguilera82/lucia-al-detalle-tecnico-8dk). El plan está en `docs/plan/2026-10-14-metodo-lucia.md`; las decisiones B y las tareas T remiten a él.

El plugin ya aplica, a la manera de Appian, buena parte de L.U.C.I.A. Lo que aporta es su frontera: la IA prepara, y desde el paquete todo lo hacen Appian y scripts, con la firma de personas. Con las dos rondas de observaciones de Raúl, el plan son once cambios acotados y tres mediciones; entre ellos, un repositorio git por proyecto, flujos con una sola fuente, requisitos en Gherkin, issues repartidas por un script y QA con SAIL CLI.

## Conclusiones

1. **El plugin ya hace buena parte de L.U.C.I.A., traducido a Appian.** Tiene los requisitos versionados con su fuente y lo mecánico en scripts (`proyecto.py`, `indice.py encargo`, `verificar`). Una persona aprueba lo que importa: el analista, el informe de impacto; el jefe de proyecto, la unidad. Las decisiones llevan su alternativa descartada (DT) y las urgencias van por un camino corto. El artículo confirma el rumbo; no pide rehacer nada.
2. **Lo que vale del método no es su ceremonia, sino su frontera.** La IA propone y prepara; desde el Merge Request todo es determinista y lo firma una persona. En Appian, ese punto es el paquete. Y dos reglas de fondo: IA solo donde hay carga cognitiva, y el contexto se consulta bajo demanda, sin cargar el corpus entero.
3. **Copiado tal cual, repetiría appian-harness.** Rama y Merge Request por tarea, TDD en todo, cobertura del 85 % y lint suponen un repositorio git con tests locales. Appian no tiene ramas, valida al guardar y guarda las pruebas dentro de la plataforma.
4. **Las observaciones de Raúl encajan, con ajustes por Appian.** Las issues se agrupan si comparten pantalla o proceso, con una «Base» primero: en un entorno compartido, dos issues no deben tocar el mismo objeto. El repositorio de cada proyecto se trabaja sobre main, sin ramas, porque el código está en Appian. Y SAIL CLI va en el QA de la unidad, en otra sesión, no en la issue.
5. **Quedan once cambios acotados y tres mediciones.** Están en «Lo que se adopta». Según lo medido, el que más ahorra sigue siendo que la IA consulte bajo demanda; la issue lo lleva a la construcción, porque trae solo el extracto que necesita.
6. **El mayor riesgo de burocracia está ahora en la construcción.** La skill oficial de Appian obliga a cargar su `SKILL.md` y siete referencias antes de cualquier llamada al Dev MCP: unas 5.600 líneas (228 KB) en cada sesión, sea cual sea el cambio. Por eso varias issues pueden ir en la misma sesión. Ahí puede volver la «hora por un cambio menor»: se mide antes de decidir y, si domina, un retoque cosmético se hace a mano en Designer.

## Observaciones de Raúl: a favor, en contra y qué se hace

Entran casi todas, también las de la segunda ronda, al final de la tabla. Se ajustan dos: las issues se agrupan por pantalla o proceso, y SAIL CLI va en el QA de la unidad, no en la issue.

| Observación | A favor | En contra | Qué se hace |
| --- | --- | --- | --- |
| El producto como pequeño cerebro: cada fuente nueva se encaja analizando su impacto | Es lo que ya hace el plugin: fuentes FU, informe de impacto que aprueba el analista, piezas 🔒 | Nada nuevo; el coste medido está en releer documentos enteros | **Ya existe.** La fase 1 lo abarata: consultar por partes |
| Repositorio del proyecto con su estructura y la visión del producto; el código vive en Appian | Un sitio común para personas y agentes, igual en cada proyecto y con su historial | Un product\_vision.md aparte repetiría funcional §1. Ramas y PR serían burocracia: el código no está ahí. Word, capturas y vídeos no se fusionan bien en git | **Sí, obligatorio** (B9): `proyecto.py iniciar` crea el repositorio; se trabaja sobre main, sin ramas; sube todo, también las fuentes, menos las grabaciones; el Word y las capturas se regeneran en vez de fusionarse. La visión es funcional §1 |
| Requisitos en Gherkin | Criterio comprobable y sin ambigüedad. Appian Max lo propone. Pasa a `.feature` sin IA y sirve a QA y a herramientas BDD | Alarga el DF. Los criterios actuales están escritos de otra forma. Los pasos de pantalla no los entiende el cliente | **Sí (B5):** un escenario de una línea por criterio, en lenguaje de negocio y con su ID de siempre. El `.feature` lo genera un script. Un criterio viejo se reescribe cuando se cambia |
| Una issue por requisito | Trazabilidad del requisito a la prueba; trabajo pequeño; el agente recibe solo lo que necesita | Varios requisitos comparten objetos (un record type, una pantalla, un proceso) y en paralelo chocan. Lo común no es de ningún requisito. Cada issue en una sesión nueva paga la carga fija de la skill oficial | **Sí, con dos ajustes:** si dos requisitos comparten pantalla o proceso, van en la misma issue; lo común (datos, grupos, constantes, sistemas conectados) va en una issue «Base», la primera. Varias issues pueden construirse en la misma sesión |
| El reparto lo hace un script que convierte el requisito en lo que espera el agente | Determinista y sin coste de IA. Ya hay base: `indice.py encargo` y las colisiones | Hoy el técnico no dice qué objeto sirve a qué requisito: el script tendría que adivinarlo | **Sí:** técnico §13 gana la columna «Para» (HU, PAN o ACT de cada objeto), el equivalente Appian del mapeo técnico del artículo. La issue lleva el extracto del técnico y del prototipo que necesita |
| La issue incluye las pruebas con SAIL CLI | Prueba como un usuario, con pocos tokens. Sus referencias se mantienen entre cargas, así que un recorrido se guarda como guion y se repite sin IA | Escrito en la issue, repite cada escenario en otro formato y antes de que exista la pantalla. Crea datos y lanza procesos: solo en desarrollo. No ve la pantalla dibujada | **Sí, en el QA de la unidad (B8), no en la issue:** la issue solo dice qué escenarios se comprueban con SAIL CLI (técnico §14); el guion lo deja QA después de construir, en `qa/` |
| `AGENTS.md` y `.agents/` con workflows y skills | Cualquier agente o persona trabaja igual; Claude Code lo lee si `CLAUDE.md` lo importa | Copiar skills al proyecto duplica el plugin y diverge. Si cada proyecto edita sus workflows, se pierde la fuente única | **Sí, generados:** `AGENTS.md` y `.agents/workflows/` los escribe el plugin y se regeneran al cambiar de versión. Sin `.agents/skills/`: son las del plugin y la oficial de Appian |
| Un script crea la estructura de forma determinista | Todos los proyectos iguales | Crear todas las carpetas, se usen o no, es ruido | **Sí:** se amplía `proyecto.py iniciar`. Las carpetas que no siempre hacen falta las crea, con nombre fijo, el script que escribe en ellas |
| El Dev MCP gana herramientas: ingeniería inversa, ejecutar casos de prueba… | Aprovechar lo nuevo sin esperar | Una regla escrita para una herramienta concreta se queda vieja | **Sí:** el plugin no fija la lista. Pregunta al Dev MCP qué ofrece y lo traduce a capacidades (leer, escribir, probar), como ya hace ingeniería inversa. Cada paso dice qué hacer con y sin cada capacidad |
| Despliegue con el método de cada cliente; más adelante, API o MCP | Neutral | — | **Sí:** el plugin registra el pase y pide la revisión de objetos; nada de un cliente concreto |
| Probar con el repositorio de reuniones y apuntar lecciones | Material real y mejora medida | Son datos de clientes: no pueden entrar en el repositorio del plugin. Un fichero de lecciones que nadie lee es burocracia | **Sí:** las pruebas se hacen fuera del repositorio. Una lección se apunta solo si pide un cambio y sin datos del cliente: pendiente en `siguiente-version.md`, aplicada en `evaluaciones.md` (ya existen) |
| Catálogo de flujos con fuente única | Todos trabajan igual y se ve el recorrido entero, hoy repartido entre skills | Un tercer sitio que cuente lo mismo que las skills | **Sí:** un fichero corto por flujo en el plugin (pasos, quién y skill) que enlaza el detalle de cada skill sin repetirlo. Catálogo, en «Cómo trabajaremos» |
| B2: una persona puede marcar una prueba como «no necesaria para avanzar» | No se bloquea por una prueba que no aplica o que depende de datos | Si se usa mucho, la red de regresión deja de proteger | **Sí:** con motivo y solo una persona, nunca en una sesión desatendida. Queda escrito en la unidad y sale en la revisión del paquete |
| B1: QA incluido; ¿lo prueba quien construye, en el mismo turno, o va aparte, quizá con otro modelo? | Aparte, prueba lo que se pidió y no lo que entendió quien construye; esa sesión no carga la skill oficial | Una sesión más por unidad, y una ida y vuelta si falla. L.U.C.I.A. no lo resuelve: pone los tests en el agente que construye y crea una issue de QA aparte, sin decir quién la hace | Los casos de prueba guardados, en la misma sesión de construir (T13). Los escenarios, en otra sesión, solo con los `.feature` y por unidad completa (T15). El modelo, el que gane el ensayo de T16 |
| Una skill que haga las pruebas con SAIL CLI | Un solo sitio para el método de QA; otros agentes lo siguen por `.agents/workflows/` | Otra pieza que mantener | **Sí: appian-qa** (T15), pequeña: escenario, SAIL CLI, guion en `qa/` y resultado |
| Playwright CLI además de SAIL CLI | Usa un navegador de verdad: ve la maquetación y los estilos, y puede grabar los pasos como código Playwright | Para los escenarios, SAIL CLI hace lo mismo con menos tokens, según Appian. Un guion de Playwright depende del HTML que genera Appian. No está entre las herramientas de prueba de interfaz que cita Appian | **No por defecto.** T16 lo compara con SAIL CLI en los mismos escenarios, con un defecto visual; entra solo para lo que SAIL CLI no ve, si compensa |
| B6: GitHub Issues, solo si no frena y aporta | Tablero, asignación y comentarios | Ata el método a una plataforma, y el alojamiento depende del proyecto. Dos fuentes que sincronizar y llamadas a una API en cada paso, como en el harness | **No, por ahora:** la issue es un fichero y reservarla es un commit. Si alguien necesita un tablero, un script lo publicará en un solo sentido |

## Cómo trabajaremos

Un repositorio git por proyecto, siempre con la misma forma; nueve flujos con una sola fuente; criterios en Gherkin; un script que convierte cada requisito en una issue lista para construir; y QA con SAIL CLI.

### El repositorio del proyecto

Lo crea `proyecto.py iniciar`, ya como repositorio git. Lo marcado «nuevo» es lo que se añade a lo que crea hoy.

```text
<proyecto>/
├── AGENTS.md              nuevo: dónde está cada cosa, reglas y flujos (generado entero; lo del proyecto, en proyecto.md)
├── CLAUDE.md              nuevo: solo «@AGENTS.md», para Claude Code
├── .agents/workflows/     nuevo: copia de los flujos del plugin (generada, no se edita)
├── .gitignore             nuevo: lo que no se sube (secretos, grabaciones)
├── proyecto.md            estado y siguiente paso
├── fuentes/ notas/ impacto/      lo que entra y cómo encaja
├── analisis/              funcional.md (visión en §1, historias con Gherkin), tecnico.md, decisiones.md, cambios.md, diagramas/
├── prototipo/             pantallas y capturas
├── construccion/<U>/      nuevo: issues de la unidad (índice, ISS-nn.md, ISS-nn.feature) y su verificación
├── qa/<U>/                nuevo: un guion de SAIL CLI por escenario y sus resultados
├── as-is/ refactorizacion/       solo si hay una aplicación existente
└── entregables/ versiones/
```

Sin `.agents/skills/` ni `product_vision.md`. El código sigue en Appian; el repositorio guarda todo lo demás, también las fuentes. Se trabaja sobre main: pull antes, push después, sin ramas ni PR. Reservar una issue es un commit. El Word, las capturas y los PNG de los diagramas se regeneran en vez de fusionarse. Dónde se aloja lo decide cada proyecto: los scripts solo usan git.

### Flujos

Un fichero corto por flujo en el plugin: pasos, quién hace cada uno y qué skill. El detalle sigue en las referencias de cada skill.

| Flujo | Cuándo | Empieza en | Termina en |
| --- | --- | --- | --- |
| F1 Aplicación nueva | Reuniones, correos o el DF del cliente para una aplicación que no existe | Analista | DF validado, técnico y la unidad EV-01 con sus issues |
| F2 Incorporar una fuente | Reunión, correo, documento, demo o comentarios al DF | Analista | Informe de impacto aprobado y cambios puntuales; un retoque, por el camino corto |
| F3 Evolutivo | Cambiar o ampliar una aplicación construida, propia o ajena ya documentada | Analista | Unidad EV aprobada, DF del cambio e issues |
| F4 Defecto | La aplicación no hace lo acordado y no es crítico | Analista | El escenario que lo reproduce y su issue de corrección |
| F5 Urgente | Algo crítico en producción | Analista | Ficha URG, corrección y reaplicación en desarrollo |
| F6 Ingeniería inversa | Entender una aplicación existente | Ingeniería inversa | `as-is/`; sigue por F3 (evolucionar una parte) o por F7 (rehacerla) |
| F7 Refactorización | Rehacer una aplicación, entera o una parte, desde cero | Refactorización | Propuesta validada, técnico con la migración y una unidad por fase |
| F8 Construir y verificar | Una unidad aprobada | Buenas prácticas, con la skill oficial; el QA, appian-qa | Issues construidas y verificadas, y la unidad con su QA, en desarrollo |
| F9 Pase a producción | Una unidad construida | Una persona | Objetos revisados, pase por el método del cliente y su registro |

Sin flujo propio, como variantes: DF del cliente ya hecho (F1), demo (F2), retoque (F2 y, si B4 lo decide, a mano en Designer), integración nueva (F3) y datos u operación en producción (F5). Más adelante: mantenimiento de plataforma (subida de versión, plug-ins, Health Check) y prueba de concepto técnica. «Probar el plugin con reuniones reales» es del propio plugin y va en su `CLAUDE.md`.

### Skills

Una nueva, appian-qa, para el QA con SAIL CLI. El reparto en issues es un script del analista y los flujos son documentos.

| Skill | Hace | Flujos |
| --- | --- | --- |
| `appian-functional-analyst` | Fuentes → funcional con Gherkin, DF y técnico; unidades e issues | F1 a F5, F7 |
| `appian-diagramas-bpmn` | Procesos en draw.io | F1, F3, F6 |
| `appian-prototipos` | Pantallas y capturas | F1, F3, F7 |
| `appian-reverse-engineering` | Documenta lo que existe y verifica lo construido | F6, F8 |
| `appian-refactorizacion` | Propone cómo rehacer | F7 |
| `appian-best-practices` | Doctrina y construcción | F5, F8 |
| `appian`, la oficial de Appian | Mecánica del Dev MCP | F8 |
| appian-qa | QA de la unidad con SAIL CLI; guiones repetibles en `qa/` | F8 |

### Requisitos en Gherkin

En el funcional y en el DF, cada criterio es un escenario de una línea, con su ID de siempre:

```markdown
Se acepta si:
- `HU-03.1` Dada una solicitud devuelta, cuando la unidad solicitante la reenvía, entonces vuelve a «En revisión» con el mismo número.
- `HU-03.2` Dada una solicitud en revisión, cuando la unidad solicitante intenta cambiarla, entonces no puede.
```

El script lo escribe en Gherkin formal para la issue y para QA:

```gherkin
# language: es
Característica: HU-03 Subsanar una solicitud

  Escenario: HU-03.1
    Dada una solicitud devuelta
    Cuando la unidad solicitante la reenvía
    Entonces vuelve a «En revisión» con el mismo número
```

Un «cuando» por criterio, en palabras del cliente y sin botones ni campos. Si no cabe en una frase, son dos criterios.

### Del requisito a la issue

1. Técnico §13 dice para qué requisito es cada objeto (columna «Para»). Lo común lleva «Base».
2. `indice.py issues <p> <U>` hace una issue por requisito. Los que comparten pantalla o proceso van juntos, y lo «Base», en la issue 1.
3. Las ordena por dependencias y marca cuáles pueden ir en paralelo: las que no comparten objetos.
4. Cada issue lleva lo que necesita el agente y nada más: el extracto del técnico y del prototipo, no la orden de leerlos enteros.
5. `--siguiente` da la próxima: la primera sin hacer cuyas dependencias están hechas. Una issue está hecha cuando su última verificación pasa y es de su versión actual; si al regenerarla cambia, vuelve a estar pendiente. Lo dice el fichero que deja `verificar`, sin otro estado que mantener a mano.
6. Se genera y no se edita: si cambia el análisis, se vuelve a generar y cada issue conserva su número.

Así se vería una, con datos ficticios:

```markdown
# ISS-03 · Subsanar una solicitud devuelta · EV-01
Requisitos: HU-03, HU-04 (comparten PAN-03) · Depende de: ISS-01 (Base) · En paralelo con: ISS-05

## Qué se pide
HU-03: como unidad solicitante, quiero corregir la solicitud devuelta para que siga su curso.

## Escenarios (ISS-03.feature) y cómo se comprueban
- HU-03.1 Dada una solicitud devuelta, cuando la unidad solicitante la reenvía, entonces vuelve a «En revisión» con el mismo número. → SAIL CLI

## Objetos
| Objeto                  | Tipo          | Situación | Qué dice el técnico                       |
| `AUT_SubsanarSolicitud` | Interfaz      | Nuevo     | §7 PAN-03; composición: prototipo PAN-03 |
| `AUT_ReenviarSolicitud` | Process model | Nuevo     | §8, nodo de ACT-06                        |
No tocar: `AUT Solicitud` (es de ISS-01).

## Terminar
verificar … --esperado ISS-03-esperado.json
```

### QA con SAIL CLI (B1 y B8)

SAIL CLI viene en el paquete del Dev MCP. Su ayuda (versión 26.6.110) dice tres cosas que deciden el método:

- Entra con una cuenta local de Appian, o importa la sesión SSO del Dev MCP, y cada sesión vive en su `--data-dir`: una por rol, y varias pruebas a la vez sin pisarse.
- Las referencias que imprime se mantienen entre cargas, así que un recorrido se puede escribir como guion; y `--json` da una salida que lee un script.
- No dibuja la pantalla: trabaja con lo que viaja entre Appian y el navegador. Maquetación y estilos quedan fuera.

Cómo se usa:

1. Técnico §14 dice qué criterios se comprueban con SAIL CLI; la issue lo lista, sin pasos.
2. Quien construye cierra su issue con los casos de prueba guardados (T13). Puede usar SAIL CLI mientras construye, pero no le hace falta para terminar.
3. Con la unidad completa, QA abre otra sesión, solo con los `.feature` de la unidad. Puede ser otro agente, como Antigravity: el flujo está en `.agents/workflows/`. Por escenario, prepara el «dado» como un usuario, lo recorre con la cuenta de su rol y comprueba el «entonces» en el `--json`.
4. Un recorrido que pasa se guarda como guion en `qa/<U>/`: las órdenes de SAIL CLI y lo que debe salir. Un fallo devuelve su issue a pendiente.
5. Antes de cada paquete, un script del plugin repite los guiones sin IA, y los fallos salen en la revisión de T18. Si una pantalla cambió a propósito, QA rehace su guion.
6. Solo en desarrollo, porque crea datos y lanza procesos; en una urgencia, en el entorno de corrección. Al terminar, `sail logout` borra la sesión y lo tecleado.
7. En un retoque cosmético no hay QA. Si cambia un texto que usa un guion, se rehace solo ese guion.

Lo que SAIL CLI no ve lo mira una persona con la captura, o Playwright si el ensayo de T16 lo justifica.

## La frontera en Appian

```text
Análisis (IA; validan analista y cliente)
  → Unidad aprobada (jefe de proyecto; T14: aviso si hay riesgo)
  → Issues (indice.py issues: una por requisito, en orden)
  → Construir en desarrollo (IA por el Dev MCP, o persona; T12: solo en desarrollo)
  → Verificar y QA (casos de prueba y SAIL CLI; T13 y T15)
  → Construida (proyecto.py cambio)
── frontera: el paquete; desde aquí, sin IA ──
  → Paquete y revisión (una persona mira la comparación de objetos; T18)
  → Pase a producción (mismo paquete, ICF por entorno, método de cada cliente)
  → En producción (proyecto.py, con --ref)
```

Hasta construir y verificar, la IA prepara y los scripts comprueban; desde el paquete, solo actúan personas, Appian y scripts. Los cambios T12, T13, T14, T15 y T18 están marcados en su paso.

## Por qué no se copia tal cual

L.U.C.I.A. está pensado para código en repositorios git; Appian construye objetos en un entorno vivo. Es el mismo supuesto que hizo fallar appian-harness.

| El método da por hecho | En Appian |
| --- | --- |
| Rama y Merge Request por tarea; nunca se trabaja en `main` | Un entorno de desarrollo compartido, sin ramas. Protegen el `versionId` (409 si otro guardó antes), las colisiones entre unidades y el entorno de corrección. El repositorio del proyecto se trabaja sobre `main`: guarda análisis e issues, no código |
| `./tk v`: build, tests, cobertura de al menos el 85 % y lint en local | La plataforma valida al guardar. Las pruebas son casos de prueba guardados en reglas e interfaces. No hay cobertura de líneas: Designer solo dice qué reglas no tienen casos de prueba |
| Una imagen que se construye una vez y se promueve | Un paquete, con un ICF por entorno, que se promueve con Compare and Deploy o la API de despliegue. A producción, por el método de cada cliente |
| Un requisito se reparte en issues, una por repositorio | Una sola aplicación: lo que se reparte son objetos, y dos personas no deben tocar el mismo a la vez |
| La IA escribe ficheros y se revisa el diff | La IA escribe objetos en el entorno por el Dev MCP; lo cambiado se ve en el historial del objeto y en la comparación de Compare and Deploy |

## Pieza a pieza

De 19 piezas, 4 ya existen, 11 se adoptan o adaptan, 1 la resuelve Appian de forma nativa y 3 se quedan fuera. Los números T remiten al plan.

| Pieza de L.U.C.I.A. | En el plugin o en Appian | Veredicto |
| --- | --- | --- |
| Frontera: la IA prepara; desde el Merge Request, todo determinista | En Appian, ese punto es el paquete. Falta que el Dev MCP no pueda escribir fuera de desarrollo | **Adoptar** (T12) |
| Lo repetible es un comando; lo determinista no va a la IA | Ya es regla del plugin («lo mecánico lo hace un script; lo que pide juicio, el modelo») | **Ya existe**; T1 lo comprueba |
| El contexto se consulta bajo demanda; nunca el corpus entero | `indice.py` y `seccion.py` consultan por partes, pero en la medida real (0.6.0-beta.1) la IA leyó documentos enteros | **Adoptar como método** (T1 a T3); la issue lleva solo su extracto (T11) |
| Código de cuatro colores: fichero, IA, persona, automatismo | Completa la pregunta del `CLAUDE.md` «¿qué se rompe si no se añade?» | **Adoptar como pregunta de diseño** (T1, T4) |
| Métricas de script frente a IA, por fase | Ya se mide el retoque de análisis (tope de 25 llamadas); faltan la construcción y el QA | **Ampliar** (T6, T16, T17) |
| Discovery: requisitos versionados con criterios de aceptación | `funcional.md` con «Se acepta si», escenarios `ESC`, piezas 🔒 e informe de impacto de cada fuente nueva; ahora, en un repositorio git (T8) | **Ya existe** |
| Criterios en Gherkin | Appian Max propone Dado-Cuando-Entonces como uno de varios formatos. Hoy los criterios son frases libres | **Adoptar** (B5, T9): una línea por criterio; el `.feature` lo escribe un script |
| Tests primero, uno por escenario | Appian lo recomienda en reglas de expresión; la skill oficial pide casos de prueba tras guardar reglas con lógica e interfaces; SAIL CLI recorre las pantallas como un usuario | **Adaptar**: pruebas de la issue (T13) y QA con SAIL CLI (T15) |
| Dispatcher: un script reparte el requisito en issues | `indice.py encargo` da el encargo de la unidad entera; el técnico no dice qué objeto sirve a cada requisito | **Adaptar** (T10, T11): issues por requisito, juntas si comparten pantalla o proceso |
| `AGENTS.md`, workflows y skills desde una sola fuente | Las skills ya tienen una: el plugin. Los flujos están repartidos entre los modos de cada skill | **Adoptar** (T7, T8): flujos en el plugin; `AGENTS.md` y `.agents/workflows/` generados; sin `.agents/skills/` |
| `tk st`, `tk v` y `tk commit`, con la salida fuera del chat de la IA | `proyecto.py estado`, `indice.py encargo`, `verificar` y `proyecto.py cambio … construida`; el detalle va a un fichero | **Ya existe**; `verificar` suma las pruebas (T13) |
| Plan y parada antes de cambios grandes | Aprobación de la unidad (alcance y coste) y calibración de buenas prácticas; falta mirar la DT en lo arriesgado | **Adaptar como aviso** (T14) |
| Decisión y alternativa descartada en el Merge Request | DT con «Descartada» | **Ya existe** |
| Revisión humana del Merge Request | En el plugin nadie revisa lo que construyó la IA. Compare and Deploy ya enseña la comparación de objetos al preparar el paquete | **Adoptar** (T18) |
| Verificación en beta antes de producción | La cubre el método de cada cliente; el plugin registra el pase | **Fuera del plugin** |
| Pipeline sin IA: misma imagen, aprobación y Git como auditoría | Nativo: «Deploy to Another Environment», ICF por entorno, la opción «Require review» y el historial del Deploy view | **Usar lo nativo** (T18) |
| Cerebro por MCP, con tokens por rol y bandeja revisada por otro agente | El cerebro corporativo, más adelante. Hoy, el de cada producto son sus fuentes, el funcional y el técnico, y el analista aprueba el impacto de cada fuente nueva | **Fuera, por ahora** |
| Shield: aduana de modelos, PII y coste por persona | Infraestructura de la empresa | **Fuera del plugin** |
| «Si mañana cae el proveedor de IA, ¿seguís entregando?» | Sí: Word, Markdown, scripts, issues y escenarios que también sirven a personas | **Adoptar como prueba de diseño** (T4) |

## Lo que se adopta, y por qué no es burocracia

Cada cambio pasa la pregunta del `CLAUDE.md`: qué se rompe si no está y quién decide con ello.

| Cambio | Qué se rompe sin él | Coste |
| --- | --- | --- |
| La IA consulta bajo demanda: los cuatro puntos de «Agilidad» (T2) | 70 minutos para incorporar una fuente corta con su prototipo (0.6.0-beta.1): 18 y 17 minutos leyendo documentos enteros, 28 esperando al prototipo y notas de 3 a 7 veces el original | Cambios en instrucciones y scripts que ya existen |
| Un repositorio git por proyecto, sobre main (T8, T11) | Varias personas y agentes no pueden trabajar a la vez sobre el análisis y las issues, ni saber quién hace qué | `proyecto.py iniciar` lo crea; pull antes y push después; reservar una issue es un commit; sin ramas ni PR |
| Flujos con una sola fuente y `AGENTS.md` generado (T7, T8) | Cada persona o agente sigue su propio recorrido; los pasos de un evolutivo o de una urgencia están repartidos entre skills | Nueve ficheros cortos en el plugin; `proyecto.py iniciar` los copia y los pone al día |
| Criterios en Gherkin de una línea (T9) | Cada criterio se interpreta al construir y al probar, y no pasa a una prueba sin IA | Escribirlo con dado, cuando y entonces; el `.feature` lo genera un script |
| Issues por requisito, repartidas por un script (T10, T11) | El agente recibe la unidad entera y lee el técnico completo para saber qué le toca; no se ve qué puede ir en paralelo | Una columna en técnico §13; `indice.py issues` sustituye a `indice.py encargo` |
| El Dev MCP no puede escribir fuera de desarrollo, salvo el entorno de corrección en una urgencia (T12) | Un `.mcp.json` que apunta a producción, por ejemplo el configurado para ingeniería inversa, deja a la IA escribir allí. Buenas prácticas ya lo prohíbe: nada se cambia a mano en producción (BP 08 §3) | Una línea por entorno: `LCP_TOOL_MODE=readonly` quita las herramientas que crean o modifican. Donde se pueda, además, un usuario que solo ve la aplicación |
| Pruebas de la issue como red de regresión (T13) | Una issue cambia una regla y rompe otra que depende de ella sin que nadie lo vea hasta pruebas | Los casos los crea quien construye (la skill oficial ya lo pide) y funcionan sin IA. Por issue se ejecuta solo lo que cambia y lo que lo usa; la regresión completa, en bloque, antes del paquete. Una persona puede marcar una prueba como «no necesaria para avanzar», con motivo |
| QA de la unidad con SAIL CLI, en otra sesión (T15) | Quien construye prueba lo que entendió, no lo que se pidió, y un fallo de pantalla llega al cliente | Una sesión por unidad completa, sin cargar la skill oficial; los guiones se repiten sin IA; en un retoque, nada |
| Aviso de revisión técnica solo en unidades de riesgo (T14) | La IA construye un cambio de datos, seguridad o integración desde una DT que nadie ha mirado; deshacerlo cuesta | Una línea al aprobar y en la issue; no bloquea |
| Una persona revisa los objetos al preparar el paquete (T18) | Lo que construyó la IA llega al pase sin que nadie lo haya mirado | Mirar la comparación de objetos que Compare and Deploy ya enseña |
| Dos preguntas más en el `CLAUDE.md` y las lecciones de cada prueba (T4) | Vuelve a entrar lo que nadie lee, o la IA hace lo que resuelve un script; lo aprendido al probar con reuniones se pierde | Tres líneas; las lecciones van a `siguiente-version.md`, que ya existe |
| Medir antes y después (T1 y T3; T6 y T17) y ensayar el QA (T16) | No sabemos si el contexto bajo demanda ahorra, si la «hora por un cambio menor» del harness ha vuelto ni qué QA encuentra más por menos | Una sesión medida dos veces; un retoque a ciegas ×3, dos veces; un ensayo con defectos sembrados |

## Reglas para no repetir appian-harness

- Antes de añadir algo: ¿qué se rompe si no está?, ¿quién decide con ello? y ¿de qué color es (script, persona, IA o fichero)? Lo determinista va a un script; lo que nadie lee no se añade.
- Solo dos bloqueos nuevos: el Dev MCP no escribe fuera de desarrollo (salvo el entorno de corrección en una urgencia), y una issue no se da por hecha con un fallo en sus propias pruebas, también las de QA, salvo que una persona marque esa prueba como «no necesaria para avanzar». Los dos evitan construir algo equivocado; lo demás son avisos.
- Ningún paso obligatorio nuevo en un retoque cosmético, ningún documento nuevo escrito a mano por cambio y ningún registro de veredictos aparte: el estado sale de los ficheros que ya dejan los scripts.
- Lo que Appian ya da (casos de prueba, Manage Test Cases, SAIL CLI, Compare and Deploy, revisión de despliegues, ICF) se usa; no se rehace.
- Se mide antes y después. Lo que no baje el tiempo, las llamadas o el riesgo, se quita.
- Git guarda el proyecto, no el código: nada del ciclo de código en git (ramas, Merge Request, build, cobertura) entra sin traducirse antes a un mecanismo de Appian.

## Anexo: hechos comprobados

Lo que se comprobó al analizar, con su fuente, para no repetirlo ni contradecirlo al ejecutar el plan.

### SAIL CLI (26.6.110, `sail --help` en el paquete del Dev MCP)

- Es un binario aparte del servidor MCP, en `bin/` del paquete (`sail-windows-amd64.exe`, `sail-linux-amd64`, `sail-darwin-arm64`); `bin/setup-*` lo deja en el PATH como `sail`.
- Entrar: `sail login <host>` con `SAIL_USERNAME` y `SAIL_PASSWORD` de una cuenta local de Appian. En un sitio solo con SSO, `sail login <host> --from-devmcp` importa la sesión que abrió el Dev MCP en el navegador (`LCP_AUTH_METHOD=browser`); `--user` si hay varias identidades guardadas.
- `--data-dir` (por defecto `$SAIL_HOME` o `~/.sail`) aísla las sesiones: una por rol o por prueba en paralelo.
- Órdenes: `pages`, `load <site> [page]`, `interact`, `navigate` (enlace de registro, de proceso o acción de registro; la acción sin formulario de inicio lleva al formulario de tarea), `show` (sin ir al servidor), `back` y `logout`.
- `interact`: campos por etiqueta y valor; desplegables, radios y casillas por índice desde 1; fechas `AAAA-MM-DD`; fecha y hora con su zona; ficheros por ruta; rejillas y gráficos por su `handle:`. Varias parejas en una orden van en una sola petición. «✓ Interacted» es que el servidor cambió algo; si aceptó la orden sin mover ningún valor, cuenta como fallo.
- Las referencias que imprime, también las «⌗» que inventa para componentes sin nombre, se mantienen entre cargas y se pueden escribir en un guion; el `_cId`, no.
- `--json` da la salida para un script. Un destino con «confirm:» se rechaza salvo con `--confirm`. No sabe rellenar desplegables agrupados ni rangos numéricos. `load` sobre una página con datos tecleados se niega salvo con `--fresh`.
- `logout` invalida la sesión en el servidor y borra el estado guardado, también lo tecleado: es el cierre de cada prueba.
- Trabaja sobre lo que Appian envía a la pantalla, sin navegador: no ve la maquetación ni los estilos.

### Dev MCP y Appian

- `LCP_TOOL_MODE=readonly` «restricts to read-only tools, disabling any that create or modify objects» (Developer MCP Servers, 26.6). No consta que afecte a SAIL CLI.
- Según el App Market (26.6.110): más de 120 herramientas; los casos de prueba se conservan al actualizar reglas e interfaces; hay `testInterface`, `testProcessModel` y análisis de impacto (los dependientes de un objeto); cada operación se hace con los permisos del usuario, y el acceso es para diseñadores y administradores. No consta una herramienta que ejecute los casos de prueba de las reglas.
- Manage Test Cases da Passed, Failed, No test cases y Outdated. Outdated sale si cambió la regla, si cambió un objeto que usa (hasta 20 niveles) o si no tiene resultados de los últimos 14 días. Por eso T13 ejecuta lo de la issue y lo que la usa, y no «lo desactualizado», que incluiría reglas ajenas.
- Testing Applications (26.6) nombra tres herramientas de prueba de interfaz: FitNesse for Appian, Cucumber for Appian y Appian Selenium API.

### Claude Code y `AGENTS.md`

- Claude Code lee `AGENTS.md` directamente solo si no hay `CLAUDE.md` en la carpeta ni por encima (desde la 2.1.277). Si hay `CLAUDE.md`, solo cuando este lo importa con `@AGENTS.md`. De ahí el `CLAUDE.md` de una línea en cada proyecto.

### Playwright CLI

- `@playwright/cli` (Node 20 o superior) está pensado para agentes: guarda las instantáneas en ficheros (`.playwright-cli/`) en vez de meterlas en el contexto, guarda y carga la sesión (`state-save`, `state-load`) y puede grabar los pasos como código Playwright. No publica cifras de tokens.

### L.U.C.I.A. y las pruebas

- El agente que construye escribe un test por escenario Gherkin antes del código; el reparto crea además una issue de QA por requisito, sin decir quién la hace; una persona verifica en beta. No habla de modelos distintos por papel.

### Del plugin, lo que se reutiliza

- `proyecto.py iniciar` no toca lo que ya existe. `proyecto.py cambio … aprobada` y `produccion` se niegan con `--desatendida` si falta el visto bueno: es el patrón para `--sin-prueba`. `construida` acepta `--manual` y deja `construccion/verificacion/<ID>.json`.
- `comprobar.py --anterior versiones/vX.Y` compara con la versión anterior: así sabe qué criterio es nuevo o cambiado sin git.
- `devmcp_extract.py` lista las herramientas del Dev MCP al conectarse y las clasifica por su firma con `devmcp_policy.json`; `verificar` debe reconocer así la de probar.
- `requisitos.py` ya sabe leer el host del Dev MCP (`LCP_URL`).
- `docs/ingenieria-inversa/SPEC-v2-devmcp.md` dejó SAIL CLI fuera de la ingeniería inversa porque un clic puede lanzar procesos o escribir datos.

### Descartado, y por qué

- GitHub Issues (B6): ata el método a una plataforma, duplica la fuente y añade llamadas en cada paso.
- Guiones de SAIL CLI dentro de la issue: repetirían el escenario y se escribirían antes de que exista la pantalla.
- Playwright por defecto: SAIL CLI cubre los escenarios con menos tokens, según Appian; queda para lo visual, si T16 lo justifica.
- Ramas y PR en el repositorio del proyecto: allí no hay código.
- Una sección propia del proyecto dentro de `AGENTS.md`: obligaría a fusionar al regenerarlo; lo propio va en `proyecto.md`.
- Comprobar la terminal para `--sin-prueba`: basta `--desatendida`, que ya existe.
- Ejecutar por issue «lo desactualizado»: entrarían reglas ajenas y las que llevan 14 días sin pasar.

### Por comprobar en T5

- Qué herramientas del Dev MCP crean y ejecutan casos de prueba, si las ejecutan en bloque y cómo dan los dependientes.
- Si `LCP_TOOL_MODE=readonly` deja fuera también a SAIL CLI.
- Si Indra-spain admite cuentas locales de prueba o hay que importar sesiones SSO con `--from-devmcp`.
- Qué devuelve `--json` al terminar un recorrido, para que `verificar` lo lea.

## Fuentes

- [L.U.C.I.A. al detalle técnico](https://dev.to/raguilera82/lucia-al-detalle-tecnico-8dk), Rubén Aguilera, DEV Community.
- Appian 26.6: [Review deployment requests](https://docs.appian.com/suite/help/26.6/deployments-view.html#review-deployment-requests) · [Deployment settings](https://docs.appian.com/suite/help/26.6/admin-infrastructure.html#deployment-settings) · [Direct Deployment Using Compare and Deploy](https://docs.appian.com/suite/help/26.6/direct-deployment.html) · [Deployments in Appian](https://docs.appian.com/suite/help/26.6/Deploy_to_Target_Environments.html) · [Manage Import Customization Files](https://docs.appian.com/suite/help/26.6/Managing_Import_Customization_Files.html) · [Expression Rule Testing: Manage Test Cases](https://docs.appian.com/suite/help/26.6/Expression_Rule_Testing.html#test-case-management) · [Start Rule Tests (Applications)](https://docs.appian.com/suite/help/26.6/Start_Rule_Tests_Applications_Smart_Service.html) · [Automated Testing for Expression Rules](https://docs.appian.com/suite/help/26.6/Automated_Testing_for_Expression_Rules.html) · [Testing Applications](https://docs.appian.com/suite/help/26.6/testing-applications.html#user-interface-ui-testing) · [Developer MCP Servers](https://docs.appian.com/suite/help/26.6/devmcp.html) (`LCP_TOOL_MODE`).
- [Appian Dev MCP en el App Market](https://appmarket.appian.com/listings/appian-dev-mcp), versión 26.6.110 (8-10-2026), y la ayuda de SAIL CLI 26.6.110 en su paquete: `sail --help` y la de `login`, `load`, `interact`, `navigate`, `show` y `logout`.
- Appian Max: [Writing Effective Acceptance Criteria](https://community.appian.com/delivery-28/writing-effective-acceptance-criteria-1266). Appian Community: [Automated Testing With Cucumber For Appian](https://community.appian.com/architecture-29/automated-testing-with-cucumber-for-appian-1314).
- Gherkin: [Reference](https://cucumber.io/docs/gherkin/reference/) y [Localisation](https://cucumber.io/docs/gherkin/languages/) (palabras clave en español).
- Claude Code: [How Claude remembers your project](https://code.claude.com/docs/en/memory) (`AGENTS.md` e importación desde `CLAUDE.md`).
- Playwright: [Getting started, CLI](https://playwright.dev/docs/getting-started-cli) y [microsoft/playwright-cli](https://github.com/microsoft/playwright-cli).
- Skill oficial [appian/dev-mcp-skills](https://github.com/appian/dev-mcp-skills), commit 6e87fb6 (23-09-2026): `SKILL.md` (carga obligatoria), `references/tools-mcp.md`, `references/expression-rules.md` y `references/interfaces.md` (casos de prueba).
- Repositorio del plugin (0.7.0-beta.4): `CLAUDE.md`, `docs/siguiente-version.md` («Agilidad»), `docs/ingenieria-inversa/SPEC-v2-devmcp.md` (SAIL CLI), `skills/appian-functional-analyst/references/cambios.md` y `urgentes.md`, los scripts `proyecto.py`, `indice.py` y `comprobar.py` del analista, `skills/appian-best-practices/references/08-alm-testing-naming.md`, `skills/appian-reverse-engineering/references/devmcp-setup.md`, `scripts/devmcp_extract.py` de ingeniería inversa y el diseño aparcado «flujo completo y construcción» (commit 5d8acb0).
