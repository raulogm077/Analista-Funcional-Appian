# Evolutivos y cambios urgentes — diseño

Estado: propuesto (10 de octubre de 2026), pendiente de aprobación de Raúl. Sustituye la parte de evolutivo de la fase
G4 de `docs/plan/2026-10-10-0.7.0-beta.2.md`.

## 1. El problema

El plugin describe bien una aplicación y la mantiene reunión a reunión, pero **no sabe qué está construido** ni qué
está en producción:

- 🔒 es «validado por el cliente», no «desarrollado». La regla «requiere aprobación si toca algo construido»
  (`actualizacion.md` §3.4) no se puede aplicar porque no hay ese dato.
- El origen de cada historia (Se conserva, Cambia, Nueva) se escribe a mano: cuesta tokens y se desalinea.
- Repetir la ingeniería inversa vuelve a numerar hallazgos y NV y rompe las citas del análisis y de la propuesta.
- No hay paquete de construcción por cambio, ni comprobación de que lo construido es lo especificado, ni un camino para
  una incidencia urgente que choca con un desarrollo en marcha.

## 2. Decisiones de Raúl (10 de octubre)

| # | Decisión |
|---|---|
| E1 | Aplicación ajena: el análisis base procesa **toda la aplicación con detalle** (historias con criterios y escenarios) |
| E2 | Dos marcas por cambio: **Construido** (hecho y verificado en desarrollo) y **En producción** |
| E3 | El informe de impacto **señala como posible petición de cambio** lo que modifica algo ya construido; decide el jefe de proyecto |
| E4 | Antes de marcar «Construido» se **leen en el entorno los objetos tocados** y se comparan con el técnico |
| E5 | Hay, o puede haber, un **entorno de corrección** con la misma versión que producción |
| E6 | **Crítico es lo que el cliente o el equipo declaran crítico**: producción parada, datos incorrectos, un sistema caducado, un comportamiento que impide hacer bien las tareas, errores técnicos visibles (pantallas que fallan, servicios que no responden)… |
| E7 | Construyen **Claude (Dev MCP y buenas prácticas) o personas**: el paquete sirve a los dos |
| E8 | Puede haber **varios evolutivos a la vez** sobre la misma aplicación |

Siguen valiendo R1-R7 del plan (chat como fuente, versión solo con cambios, 🔒 tras un cambio, neutralidad…).

## 3. Conceptos

### 3.1 Una sola fuente de verdad
`analisis/funcional.md`, `analisis/tecnico.md` y `analisis/diagramas/` describen **la aplicación como es más lo
aprobado que aún no se ha construido**. Todo lo demás (DF de un cambio, paquete de construcción, pruebas a repetir,
pantallas a capturar) se **deriva por script**; no se escribe a mano.

### 3.2 La unidad de cambio
Todo cambio sobre la aplicación es una unidad con ID:

- `EV-nn`: un evolutivo (también la construcción inicial de una aplicación nueva, `EV-01`, y cada fase de una
  refactorización).
- `URG-nn`: un cambio urgente.

Las unidades se registran en `analisis/cambios.md`, que es lo que el plugin consulta para saber qué está hecho:

```markdown
| ID | Título | Tipo | Estado | Fuentes | Versión | Construido | En producción |
|---|---|---|---|---|---|---|---|
| EV-01 | Construcción inicial | Evolutivo | En producción | FU-01–FU-09 | 1.4 | 2026-11-03 · verificado | 2026-11-10 · <referencia del pase> |
| EV-02 | Firma electrónica | Evolutivo | En construcción | FU-12, FU-14 | 1.7 | — | — |
| URG-01 | Cálculo de plazos en festivos | Urgente | En producción | FU-13 | 1.6 | 2026-11-20 · verificado | 2026-11-21 · <referencia> |
```

Estados: **En análisis → Aprobado → En construcción → Construido → En producción**, o **Descartado**. Los cambia
`proyecto.py cambio <p> <ID> <estado>`, que comprueba las condiciones de cada paso (§6). Nadie edita la tabla a mano.

