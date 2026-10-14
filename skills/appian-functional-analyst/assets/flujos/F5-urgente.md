# F5 · Urgente

**Cuándo.** El cliente o el equipo declaran crítico algo que pasa en producción; también datos u operación (datos incorrectos, procesos en curso, un certificado caducado).
**Empieza.** El analista, con `appian-functional-analyst`. **Termina en.** La ficha `impacto/URG-nn.md` cerrada y la corrección en producción; si se corrigió en el entorno de corrección, cada unidad en curso que cambia esos objetos la reaplica al construirse (F8). Sin DF ni prototipo.

| # | Paso | Quién | Con qué | Detalle |
|---|---|---|---|---|
| 1 | Catalogar el aviso y abrir la unidad | Script | `appian-functional-analyst` · `leer_fuentes.py` y `proyecto.py cambio <p> URG-nn abrir` | `appian-functional-analyst/references/urgentes.md` §2 |
| 2 | Escribir la ficha: tipo, síntoma y quién la declara crítica | IA | `appian-functional-analyst` | `appian-functional-analyst/references/urgentes.md` §1 |
| 3 | Diagnosticar: causa y objetos, leyendo solo los implicados | IA | `appian-best-practices` | `appian-best-practices/references/13-maintenance-runbooks.md` |
| 4 | Mirar si choca con las unidades en curso | Script | `appian-functional-analyst` · `indice.py colision` | `appian-functional-analyst/references/urgentes.md` §2 |
| 5 | Decidir dónde se corrige: en desarrollo o en el entorno de corrección | El equipo | — | `appian-functional-analyst/references/urgentes.md` §2 |
| 6 | Corregir solo esos objetos y probarlo | Quien construye: IA por el Dev MCP o una persona | `appian-best-practices`, con la skill oficial `appian` | `appian-best-practices/SKILL.md` «Tools» |
| 7 | Revisar el paquete en Compare and Deploy, como el de un evolutivo, y desplegarlo por el proceso de cambios urgentes del cliente, con la vuelta atrás preparada | Una persona | Appian Designer · Compare and Deploy | `appian-functional-analyst/references/urgentes.md` §2 |
| 8 | Cerrar la ficha y registrar el pase, con su referencia en el cliente | Script | `appian-functional-analyst` · `proyecto.py cambio <p> URG-nn produccion --ref "<referencia>"` | `appian-functional-analyst/references/urgentes.md` §2 |
| 9 | Poner al día el entorno de corrección con el pase | Una persona | — | `appian-functional-analyst/references/urgentes.md` §2 y §3 |

**Variante: datos u operación.** No se corrige ningún objeto de la aplicación: la ficha recoge qué se hizo y se cierra con los campos de su tipo. `appian-functional-analyst/references/urgentes.md` §1.
