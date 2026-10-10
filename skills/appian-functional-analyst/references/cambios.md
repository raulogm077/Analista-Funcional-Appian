# Evolutivos y construcción: las unidades de cambio

Cuándo: `proyecto.py estado` lista unidades en curso (`analisis/cambios.md`), o hay que abrir una porque el cambio va a
construirse. Sin `analisis/cambios.md` nada de esto aplica y el proyecto funciona como siempre. Las urgencias, en
`urgentes.md`.

Lo que no cambia: el análisis (`funcional.md`, `tecnico.md`, `diagramas/`) describe la aplicación como es **más las
unidades en curso**, y cada fuente pasa por `actualizacion.md`. Lo demás (el DF de un cambio, el encargo de construcción,
las pruebas a repetir, las pantallas a capturar) **lo calculan los scripts**: no se escribe a mano ni se deduce leyendo
documentos. Solo bloquea lo que haría perder trabajo o construir algo equivocado; el resto son avisos que se apagan solos.

## 1. Las unidades

Un cambio sobre la aplicación es una unidad: `EV-nn` (un evolutivo; también la construcción inicial de una aplicación
nueva, `EV-01`, y cada fase de una refactorización) o `URG-nn` (un cambio urgente). Se registran en
`analisis/cambios.md`, que solo escribe `proyecto.py cambio` (`<p>`, el proyecto):

| Orden | Estado | Cuándo | Bloquea si… |
|---|---|---|---|
| `cambio <p> EV-02 abrir --titulo "…"` | Abierta | Empieza el cambio | ya existe |
| `… aprobada --fuente FU-nn [--comparte "…"]` | Aprobada | El jefe de proyecto aprueba la unidad entera, una vez, con su alcance y coste; su aprobación (chat o correo) es la fuente FU-nn | hay puntos «Pendiente» en sus informes; o un objeto suyo de §13 está también en otra unidad Aprobada o Construida sin una decisión escrita (`--comparte "EV-03 en X: secuenciar (EV-02 primero)"`) |
| `… construida [--reaplicada URG-nn …] [--manual]` | Construida | Construida y verificada en desarrollo | no está Aprobada; falta `construccion/verificacion/EV-02.json` (o `--manual` sin Dev MCP, y la marca lo dice); la verificación no incluye un objeto suyo o lo encuentra distinto del técnico; o falta confirmar una corrección urgente que hay que reaplicar |
| `… produccion --ref "<pase>"` | En producción | Tras el pase | no está Construida |
| `… descartada [--informe impacto/FU-nn.md]` | Descartada | No se hace | no está Abierta; o tiene algo aplicado y no se da el informe (aplicado) que lo deshace, o §13 sigue con sus filas |

De Construida se vuelve a Aprobada (`… aprobada`, sin `--fuente`) cuando una urgencia obliga a reaplicar. Con
`--desatendida` nunca se aprueba ni se pasa a producción: lo hace el jefe de proyecto. `proyecto.py estado` imprime las
unidades en curso con sus fuentes, versiones y objetos (no se guardan: se derivan) y lo que hay que reaplicar.

**Qué es de cada unidad.**
- Sus fuentes: los informes de impacto con `Cambio: EV-02` en la cabecera (`Análisis base: versión 1.1 · Cambio: EV-02 ·
  Estado: …`). Si falta, la fuente es de la única unidad Abierta; si no aplica nada, de ninguna. Con dos Abiertas, ponla
  siempre (`estado` avisa del informe que no la lleva). Una fuente que toca dos unidades lleva una columna «Cambio» por
  punto.
- Sus piezas: los IDs de «Aplicado» y de «Cambio propuesto» de esos puntos.
- Sus objetos: las filas de técnico §13 con su ID en la columna «Cambio» (`tecnico-plantilla.md` §13). En la
  construcción inicial, las filas sin ID son de `EV-01`.

**Línea base.** Lo construido es el análisis inicial (en una aplicación ajena, el de `as-is/`) más las unidades
Construidas; lo que hay en producción, el inicial más las unidades En producción.

## 2. Cómo entra cada caso

- **Aplicación ajena** (`as-is/`): análisis base de toda la aplicación con detalle (SKILL.md, «Aplicación existente»).
  Es la versión 1.0, **sin unidad**: construida y en producción por definición, con la fecha del `as-is/`. Cada cambio
  después es una `EV-nn`.
