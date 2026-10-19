# Para la siguiente versión

Trabajo que queda abierto después de aplicar las lecciones de automejora del 19 de octubre de 2026, sobre la
0.8.0-beta.1. Raúl pidió abordar los temas aplazados antes de publicar: la fase activa está en
`docs/plan/2026-10-19-temas-aplazados.md`. Los cambios terminados y sus pruebas están en `docs/evaluaciones.md`;
la primera tanda quedó cerrada en `docs/plan/2026-10-19-aplicar-automejora.md`. Esta lista no autoriza publicar ni actuar en un entorno.

La rama de trabajo única es `automejora-pruebas`: contiene la primera tanda de Claude y los cambios posteriores. La
app de escritorio queda como comprobación visual pendiente, sin bloquear por sí sola la publicación. `getAgent`
queda aparcado tras el reporte de Raúl a Appian; no se repetirá en la medición de esta fase.

## Antes de subir y publicar

- Probar el comportamiento de las skills modificadas con `claude --plugin-dir <carpeta>` en un proyecto fuera del
  repositorio. Los selftests y las regresiones sobre copias de P10 no sustituyen esa prueba.
- Cuando Raúl autorice subir: PR y batería completa en Linux. Antes de publicar una versión, las siete combinaciones
  de sistema/Python y la comprobación de anclas, como indica `CLAUDE.md`. La versión sigue sin cambiar.
- Instalar el paquete en un Windows con algún requisito sin instalar y comprobar que el primer mensaje lo explica. En
  Linux con Claude Code ya se vio; el hook de Windows dejó su marca con 0.7.0-beta.1, pero falta ver el mensaje con un
  requisito ausente. Comprobar visualmente la instalación en la app de escritorio cuando esté disponible; registrar
  ese resultado por separado, sin usarlo como puerta de publicación.

## Construcción y verificación

- D1, D7 y C8 ya están implementados: secuenciación de piezas compartidas, subtareas con avance guardado y
  diferencias confirmadas de permisos con aceptación humana acotada. Resultados y comprobaciones en el plan de esta
  fase y en `docs/evaluaciones.md`. El acceso efectivo sigue requiriendo QA con usuarios de cada rol.
- Prueba diferencial de una refactorización (E3): no se encontró un cambio Appian real con antes/después y criterios
  en la aplicación elegida. Los cambios del portal o de herramientas no lo sustituyen. Concretar un caso antes de
  ejecutarlo; cualquier ejecución de reglas o procesos se delimitará por separado.
- «No evaluable» reconoce el límite de la rejilla con filtros de usuario (`flow!userFilterSetData`). Añadir otro límite
  a `devmcp_policy.json` solo si aparece y se comprueba.

## Ingeniería inversa y diagramas

- Ejecutar `deriva` de punta a punta y medir LEEME con la aplicación real elegida (extracción incompleta y detenida).
  El historial existe en el Dev MCP real; el LEEME anterior llegó al 96 % con 42 objetos y los demás documentos
  quedaron al 20–54 %. No se cambia el presupuesto antes de medirlo (E6).
- `getAgent` sigue devolviendo 401 por la API nativa, aunque Raúl ve el agente en Designer y `getApplication`
  funciona por el servlet. Raúl lo ha reportado a Appian y ha decidido aparcarlo. La medición de esta fase excluye
  esa llamada; el extractor detiene la cola ante errores de acceso/login y conserva la evidencia parcial. No
  reanudar en bucle una extracción que pide login.
- Volver a medir la evaluación de malas prácticas con propuestas reales; sus `claves` se fijaron sin esas propuestas.
- La campaña de 1.000 procesos (semilla 11) ya deja cero etiquetas atravesadas. Persisten 126 conexiones falsas
  detectadas, frente a 142 antes de esta fase. La revisión confirmó 38 intersecciones de etiquetas y 88 tramos
  coincidentes en 71 procesos; los casos 43 y 677 contienen defectos reales, y el 46 un posible sobreconteo corto.
  Un cambio de rutas y posición de etiquetas debe compararse caso a caso con la campaña guardada.
- F6 y `devmcp-setup.md` ya documentan `--skip "^testInterface$"` con datos reales; la política permite esa prueba
  en desarrollo con datos ficticios. La exclusión no borra respuestas de pantalla guardadas en otra lectura.
- Revisar las URL fijas `/help/26.6/` de `data-fabric.md`, `devmcp-setup.md` y `agents/data-modeler.md` cuando cambie
  la versión del Appian MCP Server.

## Comprobaciones pendientes de los cambios terminados

- Contraste sobre imagen medido: cuatro textos visibles cumplen el umbral; ocho apariciones detrás de diálogos están
  ocultas y no cuentan como contenido visible. El auditor automático aún no mide ese fondo compuesto.
- Medir en CI la batería completa con la concurrencia limitada y los tiempos por grupo (E7). La pareja QA y
  refactorización pasa en serie y en paralelo; esa mejora local no acredita aún el tiempo del conjunto.

## Pasos de Raúl

- La antigua skill suelta `~/Proyectos IA/appian-reverse-engineering` quedó descartada: Raúl confirmó que ya no existe
  ni se usa. No hace falta archivarla ni avisar por ella.
- Avisar a Appian de que `LCP_TOOL_MODE=readonly`, descrito en su documentación, no está en Dev MCP 26.6.110
  (`docs/evaluaciones.md`, «Fase 2 · T5»).
- Las seis tablas `cpr_*` de P6 dejan de figurar como borrado pendiente: Raúl indica que probablemente ya las borró y
  no encuentra ninguna con ese nombre en su consola. No se ha comprobado el catálogo desde esta sesión ni se hará
  un borrado adicional sin identificar de nuevo una tabla concreta.
- Repetir P8 con Codex desde un terminal normal: el intento anterior dentro de otra sesión no fue concluyente porque
  no arrancó su sandbox. La ruta local del plugin ya tiene solución; falta repetir la prueba de comportamiento.
- Conciliar el índice del cerebro corporativo: marca 1.692 reuniones transcritas y se encontraron 1.095 en disco.
  Copilot lleva esta tarea; comprobar su resultado antes de darla por cerrada, sin editar el índice a la vez.
