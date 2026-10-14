# F6 · Ingeniería inversa

**Cuándo.** Hay que entender una aplicación Appian que ya existe, para documentarla o antes de evolucionarla o de rehacerla.
**Empieza.** Ingeniería inversa, con `appian-reverse-engineering`; todo es lectura. **Termina en.** `as-is/`, con cada dato con su evidencia y lo que no se pudo verificar. Sigue por F3 (evolucionar una parte) o por F7 (rehacerla).

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Comprobar la conexión con el entorno y preguntar qué aplicación es y qué necesita saber el equipo | Script comprueba; IA pregunta; quien lo pide responde | `appian-reverse-engineering` · `devmcp_extract.py doctor` | `appian-reverse-engineering/SKILL.md` «Flujo de trabajo», fase 0, y `appian-reverse-engineering/references/devmcp-setup.md` |
| 2 | Plan de extracción y extracción | Script | `appian-reverse-engineering` · `devmcp_extract.py plan` y `extract` | `appian-reverse-engineering/SKILL.md` «Flujo de trabajo», fases 1 y 2 |
| 3 | Modelo, anexo de definiciones y posibles secretos | Script | `appian-reverse-engineering` · `build_model.py`, `build_annex.py` y `detect_secrets.py` | La misma, fase 3 |
| 4 | Analizar por áreas (funcional, arquitectura, datos, seguridad, integraciones, procesos, pantallas y reglas) y dibujar cada proceso | IA | `appian-reverse-engineering`; `appian-diagramas-bpmn` · `diagrama.py` | La misma, fase 4 |
| 5 | Pintar los demás diagramas y comprobar los de cada documento | Script | `appian-diagramas-bpmn` · `mermaid.py` | La misma, fase 5 |
| 6 | Coherencia entre documentos, inventario, `LEEME.md` y `as-is/datos/` | IA; Script | `appian-reverse-engineering` · `build_summary.py` y `build_datos.py` | La misma, fase 6 |
| 7 | Validar la documentación | Script | `appian-reverse-engineering` · `comprobar_asis.py` | La misma, fase 8 |
| 8 | Leer `as-is/LEEME.md`, decidir cómo se sigue (F3 o F7) y subir `as-is/`. Si hay hallazgos de seguridad con valores, esos secretos están en claro en `as-is/`: el equipo decide antes de subirla | El equipo | — | `appian-reverse-engineering/references/security-rules.md` «Acción ante un secreto» |
