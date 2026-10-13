# F9 · Pase a producción

**Cuándo.** Una unidad está «Construida» y toca llevarla a pruebas o a producción.
**Empieza.** Una persona: desde el paquete no actúa la IA. **Termina en.** El paquete desplegado por el método del cliente y el pase registrado en el proyecto.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Preparar el paquete con los objetos de la unidad y su configuración por entorno | Quien prepara el paquete | Appian Designer | `appian-best-practices/references/08-alm-testing-naming.md` §3 |
| 2 | Revisar lo que lleva el paquete antes de desplegarlo <!-- (T18) Qué se revisa: la comparación de los objetos en Compare and Deploy, como en un Merge Request, los fallos de la regresión (casos de prueba y guiones de QA) y las pruebas marcadas como no necesarias. --> | Quien prepara el paquete | Appian Designer | `appian-best-practices/references/10-quality-gates.md` §7 y `appian-best-practices/references/11-reliability-operations.md` «Operational Readiness Gate» |
| 3 | Desplegar por el método del cliente: el mismo paquete en cada entorno | Una persona | — | `appian-best-practices/references/08-alm-testing-naming.md` §3 |
| 4 | Registrar el pase, con su referencia en el cliente | Script | `appian-functional-analyst` · `proyecto.py cambio <p> <U> produccion --ref "<referencia>" --fecha <AAAA-MM-DD>` | `appian-functional-analyst/references/cambios.md` §1 |
| 5 | Poner al día el entorno de corrección con el pase | Una persona | — | `appian-functional-analyst/references/urgentes.md` §3 |