**Qué pertenece a cada unidad.** Cada informe de impacto dice en su cabecera a qué unidad va (`Cambio: EV-02`; si una
fuente toca dos, una columna «Cambio» por punto). Como toda pieza que cambia cita la fuente nueva en su trazabilidad
(regla ya existente), **las piezas de una unidad son las que citan sus fuentes**: no hay que marcarlas. Los objetos de
la unidad son las filas de §13 del técnico con su ID en una columna nueva, «Cambio».

**La línea base** (lo construido) es el análisis inicial —en una aplicación ajena, el que sale de ingeniería
inversa— más las unidades Construidas; **lo que hay en producción**, el inicial más las unidades En producción.

### 3.3 Las tres diferencias
Con las unidades y las copias de `versiones/` se calculan, sin leer documentos:

| Diferencia | Para qué |
|---|---|
| Lo de una unidad (sus piezas y objetos) | DF del cambio, paquete de construcción, pruebas, pantallas a capturar |
| Unidades no en producción, entre sí y con una URG | Colisiones |
| DF entregado → análisis actual | Lo que el cliente aún no ha validado |

El «Origen» de cada historia deja de escribirse a mano: Nueva, Cambia o Se conserva sale de comparar con la copia
anterior a la primera fuente de la unidad.

## 4. Cómo entra cada caso

### A. Aplicación ajena que vamos a evolucionar
1. **Ingeniería inversa completa, una vez** (`as-is/`). No se repite entera nunca (ver §7, deriva).
2. **Análisis base con todo el detalle (E1)**: el funcional de toda la aplicación desde `as-is/` y, si existe, el DF del
   cliente (modo «DF ya hecho»), por módulos y en paralelo (`volumen-grande.md`). Los criterios y escenarios describen
   el comportamiento real con su evidencia: ✅ si la evidencia es directa (una validación en la regla), 🔶 si es
   inferida. Nada es 🔒 salvo lo que venga de un DF validado. El técnico describe los objetos existentes (§13 con
   Situación «Existe»).
3. Es la **versión 1.0, sin unidad**: construida y en producción por definición, con la fecha del `as-is/`. Word solo
   si se pide (documentación de la aplicación).
4. Desde aquí, cada evolutivo es una `EV-nn` (§5).

### B. Refactorización
1. A completo (as-is y análisis base).
2. La propuesta de refactorización entra como fuente; cada fase de su Hoja de ruta es una `EV-nn` con sus objetos
   «Sustituye a» y su migración de datos. Mientras conviven lo nuevo y lo viejo, las colisiones se miran igual.

### C. Aplicación nueva desde reuniones
1. Análisis desde las reuniones, como hoy.
2. La construcción inicial es `EV-01`. Cuando pasa a producción, cualquier cambio de requisitos sobre lo hecho es una
   `EV-nn` nueva y el informe de impacto lo señala como posible petición de cambio (E3).

## 5. El bucle de un evolutivo

| Paso | Qué se hace | Quién | Lee | Escribe |
|---|---|---|---|---|
| 1. Fuente | Catalogar la reunión, el correo o el chat | analista | la fuente | `fuentes/` |
| 2. Impacto | Informe de impacto, como hoy, con la unidad y dos señales nuevas | analista | solo las piezas candidatas (`indice.py`) | `impacto/FU-nn.md` |
| 3. Aprobación | El analista o el jefe de proyecto deciden; lo construido requiere aprobación | persona | el resumen | — |
| 4. Aplicar | Solo lo afectado; versión +0.1 | analista | `ficha --lineas` | `analisis/` |
| 5. Técnico | Lo afectado, con «Cambio sobre lo construido» si toca algo hecho | analista | los apartados afectados | `tecnico.md` |
| 6. Derivados | DF del cambio, pantallas, paquete | scripts | — | `entregables/` |
| 7. Construir | Con el paquete | Claude o personas | el paquete | entorno |
| 8. Verificar | Leer los objetos tocados y comparar | ingeniería inversa | entorno (solo lectura) | `construccion/verificacion/` |
| 9. Marcar | Construido y, tras el pase, En producción | `proyecto.py` | — | `analisis/cambios.md` |

