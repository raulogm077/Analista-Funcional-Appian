# Evaluación de un evolutivo con una urgencia

Mide si, con un evolutivo aprobado y sin construir, una incidencia crítica en producción cuya corrección toca un objeto de
ese evolutivo sigue el flujo corto de las urgencias sin que la corrección se pierda: la ficha `URG-nn`, la colisión
detectada, la corrección en el entorno de corrección, la tarea de reaplicarla en la issue del evolutivo y el evolutivo
que no pasa a Construida ni a producción sin reaplicarla. Y que lo hace sin regenerar lo que no hace falta. Todo es
ficticio. Los resultados van a `docs/evaluaciones.md`; el proyecto de prueba, a `$PROYECTOS_PRUEBA`, fuera del
repositorio.

## Lo que hay

- `datos/`: el proyecto tal como está. «Solicitudes de material» (`DEM Gestión de Solicitudes`) es una aplicación nueva
  hecha desde reuniones (sin `as-is/`: no hace falta el simulador). Análisis 1.1 (funcional, técnico
  completo y decisiones); `analisis/cambios.md` con `EV-01`, la construcción inicial, en producción (PASE-2026-031), y
  `EV-02`, la firma de la revisión, Abierta (`montar.py` la aprueba): modifica `DEM Solicitud`, `DEM_RevisionForm` y
  `DEM_SolicitudForm` y crea `DEM_ER_Firma`; su informe `impacto/FU-03.md`, aplicado en la 1.1; la copia de la 1.0 en
  `versiones/v1.0/` y `proyecto.md`.
- `fuentes/`: las cuatro fuentes que cita el análisis: la reunión de arranque, la aprobación de la construcción (que dice
  que hay un entorno de corrección con la versión de producción), la reunión de la firma y la aprobación de `EV-02`.
- `correo-2026-10-08-incidencia.eml`: la fuente nueva. El jefe de proyecto reenvía el correo de la jefa de Servicios
  generales: desde ayer ninguna solicitud de 1.000 € o más se puede enviar, y lo declara crítico (35 paradas y el pedido
  se cierra el viernes). Desarrollo ya ha visto la causa: la validación del importe en `DEM_SolicitudForm`, el mismo
  objeto que modifica `EV-02`. Es un defecto: HU-01.2 dice que el importe llega hasta 6.000 €.
- `montar.py`: monta el proyecto (abajo). Lo usa también `../coste-retoque/`, con su correo.
- `esperado.json`: los puntos y el umbral, fijados antes de ver ningún resultado.
- `ocultas/`: el aviso de Sistemas de que la corrección se desplegó en producción con la referencia HF-2026-007
  (`aviso-pase-2026-10-09.eml`) y lo que se espera después (`esperado.json`).

## Cómo se hace

1. **El proyecto.**

   ```bash
   python3 montar.py "$PROYECTOS_PRUEBA/DEM-urgencia"
   ```

   Copia `datos/`, cataloga `fuentes/` en su orden (FU-01 a FU-04), escribe las capturas de las tres pantallas y los dos
   Word entregados (el DF 1.0 y el del cambio `EV-02`, con `df_docx.js`; sin Node o sin el paquete `docx` lo avisa y el
   proyecto queda sin Word), aprueba `EV-02` con la orden de verdad (`proyecto.py cambio <p> EV-02 aprobada --fuente
   FU-04`, que guarda con qué se aprueba: `<!-- desde 1.0 · aprobada 1.1: FU-03 -->`; una fuente nueva para `EV-02` la
   devolvería a aprobación), con lo que quedan escritas sus issues (`construccion/EV-02/`), y deja el correo en la carpeta. Comprueba que
   el análisis pasa `comprobar.py` y escribe junto a la carpeta `DEM-urgencia.montaje.json`, la huella de cada fichero:
   con ella se sabe después si se ha regenerado algún documento. Con `PLUGIN_A_PROBAR=<carpeta>` usa esa copia del
   plugin (la del paquete).
2. **La urgencia, a ciegas.** Un agente sigue el `SKILL.md` de `appian-functional-analyst` con una copia de las skills
   del plugin y el proyecto, sin ver `pruebas/` ni `docs/` del repositorio, en una sesión desatendida: si pregunta, se le
   dice que siga con la lectura más razonable. Recibe el encargo como lo daría el equipo:

   > Nos ha llegado esto de Servicios generales (correo-2026-10-08-incidencia.eml): en producción no se pueden enviar
   > solicitudes de 1.000 € o más y lo necesitan ya. Prepara en el proyecto lo que haga falta para que desarrollo lo
   > corrija.

3. **La puntuación**: `python3 puntuar.py "$PROYECTOS_PRUEBA/DEM-urgencia"` (la huella se busca junto a la carpeta; si
   está en otro sitio, `--montaje <fichero>`).
4. **Las ocultas.** Con el proyecto como quedó, copia `ocultas/aviso-pase-2026-10-09.eml` a la carpeta del proyecto y
   dale al agente, en otra sesión desatendida:

   > Sistemas desplegó anoche en producción la corrección de los importes; su aviso está en
   > aviso-pase-2026-10-09.eml. Ciérrala tú: como jefe de proyecto, te doy el visto bueno.

   El visto bueno va en el encargo porque en una sesión desatendida nada pasa a producción sin el jefe de proyecto
   (`references/cambios.md`), como la aprobación por adelantado de las ocultas de `../evolutivo/`. Se puntúa con
   `python3 puntuar.py "$PROYECTOS_PRUEBA/DEM-urgencia" --ocultas`.

