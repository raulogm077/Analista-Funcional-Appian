# Marca del prototipo

## Dónde va

- **Por defecto**, el aspecto estándar de Appian: `assets/brand-appian.json`, con los valores por defecto del objeto Site
  (Appian 26.6), sin logo y sin perfil CSS propio.
- **La de un cliente** es un fichero de su proyecto, como sus fuentes: `<p>/prototipo/brand-<id>.json`, junto al
  `app.json`, con su logo en la misma carpeta. `<id>` es lo que va en el nombre del fichero y en `--brand`. La saca
  `scripts/marca.py` (abajo). El plugin no lleva la marca de ningún cliente.
- **Uso**:
  - `validate.py app.json --brand <id>` y `build.py app.json -o prototipo-<app>.html --brand <id>`. Sin `--brand`, la
    estándar. Si `brand-<id>.json` no está junto al `app.json`, salen con un error que dice dónde ponerlo.
  - En el script que escribe el spec, antes de `from sail_helpers import *`:
    `import sail_helpers; sail_helpers.usar_marca("<id>", r"<p>/prototipo")`. Así los helpers (botón principal, cabeceras
    oscuras, estados, gráficos, calendario) usan sus colores. Lo que la marca no define lo toman de la estándar.

## Qué lleva la configuración de un cliente

`marca.py crear` deja en `<p>/prototipo/`:

| Fichero | Qué es | Lo usa |
|---|---|---|
| `brand-<id>.json` | La marca: el objeto Site con su logo, la tipografía, la paleta, botones y tarjetas, los colores de gráfico, los estados y el perfil CSS | `validate.py`, `build.py` y los helpers |
| `logo-<id>-on-dark.svg` | El logo para fondo oscuro, el de la cabecera del site (y `logo-<id>-on-light.svg`, el de fondo claro) | El prototipo; en Appian se sube en PNG |
| `perfil-css-<id>.txt` | El perfil CSS para pegar en Admin Console › Branding › CSS Profiles (el mismo texto que escribe `build.py`) | Quien administra Appian |
| `marca-<id>.md` | La guía de marca: el Site para copiar tal cual, el perfil CSS y las capacidades que pide, la paleta con el contraste de cada color, botones y tarjetas, estados, gráficos, tipografía, logo, fuentes con su fecha, ajustes de contraste y lo que tiene que confirmar el cliente | Quien construye en Appian y quien diseña las pantallas |

## Formato de `brand-<id>.json`

| Clave | Qué lleva | Lo usa |
|---|---|---|
| `id`, `name`, `source` | El `<id>` del nombre del fichero, el nombre de la marca y de dónde salen los valores (URL o documento, con la fecha) | El HTML (`px-brand`) |
| `site` | Las propiedades del objeto Site, tal cual se copian en Appian: `navigationLayout` (`HEADER_BAR`, `SIDEBAR`), `headerBarStyle` (`MERCURY`, `HELIUM`, `OXYGEN`), `backgroundColor`, `selectedPageHighlightColor`, `accentColor`, `loadingBarColor`, `buttonShape`, `inputShape` y `dialogShape` (`SQUARED`, `SEMI_ROUNDED`, `ROUNDED`), `useUppercase` (etiquetas de botón en mayúsculas), `useUppercasePageTitles` (títulos de página de la cabecera en mayúsculas) y `showUserMenu`. Si la marca tiene logo: `logo` (el SVG para fondo oscuro, junto al JSON) y `logoAltText`. `backgroundColor`, `selectedPageHighlightColor` y `accentColor` son obligatorios | `build.py`, el runtime (cabecera del site) y `validate.py` (contraste) |
| `palette` | Colores para usar como hex en SAIL. Los helpers leen `navy` (el oscuro de la marca: cabecera de registro, cabecera «hero», barra lateral), `slate` (texto secundario, 4,5:1 sobre blanco), `steel`, `red` y `greenDark` (tipos de evento del calendario y kanban), `amber` (icono de los avisos `WARN` cuando el ámbar de la marca no llega a 3:1 sobre el fondo de aviso), `lineStrong` (líneas que deben verse, 3:1), `pageBg` (gris de página) y `grayLight` (líneas finas) | Los helpers; `validate.py` avisa de un hex del `app.json` que no es de la marca |
| `components` | `primaryButton` (estilo y color del botón principal: hex o `ACCENT`), `secondaryButton`, `destructiveButton`, `toolbarButton`, `contentCard` y `pageBackground` (convenciones de la guía) y `chartColorScheme` (series de gráficos en orden: 3:1 sobre blanco, salvo la última, que solo va con etiquetas de datos) | Los helpers (`PRIMARY`, `CHART`), el runtime (botón principal y gráficos sin `colorScheme`) y `validate.py` |
| `states` | La paleta de estados de toda la app: `neutral`, `enCurso`, `atencion`, `positivo` y `negativo`, cada uno con `tag` (fondo apagado de la etiqueta, hex, con texto `STANDARD` encima) y `enum` (color de icono, texto o barra de gráfico: un enumerado o un hex) | Los helpers (`state_map`, `state_chart_colors`, kanban, revisión de IA) y `validate.py` |
| `typeface` | La tipografía del prototipo (Open Sans) y cómo se configura la del cliente en Appian | Documentación |
| `appianSemanticApprox` | Aproximaciones de los colores semánticos de Appian (en SAIL van siempre los enumerados) | Documentación |
| `cssProfile` | Opcional. El perfil CSS de Appian (Admin Console › Branding › CSS Profiles; capacidades avanzadas y premium): `name`, `typeface` y `groups` con `comment` y `properties`. Solo lo que cambia respecto a Appian | `validate.py` (nombres de propiedad de Appian 26.9), `build.py` (lo aplica al prototipo y escribe `<prototipo>-perfil-css.txt`) |

