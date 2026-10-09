<!--
  Plantilla de refactorizacion/propuesta.md (appian-refactorizacion). Los seis apartados y sus títulos son fijos: el
  analista y las comprobaciones los buscan por su título. Los {{marcadores}} se sustituyen y los comentarios se borran.
  Hechos del as-is, propuesta propia: el Diagnóstico solo afirma lo que está en as-is/ y lo enlaza; la Solución propone.
  Enlaces relativos a este fichero (../as-is/…), a la ficha del anexo o al documento de as-is/ que lo muestra; nunca a
  la extracción en bruto.
  Objetos de Appian entre comillas invertidas, con su nombre del inventario. Un objeto nuevo de la Solución lleva el
  prefijo de la aplicación y no está en el inventario.
  Certeza: ✅ verificado, 🔶 inferido, ❓ pendiente; en una REF, la del hallazgo que cita.
-->

# Propuesta de refactorización: {{aplicación o parte}}

> **Responde a:** qué está mal hecho y por qué, cómo debería estar hecho, cómo se pasa de lo que hay a lo nuevo y qué
> falta por decidir.

Base: [as-is](../as-is/LEEME.md) de {{fecha}}, entorno {{entorno}}, Appian {{versión}}.

## 1. Alcance

- **Se rehace:** {{módulos, procesos o capas}}.
- **Se queda como está:** {{lo que no se toca y por qué}}.
- **Límites:** {{plazo}}; no se puede tocar {{otras aplicaciones, contratos externos, tablas compartidas}}.

## 2. Diagnóstico

<!-- Una ficha por problema, de más prioridad a menos. Una REF por problema: varios objetos con el mismo problema son
     una REF, y dos hallazgos del mismo objeto y el mismo problema visto por dos señales (un proceso huérfano y sin
     ejecuciones) también, citando los dos.
     Evidencia: el H-… y su certeza si sale de un hallazgo, y el enlace a lo que lo muestra en as-is/. Si el hallazgo es
     inferido o pendiente, la ficha lo dice y la Hoja de ruta pone antes «Verificar H-…».
     Regla: la sección de appian-best-practices que lo trata, «BP nn §x» (seccion.py nn x la imprime).
     Efecto: en rendimiento, mantenimiento o riesgo, en una línea.
     Prioridad: Alta (riesgo de seguridad o de datos, o bloquea otras fases) · Media · Baja (higiene).
     Esfuerzo, por persona: S (hasta 2 días) · M (de 3 a 10 días) · L (más de 2 semanas), y por qué. -->

**REF-01 — {{Problema, en una línea}}**

- Evidencia: {{H-DAT-01}} ✅ {{qué muestra}} · [`mcp:{{tipo}}/{{nombre}}#{{ubicación}}`](../as-is/anexo/{{tipo}}/{{slug}}.md)
- Regla: BP {{nn}} §{{x}}
- Efecto: {{…}}
- Prioridad: {{Alta}}
- Esfuerzo: {{M}}, {{nº de objetos, migración de datos, pruebas}}

## 3. Solución

<!-- Una fila por capa que cambia: datos, seguridad, procesos, pantallas, integraciones. Hasta entidades, procesos y
     patrones de pantalla («un record type sincronizado en lugar de dos CDT»); los campos, los nodos y las interfaces
     los detalla el técnico del analista, que cita cada REF. Cada REF del Diagnóstico sale en alguna fila.
     Oportunidades (Process HQ, AI skills…), solo si resuelven una necesidad que se ve en as-is/. -->

| Capa | Qué se hace | Por qué | Se descarta |
|---|---|---|---|
| {{Datos}} | {{…}} | {{REF-01}}: {{…}} (BP {{nn}} §{{x}}) | {{alternativa y por qué no}} |

## 4. Migración y convivencia

<!-- Estrategia: cambiar la aplicación actual, hacer una nueva a su lado o mixta, con su porqué y por qué no las otras.
     Cómo pasan los datos, qué pasa con los procesos en curso, los contratos con fuera (Web APIs, integraciones,
     objetos de otras aplicaciones) y cómo conviven lo viejo y lo nuevo hasta retirar lo viejo. -->

**Estrategia:** {{…}}.

- **Datos:** {{tablas que se reutilizan, qué se migra y volúmenes}}.
- **Procesos en curso:** {{…}}.
- **Contratos con fuera:** {{…}}.
- **Convivencia y retirada:** {{…}}.

## 5. Hoja de ruta

<!-- Fases en orden de dependencias. Cada REF en una fase; una REF sobre un hallazgo inferido o pendiente, después de
     su «Verificar H-…». -->

| Fase | Qué | Depende de |
|---|---|---|
| 0 | Verificar {{H-…}}: {{cómo}} | — |
| 1 | {{REF-01}}: {{…}} | {{Fase 0}} |

## 6. Pendientes

<!-- Lo que tiene que decidir el equipo o el cliente (DEC-nn, con sus opciones y la recomendada) y los NV de
     as-is/datos/sin-verificar.json que condicionan la solución, con su ID. -->

| ID | Qué falta | Quién | Condiciona |
|---|---|---|---|
| DEC-01 | {{decisión: opciones y la recomendada}} | {{Negocio · Equipo}} | {{REF-…}} |
| {{NV-ARQ-01}} | {{pregunta del NV}}; hace falta {{qué hace falta}} | {{a quién}} | {{REF-…}} |
