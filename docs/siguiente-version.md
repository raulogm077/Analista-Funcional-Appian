# Pendiente

La única lista de lo que falta, en el orden en que se hace: un paso cada vez, y cada punto con su commit y su prueba.
Lo hecho, con sus pruebas y límites, pasa a [evaluaciones.md](evaluaciones.md). Cada punto dice a quién toca. Esta
lista no autoriza publicar, desplegar, enviar ni borrar.

**Ahora:** paso 2, punto 2.1: Claude trae su recomendación, cuando Codex dé por revisados los ajustes del paso 1
(`COMMITREV`).

## 1. En la rama actual, por orden

### Paso 2 · Decisiones de Raúl

Claude trae una recomendación por punto; se aplica lo que Raúl decida.

- **2.1 Documentos al cerrar un incremento.** En la prueba con y sin el plugin, los documentos quedaron a medias en los
  dos brazos. Con el plugin: decisiones antiguas marcadas como vigentes, contradicciones puntuales y el estado del
  proyecto sin cerrar. Los diagramas de estados sí se pusieron al día. Raúl lo quiere mejorar. Es juicio del modelo al
  cerrar la unidad. Falta decidir dónde se le pide (F8 o `cambios.md`), sin añadir un control. [flujo]
- **2.2 Coste del análisis.** Con el plugin, el análisis costó más en los tres incrementos. Un reparto contable de las
  transcripciones (hipótesis, no ahorro causal) apunta a dos causas:
  - los pasos del método por incremento: unos 155 de 482 turnos usan órdenes o ficheros propios del plugin;
  - los documentos vivos grandes (`funcional.md` ~94 KB y `tecnico.md` ~196 KB), que se editan por parches y se
    releen con un contexto de hasta 760–930k tokens.

  El texto de skills y referencias pesa poco. Antes de recortar, decidir qué pasos se juntan o pasan a scripts y cómo
  leer solo la parte del técnico que toca. Medirlo en una unidad real, junto con la regla de F8 «varias issues por
  sesión», que también es una hipótesis. [flujo y scripts]
- **2.3 Aviso «criterios sin objeto».** No se apaga al marcar la unidad construida, porque las historias no tienen la
  marca «Otra unidad». Decidir si basta una frase en la plantilla o hace falta una marca para historias.
  [`comprobar.py`, `indice.py`]
- **2.4 Cambiar una issue ya verificada.** Falta un camino corto: dónde se escribe, qué subtareas lleva y qué cambió.
  [F8]
- **2.5 Referencias de la skill oficial por tipo de objeto.** Cargarla entera costaba un 37–72 % de una sesión hasta su
  primera escritura. Decidir si F8 dice qué referencias cargar según el objeto. [F8]
- **2.6 F9.** Decidir si la IA puede dejar preparado el paquete en desarrollo; hoy lo prepara una persona. Si puede,
  decir que `addPackageObjects` en lote no admite los objetos de contenido. [F9]

### Paso 3 · Prueba con el plugin cargado desde la carpeta

- **Probar los cambios de comportamiento con el plugin cargado desde la carpeta** (`claude --plugin-dir`) en un
  proyecto de prueba, como pide `CLAUDE.md`. Comprobar: el localizador con una sesión real; «gasta» en un guion de QA,
  que la skill lo pone al preparar el guion y no solo que el motor lo respeta; la línea «Unidades», el aviso y que el
  analista pone al día «Siguiente paso»; una tarea de una persona en Designer en la entrega; `git push` con un remoto
  local, con y sin autorización, y sin remoto; y lo que cambien los pasos 1 y 2. Aprobarla no autoriza escribir en
  Indra-spain ni subir a GitHub. [prueba]

### Paso 4 · Residuos de las pruebas

- En `Pruebas-plugin`, revisar `automejora/`, `automejora-codex-20261019/`, `T1-agilidad/`, `T5-devmcp-sail/`,
  `T6-retoque-construido/`, `T13-pruebas-issue/`, `T15-qa/`, `T16-ensayo-qa/` y `retoque-analisis/`. Antes de borrar
  cada una, comprobar que sus lecciones estén aquí o en `evaluaciones.md`, si la cita como evidencia algún documento
  que se conserva (el seguimiento del ensayo, la revisión de Codex) y qué objetos dejó en Indra-spain
  (`T6-retoque-construido/objetos-creados.md`). Se guarda lo que haga falta; lo demás, y sobre todo lo que lleve datos
  del cliente, se borra con la confirmación de Raúl, que lanza él el borrado si la sesión no puede. [persona y sesión]
- En Indra-spain, la regla desechable `IFA_PruebaTestInputsDevMcp` de la aplicación IFA, que dejó la comprobación del
  1.3; se borra con la confirmación de Raúl. [sesión]

### Paso 5 · Cierre de la rama

- **Cierre**, cuando Raúl diga «sube». Antes del PR, poner al día «Trabajo en curso» de `CLAUDE.local.md`. La batería
  completa pasa en GitHub. Antes de publicar una versión, las siete combinaciones y `pruebas/comprobar_anclas.py` (con
  red). [persona y sesión]
- **Copia de seguridad.** La rama no está en GitHub; se sube como copia, sin PR, cuando Raúl lo autorice. [persona]

## 2. Cuando se dé su condición

- **Índice del DOCX.** Evaluar la caché editable solo si una entrega la necesita. [Word]
- **Dimensiones de QA sin medir:** visual y accesibilidad, roles con cuenta, autorización de servidor, vigencia causal,
  atomicidad y concurrencia. Solo las que necesite la entrega; no crear cuentas ni escribir datos por esta lista. El
  contraste automático de texto sobre fondo compuesto, si un caso visible lo pide. [pruebas]
- **LEEME completo y deriva interna** de una aplicación real: siguen sin medir. La extracción masiva sigue detenida y
  `getAgent`, aparcado tras el aviso a Appian. Al reanudarla, decidir si reconoce el parámetro `object` de
  `getObjectDependents` o se queda con el grafo actual (límite en `evaluaciones.md`).
- **Diagramas.** Reducir los 30/38 avisos residuales solo con una mejora medida, sin relajar detectores.
- **URL `/help/26.6/`** de `data-fabric.md` y `agents/data-modeler.md`: revisarlas cuando cambie la versión de Appian
  del entorno.
- **Aviso a Appian** (`aviso-appian-devmcp.md`, en la carpeta de pruebas): revisarlo con el servidor 26.9.5, porque el
  punto 10 ya está en parte corregido. Añadir la discrepancia de `LCP_TOOL_MODE=readonly`. Lo envía Raúl. [persona]
- **Rama `yaroslav/plantilla-DF-cliente`** en GitHub, solo si Raúl lo pide: 17 commits del 19-oct sin PR, ni en
  `main` ni en esta rama; es independiente de ella. [persona]
- **Tarea no prioritaria**, solo cuando Raúl lo pida: renombrar el plugin a «Appian Software Factory» en todos los
  sitios (GitHub, carpeta local, `plugin.json`, el prefijo de las skills, README, gráficos y `CLAUDE.md`).
