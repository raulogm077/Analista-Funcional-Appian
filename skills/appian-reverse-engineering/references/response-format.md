# Formato de la respuesta final al usuario

Plantilla de la respuesta que devuelve la skill **al terminar** todas las fases. Rellena cada bloque con datos reales del análisis. **No añadas párrafos genéricos antes o después**: el usuario quiere una salida operativa y escaneable.

---

## Plantilla

```markdown
# Reingeniería inversa de <Aplicación> completada

**Carpeta:** `<salida>/` · **Entorno:** `<url>` (lectura en vivo, sin cambios en Appian)

## Estado de los MCP
- Dev MCP: ok (<N> herramientas usadas, <N> excluidas por seguridad)
- Appian MCP Server: ok / no disponible (sin volúmenes de datos)
- Docs MCP: ok (<N> consultas) / no disponible (recomendaciones sin verificar para la versión)

## Documentos
- Empieza por `LEEME.md` (guía de lectura por perfil).
- A. Cómo está hecha: `00`–`11`, `INVENTARIO.md`
- B. Reconstruir y modernizar: `12-especificacion-reconstruccion.md`, `13-modernizacion-refactor.md`
- Diagramas: <N> Mermaid (<N> en SVG) · <N> BPMN

## La aplicación en cifras
- Objetos: <N> (Records <N> · Process models <N> · Interfaces <N> · Reglas <N> · Integraciones <N> · Web APIs <N> · Grupos <N> · Constantes <N> · <otros>)
- Casos de uso <N> · Pantallas <N> · Reglas de negocio <N> · Requisitos <N>
- Uso real: <procesos más usados / sin ejecuciones, o «sin historial disponible»>

## Modernización
**Veredicto:** <Mantener y mejorar / Refactorizar por fases / Reconstruir> — <una línea>
- Hallazgos: <N> (alta <N> · media <N> · baja <N>). Principales: <MOD-xxx título>, …

## Riesgos principales
- …

## No disponible en esta ejecución
- <tipos sin definición, seguridad por objeto, valores por entorno, MCP opcionales ausentes…>

## Pendientes de validación
- … (detalle en `12`, sección «Preguntas abiertas»)

## Salidas adicionales
- 📄 PDF: `<salida>/EXPORT.pdf` (si se pidió)
- 🖥️ Dashboard: `<salida>/dashboard/index.html` (si se pidió)

> `<trabajo>/` contiene datos en bruto de la aplicación: no la compartas.
```

---

## Reglas

- **Sin saludos** ni explicación de lo que se hizo: los documentos ya lo explican.
- **Cifras concretas**, no aproximaciones.
- Si un documento no aplica (p. ej. `07` sin batches), dilo en la lista.
- Nunca incluyas secretos ni nombres de usuario.

---

## Criterios de aceptación

Sobre una aplicación real, la skill es correcta cuando:

- Documenta el 100 % de los objetos de la aplicación que lista el Dev MCP, y dice cuáles no tienen definición y por qué.
- Genera los 16 entregables, y todos los diagramas se renderizan o quedan como pendientes.
- Cada integración queda con endpoint (enmascarado), método, autenticación y callers.
- Cada Web API queda con URL, método, qué dispara y grupos autorizados (o 🟡 si la seguridad no está disponible).
- Cada process model tiene su BPMN y su uso real (o «sin historial»).
- Cada pantalla y cada regla de negocio tiene identificador, evidencia y aparece en la trazabilidad de `12`.
- Cada hallazgo de `13` tiene evidencia y fuente oficial (o está marcado como heurística).
- No hay secciones vacías, placeholders, secretos ni nombres de usuario.
