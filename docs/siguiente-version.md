# Para la siguiente versión

Trabajo que queda abierto después de aplicar las lecciones de automejora del 19 de octubre de 2026, sobre la
0.8.0-beta.1, consolidadas para la entrega 0.8.0-beta.2. Raúl pidió abordar los temas aplazados antes de publicar;
el plan de esa fase está en
`docs/plan/2026-10-19-temas-aplazados.md`. Los cambios terminados y sus pruebas están en `docs/evaluaciones.md`;
la primera tanda quedó cerrada en `docs/plan/2026-10-19-aplicar-automejora.md`. Esta lista no autoriza publicar ni actuar en un entorno.

La rama de trabajo de esta entrega fue `automejora-pruebas`, con la primera tanda de Claude y los cambios posteriores. La
app de escritorio queda como comprobación visual pendiente, sin bloquear por sí sola la publicación. `getAgent`
queda aparcado tras el reporte de Raúl a Appian; no se repetirá en la medición de esta fase.

## Campaña Codex: pasada ejecutada y pendientes

La campaña posterior usa una sola rama, `codex/campana-mejora-20261019`, desde `ba275544`; índice y estado
en `$PROYECTOS_PRUEBA/campana-codex-20261019/`. La pasada queda documentada con fallos y límites abiertos.
La auditoría del recuento retira el objetivo del 20 %: al incluir las ediciones, la mediana del retoque
3+3 baja de 17 a 15 actividades observables (11,76 %), y el tiempo un 14,12 %. El 20 % anterior contaba
solo eventos de comandos. La corrección del resumen de impacto se acepta por calidad funcional;
la ingesta tampoco acredita ahorro. No extrapolar esas cifras a los casos restantes.

La nueva acreditación de principio a fin está en `e2e-20261020/estado.json`, bajo la misma campaña externa.
La base `5034276` ya tiene una corrida completa limpia del analista (401 controles, exit 0).
El proyecto nuevo D1 respeta el orden temporal y otra sesión completa la recuperación técnica D7;
la QA de usuario sigue pendiente. La urgencia compartida ha reproducido un bloqueo del motor:
el parche pasa los casos focales y la suite completa (401 controles, exit 0). Su repetición real sobre
`15b191d` reaplica el cambio y otro contexto completa el reservado D7 con doce casos únicos correctos.
La revisión detecta además que un técnico declarado completo sin DT ni datos omitía sus comprobaciones:
corrección focal y vecinos correctos, suite completa limpia con 401 controles y exit 0. Quedan la corrección del perfil del montaje
sin inventar grupos y las transiciones locales de cierre; QA de usuario y producción no están acreditadas.
Después siguen el flujo documental, QA automatizada por roles, los ocho agentes y la medida 3+3.

- La revisión externa se contrastó contra código y reproducciones. Quedan corregidos la localización del plugin,
  el aviso de localizador inválido, la tabla técnica, el destino pendiente de urgencias y el consumo de derivados
  antiguos. `version --inicial` promueve el borrador sin editar números a mano. Los IDs retirados sí llegan a
  `datos/` y las anotaciones ya se trasladaban; no aplicar esas dos recetas del informe. Evidencia y dictámenes
  en `revision-antigravity-20261020/RESULTADO.md`. La reserva Git D7 pasa en un montaje nuevo creado con
  `iniciar`; los montajes históricos siguen sin medir ese punto.
- D1/D7/C8 y sus tres reservados ya tienen sesiones locales terminadas; no repetir por las interrupciones
  anteriores. Enrutado y retoque 3+3 terminados con Luna. Mantener Astra como orquestador solicitado.
- Urgencia visible/reservada falla por ejecución incompleta. El falso positivo del puntuador de entorno
  pendiente ya está corregido y comparado con ocho casos y el artefacto original. La auditoría posterior
  reproduce y corrige el mismo defecto en el motor. No convierte en correcta la ejecución fallida ni
  justifica añadir instrucciones que ya existen en `urgentes.md`.
- La actualización incremental de tres dominios conserva decisiones y pendientes; son anexos parciales.
  Las síntesis de 1/4/12 fuentes y la variante de orden/duplicado están ejecutadas. La variante pierde una
  contradicción de alcance conservada en los otros lotes: FAIL de reconciliación, con fe de erratas de proyecto.
  Se usó un formato de síntesis ad hoc con la skill cargada; el flujo completo del plugin con catálogo,
  notas, funcional y comprobador sigue NOT MEASURED.
  Citas y hashes correctos no acreditan cobertura semántica exhaustiva. La demo reparada conserva los fallos iniciales; sus figuras actuales y quince
  páginas son legibles, pero el índice PDF sigue sin números. La exportación alternativa de Word no produjo
  PDF y dejó intacto el DOCX. La reparación del diagrama pasa revisión visual acotada y suite completa de su
  capacidad con navegador: 145 comprobaciones, exit 0, conservando geometría manual/importada. No elimina
  todos los avisos de otros casos ni acredita ahorro de tiempo.
