# Aplicar las lecciones de automejora

El trabajo corrige los fallos recogidos tras P1–P10 y mejora el paso del análisis a la construcción. Autorizado el
19 de octubre de 2026 después de una revisión del código. Parte de `automejora-pruebas` (`2deab8c`), sobre `main`
(`2f9151d`). La rama de integración es `codex/aplicar-automejora`; la versión sigue en 0.8.0-beta.1.

La sesión principal integra y revisa. Tres subagentes trabajan en worktrees separados: analista/issues/QA,
inversa/diagramas e ingesta/plantillas/prototipos. Las pruebas con proyectos generados van fuera del repositorio.
No se publica, abre PR, cambia la versión ni escribe en Appian con este encargo.

## Alcance y comprobación

Los identificadores corresponden al orden de la lista entregada por el usuario. «Aplicado» describe el código y la
documentación local; la evidencia y sus límites están en `docs/evaluaciones.md`. Los puntos aparcados quedan en
`docs/siguiente-version.md`, sin repetir allí lo que ya se haya aplicado.

| ID | Resultado que debe quedar | Estado |
|---|---|---|
| A1 | Regenerar el anexo rechaza contenido manual que perdería; conserva las otras secciones | Aplicado |
| A2 | Colisión desconocida cuando falta el grafo; sin recomendación de entorno basada en una comprobación inexistente | Aplicado |
| A3 | Una constante sigue siendo constant aunque su valor sea TEXT o GROUP | Aplicado |
| A4 | Campos adicionales no bloquean objetos nuevos; las demás diferencias siguen contando; auditoría en cada tabla | Aplicado |
| A5 | §13 en lista pide conversión a tabla antes de generar issues, en comando, comprobador y flujo | Aplicado |
| A6 | Construida manualmente enumera issues pendientes | Aplicado |
| A7 | Aplicación exacta y prefijo separados; no recortar paréntesis legítimos del nombre | Aplicado |
| A8 | IDs nuevos conservan ancho por tipo, sin renumerar existentes | Aplicado |
| A9 | La fuente de aprobación registrada cuenta como procesada | Aplicado |
| A10 | Imágenes enlazadas pertenecen al Markdown; las independientes siguen siendo fuentes | Aplicado |
| A11 | Registrar la versión inicial y sus fuentes sin aumentar 1.0 a 1.1 | Aplicado |
| A12 | El mensaje del QA no contradice una excepción humana vigente | Aplicado |
| A13 | No reutilizar el número de una issue eliminada al regenerar | Aplicado |
| A14 | Ayuda UTF-8 antes de parsear argumentos; unir_modulos ya lo hacía | Aplicado |
| A15 | Cuerpo EML normalizado sin retornos de carro incrustados | Aplicado |
| A16 | Conservar LF o CRLF del fichero existente al reescribir | Aplicado |
| A17 | El montaje de evaluaciones crea el proyecto con iniciar | Aplicado |
| A18 | Herramientas específicas clasificadas por tipo con evidencia de su contrato real | Aplicado |
| A19 | Comprobar as-is admite nombres completos con guion y muestra ayuda | Aplicado |
| A20 | Textos localizados y savedBy interpretados sin alterar la respuesta fuente | Aplicado |
| A21 | Grupos excluidos del indicador de huérfanos | Aplicado |
| A22 | Salida 14 explica por qué no se obtuvo la lista de aplicaciones | Aplicado |
| B1 | Retoque por chat crea primero su fuente | Aplicado |
| B2 | F1 aclara las notas por fuente y la excepción de fuentes cortas | Aplicado |
| B3 | Site y páginas en la issue de la primera pantalla que publican | Aplicado |
| B4 | Textos de más de 255 caracteres: Long Text; no atribuir un límite al MCP sin evidencia | Aplicado |
| B5 | Guion QA documenta load para cambiar de página | Aplicado |
| B6 | Ejemplo de una fuente que afecta a dos unidades | Aplicado |
| B7 | Rangos completos de IDs, técnico común del coordinador y F1 enlaza volumen grande | Aplicado |
| B8 | Secuencias repetidas tres veces o más: descripción común y tabla que cita todos los nodos | Aplicado |
| B9 | Nodo que inicia otro proceso: distinguirlo del Subprocess ya documentado | Aplicado; contrato P5b |
| B10 | El analista fija entradas y salidas esperadas para los criterios basados en reglas | Aplicado |
| C1 | Una issue que espera a otras lo avisa al abrirla | Aplicado |
| C2 | Regeneración informa cambios y reservas; el constructor ve si su versión cambió | Aplicado |
| C3 | DF de cambio advierte de revisar capturas de pantallas modificadas | Aplicado |
| C4 | Impacto localiza filas y secciones con sus líneas | Aplicado |
| C5 | Aviso Gherkin también en primera versión | Aplicado |
| C6 | Aviso de Con qué ausente en §14 | Aplicado |
| C7 | Pruebas expresamente exigidas y ausentes dejan issue pendiente, con excepción humana motivada | Aplicado |
| C8 | Verificar permisos de acciones e inicio de procesos | Aparcado |
| D1 | Cambio sobre pieza de una unidad sin construir sigue en esa unidad; sin snapshots nuevos | Aplicado |
| D2 | Supuestos por PC/objeto llegan a la issue; PC respondido pasa por impacto | Aplicado |
| D3 | Ruta local del plugin ignorada por git y localizable desde AGENTS | Aplicado |
| D4 | Índice con palabras y reparto en bloques de 20.000–25.000 palabras | Aplicado |
| D5 | Candidatas casi duplicadas visibles; exclusión de lectura/cobertura explícita y trazable | Aplicado |
| D6 | Concepto o contradicción compartidos con módulo dueño | Aplicado |
| D7 | Título de issue refleja lo agrupado y lista paralela resumida; sin partición automática | Aplicado |
| D8 | Cierre manual por issue con motivo | Aplicado; cierre humano con motivo y versión |
| D9 | Inventario y huérfanos por script, conservando descripciones interpretadas y enlaces | Aplicado |
| D10 | Entrada de cada tramo indica paso de origen | Aplicado |
| D11 | Chat ajustado al alto visible tras reproducir; pestaña nueva aparcada | Aplicado |
| E1 | Borrador de §13 por script | Medir antes |
| E2 | Corregir dependencias de issues a mano | Aparcado hasta caso real |
| E3 | Prueba diferencial en refactorización | Aparcada hasta refactorización real |
| E4 | Pedir dependientes de cada objeto durante extracción | Descartado; conservar grafo y verificación existentes |
| E5 | Ancho de arquitectura Mermaid | Aparcado, sin criterio nuevo acordado |
| E6 | Presupuesto LEEME | Medir con aplicación grande |
| E7 | Paralelizar batería completa | Aparcado |

