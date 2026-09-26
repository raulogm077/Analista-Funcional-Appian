# Ejemplos del kit

Los ejemplos enseñan **técnica**: cómo se pasa de un documento a pantallas, cómo se usan los
patrones, los helpers y los componentes de Appian. **No enseñan un dominio.** El kit sirve para
cualquier proceso (acuerdos con terceros, medioambiente, servidumbres, informes, expedientes…) y
ninguno tiene más peso que otro.

En cada proyecto, las entidades, roles, estados, códigos, textos, reglas y datos salen de **su**
`ddf.md`. De un ejemplo se copia la forma de resolver una pantalla, nunca sus nombres, su flujo
ni sus datos.

| Carpeta | Qué es | Dominio de los datos (ficticio) |
|---|---|---|
| `casos/<proceso>/` | Casos completos, uno por proceso y todos al mismo nivel: documento de entrada → `ddf.md` → `generar_app.py` → prototipo, trazabilidad y perfil CSS | El de cada caso |
| `../templates/` | Los 12 patrones de pantalla (P01–P12) y su catálogo navegable (`catalogo-patrones.json`) | Genérico: expedientes de una unidad |
| `bloques/` | Galería de los bloques de `scripts/sail_helpers.py` y de los patrones de 26.9 (calendario, comentarios, kanban) | Mantenimiento de terminales |
| `ia/` | Componentes de IA de Appian en pantallas completas | Incidencias y pliegos |
| `componentes/` | Los 147 componentes de interfaz de Appian 26.9, uno a uno | Incidencias y proveedores |

## Casos disponibles

| Caso | Entrada | Modo del análisis | Pantallas | Qué muestra |
|---|---|---|---|---|
| `casos/atp/` · Acuerdos con terceras partes | ERS de ejemplo (ficticia) | Fiel | 8 | Inicio con tareas, listado con filtros, ficha con vistas, asistente de alta, tarea de revisión con decisión, diálogos de acción e informes |

## Añadir un caso (medioambiente, servidumbres, informes…)

1. Crea `casos/<proceso>/` con el documento de entrada **ficticio o anonimizado** (nunca material
   real del cliente), el `ddf.md` que genera `appian-functional-analyst` y un `generar_app.py`
   que importe los helpers con `sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "scripts"))`.
2. Genera y construye:
   ```bash
   python3 generar_app.py app.json
   python3 ../../../scripts/build.py app.json -o prototipo-<proceso>.html
   ```
3. Añade una fila a la tabla de casos de este fichero. `scripts/selftest.py` descubre los casos
   solo: valida, construye y pasa la prueba de humo y la auditoría de contraste a cada uno.
