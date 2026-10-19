# F9 · Pase a producción

**Cuándo.** Una unidad está «Construida» y toca llevarla a pruebas o a producción.
**Empieza.** Una persona: desde el paquete no actúa la IA. **Termina en.** El paquete desplegado por el método del cliente y el pase registrado en el proyecto.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Pasar la regresión en desarrollo: todos los casos de prueba de la aplicación, con la orden que da `indice.py issues <p> <U> --regresion`; por la salida, solo lo que falla | Script | `appian-reverse-engineering` · `devmcp_extract.py regresion` (sin Dev MCP que ejecute casos, en Appian: las reglas con Manage Test Cases y las interfaces desde cada una) | `appian-reverse-engineering/SKILL.md` «Verificar o deriva» y `appian-functional-analyst/references/cambios.md` §6 |
| 2 | Repetir sin IA los guiones de QA de todas las unidades, en desarrollo: un fallo es una pantalla que dejó de hacer lo acordado, y va a la revisión del paso 4 | Script, lanzado por quien prepara el paquete | `appian-qa` · `qa.py repetir <p>` | `appian-qa/SKILL.md` «Repetir» |
| 3 | Preparar el paquete con los objetos de la unidad y su configuración por entorno | Quien prepara el paquete | Appian Designer | `appian-best-practices/references/08-alm-testing-naming.md` §3 |
| 4 | Revisar lo que lleva el paquete antes de desplegarlo: la comparación de sus objetos, como en un Merge Request, con lo que falla en los pasos 1 y 2 (`construccion/<U>/regresion.json` y `qa/<U>/resultado.json`), las pruebas marcadas como no necesarias y los cierres manuales con su motivo (`construccion/<U>/indice.md`) | Quien prepara el paquete | Appian Designer · Compare and Deploy | `appian-functional-analyst/references/cambios.md` §6, `appian-best-practices/references/10-quality-gates.md` §7 y `appian-best-practices/references/11-reliability-operations.md` «Operational Readiness Gate» |
| 5 | Desplegar por el método del cliente: el mismo paquete en cada entorno, con un ICF por entorno y, si el despliegue es directo o por API, con «Require review» activado en el destino | Una persona | — | `appian-functional-analyst/references/cambios.md` §6 y `appian-best-practices/references/08-alm-testing-naming.md` §3 |
| 6 | Registrar el pase, con su referencia en el cliente | Script | `appian-functional-analyst` · `proyecto.py cambio <p> <U> produccion --ref "<referencia>" --fecha <AAAA-MM-DD>` | `appian-functional-analyst/references/cambios.md` §1 |
| 7 | Poner al día el entorno de corrección con el pase | Una persona | — | `appian-functional-analyst/references/urgentes.md` §3 |