## Validación y relevo

Cada subagente ejecuta las pruebas de las capacidades modificadas y la comprobación básica antes de su commit.
La integración revisa los contratos compartidos (esperado de la issue, fuentes duplicadas y ruta local), vuelve a
comprobar el conjunto y revisa visualmente los dos SVG de `.github/assets/` y el chat. La batería `--completo`
corresponde al PR en Linux; no se lanza en este equipo.

La prueba de comportamiento con `claude --plugin-dir` queda separada de los selftests: si no se puede ejecutar por
la cuota de Claude, se deja expresamente pendiente antes de subir. No se presenta una prueba local como validación
en Appian ni como aprobación del pase.

Al terminar, este plan indica commits, resultado de integración y siguiente paso para Claude; `evaluaciones.md`
guarda las medidas y `siguiente-version.md` solo conserva trabajo pendiente. La carpeta principal queda en `main`.

## Decisiones concretas al aplicar

- A7 conserva los paréntesis que sean parte del nombre real de la aplicación; los comentarios y el prefijo van fuera
  de esa celda. A14 requería corregir `leer_fuentes.py`; `unir_modulos.py` ya configuraba UTF-8 antes de argparse.
- B9 corresponde a Start Process (`appian.system.smart-services.start-process-5`), comprobado en la extracción
  guardada de P5b; se documenta separado de Subprocess. B4 recomienda Long Text sin atribuir al MCP un fallo no
  vuelto a medir.
- C7 bloquea el cero confirmado de casos exigidos, no una lectura fallida. Se mantiene la excepción humana
  `--sin-prueba --motivo`. D8 permite cierre individual con `--manual --motivo`, autor, fecha y versión; no escribe una
  verificación ni oculta fallos vigentes sin su propia excepción. `--automatico` retira el cierre; cambiar la issue lo
  invalida. La unidad y F9 conservan esa procedencia.
- D5 solo propone las fuentes casi idénticas; `--duplicada FU-nn=FU-mm --motivo` excluye una tras decidirlo y
  `--restaurar` permite recuperarla. No se descarta contenido automáticamente por similitud.
- D9 preserva texto humano y enlaces por UUID. Si el inventario antiguo no delimita lo generado, `--borrador` crea
  salidas aparte para migrarlo tras revisar; no se sobrescribe el documento antiguo.

## Relevo

Commits de integración: `21d2f8b` (gráficos y alcance), `cf22965` (ingesta, plantillas y chat), `f61e779`
(analista, issues y QA) y `3c0b807` (inversa, inventario y diagramas). El commit de cierre añade las medidas, limpia
los pendientes y actualiza este relevo.

Integración comprobada: analista 392 comprobaciones correctas, QA 57, prototipos 45, inversa 203 y dos omisiones
documentadas, diagramas correctos. P10 recibe 25/25 supuestos y las reglas generales en sus 25 issues. La comprobación
básica da siete skills, cero errores y cero avisos. Detalle, suplementos y límites en `docs/evaluaciones.md`.

Retomar en `Proyectos IA/Plugin-automejora-codex`, rama `codex/aplicar-automejora`, y leer primero este plan.
La carpeta `Plugin Analista funcional Appian` sigue en `main`; `automejora-pruebas` conserva el trabajo previo de
Claude. No copiar el plugin instalado sobre ninguna de estas carpetas.

Los artefactos de esta sesión están en `Proyectos IA/Pruebas-plugin/automejora-codex-20261019/`: resultados P10 antes y
después, capturas del chat, renders de ambos SVG, logs de selftests y evidencia de inversa. Contienen salidas de
proyectos reales; no se añaden al repositorio. La matriz anterior cubre todos los puntos A–E; no volver a implementar
los ya aplicados ni reabrir los aparcados sin un caso o una decisión nueva.

El siguiente paso antes de subir es probar el comportamiento con `claude --plugin-dir` desde este worktree, en un
proyecto externo. No se ha medido en esta sesión. Después, resumir el resultado a Raúl; el PR, la integración en main
y la publicación siguen el permiso y las comprobaciones de `CLAUDE.md`. La versión continúa en 0.8.0-beta.1.
