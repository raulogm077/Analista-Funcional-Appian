# Evolutivos y construcción: las unidades de cambio

Cuándo: `proyecto.py estado` lista unidades en curso (`analisis/cambios.md`), o hay que abrir una porque el cambio va a
construirse. Sin `analisis/cambios.md` nada de esto aplica y el proyecto funciona como siempre. Las urgencias, en
`urgentes.md`.

Lo que no cambia: el análisis (`funcional.md`, `tecnico.md`, `diagramas/`) describe la aplicación como es **más las
unidades en curso**, y cada fuente pasa por `actualizacion.md`. Lo demás (el DF de un cambio, las issues de construcción,
las pruebas a repetir, las pantallas a capturar) **lo calculan los scripts**: no se escribe a mano ni se deduce leyendo
documentos. Solo bloquea lo que haría perder trabajo o construir algo equivocado; el resto son avisos que se apagan solos.

**Dos palabras.** «Abierta» es un estado: la unidad ha empezado y no está aprobada. «En curso» es toda unidad que no ha
pasado a producción ni se ha descartado: Abierta, Aprobada o Construida.

## 1. Las unidades

Un cambio sobre la aplicación es una unidad: `EV-nn` (un evolutivo; también la construcción inicial de una aplicación
nueva y cada fase de una refactorización) o `URG-nn` (un cambio urgente). Se registran en `analisis/cambios.md`, que solo
escribe `proyecto.py cambio` (`<p>`, el proyecto). Cada error dice la salida.

| Orden | Estado | Cuándo | Bloquea si… |
|---|---|---|---|
| `cambio <p> EV-02 abrir --titulo "…"` | Abierta | Empieza el cambio | ya existe |
| `… aprobada --fuente FU-nn [--comparte "…"]` | Aprobada | El jefe de proyecto aprueba la unidad entera, con su alcance y coste; su aprobación (chat o correo) es la fuente FU-nn. Deja escritas sus issues de construcción (§5) | hay puntos «Pendiente» en sus informes; o un objeto suyo de §13 está también en otra unidad Aprobada o Construida sin una decisión escrita (`--comparte "EV-03 en X: secuenciar (EV-02 primero)"`), salvo que una de las dos solo cambie en él una parte que no guarda datos ni da permisos (§4): eso se avisa |
| `… construida [--reaplicada URG-nn …] [--manual]` | Construida | Todas sus issues, construidas y verificadas en desarrollo (§6) | no está Aprobada; ha crecido desde que se aprobó; alguna issue no está hecha (dice cuál y por qué; con `--manual`, sin Dev MCP, no se mira, y la marca lo dice); o falta confirmar una corrección urgente que hay que reaplicar |
| `… produccion --ref "<pase>" --fecha <AAAA-MM-DD del pase>` | En producción | Tras el pase | no está Construida |
| `… descartada [--informe impacto/FU-nn.md]` | Descartada | No se hace | no está Abierta; o tiene algo aplicado y no se da el informe (aplicado) que lo deshace, o §13 sigue con sus filas |

**Aprobar guarda con qué se aprueba** (la versión y sus informes, en la celda de su ID). Una fuente nueva para una
unidad Aprobada (otro informe con su `Cambio:`, o un punto «Pendiente») la devuelve a aprobación: `issues` y
`construida` fallan con «ha crecido desde que se aprobó» hasta que se vuelve a aprobar con `--fuente`. Si no conviene,
lo nuevo va en otra unidad. Sin `--fuente`, de Construida se vuelve a Aprobada cuando una urgencia obliga a reaplicar.
Con `--desatendida` no se aprueba ni se pasa a producción sin el visto bueno del jefe de proyecto; si lo da (también
en lo que se le pide a la sesión), se cataloga como fuente de tipo Aprobación y se pasa con ella. «En producción» registra un pase
que ya ha ocurrido: lo que quede por comprobar se apunta, no lo frena. `proyecto.py estado` imprime
las unidades en curso con sus fuentes, versiones y objetos (no se guardan: se derivan) y lo que hay que reaplicar.