- **Refactorización**: como la anterior; la propuesta entra como fuente y cada fase de su Hoja de ruta es una `EV-nn`,
  con una columna «Cambio» por punto en su informe.
- **Aplicación nueva**: el análisis como siempre; la construcción inicial es `EV-01`. Cuando pasa a producción, un
  cambio sobre lo hecho es una `EV-nn` nueva.

## 3. El informe de impacto con unidades

Igual que en `actualizacion.md`, con lo que imprimen `indice.py ficha` e `impacto` por pieza: `Construido: as-is, EV-01 ·
En curso: EV-03`. Se copia, no se deduce:
- **Construido**: un punto que lo cambia **no pide aprobación por eso**; va al Resumen como `- Posible petición de
  cambio: puntos 3 y 5` y el jefe de proyecto lo decide una vez, al aprobar la unidad.
- **En curso en otra unidad**: el punto requiere aprobación, `Requiere: Sí (EV-03)`, porque hay que decidir el orden o
  unirlas antes de construir.

Las demás reglas de aprobación no cambian (🔒, alcance, fuente interna, dos personas del cliente). El «Origen» de las
historias (Nueva, Cambia, Se conserva) ya no se escribe: lo da `indice.py cambios`.

## 4. El técnico de una unidad

- **§13** lleva la columna «Cambio» con la unidad de cada fila. La Situación (Nuevo, Modifica, Existe, Sustituye) se
  compara con la línea base: lo que creó una unidad Construida ya existe.
- **Completo** es lo de las unidades en curso: `comprobar.py` exige en el técnico sus pantallas, pasos, avisos,
  criterios y datos de §6 que han cambiado, no los de toda la aplicación. En una aplicación ajena el técnico lleva Entorno
  y Convenciones y remite a `as-is/` para lo existente.
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

## 5. Derivados: al enviar o al construir, no con cada fuente

Ninguno se regenera si no cambia (R2).
```bash
python3 <skill>/scripts/indice.py cambios <p> EV-02 [--json]   # piezas nuevas, que cambian (antes y después) y anuladas,
                                     # pantallas, diagramas, técnico, objetos, pruebas a repetir, colisiones y reaplicar
node <skill>/scripts/df_docx.js <p> --cambio EV-02     # el DF del cambio; al enviarlo: proyecto.py entregar <p> --cambio EV-02
python3 <prototipos>/scripts/capture.py prototipo-<app>.html app.json -o capturas/ --solo PAN-01,PAN-02
python3 <skill>/scripts/indice.py encargo <p> EV-02    # construccion/EV-02.md y EV-02-esperado.json (unidad Aprobada)
```
- **DF del cambio**: lo nuevo y lo que cambia, más las historias que se conservan pero comparten pantalla o paso con
  ellas (T5); lo demás, un párrafo. El DF completo se sigue pudiendo generar.
- **Encargo** (`construccion/EV-02.md`): **qué** construir: por objeto, su situación, qué cambia y dónde está en el
  técnico; los puntos de «Cambio sobre lo construido»; las pruebas; las correcciones urgentes que reaplicar o que congelan
  objetos; y la orden de verificar. Sin orden ni lista de cierre propios: los dan la skill oficial de Appian
  (`change-planning`) y las puertas de `appian-best-practices`. Se genera, no se edita. Sirve a Claude y a personas.

## 6. Construir, verificar y marcar

1. **Construir** con el encargo: `appian-best-practices` (que lo lee como alcance) y el Dev MCP, o una persona.
2. **Verificar** (solo lectura): la orden del encargo, el atajo «Verificar» de `appian-reverse-engineering`
   (`devmcp_extract.py verificar … --esperado <p>/construccion/EV-02-esperado.json --out
   <p>/construccion/verificacion/EV-02.json`). Comprueba que cada objeto existe, su tipo y, de record types y CDT, los
   campos de esta unidad (de uno que se modifica, que tenga más campos que los suyos no cuenta); la fecha de última
   modificación es un dato, no una prueba. Lo semántico lo garantizan las pruebas de quien construye. El avance entre
   sesiones se ve volviendo a verificar.
3. **Marcar**: `proyecto.py cambio <p> EV-02 construida` y, tras el pase, `… produccion --ref "<pase>"`.

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
