# Para la siguiente versión

Trabajo que queda abierto después de aplicar las lecciones de automejora del 19 de octubre de 2026, sobre la
0.8.0-beta.1; la entrega 0.8.0-beta.2 está preparada y aún no publicada. Raúl pidió abordar los temas aplazados antes
de publicar: la fase activa está en
`docs/plan/2026-10-19-temas-aplazados.md`. Los cambios terminados y sus pruebas están en `docs/evaluaciones.md`;
la primera tanda quedó cerrada en `docs/plan/2026-10-19-aplicar-automejora.md`. Esta lista no autoriza publicar ni actuar en un entorno.

La rama de trabajo única es `automejora-pruebas`: contiene la primera tanda de Claude y los cambios posteriores. La
app de escritorio queda como comprobación visual pendiente, sin bloquear por sí sola la publicación. `getAgent`
queda aparcado tras el reporte de Raúl a Appian; no se repetirá en la medición de esta fase.

## Antes de subir y publicar

- Probar el comportamiento de las skills modificadas con `claude --plugin-dir <carpeta>` en un proyecto fuera del
  repositorio. La campaña D1/D7/C8 está preparada y sus diez controles offline pasan; el runner externo
  `claude-comportamiento/campana_claude.py` permite ejecutarla desde el 20/10 a las 16:00 de Madrid, cuando se
  restablece la cuota acreditada. Los selftests y las regresiones no sustituyen esa conducta aún no medida.
- Raúl autorizó el 19/10 subir la rama, abrir un único PR, ejecutar la matriz e integrar y publicar cuando las pruebas
  pasen. Se ejecutan la batería completa en Linux y las siete combinaciones de sistema/Python de `CLAUDE.md`.
  Las anclas ya pasaron: 1.265 citas en 312 páginas, cero rotas. El job
  nuevo de PDF real con LibreOffice y la medición manual de concurrencia quedan por ejecutar en Actions. La versión
  0.8.0-beta.2 está preparada, pendiente de las pruebas de entrega. LibreOffice ya convirtió el DF ficticio localmente
  y conservó todo su texto y las dos figuras:
  12 páginas frente a las 13 de Word. Falta medir el job de CI; el índice de LibreOffice queda sin números de página
  y el script ya avisa de revisarlo antes de entregar.
- Instalar el paquete en un Windows con algún requisito realmente ausente y comprobar el primer mensaje. La orden
  del hook en PowerShell 5.1, con `docx` simulado como ausente, ya mostró el aviso y dejó la marca de una vez por
  versión; aún falta la instalación real con esa carencia. Comprobar visualmente la instalación en la app de
  escritorio cuando esté disponible; registrar ese resultado por separado, sin usarlo como puerta de publicación.

## Construcción y verificación

- D1, D7 y C8 ya están implementados: secuenciación de piezas compartidas, subtareas con avance guardado y
  diferencias confirmadas de permisos con aceptación humana acotada. Resultados y comprobaciones en el plan de esta
  fase y en `docs/evaluaciones.md`. El acceso efectivo sigue requiriendo QA con usuarios de cada rol.
- Prueba diferencial de una refactorización (E3) realizada con autorización sobre una regla de texto real: versión
  inicial y propuesta coincidieron en 3 casos guardados y cinco bordes; se restauró exactamente la definición
  original y los 3 casos siguieron pasando. `deriva` detectó el historial de edición 1→3. Queda limitada a una regla;
  no acredita sensibilidad global de la aplicación.
- «No evaluable» reconoce el límite de la rejilla con filtros de usuario (`flow!userFilterSetData`). Añadir otro límite
  a `devmcp_policy.json` solo si aparece y se comprueba.

## Ingeniería inversa y diagramas

- LEEME completo y deriva de cambios internos en la aplicación real siguen sin medir: la extracción anterior tiene
  respuestas correctas para 24 de 248 UUID y carece de historiales de versión. Una extracción amplia se estimó en
  al menos unas 1.073 lecturas de objeto, pero **no fue necesaria** para comparar inventarios: con 23 respuestas de
  listas, la aplicación pasó de 248 a 249 objetos (una interfaz nueva, ninguna baja). El `as-is` ficticio de MNT,
  reconstruido y validado, usa 731 de 1.350 palabras de LEEME con 44 objetos; no mide el conjunto real ni se cambia
  el presupuesto por ella (E6).
- `getAgent` sigue devolviendo 401 por la API nativa, aunque Raúl ve el agente en Designer y `getApplication`
  funciona por el servlet. Raúl lo ha reportado a Appian y ha decidido aparcarlo. La medición de esta fase excluye
  esa llamada; el extractor detiene la cola ante errores de acceso/login y conserva la evidencia parcial. No
  reanudar en bucle una extracción que pide login.
- La evaluación ciega de malas prácticas ya cumple el criterio fijado: 10/11 visibles, 3/3 ocultas y cero errores o
  avisos del comprobador tras precisar la comparación de catálogos compartidos. Una auditoría independiente de la
  propuesta anterior encontró ocho problemas o matices adicionales; valorarlos si se usa esa propuesta para un
  trabajo real. Resultado y límites en `docs/evaluaciones.md` y
  `$PROYECTOS_PRUEBA/aplazados-codex-20261019/RESULTADO-MNT-CIEGA.md`.
- El nuevo enrutado conservador reduce las conexiones ambiguas en las campañas de 1.000 procesos: 126→30 avisos
  (semilla 11) y 103→38 (semilla 23), sin regresiones por caso ni aumento de dimensiones. Los casos 43/46/677 quedan
  resueltos, con rutas manuales/importadas protegidas. Persisten 30 y 38 avisos: ampliar el espacio o los candidatos
  para esos casos requiere otra mejora medida, sin suprimir el detector. Resultado y límites en `docs/evaluaciones.md`.
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
- Conciliar el índice del cerebro corporativo: marca 1.692 reuniones transcritas y se encontraron 1.095 en disco.
  Copilot lleva esta tarea; comprobar su resultado antes de darla por cerrada, sin editar el índice a la vez.
