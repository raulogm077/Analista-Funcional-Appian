# Flujo de análisis: checklists por fase

Detalle operativo de las fases de `SKILL.md`. Marca cada casilla en la lista de tareas.

**Convenciones**

- Evidencia: `mcp:<tipo>/<nombre>#<ubicación>` (ver `lectura-mcp-raw.md`).
- Carpeta de salida: `<salida>` = `./appian-docs/<PREFIJO>/` salvo que el usuario indique otra.
- Scripts: `uv run --with "mcp>=1.2,<2" python <skill>/scripts/devmcp_extract.py …`, lanzado desde la carpeta de trabajo del usuario.

---

## Fase 0 — Preflight

- [ ] `doctor --json` ejecutado.
- [ ] Docs MCP comprobado en la sesión, con una consulta de prueba si existe.
- [ ] Appian MCP Server: estado según `doctor` o según la sesión.
- [ ] Tabla de estado mostrada al usuario (estado · qué se pierde · cómo activarlo).
- [ ] Si el Dev MCP no está `ok`: mostrado el paso de `devmcp-setup.md` y **parada**.
- [ ] Aplicación confirmada.
- [ ] Formatos adicionales preguntados; `output_preferences.json` guardado.
- [ ] `preflight.json` guardado.

**Qué pierde el usuario sin cada MCP opcional**

| Falta | Consecuencia |
|---|---|
| Appian MCP Server | Sin volúmenes de datos: 03 no tiene filas por entidad y los requisitos de volumen de 12 pasan a preguntas abiertas. |
| Docs MCP | Las recomendaciones de 13 se basan en las URLs de `modernization-guide.md` (26.6) y se marcan «sin verificar para la versión»; sin explicaciones oficiales de nodos o funciones desconocidos. |

## Fase 1 — Plan

- [ ] `plan --app <app> --out <salida>` sin errores.
- [ ] Resumen mostrado al usuario: objetos por tipo, herramientas usadas y excluidas, llamadas estimadas.
- [ ] Si `trustedMode` es `false`: avisado de que el servidor no respeta `readonly` y de que se usan solo herramientas de lectura evidentes.
- [ ] Si `needsConfirmation`: confirmación del usuario.
- [ ] Si hay herramientas `manual` o excluidas que parecen útiles y seguras, anotado para el usuario: puede ajustar `devmcp_policy.json`.

## Fase 2 — Extracción

- [ ] `extract` terminado. Si se corta, repetir: reanuda desde lo descargado.
- [ ] `extraction_report.json` revisado: `errorCount`, `disabledAfterProbe`, `toolsExcluded`.
- [ ] Si fallan más del 20 % de las definiciones: avisado al usuario.
- [ ] Data fabric: `datafabric.json` generado (script o sesión) o anotado como no disponible.

**Errores típicos**

| Síntoma | Causa probable | Qué hacer |
|---|---|---|
| Código 13 al arrancar | Sesión SSO caducada o bundle mal instalado | Repetir: se abre el navegador. Si persiste, `devmcp-setup.md`. |
| Código 15 | Aplicación no encontrada o ambigua | Usar el uuid o el prefijo exacto de `doctor`. |
| Muchas llamadas de un tipo desactivadas | La herramienta no admite ese tipo | Normal. Aparece en el informe y en `INVENTARIO`. |
| Timeouts | Entorno lento | `--concurrency 2` y repetir (reanuda). |

## Fase 3 — Modelo

- [ ] `build_model.py` sin errores; revisar la línea de resumen (objetos, aristas por origen, huérfanos).
- [ ] `detect_secrets.sh` sobre `mcp_raw`: anotar qué tipos de secreto hay, sin copiar valores.
- [ ] Si `graph.json` tiene pocas aristas `dependents`: la herramienta de dependencias no estaba o falló → las conclusiones de callers llevan 🔵.

## Fase 4 — Análisis

- [ ] 4.1 `interface-analyzer` → 01, 02.
- [ ] 4.2 en paralelo: `data-modeler` (03), `integration-security-analyzer` (04–06), `process-modeler` (08), `ui-rules-analyzer` (10–11).
- [ ] 4.3 orquestador → 07 y 09 (plantillas; datos de `inventory.json`, `graph.json` y los documentos anteriores).
- [ ] 4.4 `rebuild-architect` → 12, 13.
- [ ] Consultas al Docs MCP contadas (`<trabajo>/docs_cache/*.json`) ≤ 30.

**07-batches (orquestador):** process models con `startType: timer`. Por cada uno: frecuencia legible desde `schedule`, cron equivalente si es traducible, uso real (`usage`), qué hace (del `.md` de 08) y qué toca. Sin batches: la frase exacta de la plantilla.

**09-valor-adicional (orquestador):** solo secciones con hallazgos reales:

- constantes por entorno y secretos (enmascarados);
- expression rules reutilizables (hubs);
- huérfanos: grafo, más ejecuciones 0 si hay historial;
- avisos de validación de la plataforma;
- versionado (último cambio por objeto si hay herramienta de versiones);
- métricas (tamaño de SAIL, nodos);
- riesgos;
- glosario.

## Fase 5 — Diagramas

- [ ] Todos los `.mmd` validados con `validate_mermaid.py`.
- [ ] `render_diagrams.sh --check` y luego `--batch <salida>` si hay `mmdc`; si no, los bloques quedan embebidos.
- [ ] Diagramas que fallan 3 veces sustituidos por tabla.

## Fase 6 — Resumen, inventario y guía

- [ ] `00-resumen-ejecutivo.md`: volumen, procesos e integraciones críticos, riesgos, uso real, veredicto de 13, pendientes.
- [ ] `INVENTARIO.md`: una sección por tipo presente, cobertura de la extracción y objetos sin definición.
- [ ] `LEEME.md`: guía por perfil, qué no estuvo disponible y glosario.

## Fase 6.5 — summary.json

- [ ] `build_summary.py <salida>` sin errores.

## Fase 7 — Publicación opcional

- [ ] PDF y/o dashboard según `output_preferences.json`.

## Fase 8 — Validación y respuesta

- [ ] Validación final de `SKILL.md` superada.
- [ ] Respuesta con la plantilla de `response-format.md`.
