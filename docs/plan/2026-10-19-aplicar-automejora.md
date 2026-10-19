# Aplicar las lecciones de automejora

El trabajo corrige los fallos recogidos tras P1–P10 y mejora el paso del análisis a la construcción. Autorizado el
19 de octubre de 2026 después de una revisión del código. Parte de `automejora-pruebas` (`2deab8c`), sobre `main`
(`2f9151d`). La rama de integración es `codex/aplicar-automejora`; la versión sigue en 0.8.0-beta.1.

La sesión principal integra y revisa. Tres subagentes trabajan en worktrees separados: analista/issues/QA,
inversa/diagramas e ingesta/plantillas/prototipos. Las pruebas con proyectos generados van fuera del repositorio.
No se publica, abre PR, cambia la versión ni escribe en Appian con este encargo.

## Alcance y comprobación

Los identificadores corresponden al orden de la lista entregada por el usuario. «Pendiente» no equivale a probado;
cada bloque se cierra con su evidencia en `docs/evaluaciones.md`. Los puntos aparcados quedan en
`docs/siguiente-version.md`, sin repetir allí lo que ya se haya aplicado.

| ID | Resultado que debe quedar | Estado |
|---|---|---|
| A1 | Regenerar el anexo rechaza contenido manual que perdería; conserva las otras secciones | Pendiente |
| A2 | Colisión desconocida cuando falta el grafo; sin recomendación de entorno basada en una comprobación inexistente | Pendiente |
| A3 | Una constante sigue siendo constant aunque su valor sea TEXT o GROUP | Pendiente |
| A4 | Campos adicionales no bloquean objetos nuevos; las demás diferencias siguen contando; auditoría en cada tabla | Pendiente |
| A5 | §13 en lista pide conversión a tabla antes de generar issues, en comando, comprobador y flujo | Pendiente |
| A6 | Construida manualmente enumera issues pendientes | Pendiente |
| A7 | Aplicación exacta y prefijo separados; no recortar paréntesis legítimos del nombre | Pendiente |
| A8 | IDs nuevos conservan ancho por tipo, sin renumerar existentes | Pendiente |
| A9 | La fuente de aprobación registrada cuenta como procesada | Pendiente |
| A10 | Imágenes enlazadas pertenecen al Markdown; las independientes siguen siendo fuentes | Pendiente |
| A11 | Registrar la versión inicial y sus fuentes sin aumentar 1.0 a 1.1 | Pendiente |
| A12 | El mensaje del QA no contradice una excepción humana vigente | Pendiente |
| A13 | No reutilizar el número de una issue eliminada al regenerar | Pendiente |
| A14 | Ayuda UTF-8 antes de parsear argumentos; unir_modulos ya lo hacía | Pendiente |
| A15 | Cuerpo EML normalizado sin retornos de carro incrustados | Pendiente |
| A16 | Conservar LF o CRLF del fichero existente al reescribir | Pendiente |
| A17 | El montaje de evaluaciones crea el proyecto con iniciar | Pendiente |
| A18 | Herramientas específicas clasificadas por tipo con evidencia de su contrato real | Pendiente |
| A19 | Comprobar as-is admite nombres completos con guion y muestra ayuda | Pendiente |
| A20 | Textos localizados y savedBy interpretados sin alterar la respuesta fuente | Pendiente |
| A21 | Grupos excluidos del indicador de huérfanos | Pendiente |
| A22 | Salida 14 explica por qué no se obtuvo la lista de aplicaciones | Pendiente |
| B1 | Retoque por chat crea primero su fuente | Pendiente |
| B2 | F1 aclara las notas por fuente y la excepción de fuentes cortas | Pendiente |
| B3 | Site y páginas en la issue de la primera pantalla que publican | Pendiente |
| B4 | Textos de más de 255 caracteres: Long Text; no atribuir un límite al MCP sin evidencia | Pendiente |
| B5 | Guion QA documenta load para cambiar de página | Pendiente |
| B6 | Ejemplo de una fuente que afecta a dos unidades | Pendiente |
| B7 | Rangos completos de IDs, técnico común del coordinador y F1 enlaza volumen grande | Pendiente |
| B8 | Secuencias repetidas tres veces o más: descripción común y tabla que cita todos los nodos | Pendiente |
| B9 | Nodo que inicia otro proceso: distinguirlo del Subprocess ya documentado | Pendiente de evidencia |
| B10 | El analista fija entradas y salidas esperadas para los criterios basados en reglas | Pendiente |
| C1 | Una issue que espera a otras lo avisa al abrirla | Pendiente |
| C2 | Regeneración informa cambios y reservas; el constructor ve si su versión cambió | Pendiente |
| C3 | DF de cambio advierte de revisar capturas de pantallas modificadas | Pendiente |
| C4 | Impacto localiza filas y secciones con sus líneas | Pendiente |
| C5 | Aviso Gherkin también en primera versión | Pendiente |
| C6 | Aviso de Con qué ausente en §14 | Pendiente |
| C7 | Pruebas expresamente exigidas y ausentes dejan issue pendiente, con excepción humana motivada | Pendiente |
| C8 | Verificar permisos de acciones e inicio de procesos | Aparcado |
| D1 | Cambio sobre pieza de una unidad sin construir sigue en esa unidad; sin snapshots nuevos | Pendiente |
| D2 | Supuestos por PC/objeto llegan a la issue; PC respondido pasa por impacto | Pendiente |
| D3 | Ruta local del plugin ignorada por git y localizable desde AGENTS | Pendiente |
| D4 | Índice con palabras y reparto en bloques de 20.000–25.000 palabras | Pendiente |
| D5 | Candidatas casi duplicadas visibles; exclusión de lectura/cobertura explícita y trazable | Pendiente |
| D6 | Concepto o contradicción compartidos con módulo dueño | Pendiente |
| D7 | Título de issue refleja lo agrupado y lista paralela resumida; sin partición automática | Pendiente |
| D8 | Cierre manual por issue con motivo | Pendiente de decisión |
| D9 | Inventario y huérfanos por script, conservando descripciones interpretadas y enlaces | Pendiente |
| D10 | Entrada de cada tramo indica paso de origen | Pendiente |
| D11 | Chat ajustado al alto visible tras reproducir; pestaña nueva aparcada | Pendiente |
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
