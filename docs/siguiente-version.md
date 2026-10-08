# Para la siguiente versión

El alcance de la 0.7.0 está congelado hasta F9 (Raúl, 8 de octubre de 2026): lo nuevo que surja mientras tanto se
apunta aquí y entra en la siguiente versión. Cada línea dice qué, dónde y de dónde sale.

## Prototipos

- Partir `scripts/marca.py` en módulos (lector web aparte; `crear` en validar, calcular, perfil y escribir). Hoy es un
  solo fichero, como pide el plan, y lo cubren las pruebas. Revisión de la Tarea 0c.
- `marca.py web` busca «logo» como palabra entera: se le escapan compuestos en minúsculas como `logomark` o `logoimg`.
  Revisión de la Tarea 0c.
- La lista «Comprobado con WCAG 2.2 AA» de `marca-<id>.md` da por hecho el 4,5:1 del texto del botón principal, que en
  Appian es automático. Revisión de la Tarea 0c.
- `$assumption` repite la fecha si `--fuente` ya acaba en una. Revisión de la Tarea 0c.
- Con más de 8 colores de marca, `marca.py` se queda con los 8 primeros sin decirlo, y `references/marca.md` dice que
  solo se quedan fuera los que no llegan a 3:1. Revisión de la Tarea 0c.
- `build.py` tiene su propia `_lum`, duplicada de `validate.py`. Revisión de la Tarea 0c.

## Ingeniería inversa

- `build_model.py` lee todos los `*.json` de la carpeta de cada objeto: si dos equipos extraen a la vez en una carpeta
  sincronizada, las copias de conflicto de OneDrive (`…-PC.json`) contarían como respuestas. Revisión de F2.
