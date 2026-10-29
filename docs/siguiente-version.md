# Para la siguiente versión

Sólo trabajo pendiente, ordenado por área. Resultados, commits y límites medidos en [evaluaciones.md](evaluaciones.md).
Cada punto dice qué falta y a quién toca. Esta lista no autoriza publicar, desplegar, enviar ni borrar.

## Antes de subir la rama actual

- **Probar los cambios de comportamiento con el plugin cargado desde la carpeta** (`claude --plugin-dir`) en un
  proyecto de prueba, como pide `CLAUDE.md`. Comprobar: el localizador con una sesión real; «gasta» en un guion de QA;
  la línea «Unidades» y el aviso del siguiente paso; una tarea de una persona en Designer en la entrega; y `git push`
  con y sin autorización. [prueba]
- **Cierre de la rama**, cuando Raúl diga «sube». Antes del PR, poner al día «Trabajo en curso» de
  `CLAUDE.local.md`. La batería completa pasa en GitHub. Antes de publicar una versión, las siete combinaciones y
  `pruebas/comprobar_anclas.py` (con red). [persona y sesión]

## Análisis y documentos

- **Documentos al cerrar un incremento.** En la prueba con y sin el plugin, los documentos quedaron a medias en los dos
  brazos. Con el plugin: decisiones antiguas marcadas como vigentes, contradicciones puntuales y el estado del proyecto
  sin cerrar. Los diagramas de estados sí se pusieron al día. Raúl lo quiere mejorar. Es juicio del modelo al cerrar la
  unidad. Falta decidir dónde se le pide (F8 o `cambios.md`), sin añadir un control. [flujo]
- **Coste del análisis.** Con el plugin, el análisis costó más en los tres incrementos. Un reparto contable de las
  transcripciones (hipótesis, no ahorro causal) apunta a dos causas:
  - los pasos del método por incremento: unos 155 de 482 turnos usan órdenes o ficheros propios del plugin;
  - los documentos vivos grandes (`funcional.md` ~94 KB y `tecnico.md` ~196 KB), que se editan por parches y se
    releen con un contexto de hasta 760–930k tokens.

  El texto de skills y referencias pesa poco. Antes de recortar, decidir qué pasos se juntan o pasan a scripts y cómo
  leer solo la parte del técnico que toca. Medirlo en una unidad real, junto con la regla de F8 «varias issues por
  sesión», que también es una hipótesis. [flujo y scripts]
- **Estado tras validar el DF.** `version --decision VALIDA` dejaba el funcional y `proyecto.md` en «borrador», y
  `estado` decía «fuentes: —». Comprobarlo con un proyecto ficticio. Si sigue, que el estado refleje la validación, sin
  inferir la entrega. [`proyecto.py`]
- **Aviso «criterios sin objeto».** No se apaga al marcar la unidad construida, porque las historias no tienen la marca
  «Otra unidad». Decidir si basta una frase en la plantilla o hace falta una marca para historias.
  [`comprobar.py`, `indice.py`]
- **Huecos de la plantilla técnica**, una frase cada uno:
  - el formato de los importes, con una expresión probada (dio «8600; 000,00 €» en dos interfaces);
  - que la aplicación crea `<prefijo> Users` y `<prefijo> Administrators`, y qué vistas por defecto se ocultan;
  - una tabla de relaciones en §3, y en §0 la cuenta del Dev MCP, la versión y la fuente de datos (se ahorraban 11
    lecturas);
  - qué hace F1 con fuentes que mejoran una aplicación que no se puede leer.

  [plantilla técnica]
- **Índice del DOCX.** Evaluar la caché editable solo si una entrega la necesita. [Word]

## Construcción y verificar (F8, F9)

- **Dependencias entre issues.** Que el orden calculado vea que un `a!recordLink` necesita la vista de resumen que hace
  otra issue. Que las correcciones de dependencias no caduquen por cualquier cambio de la issue. [`issues.py`]
- **Cambiar una issue ya verificada.** Falta un camino corto: dónde se escribe, qué subtareas lleva y qué cambió.
  [F8]
