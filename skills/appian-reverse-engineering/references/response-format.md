# Formato de la respuesta final al usuario

Plantilla de la respuesta que devuelve la skill **al terminar** todas las fases (fase 8). Todas las cifras salen de `<trabajo>/summary.json` y de los documentos ya escritos; lo que no se pudo verificar, de `<salida>/datos/sin-verificar.json`. **No añadas párrafos genéricos antes o después**: el usuario quiere una salida operativa y escaneable.

---

## Plantilla

```markdown
# Ingeniería inversa de <Aplicación> completada

**Carpeta:** `<salida>/` · **Entorno:** `<url>` (<producción / no productivo / no consta>; lectura en vivo, sin cambios en Appian)

## Estado de los MCP
- Dev MCP: ok (<N> herramientas usadas, <N> excluidas por seguridad)
- Appian MCP Server: ok / no disponible (sin volúmenes de datos)
- Docs MCP: ok / no disponible, dudas por la web / sin MCP ni web (lo que depende de la documentación oficial va «sin verificar») · <N> de 30 consultas

## Preguntas de esta revisión
- <cada pregunta de `preguntas`: Respondida, Parcial o Sin resolver; las que quedan abiertas, con su NV o la limitación que lo impide>

## Documentos
- Empieza por `LEEME.md` (preguntas de esta revisión y rutas de lectura por perfil).
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
- <tipos sin definición, seguridad por objeto, valores por entorno, MCP opcionales ausentes…: lo de «Qué no incluye» de LEEME>

## Sin verificar
- <cada NV abierto o parcial: su ID, la pregunta y qué hace falta> (tabla en `LEEME.md`, «Sin verificar»)

## Salidas adicionales
- 📄 PDF: `<salida>/EXPORT.pdf` (si se pidió)
- 🖥️ Dashboard: `<salida>/dashboard/index.html` (si se pidió)

> La extracción va con el proyecto, en `<salida>/extraccion/`, tal cual la devolvió el Dev MCP. Es la fuente de la documentación, no parte de ella.
```

---

## Reglas

- **Sin saludos** ni explicación de lo que se hizo: los documentos ya lo explican.
- **Cifras concretas**, las de `summary.json`; ninguna recalculada a mano.
- Los hallazgos se citan por su ID con su título; la severidad va en el recuento, no repetida en cada línea. Un hallazgo ❓ se explica en su documento propietario; lo que falta para resolverlo, en su NV.
- Si un documento no aplica (p. ej. `07` sin procesos programados), dilo en la lista.
- Sin NV abiertos ni parciales, la sección «Sin verificar» es una línea: «Ninguna pregunta quedó sin verificar.»

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
- Lo que no se pudo verificar está en «Sin verificar» de `LEEME` con dónde se buscó, qué hace falta y a quién pedirlo, y cada pregunta de la revisión está cerrada en «Preguntas de esta revisión».
- No hay secciones vacías, placeholders ni enlaces a `<trabajo>/`.
