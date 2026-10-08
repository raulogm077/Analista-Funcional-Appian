# Evaluación del recién llegado

Mide si alguien que llega nuevo al equipo encuentra en `as-is/` lo que necesita para mantener una aplicación, con su
evidencia, y si la documentación es más corta. La aplicación es la ficticia MNT (`MOCK_APP=fixture_mal_hecha`, Tarea
7) y las preguntas, las de `../aplicacion-ficticia/preguntas.json` y las 7 de `ocultas/`. Los resultados van a
`docs/evaluaciones.md`; los proyectos de prueba, a `$PROYECTOS_PRUEBA`, fuera del repositorio.

## Cómo se hace

1. **El proyecto.** `$PROYECTOS_PRUEBA/MNT-antes/` o `$PROYECTOS_PRUEBA/MNT/` con un `.mcp.json` de dos servidores:
   - `appian`: `python3 <repo>/pruebas/appian-reverse-engineering/mock_devmcp/lcp_mcp_server_mock.py --module
     lcp_mcp_server`, con `LCP_URL=https://pre.mnt.example.org`, `LCP_TOOL_MODE=readonly`,
     `MOCK_APP=fixture_mal_hecha` y `MOCK_VARIANT=a`;
   - `appian-mcp`: `{"type": "http", "url": "http://127.0.0.1:<puerto>/mcp"}`, con el servidor arrancado así:
     `MOCK_APP=fixture_mal_hecha python3 appian_mcp_server_mock.py <puerto>`. No está en `<LCP_URL>/mcp`, así que
     `doctor` y `datafabric` lo reciben con `--mcp-server-name appian-mcp`.
2. **La documentación.** Un agente sigue el `SKILL.md` de ingeniería inversa de la versión que se mide (para «antes», la
   del commit `f3-antes`) contra el simulador, con salida en `<proyecto>/as-is/`. Sin PDF ni dashboard.
3. **Las respuestas.** Otro agente, que solo ve una copia de `as-is/` sin `extraccion/`, recibe las preguntas sin las
   respuestas (`id`, `pregunta` y `tipo`) y escribe `respuestas.json`:
   `[{"id": "Q-01", "respuesta": "…", "evidencia": "ruta#ancla"}]`. La evidencia es el documento de `as-is/` donde lo
   leyó; en una de tipo `lista`, `respuesta` es una lista.
4. **La puntuación**:

   ```bash
   python3 puntuar.py respuestas.json <proyecto>/as-is --minimo 20 --obligatorias Q-21
   python3 puntuar.py respuestas-ocultas.json <proyecto>/as-is --ocultas --minimo 6
   python3 evidencia.py <proyecto>/as-is
   python3 <repo>/skills/appian-reverse-engineering/scripts/comprobar_asis.py <proyecto>/as-is
   python3 palabras.py <proyecto>/as-is
   ```

Criterio de la Tarea 9 («después»): las dos puntuaciones salen 0, `evidencia.py` sale 0, `comprobar_asis.py` da 0
errores y hay menos palabras que «antes».