**Qué es de cada unidad.**
- Sus fuentes: los informes de impacto con `Cambio: EV-02` en la cabecera (`Análisis base: versión 1.1 · Cambio: EV-02 ·
  Estado: …`). Si falta, la fuente es de la única unidad Abierta; si no aplica nada, de ninguna. Con dos Abiertas, ponla
  siempre (`estado` avisa del informe que no la lleva). Una fuente que toca dos unidades lleva una columna «Cambio» por
  punto.
- Sus piezas: los IDs de «Aplicado» y de «Cambio propuesto» de esos puntos.
- Sus objetos: las filas de técnico §13 con su ID en la columna «Cambio» (§4).

**Línea base.** Lo construido es el análisis inicial (en una aplicación ajena, el de `as-is/`) más las unidades
Construidas; lo que hay en producción, el inicial más las unidades En producción.

## 2. Cómo entra cada caso, y con qué número

- **Aplicación ajena** (`as-is/`): análisis base de toda la aplicación con detalle (SKILL.md, «Aplicación existente»).
  Es la versión 1.0, **sin unidad**: construida y en producción por definición, con la fecha del `as-is/`. El primer
  cambio es `EV-01`.
- **Refactorización**: como la anterior; la propuesta entra como fuente y cada fase de su Hoja de ruta es una unidad,
  desde `EV-01` (o la siguiente libre), con una columna «Cambio» por punto en su informe.
- **Aplicación nueva**: el análisis como siempre; la construcción inicial es `EV-01`. Cuando pasa a producción, un
  cambio sobre lo hecho es `EV-02`, y así.
- **Defecto que nadie declara crítico** (la aplicación no hace lo acordado): va en una unidad `EV-nn`, la Abierta o una
  nueva. El funcional no cambia; el técnico gana en §14 la prueba que reproduce el fallo, junto al criterio que no se
  cumple, y en §13 los objetos que se corrigen, «Para» ese criterio (`HU-03.2`): es el escenario de su issue.
- **Urgencias**: `URG-01`, `URG-02`…, numeradas aparte.

## 3. El informe de impacto con unidades

Igual que en `actualizacion.md`, con lo que imprimen `indice.py ficha` e `impacto <p> <IDs> --cambio EV-02` (la unidad
del informe) por pieza: `Construido: as-is, EV-01 · En curso: EV-03`. Se copia, no se deduce:
- **Construido**: un punto que lo cambia **no pide aprobación por eso**; va al Resumen como `- Posible petición de
  cambio: puntos 3 y 5` y el jefe de proyecto lo decide una vez, al aprobar la unidad.
- **En curso en otra unidad**: el punto requiere aprobación, `Requiere: Sí (EV-03)`, porque hay que decidir el orden o
  unirlas antes de construir. `impacto` no lo sugiere para la propia unidad.

Las demás reglas de aprobación no cambian (🔒, alcance, fuente interna, dos personas del cliente). El «Origen» de las
historias (Nueva, Cambia, Se conserva) ya no se escribe: lo da `indice.py cambios`.

## 4. El técnico con unidades

- **No repite `as-is/`.** En una aplicación ajena lleva Entorno y Convenciones y remite a `as-is/` para lo existente;
  sus apartados se escriben con cada unidad, solo para lo que toca.
- **§13** suma la columna `Cambio` con la unidad de cada fila y la columna `Para` con su requisito o «Base» («| 5 | `X` |
  Interfaz | Modifica | — | EV-02 | PAN-03 |», `tecnico-plantilla.md` §13): son los objetos de sus issues, una por
  requisito (§5). Una fila sin unidad es de `EV-01` solo en una aplicación nueva (su construcción inicial); con
  `as-is/` no es de ninguna. La Situación se compara con la línea base: lo que creó una unidad Construida ya «Existe»
  o se «Modifica».
- **Completo** es lo de las unidades en curso: `comprobar.py` exige en el técnico sus pantallas, pasos, avisos,
  criterios y datos de §6 que han cambiado, no los de toda la aplicación.
- **Cada punto aplicado** se refleja en el técnico: filas de §13 de su unidad o una DT que cite su fuente. Si no hay nada
  que construir (un dato que ya se guarda, una aclaración), el punto lo dice: `Sin cambio técnico: <motivo>`.
