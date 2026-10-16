# El DF del cliente desde las fuentes

Cómo se escribe el DF del cliente (`analisis/df-cliente.md`, formato en `df-cliente-plantilla.md`) a partir del
material del proyecto y cómo entra cada fuente nueva. El trabajo es iterativo: cada reunión, correo o documento llega
sobre un DF que ya existe, y **la última decisión manda**, también sobre lo que se aceptó en la reunión anterior.

Se apoya en lo que el plugin ya hace con las fuentes: `leer_fuentes.py` para catalogarlas, las citas de
`ingesta-fuentes.md` §2, la nota de la fuente, el informe de impacto y `decisiones.md`. `<p>`: el proyecto.

## 1. Desde cero

1. **Catalogar todo** lo que se haya pasado: `leer_fuentes.py <ficheros o carpetas> -o <p>/fuentes/`. Lo que llega por
   el chat también es una fuente (`ingesta-fuentes.md` §1).
2. **Leer todas las fuentes antes de escribir**, en orden de fecha. Las reuniones posteriores cambian lo anterior: lo
   que vale es la última decisión. Con muchas fuentes, una nota por fuente (`volumen-grande.md`).
3. **Qué da cada fuente:**

   | Fuente | Sobre todo para |
   |---|---|
   | Reunión de descubrimiento | 1.1 cómo se hace hoy, 1.2 alcance, 2.5 cifras de hoy |
   | Reunión de diseño o revisión | 2.1 reglas comunes, 2.2 actividades, 2.3 pantallas, 2.4.1 quién hace qué |
   | Correo del cliente | Confirma o cambia lo dicho en una reunión; pesa más que la reunión (`ingesta-fuentes.md` §4) |
   | Diagrama del proceso | 2.1 diagrama y 2.2 una ficha por actividad, con sus identificadores |
   | Captura o prototipo | 2.3 lo que se ve y nadie dijo: textos, columnas, botones, estados |
   | Plantilla de correo, hoja de datos del cliente | 2.4.2 textos literales, listas de valores de las pantallas |
   | DF anterior o del cliente | La base, como versión 1.0 validada (🔒 en cada bloque) |
   | Análisis funcional del proyecto (`funcional.md`), si lo hay | Una fuente más: se cita como cualquier otra |

4. **Checkpoint** en un solo mensaje, una o dos líneas por punto: el proceso, los roles, las actividades, las áreas de
   pantallas, las reglas comunes, las contradicciones y lo que falta. Termina con «¿Es correcto o ajusto algo antes de
   escribir?». Con cualquier confirmación, sigue; si nadie responde, sigue con la lectura más razonable y deja las
   dudas en `df-cliente-pendientes.md`.
5. **Escribir** `analisis/df-cliente.md` desde `assets/plantillas/df-cliente.md`, apartado a apartado y guardando al
   terminar cada uno, con `df-cliente-plantilla.md` y, en las pantallas, `requerimientos-pantallas.md`. A la vez, la
   fila de cada bloque en `analisis/df-cliente-fuentes.md`, con su estado y sus citas: el DF no lleva ninguna.
6. **Lo que falta se pregunta**: un dato que las fuentes no dan (un texto literal, quién ve una acción, una cifra) es
   «pendiente de confirmar» en la frase y una fila en `analisis/df-cliente-pendientes.md`. Un detalle menor se resuelve
   con la opción más razonable, dicha en el texto.

## 2. Una fuente nueva

Una fuente cada vez, en orden de fecha.

1. **Catalogar** sobre la misma carpeta (`leer_fuentes.py <fichero> -o <p>/fuentes/`) y **leerla entera**.
2. **Puntos**: uno por decisión, cambio, dato nuevo, respuesta o pregunta, con su cita. Para cada uno, dónde encaja en
   el DF (el apartado y el bloque: «2.2 ACT-03», «2.3 pantalla "Nueva solicitud"», «2.4.1 matriz»; para encontrarlo,
   `df-cliente-fuentes.md` dice qué bloques salen de cada tema y de cada fuente) y su tipo, como en
   `actualizacion.md` §3: NUEVO, COMPLETA, CONFIRMA, VALIDA, CAMBIA, ANULA, RESPONDE, ALCANCE+ o ALCANCE−, PREGUNTA,
   SIN IMPACTO.
