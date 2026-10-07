# Marca del prototipo

## Dónde va

- **Por defecto**, el aspecto estándar de Appian: `assets/brand-appian.json`, con los valores por defecto del objeto Site
  (Appian 26.6), sin logo y sin perfil CSS propio.
- **La de un cliente** es un fichero de su proyecto, como sus fuentes: `<p>/prototipo/brand-<id>.json`, junto al
  `app.json`, con su logo en la misma carpeta. `<id>` es lo que va en el nombre del fichero y en `--brand`. El plugin no
  lleva la marca de ningún cliente.
- **Uso**:
  - `validate.py app.json --brand <id>` y `build.py app.json -o prototipo-<app>.html --brand <id>`. Sin `--brand`, la
    estándar. Si `brand-<id>.json` no está junto al `app.json`, salen con un error que dice dónde ponerlo.
  - En el script que escribe el spec, antes de `from sail_helpers import *`:
    `import sail_helpers; sail_helpers.usar_marca("<id>", r"<p>/prototipo")`. Así los helpers (botón principal, cabeceras
    oscuras, estados, gráficos, calendario) usan sus colores. Lo que la marca no define lo toman de la estándar.

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

1. **Fuente**: su guía de marca (manual de identidad corporativa) o, si no la hay, su web pública: el logotipo en SVG y
   los colores de su hoja de estilos. Anota en `source` de dónde sale cada cosa y la fecha. Solo lo público o lo que el
   cliente ha entregado.
2. **Site**:
   - `backgroundColor`: el color corporativo oscuro. La cabecera lleva texto blanco encima: 4,5:1 como mínimo.
   - `selectedPageHighlightColor`: un color de realce de la marca que se vea sobre `backgroundColor` (3:1).
   - `accentColor`: enlaces, pestañas y bordes `OUTLINE`, con 4,5:1 sobre blanco y sobre el gris de página (`#F4F5F7`).
     Si el color corporativo no llega, una variante más oscura del mismo tono.
   - `loadingBarColor`: el acento o el de realce.
   - Las formas de la marca: esquinas rectas, `SQUARED`; suaves, `SEMI_ROUNDED`.
   - `logo`: la versión para fondo oscuro, en SVG, sin lema, con su `logoAltText`.
3. **`palette`**: `navy`, el mismo `backgroundColor`; `slate`, un gris de texto secundario con 4,5:1 sobre blanco; los
   demás, de la marca o los de la estándar.
4. **`components.primaryButton.color`**: `ACCENT` o el color corporativo, si el botón se distingue del fondo (3:1). El
   texto del botón lo elige el prototipo (blanco o casi negro).
5. **`chartColorScheme`**: de 5 a 8 colores de la marca que se distingan entre sí, con 3:1 sobre blanco; el más claro, el
   último.
6. **`states`**: fondos de etiqueta apagados y, en `enum`, los semánticos de Appian (`SECONDARY`, `WARN`, `POSITIVE`,
   `NEGATIVE`; para «en curso», un azul en hex, porque el texto enriquecido no admite `INFO`).
7. **`cssProfile`**, solo si el cliente tiene capacidades avanzadas o premium y quiere un perfil propio.
8. **Tipografía**: si la marca tiene la suya, se anota en `typeface`; en Appian se configura en Admin Console y el
   prototipo sigue con Open Sans.

Para empezar, copia `assets/brand-appian.json` en `<p>/prototipo/brand-<id>.json`, cambia `id`, `name` y `source` y
sustituye los valores de la marca.

## Comprobar el contraste

- `python3 <KIT>/scripts/validate.py <p>/prototipo/app.json --brand <id>` aplica la marca a las pantallas y avisa:
  - «UX · contraste …» de cada texto, icono, etiqueta, sello o serie de gráfico que no llega al mínimo de WCAG 2.2 AA
    sobre su fondo, con un color alternativo que sí llega;
  - «fuera de la paleta de marca» de cada hex del `app.json` que no es de la marca.
- Con el HTML construido con `--brand <id>`, `python3 <KIT>/scripts/contrast_audit.py prototipo-<app>.html app.json` mide
  en el navegador cada texto, marcador de posición, borde de campo (3:1) y texto de gráfico. Tiene que dar 0.
- Si falla un color de la marca, se corrige en `brand-<id>.json`, no en el `app.json`, y se vuelve a construir. Si el
  cliente no acepta el cambio, queda como pregunta abierta.