- **«Cambio sobre lo construido»**: una DT por unidad, `**DT-nn — Cambio sobre lo construido: EV-02**`, solo con los
  puntos que tocan por el tipo de los objetos construidos que la unidad modifica o sustituye:

  | Si modifica… | Punto (fila de la DT) | Buenas prácticas |
  |---|---|---|
  | record type, CDT o tabla | **Datos existentes**: valores para lo que ya hay, migración y orden | BP 01, BP 08 §3 |
  | process model | **Procesos en curso**: compatible hacia atrás, Process Upgrade o Edit Process | BP 03 §12 |
  | Web API o integración que usan otros | **Compatibilidad**: compatible o versión nueva | BP 07 §6 |
  | grupo o seguridad | **Permisos** que cambian | BP 06 |
  | cualquiera de los anteriores | **Despliegue y vuelta atrás** | BP 08 §3, BP 11 §7 |

  Con **Capa** (Operación), **Necesidad**, **Por qué** (la BP) y **Verificado**, como cualquier DT. Interfaces, reglas,
  constantes y textos no la necesitan: cambiar el texto de un botón construido es una fila «Modifica» en §13, sin DT ni
  aprobación.

  Se gradúa por lo que cambia, no por el tipo del objeto. Si de un objeto solo cambia una parte, la fila de §13 la
  nombra y manda la parte: el nombre de una acción de registro (`DEM Solicitud — acción «Nueva solicitud»`), una vista
  o un filtro son un retoque aunque vivan en un record type, sin DT y sin decidir el orden con la unidad que modifica
  ese record type (se avisa: el paquete lleva el objeto entero). Un campo o una relación (`… — campo importe`) sí piden
  «Datos existentes»; la seguridad de una acción o de una vista, «Permisos».

## 5. Derivados: al enviar o al construir, no con cada fuente

Ninguno se regenera si no cambia (R2).
```bash
python3 <skill>/scripts/indice.py cambios <p> EV-02 [--json]   # piezas nuevas, que cambian (antes y después) y anuladas,
                                     # datos de §6, pantallas, diagramas, técnico, objetos, pruebas a repetir, colisiones
node <skill>/scripts/df_docx.js <p> --cambio EV-02     # el DF del cambio; al enviarlo: proyecto.py entregar <p> --cambio EV-02
python3 <prototipos>/scripts/capture.py prototipo-<app>.html app.json -o capturas/ --solo PAN-01,PAN-02
python3 <skill>/scripts/indice.py issues <p> EV-02     # sus issues de construcción, en construccion/EV-02/ (unidad Aprobada)
```
- **DF del cambio**: lo nuevo y lo que cambia (también los datos de §6), más las historias que se conservan pero
  comparten pantalla o paso con ellas o cuya pantalla o paso cambia (T5); lo demás, un párrafo. El DF completo se sigue
  pudiendo generar.
- **Issues de construcción** (`construccion/EV-02/`): una por requisito de «Para» de técnico §13. Los requisitos que
  comparten pantalla o proceso van en la misma; lo «Base», en la primera; las demás, en orden, y el índice (`indice.md`)
  dice de cuáles depende cada una y con cuáles puede ir a la vez (las que no comparten objetos). Cada `ISS-nn.md` lleva
  lo que necesita quien construye y nada más: **qué** se pide, sus escenarios (`ISS-nn.feature`, en Gherkin) con cómo se
  comprueba cada uno (técnico §14), sus objetos, lo que el técnico dice de ellos (lo que cambia, con lo de antes), lo
  que no debe tocar por ser de otra issue, los puntos de «Cambio sobre lo construido» y las correcciones urgentes que
  reaplicar o que congelan objetos. Si no cambia criterios ni reglas, lo dice: no hay pruebas que ejecutar. Sin orden
  ni lista de cierre propios: los dan la skill oficial de Appian (`change-planning`) y las puertas de
  `appian-best-practices`. Se escriben solas al aprobar la unidad y `indice.py issues` las vuelve a generar: con los
  mismos datos salen las mismas, y si el análisis cambia cada una conserva su número. No se editan. Sirven a Claude, a
  otros agentes y a personas. No se generan si la unidad no está aprobada o ha crecido desde que se aprobó. Un técnico
  cuyo §13 aún no dice «Para» da una sola issue con toda la unidad.