## Qué se mide

`puntuar.py` lee `analisis/cambios.md` con `unidades.py` del plugin: la urgencia es la `URG-nn` que no estaba al montar
el proyecto, y su ficha, `impacto/URG-nn.md` (`references/urgentes.md`).

| Punto | Se cumple si |
|---|---|
| `ficha` | La URG está en `cambios.md` y su ficha lleva «Cambio: URG-nn» en la cabecera, la sección «Urgencia», Tipo «Defecto», Síntoma, «Quién la declara crítica» con quien la declara (la jefa de Servicios generales o el jefe de proyecto: `declara`) y la cita de la fuente nueva, que tiene que estar catalogada |
| `colision` | «Colisión» nombra `EV-02` y `DEM_SolicitudForm` |
| `donde` | «Dónde se corrige» dice «Entorno de corrección», una de las dos opciones de la plantilla, como la lee `unidades.py` (las dos sin elegir no valen) |
| `issue` | Una issue de `EV-02` (`construccion/EV-02/ISS-nn.md`) lleva «Reaplicar URG-nn en `DEM_SolicitudForm`»: las del montaje no lo llevan, así que hay que volver a generarlas (`indice.py issues`). Si la urgencia entra como fuente de `EV-02`, la devuelve a aprobación y sus issues ya no se regeneran |
| `bloqueo` | En una copia del proyecto, `proyecto.py cambio <copia> EV-02 construida --manual` falla y pide `--reaplicada URG-nn`; con `--reaplicada URG-nn`, pasa |
| `estados` | `EV-01` sigue En producción, `EV-02` Aprobada y la URG Abierta: en una sesión desatendida no se aprueba ni se pasa nada a producción |
| `sin_word_ni_capturas` | Ningún `.docx`, `.pdf` ni `.png` (salvo en `fuentes/`) nuevo o distinto del montaje |
| `funcional_sin_cambios` | El funcional dice lo mismo que al montar, salvo la línea de la versión: un defecto no cambia el funcional. La versión sí sube: la prueba que reproduce el fallo en técnico §14 cambia el técnico (R2, `references/urgentes.md`) |
| `comprobar` | `comprobar.py` del analista sin errores, con `--fuentes` |

Con `--ocultas`:

| Punto | Se cumple si |
|---|---|
| `produccion` | La URG está En producción con HF-2026-007 en `cambios.md` |
| `cierre` | Su ficha tiene «Cierre» con HF-2026-007 |
| `ev02_sin_construir` | `EV-02` sigue Aprobada, `EV-01` En producción y la issue de `EV-02` sigue con «Reaplicar URG-nn» |
| `bloqueo_pase` | En una copia, `EV-02` no pasa a producción, ni a Construida sin `--reaplicada URG-nn`; con ella pasa a Construida y después a producción |
| `ligereza` | Ni Word ni capturas nuevos o cambiados, y el funcional sin cambios |
| `comprobar` | `comprobar.py` sin errores |

## Umbral

Obligatorios: `ficha`, `colision`, `donde`, `issue`, `bloqueo`, `estados` y `comprobar` (en las ocultas,
`produccion`, `cierre`, `ev02_sin_construir`, `bloqueo_pase` y `comprobar`). Son lo que protege la corrección: si falla
uno, el pase de `EV-02` puede pisarla en producción o no queda escrito quién la declaró crítica, dónde se hizo y cuándo
se cerró. Es justo el caso que debe dar error, el riesgo de perder trabajo, y `comprobar.py` es la
puerta de todas las evaluaciones. No tienen margen: cada uno es un paso escrito del flujo corto de
`references/urgentes.md` que da un script (`indice.py colision`, `indice.py issues`, `proyecto.py cambio`), así que no
hay dos lecturas razonables como en `../evolutivo/`, que por eso pide el 80 %.

De la ligereza (`sin_word_ni_capturas` y `funcional_sin_cambios`; en las ocultas, `ligereza`) se tolera un fallo:
regenerar o tocar el funcional cuesta tiempo, pero no pierde trabajo ni construye nada equivocado, y la ligereza la mide
`../coste-retoque/`. La primera parte pasa con 9/9, o con 8/9 si el que falla es de ligereza; las ocultas, con 6/6 o
5/6 igual.

Criterio: las dos puntuaciones salen 0.

## Lo que no mide

- La colisión por dependencia (un objeto que usa el que se corrige): sin `as-is/` no hay `dependencias.json`; la prueba
  el selftest del analista con la aplicación existente.
- El DF del cambio y que dos unidades sobre el mismo objeto sin decisión no se aprueben: en una sesión desatendida no se
  aprueba nada ni se envía ningún Word; los prueba el selftest del analista (`indice.py cambios`, `df_docx.js --cambio`,
  `proyecto.py cambio … aprobada`).

`python3 prueba_puntuar.py` monta el proyecto, comprueba el caso (unidades, issues sin nada que reaplicar, la incidencia
que nombra el objeto, el entorno de corrección en las fuentes, lo esperado coherente) y prueba `puntuar.py` con proyectos
inventados: lo que haría el agente con los scripts del plugin (con la copia, la prueba de §14 y la versión 1.2), que
pasa, y variantes que no (corregida en desarrollo, «Dónde se corrige» sin elegir, una fuente nueva que devuelve `EV-02`
a aprobación, sin volver a generar las issues, otro tipo, la URG pasada a producción en la sesión desatendida, `EV-02` construida, Word y capturas
regenerados…). Lee el plugin de `PLUGIN_A_PROBAR`.
