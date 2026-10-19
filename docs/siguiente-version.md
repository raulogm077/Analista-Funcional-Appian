# Para la siguiente versión

Trabajo que queda abierto después de aplicar las lecciones de automejora del 19 de octubre de 2026, sobre la
0.8.0-beta.1. Los cambios aplicados y sus pruebas están en `docs/evaluaciones.md`; el alcance y el relevo, en
`docs/plan/2026-10-19-aplicar-automejora.md`. Esta lista no autoriza publicar ni actuar en un entorno.

## Antes de subir y publicar

- Probar el comportamiento de las skills modificadas con `claude --plugin-dir <carpeta>` en un proyecto fuera del
  repositorio. Los selftests y las regresiones sobre copias de P10 no sustituyen esa prueba.
- Cuando Raúl autorice subir: PR y batería completa en Linux. Antes de publicar una versión, las siete combinaciones
  de sistema/Python y la comprobación de anclas, como indica `CLAUDE.md`. La versión sigue sin cambiar.
- Instalar el paquete en la app de escritorio y en un Windows con algún requisito sin instalar; comprobar que el primer
  mensaje lo explica. En Linux con Claude Code ya se vio; el hook de Windows dejó su marca con 0.7.0-beta.1, pero falta
  ver el mensaje con un requisito ausente.

## Construcción y verificación: esperar a un caso real

- Dos unidades sobre la misma pieza sin construir: por ahora el cambio va en la misma unidad. Tomar el texto de la
  versión con que se aprobó cada unidad solo si vuelve a ocurrir la mezcla observada en P10 (D1).
- Borrador de técnico §13 por script: medir primero si ayuda con el volumen de P10; no añadir generación automática
  sin esa medida (E1).
- Dependencias de issues dadas de más: permitir corregirlas a mano solo cuando dificulten una construcción real (E2).
- Las issues agrupadas ya tienen un título representativo y una lista paralela resumida. Partir un process model por
  actividad sigue pendiente de que el tamaño moleste al construir (D7).
- Prueba diferencial de una refactorización: plantearla cuando haya una refactorización real, con diferencias
  aceptadas y motivo. No crear ahora un segundo recorrido de QA (E3).
- Comprobar en `verificar` quién ve una acción de registro y quién inicia un proceso: aparcado. El QA sigue siendo la
  comprobación prevista para estos permisos (C8).
- «No evaluable» reconoce el límite de la rejilla con filtros de usuario (`flow!userFilterSetData`). Añadir otro límite
  a `devmcp_policy.json` solo si aparece y se comprueba.

## Ingeniería inversa y diagramas

- Ejecutar `deriva` de punta a punta con una aplicación real. El historial sí existe en el Dev MCP real, comprobado
  con `listObjectVersions` en P4 y P5.
- Medir LEEME con una aplicación grande antes de cambiar su presupuesto: llegó al 96 % con 42 objetos; los demás
  documentos quedaron al 20–54 % (E6).
- Volver a medir la evaluación de malas prácticas con propuestas reales; sus `claves` se fijaron sin esas propuestas.
- Ancho de la arquitectura en `mermaid-rules.md`: aparcado hasta acordar un criterio visual. «Cinco cajas por capa» no
  garantiza el ancho y partirla exige decidir cómo encaja con `arquitectura-<capa>.mmd` (E5).
- En 1.000 procesos al azar (semilla 11), quedan ocho con una etiqueta cruzada por otro flujo, frente a 46 antes. Son
  puertas con varias salidas y sin espacio libre para un codo; no cambiar la colocación sin volver a medirlas.
- La política permite `testInterface` en desarrollo con datos ficticios. Si se lee un entorno con datos reales,
  documentar `--skip "^testInterface$"` en F6 y `devmcp-setup.md` antes de esa lectura.
- Revisar las URL fijas `/help/26.6/` de `data-fabric.md`, `devmcp-setup.md` y `agents/data-modeler.md` cuando cambie
  la versión del Appian MCP Server.

## Prototipos y batería

- Abrir una pantalla del prototipo en otra pestaña mediante `#ver=<pantalla>&<parámetro>=<valor>`: aparcado. El ajuste
  del chat al alto disponible sí se aplica en este trabajo (D11).
- Medir la duración de cada grupo de `comprobar_plugin.py --completo` antes de paralelizarlo. La batería tardaba
  17 minutos en Windows y 8,5 en Linux; no es urgente (E7).

## Pasos de Raúl

- Archivar la skill suelta `~/Proyectos IA/appian-reverse-engineering` en el equipo donde esté y avisar a quien la tenga;
  no estaba en su cuenta de claude.ai ni en el portátil de trabajo.
- Avisar a Appian de que `LCP_TOOL_MODE=readonly`, descrito en su documentación, no está en Dev MCP 26.6.110
  (`docs/evaluaciones.md`, «Fase 2 · T5»).
- Borrar, con autorización y desde la base de datos, las seis tablas vacías `cpr_*` de P6 en Indra-spain. El Dev MCP no
  borra tablas; la aplicación y sus objetos ya se borraron. Este trabajo no toca esas tablas.
- Repetir P8 con Codex desde un terminal normal: el intento anterior dentro de otra sesión no fue concluyente porque
  no arrancó su sandbox. La ruta local del plugin ya tiene solución; falta repetir la prueba de comportamiento.
- Conciliar el índice del cerebro corporativo: marca 1.692 reuniones transcritas y se encontraron 1.095 en disco.