### 5.1 Señales nuevas en el informe de impacto
- **Construido**: el punto cambia una pieza de una unidad Construida o En producción (o del análisis base de A).
  «Requiere: Sí (construido)» y, en el Resumen, «Posible petición de cambio: puntos 3 y 5» para el jefe de proyecto
  (E3). El plugin no decide si se cobra: lo señala.
- **En curso en EV-nn**: el punto toca una pieza que otra unidad no desplegada ha cambiado. «Requiere: Sí (EV-nn)»:
  hay que decidir el orden o unir las unidades **antes de construir**, que es cuando es barato.

### 5.2 «Cambio sobre lo construido» en el técnico
Cuando una unidad modifica algo construido, el técnico lleva una DT con estos puntos (cada uno con su sección de buenas
prácticas), o «no aplica»:
- **Datos existentes**: valores para los registros que ya hay, migración y su orden (BP 01, BP 08 §3).
- **Procesos en curso**: compatibles hacia atrás, Process Upgrade o Edit Process (BP 03 §12).
- **Integraciones que usan otros**: compatibilidad o versión nueva de la Web API (BP 07 §6).
- **Seguridad**: permisos que cambian (BP 06).
- **Despliegue y vuelta atrás**: orden de paquetes y scripts, y cómo se vuelve (BP 08 §3, BP 11 §7).

### 5.3 Derivados (scripts, sin leer documentos)
- `indice.py cambios <p> EV-02`: piezas nuevas, cambiadas y anuladas (con un antes y después breve), diagramas
  tocados, apartados del técnico, objetos de §13, pantallas y **pruebas a repetir**: los criterios de las historias
  tocadas, los escenarios que pasan por ellas y las pruebas de las URG sobre los mismos objetos. Avisa de colisiones.
- `df_docx.js <p> --cambio EV-02`: el DF del cambio para el cliente: Nuevas, Cambian y las que se conservan pero
  comparten pantalla o paso con ellas; lo demás se resume en un párrafo. El DF completo se sigue pudiendo generar.
- `capture.py --solo <PAN…>`: solo las pantallas del cambio.
- `indice.py paquete <p> EV-02` → `construccion/paquetes/EV-02.md`: el paquete de construcción (E7). Pasos en el
  orden de §13; por objeto, situación, qué cambia y dónde está en el técnico; migración y despliegue; pruebas; tareas
  obligatorias «reaplicar URG-nn» si las hay (§6.4); y la lista de comprobación de cierre. Es Markdown legible por una
  persona y con IDs y rutas estables para el agente, que construye con `appian-best-practices` y sus puertas de
  calidad.

### 5.4 Verificación (E4)
`devmcp_extract.py verificar --objetos <lista del paquete> --out <p>/construccion/verificacion/EV-02.json` (nuevo,
solo lectura): por objeto, que existe, su tipo y nombre, y para record types y CDT, sus campos frente a §3; que su
última modificación es posterior al inicio de la unidad; y que las pruebas de §14 de la unidad existen como casos de
prueba si el técnico lo pide. Lo semántico (que la regla calcula bien) lo garantizan las pruebas que pasa quien
construye con las puertas de buenas prácticas. Sin Dev MCP, la verificación queda «manual» y la marca lo dice.

## 6. Cambios urgentes

Base: Appian recomienda hotfix solo para lo crítico, un parche solo con los objetos de la corrección, construirlo sobre
una versión igual a producción (en desarrollo si no hay colisión, congelando esos objetos; en un entorno igual a
producción si la hay), llevarlo después a desarrollo con una estrategia de fusión, registrar todo y pasar regresión
(BP 08 §3; Appian Max «Deploying an Application Hotfix»). El riesgo típico: el siguiente pase pisa la corrección.

### 6.1 Entrada
Cualquiera declara la urgencia y el plugin no la discute (E6): la ficha dice **quién la declara crítica y por qué**.
Lo que nadie declara crítico es un evolutivo prioritario.

