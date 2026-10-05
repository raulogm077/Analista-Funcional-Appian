# Cómo se escribe

El DF lo lee el cliente para validar y la especificación la lee quien construye. Los dos tienen que poder
leerse deprisa y sin dudas. `comprobar.py` avisa de lo que incumple esta guía.

## Reglas

- **Frases cortas**, de una idea, en presente y en voz activa. El sujeto es el perfil o la aplicación:
  «El técnico devuelve la solicitud», no «La solicitud será devuelta».
- **Concreto.** Quién hace qué, cuándo y con qué resultado. Una cifra en vez de «pronto», «varios» o
  «rápido»; un texto literal entre comillas en vez de «un mensaje de aviso».
- **Las palabras del cliente.** Si dice «expediente», es «expediente» en todo el documento.
- **Perfiles, no personas.** Los nombres de las personas no salen en el análisis.
- **Una sola vez.** Lo que ya está escrito se cita por su ID («ver HU-07»), no se repite. Si dos sitios
  dicen lo mismo, uno sobra.
- **Sin relleno.** Nada de introducciones que anuncian lo que viene ni de cierres que lo resumen.
- **Negrita** solo en los títulos de ficha y en los nombres de campo de una ficha vertical. Sin emojis en el
  texto del DF.
- **En el DF, nada de Appian.** El cliente lee «la lista de solicitudes», no «el record list». Los
  objetos de Appian se nombran en la especificación técnica.

## Antes y después

| En vez de | Escribe |
|---|---|
| Se llevará a cabo la revisión de la documentación aportada de forma adecuada. | El técnico revisa que estén los tres documentos obligatorios. |
| Cabe destacar que el sistema notificará al usuario. | La aplicación avisa al solicitante por correo. |
| El proceso es ágil y garantiza una gestión eficiente. | Una solicitud completa se resuelve en 5 días hábiles. |
| Asimismo, el usuario podrá, en su caso, adjuntar documentos. | El solicitante puede adjuntar documentos hasta que envía la solicitud. |

## Muletillas

`comprobar.py` busca estas expresiones (sin distinguir mayúsculas ni tildes). Cada línea es
`- «expresión» → qué hacer`.

- «cabe destacar» → quítalo y di el hecho
- «es importante» → quítalo y di el hecho
- «cabe señalar» → quítalo y di el hecho
- «en este sentido» → quítalo
- «a este respecto» → quítalo
- «asimismo» → quítalo o empieza otra frase
- «por otro lado» → quítalo o empieza otra frase
- «en definitiva» → quítalo
- «en resumen» → quítalo
- «llevar a cabo» → el verbo («revisar», no «llevar a cabo la revisión»)
- «lleva a cabo» → el verbo
- «se lleva a cabo» → el verbo
- «proceder a» → el verbo
- «procede a» → el verbo
- «realizar la» → el verbo
- «realiza la» → el verbo
- «con el objetivo de» → «para»
- «con el fin de» → «para»
- «en aras de» → «para»
- «de cara a» → «para»
- «a nivel de» → «en» o quítalo
- «de forma adecuada» → di cómo
- «de manera adecuada» → di cómo
- «adecuadamente» → di cómo
- «de forma eficiente» → di la cifra
- «de manera eficiente» → di la cifra
- «de forma ágil» → di la cifra
- «en tiempo y forma» → di el plazo
- «dar respuesta a» → «responder»
- «poner en valor» → di qué aporta
- «hacer hincapié» → quítalo
- «juega un papel» → di qué hace
- «sin lugar a dudas» → quítalo
- «robusto» → di qué soporta
- «intuitivo» → di cómo se usa
- «amigable» → di cómo se usa
- «user-friendly» → di cómo se usa
- «flexible» → di qué se puede cambiar y quién
- «holístico» → quítalo
- «sinergia» → quítalo
- «crucial» → quítalo o di por qué
- «fundamental» → quítalo o di por qué
- «en su caso» → di el caso
- «si procede» → di cuándo
- «según corresponda» → di a quién o cuándo
- «etc.» → la lista completa

## Palabras que piden una cifra

`comprobar.py` avisa si aparecen sin un número en la misma frase: «rápido», «rápidamente», «pronto»,
«en breve», «periódicamente», «frecuentemente», «a tiempo», «muchos», «muchas», «varios», «varias»,
«gran volumen», «gran cantidad».