- El DF comentado conserva el requisito aprobado frente a comentario y reuniones; falló al importar la
  versión inicial y señalar el punto pendiente. La copia corregida pasa seis invariantes independientes.
  Son fallos de ejecución ante instrucciones existentes: no añadir otra regla por duplicado.
- El laboratorio ficticio ya está autorizado y construido. Diez casos guardados de reglas pasan; la interfaz
  tiene verificación estructural y el retoque técnico consume ocho llamadas. El orden de cierre local falló;
  no corregir retroactivamente la traza ni atribuir a ocho llamadas el coste completo de construcción y QA.
  QA independiente de implementación detectó dos defectos sucesivos; versión 5 y repetición final: 14 PASS/0 FAIL.
  Fue interacción CUA en preview de Designer; `qa.py`, SAIL y los guiones repetibles de `appian-qa`
  siguen NOT MEASURED.
  El cierre completo supera el límite de 25 llamadas (al menos 91 conocidas); el coste técnico focal no lo
  sustituye. Roles sin cuenta y efectos internos comprobados por QA siguen NOT MEASURED. F9 acaba en evidencias
  para revisión humana, sin despliegue ni publicación.
- La frase de renumeración del registro ya está corregida contra casos de IDs conservados/retirados.
  El as-is y diagnóstico acotados están revisados: inventario parcial, definiciones leídas y no leídas
  se distinguen, sin forzar una refactorización global. La autonomía sin red del dashboard opcional
  sigue NOT MEASURED; queda bajo demanda, sin ampliar esta campaña. No incorporar material por revisión estática solamente.

Esta fase es solo Codex; no añade una obligación de Claude. Sigue sin autorizar despliegues, publicaciones,
envíos o borrados. La batería completa se reserva a CI cuando se autorice el PR.

## Antes de subir y publicar

- La prueba de comportamiento con `claude --plugin-dir` sigue **NOT MEASURED**. Raúl decidió el 19/10 omitirla
  para esta entrega y continuar con la integración; deja de ser una puerta de publicación. La campaña D1/D7/C8
  queda preparada para una comprobación posterior, sin bloquear esta versión. Sus diez controles offline no
  acreditan la conducta de Claude.
- El [PR #19](https://github.com/raulogm077/Analista-Funcional-Appian/pull/19) pasa la batería Linux, el PDF con
  LibreOffice y `Resultado`; la matriz manual pasa sus siete combinaciones de sistema/Python y `Resultado`.
  Ambos resultados corresponden a `62ec54b39b354dad5a5393f005e4456b87515ebe`. Las anclas ya pasaron: 1.265 citas
  en 312 páginas, cero rotas. El benchmark 1, 2, 2, 1 también termina correctamente: medias de 680,5 s en serie
  y 448 s con dos grupos (34,2 % menos), sobre un runner y dos muestras por configuración. Raúl autorizó integrar
  y publicar la 0.8.0-beta.2 con estos resultados; el estado de entrega se consulta en el PR y en
  [Releases](https://github.com/raulogm077/Analista-Funcional-Appian/releases). El PDF real de CI conserva los 725 párrafos,
  51 títulos y dos figuras del fixture conocido, con 13 páginas; su índice queda sin números de página y requiere
  revisión antes de entregar.
- El hook real de requisitos pasa en las tres combinaciones Windows de la matriz, con `docx` realmente ausente,
  sin simulación: aviso en PowerShell 5.1, marca por versión y segunda ejecución silenciosa. Esto no acredita una
  instalación visual en la app de escritorio, que sigue pendiente y sin bloquear por sí sola la publicación.

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
- La medición de rendimiento de batería completa (E7) pasa en
  [Actions](https://github.com/raulogm077/Analista-Funcional-Appian/actions/runs/39290798292), mismo SHA:
  orden 1, 2, 2, 1, tiempos 684/441/455/677 s y cuatro códigos 0. Medias: 680,5 s en serie y 448 s con dos grupos,
  reducción del 34,2 %. Las cuatro pasadas ejecutan los mismos 13 grupos y terminan sin errores ni avisos.
  Son dos muestras por configuración en un runner Ubuntu/Python 3.12; no se extrapolan a otros equipos.

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
