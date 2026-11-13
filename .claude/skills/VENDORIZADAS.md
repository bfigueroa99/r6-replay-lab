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
| `test-driven-development` | superpowers | 6.4.2 | [obra/superpowers](https://github.com/obra/superpowers) tag `v6.4.2`, commit `8ca22db` | MIT | 2026-11-12 | `19157c32f1d83a9406b12263cf7cf05f591ac6277ded66caa153dc02441d4d5b` |
| `systematic-debugging` | superpowers | 6.4.2 | [obra/superpowers](https://github.com/obra/superpowers) tag `v6.4.2`, commit `8ca22db` | MIT | 2026-11-12 | `b78499fa79099bc4142a6219e33e79d61ab196e8cce82a9d34f12af76f14b673` |
| `verification-before-completion` | superpowers | 6.4.2 | [obra/superpowers](https://github.com/obra/superpowers) tag `v6.4.2`, commit `8ca22db` | MIT | 2026-11-12 | `c11152e82b0770839e941c5fc4d6665a1c11f8b1e8b9f9d14cda90ee6be6ab60` |
| `engineering-code-review` | engineering | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `59ea1d011784d4806112c2abc2ff573cfa13ab686db1704826c637e55ffba950` |
| `testing-strategy` | engineering | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `633ef3e19cc3344b234035ce52aedcfd460cdebb485afb6de85c37c4e48ce883` |
| `accessibility-review` | design | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `8f8cf23fa51f2fa38da6830cbb5d1e7c6ef1852fcd159cafa0829f93bac84427` |
| `design-critique` | design | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `265e654ffc0db40cc3b6f58fc1ab8c3e607681261bf5840c83a215da1f042360` |
| `ux-copy` | design | 1.2.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `82c878ddc1d98482d4b384eabe30cdc45f21b32313508102d53d6bf96d1b8097` |
| `modern-web-guidance` | modern-web-guidance | 0.0.194 | [GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance) commit `b31dc0a` (Release v0.0.194) y npm `modern-web-guidance@0.0.194` | Apache-2.0 | 2026-11-12 | `e0ee391c95ac503790a07c4c9f84b7dc6e842604eaf8d8a508b759d2d5858a6c` |
| `validate-data` | data | 1.1.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `17a8bb548663d00c9e9d4fd247d934f91df55efcfd404c92029faa611c69ec47` |
| `statistical-analysis` | data | 1.1.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `e03e102dcc8b552ca3ef7a5173f1df576100ae100f4793fd9b164b0666e1d5fb` |
| `sql-queries` | data | 1.1.0 | [anthropics/knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins) commit `877a617` | Apache-2.0 | 2026-11-12 | `1c361a07ac8e11e1e4735887ca09ef849f95456aefe7b478776a5bed9359b75b` |

## Cambios respecto del original

- **Todas:** `disable-model-invocation: true` en el frontmatter, por la regla del repo para las skills de afuera (`.claude/skills/equipo-dev/skills.md`, seccion "Usar"). No se activan solas: se invocan con `/<nombre>` o se leen por su ruta. El resto del contenido es el original salvo lo que dice esta lista.
- **`LICENSE.txt`:** cada una lleva el de su plugin (superpowers, MIT; knowledge-work-plugins, Apache-2.0; modern-web-guidance, Apache-2.0).
- **engineering y design** no traen `LICENSE` en la copia de la cuenta. Llevan el Apache-2.0 de knowledge-work-plugins tal como esta en sus carpetas `data/` y `product-management/`, que es el mismo `LICENSE` de la raiz en el commit inicial (`7c35640`). El de la raiz en `main` no se usa: desde `d6c8015` (#193) trae texto ajeno pegado al final de la licencia.
- **`engineering-code-review`:** renombrada (carpeta y `name`) porque `code-review` choca con la skill que trae Claude Code. Su texto sigue diciendo `/code-review`: en este repo se invoca `/engineering-code-review`, y `/code-review` es la de Claude Code.
- **`sql-queries`, `statistical-analysis`:** sin `user-invocable: false`. Junto con `disable-model-invocation: true` la skill no se podia cargar de ninguna forma salvo por su ruta; asi queda `/<nombre>` para quien la pida.
- **`modern-web-guidance`:** la CLI va fijada en `modern-web-guidance@0.0.194` en vez de `@latest` (es la version de npm cuyo `SKILL.md` trae `--skill-version 2026_10_12-dacb5911`, el de esta copia) y con `DISABLE_TELEMETRY=1` delante de cada comando: por defecto la CLI manda telemetria de uso a Google, y la regla del repo es CLI fija y sin telemetria. Las guias estan en `guides/` y se leen sin red; la copia de la cuenta no trae la CLI (`modern-web.mjs`, el indice y el modelo de busqueda), que `npx` baja de npm. La copia de la cuenta difiere de la de GitHub y de npm solo en el formato YAML de `description`.

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
