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
- Docs MCP: ok (<N> de 30 consultas) / no disponible (fuentes de 13 sin verificar para la versión)

## Documentos
- Empieza por `LEEME.md` (rutas de lectura por perfil).
- A. Cómo está hecha: `00`–`11`, `INVENTARIO.md` y `anexo/` (definición original de <N> objetos)
- B. Reconstruir y modernizar: `12-especificacion-reconstruccion.md`, `13-modernizacion-refactor.md`, `14-diseno-objetivo.md`
- Diagramas: <N> Mermaid (<N> en SVG) · <N> BPMN
- <Documentos que no aplican, p. ej. «07: la aplicación no tiene procesos programados»>

## La aplicación en cifras
- Objetos: <N> (Record types <N> · Process models <N> · Interfaces <N> · Reglas <N> · Integraciones <N> · Web APIs <N> · Grupos <N> · Constantes <N> · <otros>)
- Casos de uso <N> · Pantallas <N> · Reglas de negocio <N> · Requisitos <N>
- Confianza de la documentación: <Alto/Medio/Bajo> (<meta.confidenceBasis>)
- Uso real: <procesos más usados y sin ejecuciones, o «sin historial disponible»>. <Si el entorno no consta como producción: «cifras orientativas»>

## Hallazgos
- Registro (`09`): <N> (Alta <N> · Media <N> · Baja <N>); verificados <N>, inferidos <N>, pendientes <N>
- Principales (Alta): <H-SEG-01 título>, <H-PRO-02 título>, …
- Secretos: <N objetos con valores enmascarados, tratados en H-SEG-NN / «ninguno detectado»>

## Modernización
**Veredicto:** <Mantener y mejorar / Refactorizar por fases / Reconstruir> — <estrategia en una línea>

## No disponible en esta ejecución
- <tipos sin definición, seguridad por objeto, valores por entorno, MCP opcionales ausentes…>

## Pendientes de validación
- … (detalle en `12`, sección «Preguntas abiertas»)

## Salidas adicionales
- 📄 PDF: `<salida>/EXPORT.pdf` (si se pidió)
- 🖥️ Dashboard: `<salida>/dashboard/index.html` (si se pidió)

> `appian-docs/_trabajo/<PREFIJO>/` tiene los datos en bruto de la extracción (usuarios, hosts, definiciones completas): no la compartas; no forma parte de la documentación.
```

---

## Reglas

- **Sin saludos** ni explicación de lo que se hizo: los documentos ya lo explican.
- **Cifras concretas**, las de `summary.json`; ninguna recalculada a mano.
- Los hallazgos se citan por su ID con su título; la severidad va en el recuento, no repetida en cada línea.
- Si un documento no aplica (p. ej. `07` sin procesos programados), dilo en la lista.
- Nunca incluyas secretos ni nombres de usuario.

---

## Criterios de aceptación

Sobre una aplicación real, la skill es correcta cuando:

- Documenta el 100 % de los objetos que lista el Dev MCP (`INVENTARIO.md`) y dice cuáles no tienen definición y por qué.
- Genera los 17 documentos (`LEEME`, `00`–`14`, `INVENTARIO`) y el `anexo/`; todos los diagramas se renderizan o quedan sustituidos por una tabla.
- Cada integración queda con endpoint (sin credenciales), método, autenticación y quién la llama.
- Cada Web API queda con URL, método, qué dispara y grupos autorizados (❓ si la seguridad no está disponible).
- Cada process model tiene su BPMN y su uso real (o «sin historial»).
- Cada pantalla y cada regla de negocio tiene identificador y evidencia, y aparece en la trazabilidad de `12`.
- Cada `MOD-` de `13` tiene evidencia y fuente; cada elemento de `14` enlaza los RF, RN o MOD de los que sale.
- Cada hallazgo tiene ID, está en su documento propietario y en el registro de `09`, y `build_registry.py` termina sin errores.
- No hay secciones vacías, placeholders, secretos, nombres de usuario ni enlaces a `<trabajo>/`.