## 6. Construir, verificar y marcar

1. **Pedir la siguiente issue**: `indice.py issues <p> EV-02 --siguiente` da la primera sin hacer cuyas dependencias
   están hechas, entera y con su orden de terminar lista para copiar en ese equipo (sus rutas, su Python y el Dev MCP de
   desarrollo de su configuración, el de la «URL de desarrollo» de técnico §0). Y la reserva: escribe en el índice quién
   la tiene y desde cuándo y hace un commit y un push solo de `construccion/EV-02/`. Antes se pone al día; si el push
   falla porque otro reservó antes, quita su commit, se pone al día y da la siguiente: dos que la piden a la vez no se
   llevan la misma. Nunca falla por git, y dice cómo queda: sin remoto, un commit sin subir; si el proyecto no es un
   repositorio, sin reservar. El nombre es el de git; dos sesiones con el mismo se distinguen con `--quien <nombre>`.
   `--liberar ISS-nn` quita la reserva de una issue que nadie va a seguir. El push sube también los commits que esa
   copia tuviera sin subir.
2. **Construir** la issue: `appian-best-practices` (que la lee como alcance) y el Dev MCP, o una persona.
3. **Verificar** (solo lectura): la orden de la issue, que es el atajo «Verificar» de `appian-reverse-engineering` con
   lo esperado de la issue y con su resultado en `construccion/EV-02/verificacion/ISS-nn.json`. Comprueba que cada
   objeto existe, su tipo y, de record types y CDT, los campos de esta unidad (de uno que se modifica, que tenga más
   campos que los suyos no cuenta); la fecha de última modificación es un dato, no una prueba. Si no pudo leer los
   campos, se repite. Lo semántico lo garantizan las pruebas de quien construye.
   **Una issue está hecha** cuando su última verificación pasa y es de su versión de ahora: si al volver a generarla
   cambia lo que hay que construir o comprobar, vuelve a estar pendiente. También vuelve si uno de sus escenarios falla
   en el QA de la unidad (`qa/EV-02/resultado.json`, de `appian-qa`), hasta que se corrige y sus guiones pasan. No hay
   otro estado que mantener: su reserva se quita sola, y `indice.py issues <p> EV-02` dice cómo va cada una.
4. **Marcar**, con todas hechas: `proyecto.py cambio <p> EV-02 construida` (la orden de la última issue la trae) y,
   tras el pase, `… produccion --ref "<pase>" --fecha <AAAA-MM-DD>`. Sin Dev MCP no hay verificación: construye una
   persona siguiendo el índice y la unidad se marca con `--manual`.

**Deriva** (antes de abrir una unidad en una aplicación ajena, o para los objetos de una urgencia): `devmcp_extract.py
deriva` de ingeniería inversa compara el historial de versiones con el de `as-is/` y escribe `as-is/datos/deriva.json`; si
algo cambió fuera de nuestro control, entra como una fuente más (tipo «as-is») por el informe de impacto.

## 7. Lo que avisa comprobar.py (y cómo se apaga)

| Aviso | Se apaga cuando… |
|---|---|
| un punto aplicado de una unidad sin reflejo en el técnico | su unidad tiene filas en §13, una DT cita su fuente o el punto dice `Sin cambio técnico: <motivo>` |
| falta un punto de «Cambio sobre lo construido» | la DT de la unidad tiene esa fila |
| un criterio de una historia tocada sin prueba en §14 (error con el técnico «completo») | §14 lo cita |
| una urgencia de tipo defecto sin su prueba | §14 tiene una fila con su `URG-nn` |
| «Modifica» de un objeto que ninguna unidad ha construido (aplicación nueva) | el objeto está en una unidad Construida o la fila dice otra Situación |
| un objeto de §13 que se construye o cambia, sin «Para» (si la tabla aún no tiene la columna, un solo aviso) | la fila dice su requisito (`HU-nn`, `PAN-nn` o `ACT-nn`) o «Base» |