- **Registrar una decisión que cambia el orden.** El orden es DT, regenerar y después la corrección de la issue que
  depende. Si no, se forma un ciclo. La issue dice de cuál depende y por qué. [`cambios.md`]
- **`verificar`** dice lo que no comprueba (relaciones, seguridad de registro, grupos, datos, vistas ocultas) o lo
  comprueba. [script]
- **Referencias de la skill oficial por tipo de objeto.** Cargarla entera costaba un 37–72 % de una sesión hasta su
  primera escritura. Decidir si F8 dice qué referencias cargar según el objeto. [F8]
- **F9.** Decidir si la IA puede dejar preparado el paquete en desarrollo; hoy lo prepara una persona. Si puede, decir
  que `addPackageObjects` en lote no admite los objetos de contenido. [F9]

## QA

- **Datos que presupone cada prueba.** Cada prueba dice qué datos presupone y cómo sigue con el estado real: una
  tipología dejada para el QA rompió una regla. En una aplicación de solo consulta, los «dado» salen de los datos de
  §3.9, que el QA no lee. [`appian-qa`, plantilla]
- **Casos NO_ERRORS.** Los casos de prueba de reglas guardados con aserción NO_ERRORS prueban que no falla, no el
  contenido. Que lo diga la plantilla del técnico §14. [plantilla]
- **`fila` y `sin_fila`** aceptan una sola fila por paso, y `show` no tiene ejemplo. [`appian-qa`]
- **Dimensiones de QA sin medir:** visual y accesibilidad, roles con cuenta, autorización de servidor, vigencia y
  atomicidad. Solo las que necesite la entrega; no crear cuentas ni escribir datos por esta lista. El contraste
  automático de texto sobre fondo compuesto, si un caso visible lo pide. [pruebas]

## Ingeniería inversa y diagramas

- **LEEME completo y deriva interna** de una aplicación real: siguen sin medir. La extracción masiva sigue detenida y
  `getAgent`, aparcado tras el aviso a Appian.
- **Diagramas.** Reducir los 30/38 avisos residuales solo con una mejora medida, sin relajar detectores.

## Buenas prácticas y Dev MCP

- **Trampas de SAIL y seguridad**, de dos pruebas reales de construcción. Llevarlas a las buenas prácticas; se puede
  hacer ya, sin caso nuevo:
  - un grid no acepta una lista vacía de mapas aunque esté oculto, ni dos grupos de filtros anidados vacíos a la vez;
  - dos filtros en `AND` sobre una relación uno a muchos se cumplen con filas distintas: hace falta `AND_ALL`;
  - `append()` con un texto como primer argumento concatena;
  - la seguridad «quien ve el registro relacionado», encadenada en dos niveles, no deja ver nada;
  - las cuentas con el idioma de la máquina dan los importes en formato inglés.

  [`02-interfaces-sail.md`, `06-security.md`]
- **`listProcessInstances`.** Que un proceso no salga en la lista no prueba que no se ejecutara: faltaron instancias, y
  el orden y el «total» no cuadraban con los efectos. Añadir una fila en el doc 14 §3: contrastar con el efecto (datos,
  `listProcessEvents`, el buzón), con el build en el que se vio. [doc 14]
- **Filas del doc 14 §3** vistas con builds anteriores al 26.9.5: se quitan cuando ya no se vea el síntoma, como dice
  el propio doc. Comprobar también si `createExpressionRule` con `testInputs` sigue añadiendo un caso propio; si sigue,
  añadir su fila. [doc 14]
- **URL `/help/26.6/`** de `data-fabric.md` y `agents/data-modeler.md`: revisarlas cuando cambie la versión de Appian
  del entorno.
- **Aviso a Appian** (`aviso-appian-devmcp.md`, en la carpeta de pruebas): revisarlo con el servidor 26.9.5, porque el
  punto 10 ya está en parte corregido. Añadir la discrepancia de `LCP_TOOL_MODE=readonly`. Lo envía Raúl. [persona]

## Operación y entorno

- **Tarea no prioritaria**, solo cuando Raúl lo pida: renombrar el plugin a «Appian Software Factory» en todos los
  sitios (GitHub, carpeta local, `plugin.json`, el prefijo de las skills, README, gráficos y `CLAUDE.md`).
