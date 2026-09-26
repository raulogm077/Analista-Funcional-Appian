# Muchas fuentes o una aplicación grande

Cuándo: más de ~5 transcripciones largas, o más de 5 procesos o módulos. Probado con 25 reuniones
(≈27.000 líneas) y una aplicación de 5 módulos: 219 RF, 85 pantallas, 465 criterios.

## 1. Extraer por fuente, antes de redactar
Nadie (tampoco un modelo) retiene 25 reuniones a la vez. Primero una nota por fuente en
`notas/FU-xx.md`, con estas secciones: Resumen · Hablantes → rol (única sección con nombres) ·
Decisiones (con cita y rol que decide) · Actores del sistema · Procesos, actividades y estados ·
Pantallas (campos, filtros, ordenación, acciones, visibilidad, textos literales) · Datos · Reglas ·
Contradicciones y cambios de criterio · Pendientes · Fuera de alcance. Todo con cita
`[FU-xx hh:mm:ss]` y aplicando `ingesta-fuentes.md`.

Si la sesión permite subagentes, reparte las fuentes en bloques **cronológicos** de ~3.000–4.000
líneas y lánzalos en paralelo, cada uno con estas instrucciones. Si no, hazlo tú fuente a fuente
guardando cada nota antes de seguir.

## 2. Checkpoint
El resumen del paso 2 del SKILL.md se hace desde las notas. Propón ahí la división en módulos.

## 3. Estructura común y módulos
1. Escribe tú las secciones comunes (1–5: fuentes, contexto, alcance, supuestos, actores con
   «Participa en»): fijan roles y términos para todos los módulos.
2. Asigna a cada módulo **rangos de IDs propios** para que no choquen, p. ej.:

   | Módulo | ACT | RF | RB | PAN | INT | NOT | P |
   |---|---|---|---|---|---|---|---|
   | M1 | 01–19 | 001–099 | 001–099 | 01–19 | 001–019 | 001–019 | 001–019 |
   | M2 | 20–39 | 100–199 | 100–199 | 20–49 | 020–039 | 020–039 | 020–039 |
   | … | | | | | | | |
3. Cada módulo (tú o un subagente por módulo) escribe sus secciones 6, 8–14 y 17 en
   `modulos/Mx.md` siguiendo `ddf-plantilla.md`, buscando en **todas** las notas (la información de
   un módulo está repartida por muchas reuniones) y quedándose con la última decisión; cada cambio
   de criterio es una fila `D-?` de su «Registro de decisiones» (formato de la Sec 17 de la plantilla).
4. Une con el script: cada sección n del `ddf.md` = la parte n de cada módulo bajo «### Mx · nombre»;
   las filas `D-?` se juntan en un único registro numerado por fecha; la Sec 7 (casos de uso = tareas
   de usuario) y la matriz de la Sec 16 se generan; cada bloque Mermaid se guarda como `.mmd` con su
   imagen enlazada.
   ```bash
   python3 <skill>/scripts/unir_modulos.py ddf-base.md modulos/M*.md -o ddf.md --diagramas diagramas
   python3 <skill>/scripts/render_mermaid.py diagramas/*.mmd
   ```
   Escribe tú la 15 y los escenarios de extremo a extremo de la 16 (encadenan tareas de varios módulos).
5. A partir de aquí, cada reunión nueva se incorpora con `actualizacion.md`, sin rehacer el análisis.

## 4. Comprobar antes de entregar
```bash
python3 <skill>/scripts/comprobar_ddf.py ddf.md --fuentes fuentes/
```
IDs duplicados, criterios repetidos o citados sin definir, RF sin criterio, piezas vigentes que remiten a
anuladas, citas a minutos que no existen (`--corregir-citas` las lleva a la intervención anterior) y
nombres de participantes en el documento. 0 problemas antes de generar el Word.
