# Skills del repo en el equipo: cual en que paso

El mapa de las skills que el equipo tiene a mano y del paso de cada rol que
las usa. Es para quien cambia el loop y para el humano; el turno no lo necesita:
cada `roles/<rol>.md` cita la suya en su paso como skill `<nombre>`, con
cuando aplica, y el nucleo (`SKILL.md`, parrafo de skills de apoyo) dice como
se leen y como se anotan. `scripts/equipo-dev/pruebas.sh` (seccion `skills`)
compara esta tabla con el playbook y con `.claude/skills/VENDORIZADAS.md`.

## Mapa

`origen`: `propia` (del repo, con su archivo en el playbook), `vendorizada`
(copia fija de la cuenta, en `VENDORIZADAS.md`), `incorporada` (viene con
Claude Code; en OpenCode no existe) o `conector` (un MCP). `donde`: los
archivos del playbook que la citan en su paso, o `a mano:` con el motivo por
el que no entra al loop.

| skill | origen | donde | paso |
|---|---|---|---|
| `omc` | propia | `SKILL.md`, `roles/arquitecto.md`, `roles/dev.md`, `roles/revisor.md`, `roles/qa.md` | recetas: plan por consenso (Arquitecto), test que falla y primer filtro (Dev), revision en dos ejes (Revisor), verificacion (QA), diagnostico (P4) |
| `arena` | propia | `arena.md`, `roles/arquitecto.md`, `roles/dev.md` | un punto con enfoques genuinamente distintos |
| `find-skills` | propia | `skills.md` | buscar afuera lo que ni el repo ni estas skills resuelven |
| `replica-recon` | propia | `replica.md` | Investigador, familia 8: mapa de la referencia |
| `replica-diff` | propia | `replica.md` | Investigador, familia 8: `parity.py` |
| `replica-entrepreneur` | propia | `replica.md` | Investigador, familia 8: resenas |
| `test-driven-development` | vendorizada | `roles/dev.md` | Dev: el test de la logica pura, en rojo antes del codigo |
| `systematic-debugging` | vendorizada | `SKILL.md`, `roles/dev.md` | P4 (rojo sin causa obvia, primer intento) y Dev con `tipo: bug` |
| `verification-before-completion` | vendorizada | `SKILL.md` | principio 3: todo `estado:` que avanza y toda linea del informe |
| `testing-strategy` | vendorizada | `roles/arquitecto.md` | `## Diseno` de `tipo: tests` o con pagina, flujo o endpoint nuevo |
| `statistical-analysis` | vendorizada | `roles/arquitecto.md` | `## Diseno` con un numero o un umbral nuevo |
| `dataviz` | incorporada | `roles/arquitecto.md` | `## Diseno` con un grafico nuevo o cambiado |
| `modern-web-guidance` | vendorizada | `roles/dev.md` | Dev que escribe JSX o CSS en `frontend/src` |
| `ux-copy` | vendorizada | `roles/dev.md` | Dev que agrega o cambia texto que ve el usuario |
| `sql-queries` | vendorizada | `roles/dev.md` | Dev con un agregado que no sigue un patron vecino |
| `accessibility-review` | vendorizada | `roles/qa.md` | QA de una ficha que toca `frontend/src` |
| `design-critique` | vendorizada | `roles/qa.md` | QA de una ficha con pagina o panel nuevo |
| `validate-data` | vendorizada | `roles/qa.md` | QA de una ficha con un numero nuevo o cambiado |
| `engineering-code-review` | vendorizada | a mano: la revision del loop es la receta 2 de OMC con `revision.md` (ver abajo); a mano, `/engineering-code-review <PR>` le da al humano una segunda opinion | - |
| `code-review` | incorporada | a mano: el mismo motivo que `engineering-code-review` | - |
| `security-review` | incorporada | a mano: el eje de seguridad es `omc-security-reviewer`, con los disparadores de `revision.md` | - |
| `github` | conector | `roles/release.md`, `rutina.md` | Release: PRs y merge (`mcp__github__*`); sin el, "sin herramientas" |

Las otras del pack Replica quedan a mano por los motivos de la tabla de
`replica.md`. PO, Investigador (fuera de la familia 8) y Release no citan
ninguna: priorizan, buscan ideas o integran, y ninguna de estas les cambia el
trabajo. Revisor y QA juzgan con una vara fija y por eso no buscan afuera
(`skills.md`); una vendorizada si puede ser parte de esa vara, porque es una
copia fija con su sha256 en `VENDORIZADAS.md` y no cambia entre turnos.

