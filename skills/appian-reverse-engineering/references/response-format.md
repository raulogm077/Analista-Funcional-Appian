# Formato de la respuesta final al usuario

Plantilla de la respuesta que devuelve la skill **al terminar** todas las fases (fase 8). Todas las cifras salen de `<trabajo>/summary.json` y de los documentos ya escritos. **No añadas párrafos genéricos antes o después**: el usuario quiere una salida operativa y escaneable.

---

## Plantilla

```markdown
# Reingeniería inversa de <Aplicación> completada

**Carpeta:** `<salida>/` · **Entorno:** `<url>` (<producción / no productivo / no consta>; lectura en vivo, sin cambios en Appian)

## Estado de los MCP
- Dev MCP: ok (<N> herramientas usadas, <N> excluidas por seguridad)
- Appian MCP Server: ok / no disponible (sin volúmenes de datos)
- Docs MCP: ok (<N> de 30 consultas) / no disponible (sin explicación oficial de nodos o funciones desconocidos)

## Documentos
- Empieza por `LEEME.md` (rutas de lectura por perfil).
- `00`–`11`, `INVENTARIO.md` y `anexo/` (definición original de <N> objetos)
- Diagramas: <N> Mermaid (<N> en SVG) · <N> BPMN
- <Documentos que no aplican, p. ej. «07: la aplicación no tiene procesos programados»>

## La aplicación en cifras
- Objetos: <N> (Record types <N> · Process models <N> · Interfaces <N> · Reglas <N> · Integraciones <N> · Web APIs <N> · Grupos <N> · Constantes <N> · <otros>)
- Casos de uso <N> · Pantallas <N> · Reglas de negocio <N>
- Confianza de la documentación: <Alto/Medio/Bajo> (<meta.confidenceBasis>)
- Uso real: <procesos más usados y sin ejecuciones, o «sin historial disponible»>. <Si el entorno no consta como producción: «cifras orientativas»>

## Hallazgos
- Registro (`09`): <N> (Alta <N> · Media <N> · Baja <N>); verificados <N>, inferidos <N>, pendientes <N>
- Principales (Alta): <H-SEG-01 título>, <H-PRO-02 título>, …
- Secretos: <N objetos con secretos escritos, registrados en H-SEG-NN / «ninguno detectado»>

## No disponible en esta ejecución
- <tipos sin definición, seguridad por objeto, valores por entorno, MCP opcionales ausentes…>

## Pendientes de validación
- <hallazgos con certeza ❓, por su ID y título> (detalle en el registro de `09`)

## Salidas adicionales
- 📄 PDF: `<salida>/EXPORT.pdf` (si se pidió)
- 🖥️ Dashboard: `<salida>/dashboard/index.html` (si se pidió)

> La extracción va con el proyecto, en `<salida>/extraccion/`, tal cual la devolvió el Dev MCP. Es la fuente de la documentación, no parte de ella.
```

---

## Reglas

- **Sin saludos** ni explicación de lo que se hizo: los documentos ya lo explican.
- **Cifras concretas**, las de `summary.json`; ninguna recalculada a mano.
- Los hallazgos se citan por su ID con su título; la severidad va en el recuento, no repetida en cada línea.
- Si un documento no aplica (p. ej. `07` sin procesos programados), dilo en la lista.

---

## Criterios de aceptación

Sobre una aplicación real, la skill es correcta cuando:

- Documenta el 100 % de los objetos que lista el Dev MCP (`INVENTARIO.md`) y dice cuáles no tienen definición y por qué.
- Genera `LEEME`, `00`–`11`, `INVENTARIO` y el `anexo/`; todos los diagramas se renderizan o quedan sustituidos por una tabla.
- Cada integración queda con endpoint, método, autenticación y quién la llama.
- Cada Web API queda con URL, método, qué dispara y grupos autorizados (❓ si la seguridad no está disponible).
- Cada process model tiene su BPMN y su uso real (o «sin historial»).
- Cada pantalla y cada regla de negocio tiene identificador y evidencia.
- Cada hallazgo tiene ID, está en su documento propietario y en el registro de `09`, y `build_registry.py` termina sin errores.
- No hay secciones vacías, placeholders ni enlaces a `<trabajo>/`.