### 6.2 Flujo corto (sin informe completo, sin DF, sin prototipo)
1. **Ficha `impacto/URG-nn.md`**, que es el registro de corrección que pide Appian: síntoma, desde cuándo, a quién
   afecta, quién la declara crítica, diagnóstico, objetos, tipo, colisión, estrategia de fusión, despliegue, vuelta
   atrás y cierre. La fuente (el aviso, el correo, el chat) se cataloga como FU-nn.
2. **Diagnóstico** con `appian-best-practices` (BP 13: síntoma → causa → acción) y leyendo en solo lectura **solo** los
   objetos implicados.
3. **Tipo**:
   - **Defecto**: la aplicación no hace lo especificado. El funcional no cambia; el técnico, si hace falta; §14 gana
     una prueba que reproduce el fallo y se queda para siempre.
   - **Cambio de comportamiento**: CAMBIA aprobado por el jefe de proyecto; la pieza pasa a ✅ y el cliente la valida
     después por el camino normal (R4).
   - **Datos u operación**: corrección de datos, procesos en curso (BP 03 §12), configuración o un certificado
     caducado. No hay parche; la ficha dice qué se hizo.
4. **Colisión** (script, `indice.py colision <p> URG-nn`): objetos de la corrección frente a
   - los de las unidades no en producción (lo planificado), y
   - los modificados en desarrollo después del último pase según su historial de versiones (lo real, §7).
5. **Dónde se corrige**:
   - **Sin colisión**: en desarrollo; esos objetos quedan **congelados** para las unidades abiertas hasta el pase
     (`indice.py paquete` lo avisa).
   - **Con colisión**: en el entorno de corrección (E5). Cada unidad abierta que toca esos objetos recibe en su
     paquete la tarea obligatoria **«reaplicar URG-nn en <objeto>»** con la estrategia de fusión de la ficha y su prueba.
6. **Despliegue** por el proceso de cambios urgentes del cliente (el plugin no lo gestiona), con la vuelta atrás
   preparada: el paquete con la versión de producción de esos objetos. Restaurar una copia de seguridad es lo último:
   devuelve todo el sitio.
7. **Cierre**: verificación (§5.4) en producción en solo lectura si hay acceso, o en el entorno de corrección;
   `proyecto.py cambio URG-nn produccion`. El análisis vigente recoge la corrección y `proyecto.py` recuerda actualizar
   el entorno de corrección con cada pase.

### 6.3 Lo que evita perder una corrección
`proyecto.py cambio EV-nn construido` **no deja** marcar Construida una unidad con una tarea «reaplicar URG-nn» sin
verificar, y `… produccion` no deja pasarla si una URG en producción toca sus objetos y la verificación no la ve
reaplicada (modificación posterior a la URG y su prueba en §14).

### 6.4 Prevención
- Entorno de corrección actualizado con el mismo paquete en cada pase a producción.
- Unidades cortas: menos tiempo con objetos cambiados sin desplegar, menos colisiones.
- En cambios largos sobre objetos centrales, constantes de activación que ocultan lo no publicado (BP 08 §2, varios
  equipos sobre una aplicación).
- Cambios de proceso compatibles hacia atrás (BP 03 §12).

## 7. Deriva: alguien cambió la aplicación fuera de nuestro control
Sobre todo en el caso A. Antes de abrir una unidad y al preparar una URG:
- `devmcp_extract.py deriva --out <p>/as-is` (nuevo, solo lectura): pide solo el historial de versiones de cada objeto
  (el rol `versions`, que el extractor ya usa) y lo compara con el del `as-is/`. Lista objetos cambiados, nuevos y
  retirados. Si el Dev MCP del entorno no da el historial, lo dice y no supone nada.
- `extract --solo <objetos>` vuelve a extraer solo esos, y el registro **mantiene los IDs** de hallazgos y NV que ya
  existían (se casan por área, objetos y señal); los nuevos siguen la numeración.
- La deriva entra al análisis como una fuente más (tipo «as-is») por el informe de impacto.