## Cuando dos hacen lo mismo

- **Revisar el diff**: la receta 2 de OMC con `revision.md`, y no
  `engineering-code-review`, `code-review` ni `security-review`.
  `revision.md` es ciega al plan, trae las reglas duras de `CLAUDE.md` y usa
  la escala que decide el veredicto (un CRITICAL o HIGH es `corregir`); una
  segunda revision generica repetiria hallazgos con otra vara y otra escala,
  y la vara del Revisor tiene que ser la misma de un turno a otro.
- **Dar algo por hecho**: `verification-before-completion` es la disciplina
  de quien afirma (Dev, QA, Release, el informe); la receta 3
  (`omc-verifier`) es el auditor que la QA pone antes de `aprobado`. Una no
  reemplaza a la otra, y ninguna a `verificar.sh`.
- **Diagnosticar**: `systematic-debugging` en el primer intento, que hace el
  lider; la receta 4 (`omc-tracer`, `omc-debugger`) si ese intento no dio con
  la causa.
- **El test que falla primero**: en `tipo: bug`, `omc-test-engineer` propone
  que probar (receta 4) y el Dev lo escribe con el ciclo de
  `test-driven-development` (lo ve fallar, codigo minimo, lo ve pasar).
- **Buscar afuera**: `find-skills` no busca lo que una de estas ya cubre:
  graficos (`dataviz`), HTML, CSS y JS del navegador (`modern-web-guidance`),
  accesibilidad (`accessibility-review`), consultas (`sql-queries`) y como
  repartir los tests (`testing-strategy`).

## Las que no entran: Sentry

Las skills de Sentry (el plugin `sentry` de Claude Code, que se arma desde
https://github.com/getsentry/sentry-for-ai: sentry-get-started,
sentry-instrument, sentry-debug-issue y las demas) no se vendorizan, no
entran a ningun paso ni a este mapa, y find-skills no las trae ni las
propone para instalar (`skills.md`, "Filtrar"). Tampoco se instrumenta la
app con el SDK de Sentry ni con ningun otro reporte de errores o de uso a un
tercero. Por que: mandar los errores de la app a un servicio es telemetria,
un no-goal de `CLAUDE.md` (la app corre entera en el PC del usuario y nada
sale a la red sin un clic), y el SDK (`sentry-sdk`, `@sentry/react`) seria
una dependencia nueva en un backend que tiene `django` y `zstandard` y
punto. Su MCP tampoco es conector del loop: no hay proyecto de Sentry que
leer. Una idea de la app que lo pida va a "Ideas descartadas" de
`ALCANCE.md` con este motivo; cambiarlo es cambiar el no-goal, y eso lo
decide el humano en `CLAUDE.md`, no un turno.

`pruebas.sh` (seccion `sentry`) falla si aparece una skill de Sentry en
`.claude/skills/` (por carpeta o por `name:`), una fila suya en
`VENDORIZADAS.md`, el plugin o el MCP en la configuracion (`.claude/`,
`.mcp.json`, `opencode.json`) o el SDK en `requirements.txt`,
`requirements-dev.txt` o `frontend/package.json`.

## Registro

`Skills del repo: <skill> (<evidencia>), ... | ninguna` cierra la seccion de
la ficha que escribio el rol (`## Diseno`, `## Implementacion`, `## QA`),
igual que `OMC:`, y `**Skills del repo:**` suma las del turno en el informe.
La evidencia es lo que otro puede repetir: el comando que se vio en rojo
(`test-driven-development`), los ids de las guias aplicadas
(`modern-web-guidance`, que asi cumple su paso 4), los hallazgos por
severidad (`accessibility-review`), los valores recalculados contra la API
(`validate-data`). Una que se leyo y no cambio nada se anota igual, como
`<skill> (sin cambios: <por que>)`; `ninguna` es que no se leyo ninguna.

## Cambiar el mapa

Una skill entra a un paso con tres cosas en el mismo cambio: la cita en el
rol (skill `<nombre>`, cuando aplica y cuando no, y lo que el loop le cambia),
su fila aca y `pruebas.sh` en `PRUEBAS_OK`. Una que no esta en el repo se
vendoriza antes (`VENDORIZADAS.md`, "Como actualizarlas"); las incorporadas y
los conectores que el loop acepta son las listas `INCORPORADAS` y
`CONECTORES` de `pruebas.sh`. Como todo `.claude/`, lo mergea el humano.