Las claves que empiezan por `_` son comentarios.

## Cómo se saca la marca de un cliente

1. **Fuente**: su guía de marca (manual de identidad corporativa) o su sala de prensa y, si no las publica, su web
   oficial. Solo fuentes de la propia empresa: lo público o lo que el cliente ha entregado. La fuente y su fecha van en
   `--fuente`.
2. **Leer la web**: `python3 <KIT>/scripts/marca.py web <url> [--max-css 10] [--timeout 10]` descarga la página y las
   hojas de estilo que enlaza del mismo sitio (como mucho `--max-css`, de 2 MB cada una) y escribe un JSON:
   - `colores`: los 20 más usados, de más a menos, sin blancos ni negros (luminosidad de 96 % o más, o de 4 % o menos)
     ni grises (saturación por debajo del 10 %); cada uno con `veces`, las `variables` CSS que lo definen y su
     `contraste` sobre blanco y sobre negro;
   - `themeColor`, el de `<meta name="theme-color">`;
   - `logos`: primero los SVG en línea y las imágenes de la cabecera con «logo» en `src`, `alt`, `class` o `id` (un SVG
     en línea lleva su código en `svg` y, como `url`, la de la página con `#svg-<n>`); al final, el icono del sitio;
   - `tipografias`: la primera familia de cada `font-family`, de más a menos usada.

   Sin red o sin respuesta sale con 2 y lo dice: entonces, WebFetch pidiendo los colores en hex, la tipografía y la URL
   del logo.
3. **Papeles**:
   - `--oscuro`: el color corporativo oscuro, el de la cabecera del site, que lleva texto blanco encima.
   - `--realce`: un color de la marca que se vea sobre el oscuro: la página seleccionada y la barra de carga.
   - `--acento`: enlaces, pestañas, bordes `OUTLINE` y, si no hay `--principal`, el botón principal (`ACCENT`).
   - `--principal`: el color del botón principal, si no es el acento; que se distinga del fondo (3:1).
   - `--secundarios`: los demás colores de la marca, para gráficos y barras decorativas.
   - `--formas`: esquinas rectas, `SQUARED`; suaves, `SEMI_ROUNDED` (por defecto); de píldora, `ROUNDED` (los campos se
     quedan en `SEMI_ROUNDED`, que es lo que admite el Site).
   - `--mayusculas si|no`: etiquetas de botón y títulos de página en mayúsculas; por defecto `si`, como el Site de Appian.
   - `--tipografia`: la de la marca, si tiene una propia.
   - `--logo`: el SVG para fondo oscuro, sin lema; `--logo-claro`, el de fondo claro.