3. **La última decisión manda.** Un CAMBIA o un ANULA de una fuente del cliente (una reunión con él, un correo suyo,
   sus comentarios al Word) se aplica, aunque contradiga lo que se aceptó antes y aunque el bloque esté 🔒: es su
   decisión más reciente. No se aplica sin preguntar, y va como PREGUNTA, cuando:
   - dos personas del cliente dicen cosas distintas en la misma fuente o en fuentes de la misma fecha;
   - la fuente es interna (el equipo) y cambia algo acordado con el cliente;
   - el cambio no está cerrado («lo vemos», «a lo mejor»): es una pregunta, no una decisión.
4. **Informe de impacto** `impacto/FU-nn.md`, como en `actualizacion.md` §4, con «Encaja en» en palabras del DF. En el
   Resumen, siempre, la línea **«Cambia lo aceptado»**: los puntos que reescriben algo 🔒 o ya entregado al cliente,
   para que el analista lo vea antes de la próxima entrega. Si nada lo hace, «Cambia lo aceptado: nada».
5. **Aplicar**:
   - antes de tocar nada, la copia de la versión vigente: `proyecto.py copia <p>`;
   - se reescribe el bloque con lo nuevo y la cita se suma a su fila de `df-cliente-fuentes.md`
     (`FU-02 00:12:10; FU-06 00:04:30`); si era 🔒 y lo cambia el cliente, sigue 🔒. Un bloque nuevo, fila nueva; uno
     que se borra, sale de la tabla;
   - **lo de antes no se queda en el DF**: va a `decisiones.md` (§3);
   - **texto que queda viejo**: busca en todo el DF las palabras de lo de antes y corrige cada sitio que lo siga
     diciendo (otra pantalla, una regla común, la matriz, un correo). Es el error más frecuente;
   - lo que el cambio arrastra: una acción nueva en una pantalla es una fila nueva en la matriz; un correo nuevo, su
     NOT y su mención en la actividad; un estado nuevo, en las actividades que lo producen;
   - una pregunta respondida sale de `df-cliente-pendientes.md` (queda en `decisiones.md` como RESPONDE) y la frase
     del DF deja de decir «pendiente de confirmar»; una pregunta nueva, fila nueva;
   - la versión de la cabecera sube 0.1 (`Versión: 0.3` → `0.4`).
6. **Entregar**: en pocas líneas, los puntos por tipo, «Cambia lo aceptado» y lo que queda pendiente. El Word, solo al
   enviarlo o si se pide (§4).

Un retoque que nadie tiene que aprobar (un texto, una etiqueta, el orden de unas columnas) va por el camino corto de
`actualizacion.md`: sin nota, el informe escrito una vez al terminar.

## 3. Lo de antes: `decisiones.md`

Una fila D por cada CAMBIA, ANULA, RESPONDE, VALIDA o ALCANCE, con lo nuevo, lo de antes y su cita, y en «Afecta a» el
bloque del DF con su nombre:

```markdown
| D-04 | 2026-10-20 | FU-06 | CAMBIA | Una solicitud puede devolverse dos veces | Una solicitud puede devolverse sin límite [FU-02 00:12:10] | DF 2.2 ACT-03 | Sí |
```

Así el DF dice siempre lo vigente y cualquiera puede ver qué se decidió, cuándo y qué había antes.

## 4. Entregar el Word

```bash
python3 <skill>/scripts/df_cliente_docx.py <p>   # entregables/DF-cliente-<proceso>-v<versión>.docx
```

- Cada entrega es una versión: 1.0 la primera; las siguientes suben la versión y **añaden su fila al control de
  cambios**, con lo que cambió desde la entrega anterior en una frase para el cliente («Se limita a dos el número de
  devoluciones y se añade la prórroga, acordadas el 20/10»). Sale de las D y de los informes de impacto desde la última
  entrega.
- Nunca se sobrescribe un Word entregado; al enviarlo, `proyecto.py entregar <p> <fichero>` lo apunta.
- Antes de enviarlo, quien lo envía lo abre en Word y mira la portada, una actividad, una pantalla y la matriz.

## 5. Los comentarios del cliente al Word

El Word devuelto es una fuente más: `leer_fuentes.py` saca cada comentario y cada cambio marcado con el apartado donde
está. Cada comentario es un punto del §2; un «de acuerdo» sobre un bloque es VALIDA (pasa a 🔒 en `df-cliente-fuentes.md`). Cuando el cliente
valida el documento entero, la cabecera pasa a `Estado: validado` y la fila de esa entrega en el control de cambios
lleva el responsable y la fecha de validación.
