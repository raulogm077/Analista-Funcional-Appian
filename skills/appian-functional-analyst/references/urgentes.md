# Cambios urgentes

Cuándo: el cliente o el equipo declaran crítico algo que pasa en producción: la aplicación parada, datos incorrectos, un
sistema o un certificado caducado, un comportamiento que impide hacer bien las tareas, errores técnicos visibles
(pantallas que fallan, servicios que no responden). **La urgencia la declara alguien y el plugin no la discute**; queda
escrito quién y por qué. Lo que nadie declara crítico es un evolutivo prioritario (`cambios.md`).

Base (BP 08 §3; Appian, «Deploying an Application Hotfix»): un parche solo con los objetos de la corrección, construido
sobre una versión igual a producción, llevado después a desarrollo, registrado y con regresión. El riesgo típico: el
siguiente pase pisa la corrección. Sin DF ni prototipo.

## 1. La ficha: un informe de impacto

`impacto/URG-nn.md`, con la plantilla `assets/plantillas/urgencia.md` y la cabecera `Cambio: URG-nn`, así le sirven las
mismas comprobaciones (`comprobar.py --impacto`). Su sección «Urgencia» lleva los campos de su tipo:

| Tipo | Qué es | Campos de «Urgencia» | En el análisis |
|---|---|---|---|
| Defecto | La aplicación no hace lo especificado | Síntoma, Quién la declara crítica, Causa, Objetos, Colisión, Dónde se corrige, Despliegue y vuelta atrás, Cierre | El funcional no cambia; técnico §14 gana la prueba que reproduce el fallo (`URG-nn` en su fila) |
| Cambio de comportamiento | Hay que cambiar lo que hace | Los de defecto | Un punto CAMBIA que aprueba el jefe de proyecto (✅, R4); el cliente lo valida después |
| Datos u operación | Datos, procesos en curso (BP 03 §12), configuración, certificado | Síntoma, Quién la declara crítica, Qué se hizo, Cierre | Nada, salvo que cambie una regla |

«Objetos» son los que se corrigen, entre comillas invertidas. «Dónde se corrige» dice **«Desarrollo»** o **«Entorno de
corrección»**, una de las dos: con eso los scripts saben qué unidades tienen que reaplicarla (otra cosa solo vale si nada
choca; si choca, `produccion` falla).

**El «Estado» de su cabecera**, como en cualquier informe (`actualizacion.md`):
- al abrirla, `Estado: pendiente`;
- cuando se aplica lo que cambia el análisis, `Estado: aplicado en X.Y`. La prueba de un defecto en técnico §14 cambia el
  técnico, así que sube la versión (R2), con su fila en `decisiones.md`;
- si no cambia nada del análisis (datos u operación), `Estado: sin cambios`.

Tras `produccion`, `proyecto.py estado` ya no la lista como pendiente.

## 2. El flujo corto

1. **Catalogar** el aviso, el correo o el chat (`leer_fuentes.py`) y abrir la unidad:
   `proyecto.py cambio <p> URG-nn abrir --titulo "…"`.
2. **Diagnóstico** con `appian-best-practices` (BP 13: síntoma → causa → acción), leyendo solo los objetos implicados.
   Escribe Causa y Objetos en la ficha.
3. **Colisión**: `python3 <skill>/scripts/indice.py colision <p> URG-nn`. Compara los objetos que se corrigen **y los que
   los usan** (`as-is/datos/dependencias.json`) con los de las unidades sin pasar a producción y, si hay
   `as-is/datos/deriva.json`, con lo modificado en desarrollo. Si no está la deriva, imprime la orden para pedirla solo de
   esos objetos (sin historial de versiones, lo dice y no supone nada). Copia el resultado en «Colisión».
4. **Dónde se corrige.**
   - Sin colisión: en desarrollo. Esos objetos quedan congelados para las unidades en curso hasta el pase (su encargo lo
     avisa).
   - Con colisión: en el entorno de corrección, igual que producción. Cada unidad en curso que cambia esos objetos
     recibe en su encargo «reaplicar URG-nn en <objeto>», y no pasa a Construida sin `--reaplicada URG-nn`, que confirma
     quien construye cuando la prueba de la urgencia pasa en desarrollo.
   - Sin entorno de corrección: la ficha registra en «Colisión» lo que decide el equipo (el plugin no inventa un
     procedimiento) y «Dónde se corrige» dice igualmente una de las dos.
5. **Despliegue** por el proceso de cambios urgentes del cliente (el plugin no lo gestiona), con la vuelta atrás
   preparada: el paquete con la versión de producción de esos objetos. Restaurar una copia de seguridad es lo último.
6. **Cierre**: «Cierre» en la ficha y `proyecto.py cambio <p> URG-nn produccion --ref "<referencia>"` (falla si la ficha no
   dice «Dónde se corrige», o si no dice «Desarrollo» ni «Entorno de corrección» y algo choca). Después, actualizar el
   entorno de corrección con el pase, que `proyecto.py` recuerda.

Una urgencia va de Abierta a En producción, o a Descartada; no se aprueba ni se marca Construida como un evolutivo.

## 3. Prevención

Entorno de corrección actualizado en cada pase; unidades cortas; en cambios largos sobre objetos centrales, constantes de
activación (BP 08 §2); cambios de proceso compatibles hacia atrás (BP 03 §12).
