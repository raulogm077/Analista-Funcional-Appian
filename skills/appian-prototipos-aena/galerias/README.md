# Galerías del kit

Las galerías son el catálogo del kit: enseñan **técnica** (cómo se resuelve una pantalla con los patrones, los
helpers y los componentes de Appian), no un dominio. Cada una es una app construible: su `generar_app.py` escribe el
`app.json` con los helpers de `scripts/sail_helpers.py` y `scripts/build.py` construye con él el HTML y la
trazabilidad. La prueba del plugin, que no va en el paquete, las valida, las construye y les pasa la prueba de humo
y la de contraste.

Aquí no hay proyectos. Un proyecto tiene su propia carpeta, con sus fuentes, su análisis funcional y su prototipo
(`prototipo/`), y sus entidades, perfiles, estados, códigos, textos, reglas y datos salen de **su** análisis
funcional (`analisis/funcional.md`). De una galería se copia la forma de resolver una pantalla, nunca sus nombres,
su flujo ni sus datos.

| Carpeta | Qué enseña | Dominio de los datos (ficticio) |
|---|---|---|
| `bloques/` | Los bloques de `scripts/sail_helpers.py` (cuándo usar cada uno: `references/bloques.md`) y los patrones de 26.9: calendario, comentarios y kanban | Mantenimiento de terminales |
| `ia/` | Los componentes de IA de Appian en pantallas completas | Incidencias y pliegos |
| `componentes/` | Los 147 componentes de interfaz de Appian 26.9, uno a uno y agrupados como en la documentación | Incidencias y proveedores |
| `../templates/` | Los 12 patrones de pantalla (P01–P12) y su catálogo navegable (`catalogo-patrones.json`) | Genérico: expedientes de una unidad |
