# Ejemplos del kit

Los ejemplos enseñan **técnica**: cómo se pasa del análisis funcional a pantallas, cómo se usan los
patrones, los helpers y los componentes de Appian. **No enseñan un dominio.** El kit sirve para
cualquier proceso (acuerdos con terceros, medioambiente, servidumbres, informes, expedientes…) y
ninguno tiene más peso que otro.

En cada proyecto, las entidades, perfiles, estados, códigos, textos, reglas y datos salen de **su**
análisis funcional (`analisis/funcional.md`). De un ejemplo se copia la forma de resolver una
pantalla, nunca sus nombres, su flujo ni sus datos.

| Carpeta | Qué es | Dominio de los datos (ficticio) |
|---|---|---|
| `casos/<proceso>/` | Proyectos completos, uno por proceso y todos al mismo nivel, con la carpeta de proyecto de `appian-functional-analyst`: fuente en `fuentes/` → `analisis/funcional.md` → `prototipo/` (script, `app.json`, prototipo, trazabilidad, perfil CSS y capturas enlazadas en el funcional) | El de cada caso |
| `../templates/` | Los 12 patrones de pantalla (P01–P12) y su catálogo navegable (`catalogo-patrones.json`) | Genérico: expedientes de una unidad |
| `bloques/` | Galería de los bloques de `scripts/sail_helpers.py` y de los patrones de 26.9 (calendario, comentarios, kanban) | Mantenimiento de terminales |
| `ia/` | Componentes de IA de Appian en pantallas completas | Incidencias y pliegos |
| `componentes/` | Los 147 componentes de interfaz de Appian 26.9, uno a uno | Incidencias y proveedores |

## Casos disponibles

| Caso | Entrada | Modo del análisis | Pantallas | Qué muestra |
|---|---|---|---|---|
| `casos/atp/` · Acuerdos con terceras partes | ERS de ejemplo (ficticia) | Fiel, sin especificación técnica | 8 | Inicio con tareas, listado con filtros, ficha con vistas, asistente de alta, tarea de revisión con decisión, diálogos de acción e informe con tablas alternativas. Su `generar_app.py` lee del funcional las historias, los pasos, los PC y el `ref` y el `req` de cada pantalla con `modelo.py` del analista |

## Añadir un caso (medioambiente, servidumbres, informes…)

1. Crea `casos/<proceso>/` con la carpeta de proyecto del analista: el documento de entrada
   **ficticio o anonimizado** en `fuentes/` (nunca material real del cliente), `proyecto.md` y
   `analisis/` con `funcional.md` y `decisiones.md`. `comprobar.py` del analista, sin errores.
2. En `prototipo/`, un `generar_app.py` que importe los helpers con
   `sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "scripts"))`. Genera, construye y captura:
   ```bash
   cd casos/<proceso>/prototipo
   python3 generar_app.py app.json
   python3 ../../../../scripts/build.py app.json -o prototipo-<proceso>.html
   python3 ../../../../scripts/capture.py prototipo-<proceso>.html app.json -o capturas/
   ```
3. Enlaza cada captura en su ficha PAN con la línea de `capturas/indice.md`. `comprobar.py` ya no
   avisa de pantallas sin captura.
4. Añade una fila a la tabla de casos de este fichero. `scripts/selftest.py` descubre los casos solo
   (`casos/*/prototipo/app.json`): valida, construye y pasa la prueba de humo y la auditoría de
   contraste a cada uno.
