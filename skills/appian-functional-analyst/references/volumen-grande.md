# Muchas fuentes o una aplicación grande

Cuándo: más de unas 5 reuniones largas para arrancar, o más de 5 procesos. Probado con 25 reuniones
(≈27.000 líneas) y una aplicación de 5 módulos.

## 1. Una nota por fuente, antes de escribir
Nadie retiene 25 reuniones a la vez. Primero una nota por fuente en `notas/FU-xx.md` con estas secciones:
Resumen · Hablantes → rol (la única con nombres) · Decisiones (con cita y rol que decide) · Perfiles ·
Procesos, pasos y estados · Pantallas (partes, datos, filtros, acciones, quién ve qué, textos literales) ·
Datos · Reglas · Avisos, documentos y otros sistemas · Condiciones de uso · Contradicciones y cambios de
criterio · Pendientes · Fuera de alcance. Todo con cita `[FU-xx hh:mm:ss]` y aplicando `ingesta-fuentes.md`.

Si la sesión permite lanzar agentes, reparte las fuentes en bloques **cronológicos** de unas 3.000 a 4.000
líneas, cada uno con estas instrucciones. Si no, fuente a fuente, guardando cada nota antes de seguir.

## 2. Checkpoint
El resumen del paso 2 del SKILL.md se hace desde las notas. Propón ahí los módulos (uno por proceso o
área).

## 3. Lo común y los módulos
1. Escribe tú lo común del funcional: §1, §2 y §10. Fija perfiles y términos para todos.
2. Da a cada módulo un **rango de IDs** propio para que no choquen, por ejemplo:

   | Módulo | ACT | HU | PAN | AV | PC |
   |---|---|---|---|---|---|
   | M1 | 01–19 | 01–39 | 01–19 | 01–09 | 01–19 |
   | M2 | 20–39 | 40–79 | 20–39 | 10–19 | 20–39 |

3. Cada módulo (tú o un agente por módulo) escribe `modulos/Mx-funcional.md` con los apartados
   `## N. Título` del funcional que le tocan (3, 4, 5, 6, 7, 8, 9, 11) y solo su parte, siguiendo
   `funcional-plantilla.md`. Busca en **todas** las notas, porque la información de un módulo está
   repartida, y se queda con la última decisión. Cada cambio de criterio es una fila
   `| D-? | fecha | fuente | tipo | … |` en un apartado `## Decisiones` del módulo.
4. Une:
   ```bash
   python3 <skill>/scripts/unir_modulos.py <p> modulos/M*-funcional.md --escribir
   python3 <skill>/scripts/indice.py derivadas <p> --escribir
   python3 <skill>/scripts/comprobar.py <p> --fuentes <p>/fuentes/
   ```
   `unir_modulos.py` añade cada apartado al del proyecto y numera las decisiones por fecha.
5. Escribe tú los escenarios que cruzan módulos. Después, cada reunión nueva entra con `actualizacion.md`.

La especificación técnica se escribe igual, con `modulos/Mx-tecnico.md`, cuando el funcional esté estable.