4. **Crear**: `python3 <KIT>/scripts/marca.py crear --id <id> --nombre <nombre> --fuente "<fuente>, <fecha>" --oscuro <hex>
   --realce <hex> --acento <hex> [opciones] <p>/prototipo/`. Lo que no llega a WCAG 2.2 AA lo ajusta cambiando solo la
   luminosidad (matiz y saturación se quedan), en pasos de 0,5 %, y lo dice en la salida y en la guía
   (`acento #5DA9E9 → #1A73BE: 4,5:1 sobre el gris de página #F4F5F7…`):
   - el acento se oscurece hasta 4,5:1 sobre blanco y sobre el gris de página (`#F4F5F7`);
   - el oscuro, hasta 4,5:1 con texto blanco;
   - el realce se aclara hasta 3:1 sobre el oscuro;
   - con perfil CSS, los colores de estado y la etiqueta y el asterisco de los campos, hasta 4,5:1 sobre blanco y sobre
     su fondo.

   Si un ajuste no llega, lo dice y no escribe nada. Además:
   - **Grises**, con el matiz del oscuro: `slate` (texto secundario e instrucciones, tan legible como el de Appian), el
     del marcador de posición (4,5:1), `lineStrong` (bordes de campo, 3:1 sobre blanco y sobre el gris de página) y
     `grayLight`.
   - **Estados**: «en curso» con el tinte del acento de fondo y el oscuro de color; los demás, los de la estándar.
   - **Gráficos** (`chartColorScheme`): primero los colores de la marca con 3:1 sobre blanco y después los de la estándar,
     sin repetir ni colores casi iguales, como mucho 8.
   - **Perfil CSS**, salvo con `--sin-perfil-css` (el entorno no tiene las capacidades avanzadas o premium): solo lo que
     cambia respecto a Appian, en seis grupos: colores semánticos (texto e iconos de estado con 4,5:1 sobre blanco y sobre
     su fondo, que es el de Appian), textos de los campos (etiqueta con el oscuro; instrucciones, marcador de posición y
     asterisco con 4,5:1), campos (borde con 3:1 y radios de la forma), botones (radios), tarjetas, cajas y etiquetas
     (sombra teñida del oscuro y radios) y tooltips (fondo del oscuro, texto blanco). Los radios son los que da
     `build.py` a cada forma; con `SQUARED`, sin radios de botón ni de campo. `validate.py` lo comprueba antes de
     escribirlo.
   - **Aviso** si el logo no llega a 3:1 sobre el oscuro: hace falta su versión en negativo.
   - **Sale con 2**, sin escribir nada, si un color no es `#RRGGBB`, si un logo no existe, si el `id` no es `[a-z0-9-]` o
     si la carpeta está dentro del plugin.
5. **Después**: valida y construye con `--brand <id>`, pasa `contrast_audit.py`, enseña al usuario la cabecera con su
   logo y el resumen de `marca-<id>.md` y anota el supuesto en `app` (SKILL.md, paso 1). Si el cliente cambia un color o
   no acepta un ajuste, se vuelve a ejecutar `crear` con el color nuevo; si no hay acuerdo, queda como pregunta abierta.

## Comprobar el contraste

- `python3 <KIT>/scripts/validate.py <p>/prototipo/app.json --brand <id>` aplica la marca a las pantallas y avisa:
  - «UX · contraste …» de cada texto, icono, etiqueta, sello o serie de gráfico que no llega al mínimo de WCAG 2.2 AA
    sobre su fondo, con un color alternativo que sí llega;
  - «fuera de la paleta de marca» de cada hex del `app.json` que no es de la marca.
- Con el HTML construido con `--brand <id>`, `python3 <KIT>/scripts/contrast_audit.py prototipo-<app>.html app.json` mide
  en el navegador cada texto, marcador de posición, borde de campo (3:1) y texto de gráfico. Tiene que dar 0.
- Si falla un color de la marca, se corrige en la marca (con `marca.py crear` o en `brand-<id>.json`), no en el
  `app.json`, y se vuelve a construir. Si el cliente no acepta el cambio, queda como pregunta abierta.