## 8. Calidad y coherencia: lo que comprueban los scripts
- `comprobar.py`:
  - una pieza de una unidad sin su reflejo en el técnico (fila de §13 con la unidad o DT que cita su fuente): aviso;
  - una unidad que modifica algo construido sin «Cambio sobre lo construido»: error;
  - dos unidades abiertas sobre la misma pieza u objeto sin decisión registrada: aviso;
  - criterios de las historias tocadas sin prueba en §14, y una URG de tipo defecto sin su prueba: error.
- `proyecto.py cambio`: las condiciones de cada estado (aprobada antes de construir; verificación antes de
  Construido; Construido y reaplicaciones antes de En producción).
- Las demás comprobaciones (citas, IDs, jerga en el DF, dependencias) siguen igual.

## 9. Eficiencia
- **La base se procesa una vez** (E1), por módulos y en paralelo; después nunca se relee entera: `indice.py` da solo
  lo que hace falta.
- **Ninguna diferencia la calcula el modelo**: las unidades, las colisiones, el DF del cambio y el paquete salen de
  scripts que comparan IDs, citas y copias.
- **Ingeniería inversa no se repite entera**: deriva y reextracción de solo lo cambiado.
- **Nada se regenera si no cambia**: versión, Word, capturas y anexo solo con cambios (R2).
- **El camino urgente es corto**: una ficha y solo los objetos implicados.

## 10. Qué escribe cada skill (sin solapes)

| Ruta | Dueño |
|---|---|
| `analisis/cambios.md` | appian-functional-analyst (vía `proyecto.py`) |
| `impacto/URG-nn.md` | appian-functional-analyst |
| `construccion/paquetes/` | appian-functional-analyst |
| `construccion/verificacion/` | appian-reverse-engineering |
| `as-is/` (también la deriva y la reextracción) | appian-reverse-engineering |

`appian-best-practices` diagnostica y construye en el entorno y sigue sin escribir en `<p>`.

## 11. Cambios en el plugin (sustituyen la parte de evolutivo de G4)

**Analista**
- [ ] `analisis/cambios.md` y `proyecto.py cambio` (nuevo, estados y condiciones); plantilla y `proyecto.md` con
  «Cambios abiertos».
- [ ] Informe de impacto: cabecera «Cambio», columna opcional, señales «Construido» y «En curso en EV-nn», petición
  de cambio en el Resumen (`actualizacion.md`, `comprobar.py --impacto`).
- [ ] Técnico: columna «Cambio» en §13 (siempre tabla desde la primera construcción) y DT «Cambio sobre lo construido»
  (`tecnico-plantilla.md`, `comprobar.py`).
- [ ] `indice.py cambios`, `colision` y `paquete`; `df_docx.js --cambio` (sustituye `--cambios` de T5).
- [ ] El «Origen» de las historias pasa a derivarse: se quita de la plantilla y de `comprobar.py`, y lo calcula
  `indice.py cambios`.
- [ ] Modo «Urgente» en SKILL.md y `references/urgentes.md` (§6) con la plantilla de la ficha.
- [ ] Caso A con detalle (E1) en «Aplicación existente» y `volumen-grande.md`.

**Ingeniería inversa**
- [ ] `devmcp_extract.py verificar` y `deriva`; `extract --solo`.
- [ ] IDs estables de hallazgos y NV al reextraer (`build_registry.py`), con su prueba.

**Prototipos**
- [ ] `capture.py --solo` (ya en G5).

**Pruebas**
- [ ] Evaluación nueva «evolutivo con urgencia», a ciegas: aplicación ficticia con `EV-01` en producción, un `EV-02`
  en construcción y una URG que choca con él. Se mide: colisión detectada, tarea de reaplicar en el paquete, Construido
  bloqueado sin reaplicar, DF del cambio solo con lo suyo y ningún documento regenerado sin cambios.

## 12. Riesgos y lo que hay que confirmar
- Que el Dev MCP real devuelve el historial de versiones de cada objeto (el simulador sí; el extractor ya lo usa como
  rol `versions`). Sin él, la deriva y la parte real de la colisión no se pueden calcular y el plugin lo dice.
- La verificación es estructural; lo semántico depende de las pruebas que pase quien construye.
- El entorno de corrección y el proceso de pase los lleva el equipo; el plugin solo los recuerda.
