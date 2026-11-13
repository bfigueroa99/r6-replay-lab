# Skills vendorizadas

Copias de skills de la cuenta del dueno (plugins de Claude y skills de Anthropic), pedidas el
2026-11-12 para que esten en el repo aunque la sesion no tenga esos plugins: OpenCode con OmniRoute
(que lee `.claude/skills/`), una sesion local u otro equipo. Las skills propias del repo y las que
ya tenian su registro (pack Replica, arena, find-skills, omc) no van en esta tabla.

El origen se verifico archivo por archivo: el hash de blob de git de cada archivo de la copia de
la cuenta coincide con el del commit citado (`git ls-tree` sobre el repo publico), salvo donde la
lista de abajo dice otra cosa.

| Skill | Plugin | Version | Origen publico | Licencia | Copia | sha256 del SKILL.md (como quedo) |
|---|---|---|---|---|---|---|
| `test-driven-development` | superpowers | 7.0.2 | [obra/superpowers](https://github.com/obra/superpowers) tag `v7.0.2`, commit `22f0b46` | MIT | 2026-11-13 | `19157c32f1d83a9406b12263cf7cf05f591ac6277ded66caa153dc02441d4d5b` |
| `systematic-debugging` | superpowers | 7.0.2 | [obra/superpowers](https://github.com/obra/superpowers) tag `v7.0.2`, commit `22f0b46` | MIT | 2026-11-13 | `3e417e4a7bf639eb73dc5e673d2129451e666cf5ed9f53d9b55059dad29e4f6d` |
| `verification-before-completion` | superpowers | 7.0.2 | [obra/superpowers](https://github.com/obra/superpowers) tag `v7.0.2`, commit `22f0b46` | MIT | 2026-11-13 | `c11152e82b0770839e941c5fc4d6665a1c11f8b1e8b9f9d14cda90ee6be6ab60` |
| `engineering-code-review` | engineering | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `59ea1d011784d4806112c2abc2ff573cfa13ab686db1704826c637e55ffba950` |
| `testing-strategy` | engineering | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `633ef3e19cc3344b234035ce52aedcfd460cdebb485afb6de85c37c4e48ce883` |
| `accessibility-review` | design | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `8f8cf23fa51f2fa38da6830cbb5d1e7c6ef1852fcd159cafa0829f93bac84427` |
| `design-critique` | design | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `265e654ffc0db40cc3b6f58fc1ab8c3e607681261bf5840c83a215da1f042360` |
| `ux-copy` | design | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `82c878ddc1d98482d4b384eabe30cdc45f21b32313508102d53d6bf96d1b8097` |
| `modern-web-guidance` | modern-web-guidance | 1.0.0 | [GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) tag `v1.0.0`, commit `4dd9683`, y npm `modern-web-guidance@1.0.0` | Apache-2.0 | 2026-11-13 | `a04951c080388d691cb2a9cac90c6b2fef0ebcec374d4eb3526159e384b3ca2e` |
| `validate-data` | data | 1.1.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `17a8bb548663d00c9e9d4fd247d934f91df55efcfd404c92029faa611c69ec47` |
| `statistical-analysis` | data | 1.1.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `e03e102dcc8b552ca3ef7a5173f1df576100ae100f4793fd9b164b0666e1d5fb` |
| `sql-queries` | data | 1.1.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `1c361a07ac8e11e1e4735887ca09ef849f95456aefe7b478776a5bed9359b75b` |

## Cambios respecto del original

- **Todas:** `disable-model-invocation: true` en el frontmatter, por la regla del repo para las skills de afuera (`.claude/skills/equipo-dev/skills.md`, seccion "Usar"). No se activan solas: se invocan con `/<nombre>` o se leen por su ruta. El resto del contenido es el original salvo lo que dice esta lista.
- **`LICENSE.txt`:** cada una lleva el de su plugin (superpowers, MIT; knowledge-work-plugins, Apache-2.0; modern-web-guidance, Apache-2.0).
- **engineering y design** no traen `LICENSE` en la copia de la cuenta. Llevan el Apache-2.0 de knowledge-work-plugins tal como esta en sus carpetas `data/` y `product-management/`, que es el mismo `LICENSE` de la raiz en el commit inicial (`7c35640`). El de la raiz en `main` no se usa: desde `d6c8015` (#193) trae texto ajeno pegado al final de la licencia.
- **`engineering-code-review`:** renombrada (carpeta y `name`) porque `code-review` choca con la skill que trae Claude Code. Su texto sigue diciendo `/code-review`: en este repo se invoca `/engineering-code-review`, y `/code-review` es la de Claude Code.
- **`sql-queries`, `statistical-analysis`:** sin `user-invocable: false`. Junto con `disable-model-invocation: true` la skill no se podia cargar de ninguna forma salvo por su ruta; asi queda `/<nombre>` para quien la pida.
- **`modern-web-guidance`:** la CLI va fijada en `modern-web-guidance@1.0.0` en vez de `@latest` (es la version de npm cuyo `SKILL.md` trae `--skill-version 2026_11_09-5bcc021b`, el de esta copia) y con `DISABLE_TELEMETRY=1` delante de cada comando del `SKILL.md`: por defecto la CLI manda telemetria de uso a Google, y la regla del repo es CLI fija y sin telemetria. Las guias estan en `guides/` y se leen sin red; sus remisiones internas (`npx -y modern-web-guidance@latest retrieve "<id>"`) quedan como upstream y se siguen con la version fija o leyendo `guides/**/<id>.md`. Desde 1.0.0 la copia sale de GitHub (`skills/modern-web-guidance/` en el tag `v1.0.0`), que es identica a la carpeta del paquete de npm 1.0.0 sin su CLI (`modern-web.mjs`, `search.mjs`, `gen/`, `legacy-scan.mjs`, `watchdog/`), que `npx` baja de npm; la cuenta seguia en 0.0.194.
- **`systematic-debugging`:** desde 7.0.2 no trae `CREATION-LOG.md` ni `test-academic.md` ni `test-pressure-1.md` a `-3.md`: upstream los saco porque eran prompts de prueba de presion ("This is a real scenario. You must choose and act") que se instalaban junto al `SKILL.md`, y un turno que lee la carpeta los podia tomar por instrucciones.

## Ultima verificacion contra upstream

2026-11-13, con los repos publicos clonados en el commit citado:

- superpowers `v7.0.2` (`22f0b46`): `test-driven-development` y `verification-before-completion` sin cambios desde 6.4.2; `systematic-debugging` cambia dos lineas (el ejemplo de diagnostico por capas imprimia el valor del secreto con `${IDENTITY:-UNSET}` y `env | grep`; ahora solo `SET`/`UNSET`) y saca los cinco archivos de prueba de arriba.
- modern-web-guidance `v1.0.0` (`4dd9683`): `SKILL.md` reescrito (consultas de 2 a 5 palabras sobre una sola primitiva, partir las compuestas, nombrar la primitiva implicita; seccion final `### Modern Web Guidance` con los ids aplicados), 28 guias nuevas (entre ellas `copy-button`, `sortable-table`, `tabs`, `dialog`, `menu`, `card`), 124 cambiadas y 6 borradas.
- knowledge-work-plugins `43ccfc0`: ninguna de las skills de engineering, design y data de la tabla cambio desde `877a617`; las filas quedan como estaban.

## Como actualizarlas

1. Copiar de nuevo a una carpeta aparte, desde los plugins de la cuenta
   (`~/.claude/plugins/synced/…/skills/`, `~/.claude/skills/synced/…/`) o desde el repo publico en
   el commit nuevo.
2. Comparar con la del repo (`diff -r`) y leer el diff entero: una skill es texto que el modelo sigue.
3. Volver a aplicar los cambios de arriba, recalcular el sha256 (`sha256sum .claude/skills/<skill>/SKILL.md`)
   y poner al dia la fila: version, commit, fecha y sha256.
4. En `modern-web-guidance`, fijar la version de npm cuyo `SKILL.md` trae el mismo `--skill-version`.

Nunca `npx skills update` ni un instalador que reescriba la carpeta: pisaria `disable-model-invocation`
y los demas cambios.

## Nombres de superpowers

Dentro del texto, las skills de superpowers se nombran entre si con el prefijo del plugin
(`superpowers:test-driven-development`, `superpowers:verification-before-completion`,
`superpowers:writing-skills`). En este repo se llaman sin el prefijo
(`test-driven-development`, `systematic-debugging`, `verification-before-completion`), y `writing-skills` no esta copiada.
