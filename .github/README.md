<!-- Portada del repositorio en GitHub. No va en el paquete (.github/ es del repositorio): el manual del plugin es el README.md de la raíz. -->

<div align="center">

<img src="assets/banner.svg" alt="Analista funcional Appian, plugin de Claude: del material del cliente a lo que se valida y se construye" width="100%">

<br>

**Del material del cliente al diseño funcional que valida y a lo que se construye en Appian.**

[![Versión](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Fraulogm077%2Fanalista-funcional-appian%2Fmain%2F.claude-plugin%2Fplugin.json&query=%24.version&label=versi%C3%B3n&color=2f6fd6&style=flat-square)](../README.md#versiones)
[![Pruebas](https://img.shields.io/github/actions/workflow/status/raulogm077/analista-funcional-appian/pruebas.yml?branch=main&label=pruebas&style=flat-square)](https://github.com/raulogm077/analista-funcional-appian/actions/workflows/pruebas.yml)
![Plugin de Claude](https://img.shields.io/badge/plugin-Claude%20Code%20%C2%B7%20Claude-d97757?style=flat-square)
![Skills](https://img.shields.io/badge/skills-6-6b4fbb?style=flat-square)
![Sistemas](https://img.shields.io/badge/Windows%20%C2%B7%20macOS%20%C2%B7%20Linux-555?style=flat-square)

[Instalación](#-instalación) · [Actualizaciones](#-actualizaciones) · [Skills](#-las-seis-skills) · [Cómo trabaja](#-cómo-trabaja) · [Desarrollo](#-para-quien-desarrolla-el-plugin) · [Manual completo](../README.md)

</div>

---

## ✨ Qué es

Un plugin de Claude para equipos que analizan, documentan, rehacen y prototipan aplicaciones **Appian**. Sirve para cualquier proceso y cualquier cliente: el dominio sale siempre de las fuentes del proyecto.

- 📥 **Entra** lo que hay: reuniones, correos, actas, diagramas, el DF del cliente o una aplicación que ya existe.
- 📤 **Sale** lo que se necesita: el **DF en Word** que valida el cliente, la **especificación técnica** para construir con el Dev MCP, los **procesos BPMN** en draw.io y un **prototipo navegable** con la marca del cliente.
- 🔁 **Cada reunión nueva** cambia solo lo afectado, con un informe de impacto que aprueba el analista.

## 🚀 Instalación

> Se hace **una sola vez** por persona. Después, el plugin se actualiza solo.

**1. Comprueba que tienes Git.** Claude Code lo usa para descargar el plugin de GitHub. Abre una terminal y escribe:

```bash
git --version
```

Si no lo reconoce, instálalo:

| Windows | macOS | Linux |
|---|---|---|
| `winget install Git.Git` | `xcode-select --install` | `sudo apt install git` |

**2. Instala el plugin en Claude Code:**

```text
/plugin marketplace add raulogm077/analista-funcional-appian
/plugin install appian-analisis-funcional@appian-analisis-funcional
```

**3. Activa las actualizaciones automáticas.** En Claude Code escribe `/plugin` → **Marketplaces** → `appian-analisis-funcional` → **Enable auto-update**. Viene desactivado por defecto.

**4. Comprueba tu equipo.** Pide a Claude: *«comprueba qué le falta al plugin en este equipo»*. Te dice qué falta, qué se pierde sin ello y cómo se instala ([tabla de requisitos](../README.md#requisitos)).

<details>
<summary><b>En la app de Claude (escritorio o web)</b></summary>

<br>

**Customize** → **Plugins** → **Add** → **Add marketplace** → **Add from repository** y escribe `raulogm077/analista-funcional-appian`.

Ingeniería inversa necesita el Dev MCP en tu equipo, así que solo funciona con Claude Code (también en la pestaña Code de la app de escritorio).

</details>

## 🔄 Actualizaciones

| Cómo lo tienes | Qué pasa cuando sale una versión |
|---|---|
| ✅ Con auto-update | Llega sola: se aplica la próxima vez que abres Claude Code |
| ✋ Sin auto-update | `/plugin marketplace update appian-analisis-funcional` en una sesión, o `claude plugin update appian-analisis-funcional@appian-analisis-funcional` en la terminal |

¿Qué versión tienes? `claude plugin list`. Las novedades de cada versión están en el [historial](../README.md#versiones).

## 🧩 Las seis skills

Cada petición entra por una sola skill; las demás se usan desde ella y se pasan el trabajo en ficheros del proyecto.

| | Skill | Para qué sirve | Entrega |
|:-:|---|---|---|
| 🔍 | `appian-reverse-engineering` | Documentar cómo está hecha una aplicación que ya existe, leyéndola en solo lectura por el Dev MCP | `as-is/`: funcional, datos, seguridad, procesos, pantallas, reglas… con su evidencia |
| 🧭 | `appian-refactorizacion` | Plantear cómo debería estar hecha, entera o una parte, con buenas prácticas | `refactorizacion/propuesta.md`: diagnóstico, solución por capas, migración y hoja de ruta |
| 📝 | `appian-functional-analyst` | Convertir las fuentes en el análisis funcional y la especificación técnica; llevar evolutivos y urgencias | DF en Word para el cliente y `analisis/tecnico.md` para construir |
| 🔀 | `appian-diagramas-bpmn` | Dibujar los procesos con notación BPMN y un carril por perfil, editables en la reunión | `.drawio`, PNG y BPMN 2.0 |
| 🎨 | `appian-prototipos` | Prototipos navegables con componentes SAIL reales y la marca del cliente o la de Appian | `prototipo/` navegable y capturas para el DF |
| ✅ | `appian-best-practices` | Las buenas prácticas oficiales de Appian para diseñar, construir, revisar y diagnosticar | Decisiones de solución, reglas por dominio y quality gates |

Incluye el MCP público de documentación de Appian: lo que una skill no sabe con certeza, lo consulta antes de escribirlo.

## 🧠 Cómo trabaja

<img src="assets/como-trabaja.svg" alt="Las fuentes del cliente entran al analista funcional, cada una con su informe de impacto. Una aplicación existente pasa antes por ingeniería inversa y, si se rehace, por refactorización. Del análisis salen el prototipo navegable, el DF en Word, con las capturas del prototipo, y la especificación técnica con la que se construye por el Dev MCP. Los procesos se dibujan con diagramas BPMN. Buenas prácticas orienta el análisis y el prototipo y revisa lo construido." width="100%">

## 🔧 Para quien desarrolla el plugin

<img src="assets/desarrollo.svg" alt="Siete pasos: git pull, cambios con Claude Code, probar, pasar las pruebas, subir la versión, push a main y la versión le llega al equipo." width="100%">

1. Empieza siempre con `git pull` en la carpeta del repositorio.
2. Haz los cambios con Claude Code abierto en esa carpeta.
3. Pruébalos sin instalar nada: `claude --plugin-dir .` carga el plugin tal como está en la carpeta; tras cada cambio, `/reload-plugins` o una sesión nueva.
4. Pasa las pruebas antes de cada commit: `python3 pruebas/comprobar_plugin.py --completo` (en Windows, `python`).
5. **Sube la versión** en `.claude-plugin/plugin.json` y añade su fila al principio de [Versiones](../README.md#versiones). Sin una versión nueva, el equipo no recibe los cambios.
6. Commit en español y push a `main`.

Las reglas del repositorio están en [`CLAUDE.md`](../CLAUDE.md): nada de un cliente ni datos personales en el plugin, y lo que genera el plugin al trabajar va en la carpeta de cada proyecto, nunca aquí.

## 🔒 Confidencialidad

Lo que genera el plugin al trabajar (fuentes, análisis, prototipos) se queda en la carpeta de cada proyecto y contiene información del cliente: no se sube a este repositorio. Los diagramas se dibujan con el navegador local y los prototipos usan siempre personas y datos ficticios.

<div align="center">
<br>
<sub>📖 Todo el detalle (requisitos, empaquetado, preguntas frecuentes y versiones) está en el <a href="../README.md">manual del plugin</a>.</sub>
</div>
