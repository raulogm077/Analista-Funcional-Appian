# Cómo colaborar en el plugin

`main` es la versión buena del plugin. Nadie escribe en ella directamente: cada uno trabaja en su rama, abre un PR
y Raúl lo aprueba. Solo entonces entra en `main`.

## 1. Instalar el plugin para el día a día

Es la versión de `main`, la que se usa en los proyectos reales:

```bash
claude plugin marketplace add https://github.com/raulogm077/Analista-Funcional-Appian
claude plugin install appian-analisis-funcional@appian-analisis-funcional
```

Para que lleguen las versiones nuevas: `/plugin` → Marketplaces → `appian-analisis-funcional` → **Enable
auto-update**. Lo que falta en tu equipo te lo dice el plugin al empezar; la lista completa está en el README.

## 2. Corregir o mejorar algo

1. Descarga el repositorio la primera vez y, cada vez que empieces, ponte al día:
   ```bash
   git clone https://github.com/raulogm077/Analista-Funcional-Appian
   cd Analista-Funcional-Appian
   git checkout main
   git pull
   ```
2. Crea una rama con **tu nombre delante** y un tema corto. Una rama por trabajo:
   ```bash
   git checkout -b lucia/contraste-prototipos
   ```
3. Haz el cambio y pruébalo en un proyecto de prueba **fuera de esta carpeta**, con tu copia del plugin. Solo afecta
   a esa sesión; tu plugin instalado no cambia:
   ```bash
   claude --plugin-dir <ruta a tu copia de Analista-Funcional-Appian>
   ```
4. Antes de guardar, la comprobación básica (segundos). Si cambiaste un script, una plantilla o un dato de una skill,
   también su prueba:
   ```bash
   python3 pruebas/comprobar_plugin.py
   python3 pruebas/<skill>/selftest.py
   ```
5. Guarda y sube tu rama (mensajes de commit en español):
   ```bash
   git add -A
   git commit -m "Prototipos: contraste de los botones secundarios"
   git push -u origin lucia/contraste-prototipos
   ```
6. Abre el PR en GitHub. En la descripción: qué cambiaste, por qué y cómo lo probaste.

GitHub pasa todas las pruebas al PR. Si sale algo en rojo, se corrige en la misma rama y se vuelve a subir. Raúl
revisa y aprueba; sin su aprobación no entra.

## 3. Reglas para no pisarse

- **No toques la versión** (`.claude-plugin/plugin.json` y la tabla de versiones del README). La sube Raúl al
  publicar.
- **No trabajes en la rama de otro.** Para probar su cambio, descárgala en otra carpeta:
  ```bash
  git fetch origin
  git worktree add ../prueba-lucia lucia/contraste-prototipos
  ```
  y usa `claude --plugin-dir ../prueba-lucia`.
- **Si otro PR entra antes que el tuyo**, pulsa «Update branch» en tu PR: se pone al día y vuelve a pasar las
  pruebas.
- **Nada de clientes en el repositorio**: ni transcripciones, ni salidas reales, ni marcas. Los ejemplos son
  ficticios. Lo que el plugin genera en un proyecto se queda en la carpeta de ese proyecto.
- **Una lección de una prueba real** que pida cambiar el plugin: cuéntala en la descripción del PR o en una issue,
  sin datos del cliente.

Las demás normas del repositorio están en `CLAUDE.md`.
