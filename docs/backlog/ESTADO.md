# Estado del equipo de desarrollo autonomo

actualizado: 2026-11-04 12:10 UTC por po (sesion 20261104T1206Z-c8cAo8L; motivo: papel vacio)
playbook: origin/dev@bcdbdf5
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 11 de 40 en 7 dias
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|

Vacia: la 73 entro a dev por [PR #72](https://github.com/bfigueroa99/r6-replay-lab/pull/72).

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=3 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=80 sin_merge=no pausa=no sin_rastro_48h=0 bloqueadas=0

## Orden de merge sugerido

Sin ramas abiertas.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): DEV_7D=funcionalidad:6 (65-presencia-y-delta-por-operador 66-copiar-resumen-de-partida 70-mapas-por-version 71-version-del-mapa-en-la-partida 72-apertura-marcada-en-la-timeline 73-catalogo-y10s4-a-y11s1) otros:3
- Epicas en curso: temporada-y-modo: A4 (70) y A6 (71) en dev, A8 (74) en papel. paridad-referencia: R1 (64) y R4 (72) en dev, R2 (75) en papel. impacto: K3 (55) y K5 (59) en dev, K10 (76) en papel. datos-nuevos-del-parser: P1 (73) en dev.
- Papel: PAPEL_TIPOS=funcionalidad:3 otros:0 (propuesto y disenado; la directiva pide 3 funcionalidades antes de tests sueltos). Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 80 ideas libres (78 al empezar, 3 pasaron a ficha). Ideas nuevas de este turno: B18 prorroga por lado, D8 cuantas de tus muertes son headshot, E13 la primera partida despues de un descanso, O8 que operador eliges segun el marcador, R6 dos partidas lado a lado.
- Investigacion: ultima entrada 2026-11-03 (familias 8, 3, 5 y 6). Paridad con la referencia 79.4 / 100, must 14 de 17.
- Rotacion: ROTACION=saturadas (4 o mas de las ultimas 10): ninguna | sin entrega: ninguna
- Ciclo: CICLO=8h de reclamo a dev, mediana de las ultimas 10 funcionalidades (ficha:horas 73:8 72:7 71:38 70:8 66:4 65:6 64:8 63:12 62:8 61:32)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 74-version-del-mapa-en-el-resto-de-pantallas | propuesto | funcionalidad | temporada-y-modo | 2 | backend | - |
| 75-trades-de-los-dos-equipos | propuesto | funcionalidad | paridad-referencia | 2 | frontend | - |
| 76-aperturas-sin-trade | propuesto | funcionalidad | impacto | 3 | backend | - |
| 49-mapas-rehechos-mezclan-lados | descartado (premisa falsa) | bug | temporada-y-modo | 2 | backend | - |

3 `propuesto`, 0 `disenado`: el proximo disparo es Arquitecto (regla 9). Orden sugerido: 74 (sin migracion, tramo escrito por la 70), 75 (sin migracion, `should` de la referencia), 76 (migracion + `recompute` en `RoundPlayer`). Candidatos anotados por turnos anteriores, todavia sin ficha: `seed_demo` con `opening_kill`/`opening_death`/`entry_kill` coherentes con sus eventos (72), singular "1 baja / 1 muerte" y aviso "Copiado" (66), detalles de `DeltaLado` (65), `seed_demo` siembra Ranked 4-3 que la regla no cierra (68), `retag` imprime las filas del ID entero por cada nombre viejo (73, cosmetico).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-11-04 08:14 | (mismo turno que la QA) Entrega y mergea la 73: `aprobado` -> `entregado` -> [PR #72](https://github.com/bfigueroa99/r6-replay-lab/pull/72) -> dev bcdbdf5. Puerta a-f cumplida: dev, revisor y qa de contextos distintos, dev ec263c3 ya en la rama, `verificar.sh` VERDE 55a1c5c8d (882 backend, 153 vitest, 54 e2e). Espejo quitado de `backlog`. Borrar la rama: el clasificador nego `git push --delete` (queda en `BORRAR`). `pruebas.sh`: PRUEBAS_OK (18). |
| dev | 2026-11-04 00:20 | Implementa 73 (funcionalidad p2, `disenado` -> `implementado`, 9fbef62): Solid Snake (ataque), `FortressY10` y `Y10S4`/`Y11S1` en `constants.py`; IDs sinteticos en `test_retag.py` como pedia el diseno; 6 tests en `test_pydissect.py` y `RetagCatalogoNuevoTests` (3); docs en `formato-rec.md` y README. Revision ciega: 1 LOW (comentario) arreglado. `verificar.sh` VERDE cb26bbf12 (882 backend, 153 vitest, 54 e2e). |
| revisor | 2026-11-04 04:12 | Revisa 73 (funcionalidad p2, `implementado` -> `revisado`, 23a0eb0). Rama ya al dia con dev ec263c3; `verificar.sh` VERDE e4785f1 (882 backend, 153 vitest, 54 e2e). Revision a ciegas (estandares): aprobar, sin hallazgos; confirmado que `CODE_VERSIONS` no la lee el parser, que `FortressY10` comparte slug y etiqueta "(Y10)", que nada mapea nombres de operador y que el cambio de IDs en `test_retag.py` es solo de valor. |
| qa | 2026-11-04 08:14 | Prueba 73 (funcionalidad p2, `revisado` -> `aprobado`, 5106b4f). `verificar.sh` VERDE bcc1edd97 (882 backend, 153 vitest, 54 e2e). Base de `factories` con Fortress rehecho y Solid Snake como `Unknown`/`Solidsnake`: `retag --dry-run` 1 partida y 2 filas sin tocar la base, `retag` las nombra, segunda corrida y `unknown_ids` sin nada. API: `/api/filters/` con "Fortress (Y10)" y "Solid Snake"; bordes y base vacia en 200. 4 mutaciones caen. OMC verifier: PASS. |
| arquitecto | 2026-11-03 16:40 | Disena 73 (`propuesto` -> `disenado`): cuatro entradas en `constants.py` (Solid Snake de ataque, `FortressY10`, `Y10S4`/`Y11S1` en `CODE_VERSIONS`), tests en `test_pydissect.py` y `RetagCatalogoNuevoTests`, docs en `formato-rec.md` y README. Hallazgo: `test_retag.py` usa justo `398899676157`/`444310693746` como IDs desconocidos; catalogarlos tumba 8 tests (spike sobre ec263c3), y moverlos a IDs sinteticos `999000000001/2` deja la suite verde. Sin arena ni consenso (forma unica), sin pushes de codigo. |
| investigador | 2026-11-03 20:17 | Familias 8 (pasada semanal: `clone` al dia con dev ec263c3, 5 filas; paridad 76.1 -> 79.4, must 14 de 17; referencia sin cambios y 0 resenas), 3, 5 y 6. Siete ideas nuevas en `ALCANCE.md` (71 -> 78 libres): A9, B17, H8, H9, K10, K11 y P7, cada una con fuente abierta. Sin pushes de codigo. |
| po | 2026-11-04 12:10 | Papel vacio. Propone 74 (A8: version del mapa en mejor y peor mapa del Inicio, Clutch por mapa y sitio, Mapas que mejoran y el CSV de partidas; tramo que dejo escrito la 70), 75 (R2: trades de los dos equipos en el detalle de partida, `should` de la referencia) y 76 (K10: aperturas ganadas limpias y perdidas vengadas, del rating de Siege.GG 2026). `ALCANCE.md`: A6, R4 y P1 `en dev` (71, 72, 73); nuevas B18, D8, E13, O8 y R6: 80 libres (78 al empezar). Sin pushes de codigo. |

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca. La lista larga anterior, con las preguntas que respondiste el 2026-10-28, esta en `git log` de este archivo: commit 440e6a1.)

- Ramas borrables (el proxy y el clasificador de la nube cortan `git push --delete`; pegar en tu PC): BORRAR: git push origin --delete claude/confident-feynman-dc9apf claude/equipo-dev/30-tests-ganador-de-ronda claude/equipo-dev/31-tests-stats-por-jugador claude/equipo-dev/32-days-enorme-da-500 claude/equipo-dev/33-fecha-con-zona-da-500 claude/equipo-dev/34-trade-kill-contado-doble claude/equipo-dev/35-tests-lado-de-los-equipos claude/equipo-dev/36-mitades-y-prorroga claude/equipo-dev/37-rivales-repetidos claude/equipo-dev/38-dos-ganadores-por-ronda claude/equipo-dev/39-inercia-entre-rondas claude/equipo-dev/40-hora-y-dia-de-la-semana claude/equipo-dev/41-ronda-segun-el-marcador claude/equipo-dev/42-como-se-cierran-tus-rondas claude/equipo-dev/43-match-point claude/equipo-dev/44-records-personales claude/equipo-dev/45-remontadas-y-derrumbes claude/equipo-dev/46-primero-de-tu-equipo-en-caer claude/equipo-dev/47-modos-desconocidos-en-datos claude/equipo-dev/48-posts-sin-json-desde-otra-pagina claude/equipo-dev/50-partidas-cerradas-y-holgadas claude/equipo-dev/51-matriz-de-duelos-de-la-partida claude/equipo-dev/52-rondas-cortas-y-largas claude/equipo-dev/53-multikills-por-tamano claude/equipo-dev/54-solo-duo-o-stack claude/equipo-dev/55-clutch-intentos-y-conversion claude/equipo-dev/56-mapas-y-operadores-que-mejoran claude/equipo-dev/57-teamkills claude/equipo-dev/58-primera-ronda-de-cada-mitad claude/equipo-dev/59-clutch-por-mapa-y-sitio claude/equipo-dev/60-racha-de-rondas claude/equipo-dev/61-clutch-por-operador claude/equipo-dev/62-cuando-matas claude/equipo-dev/63-cuando-llega-la-apertura claude/equipo-dev/64-partidas-en-el-inicio claude/equipo-dev/65-presencia-y-delta-por-operador claude/equipo-dev/66-copiar-resumen-de-partida claude/equipo-dev/67-teamkills-fuera-de-las-bajas claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado claude/equipo-dev/69-clutch-cuenta-con-abandonos claude/equipo-dev/70-mapas-por-version claude/equipo-dev/71-version-del-mapa-en-la-partida claude/equipo-dev/72-apertura-marcada-en-la-timeline claude/equipo-dev/73-catalogo-y10s4-a-y11s1
- Verificar en el PC (73, en dev por PR #72): `manage.py retag --dry-run` (lista `Unknown(398899676157) -> Fortress` y las filas de Solid Snake), `retag`, `unknown_ids` (ya no muestra esos dos IDs); Mapas con "Fortress (Y10)" aparte y el equipo de Solid Snake atacando en sus rondas de ataque.
- Verificar en el PC (69, en dev por PR #71): `manage.py backup`, `recompute --dry-run` (cuenta las filas de 1vX que cambian; solo partidas anteriores a Y9S1 con abandonos) y `recompute`.
- Verificar en el PC (68, en dev por PR #66): `manage.py recompute --dry-run` ("... y N partidas (resultado)", pocas) y `recompute`; esas partidas salen `incompleta` y dejan de contar en el winrate de partidas.
- Verificar en el PC (67, en dev por PR #64): `manage.py backup`, `recompute --dry-run`, `recompute` y otra vez `recompute` ("Nada que recalcular"); K/D, KPR y rating bajan solo donde hubo teamkills. El `.exe` no corre `recompute` (aviso en la ficha).
- PRs que esperan tu merge contra dev: ninguno. Promover a main cuando quieras: RELEASE=dev lleva 96 commits que main no tiene (promover: https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1).
- Verificar en el PC (66): en Electron (`npm run desktop`), "Copiar resumen" en una partida y pegar.
- Entorno cloud (qa 20261026T2004Z): `check.sh` ya elige solo el Chromium de la imagen (`E2E_CHROMIUM`); correr `npx playwright test` suelto sin esa variable falla con `Executable doesn't exist`.
- Verificar en el PC (34, 38, 47, 55; traen migracion o tocan el parser, ya en main desde el PR #62): `manage.py backup`, `migrate`, `recompute --dry-run` (sin cambios de `clutch_vs`), `recompute`; para 38, `import_replays --force <carpeta>`; para 47, `unknown_ids` y `retag --dry-run`. Detalle en cada ficha. **Despues de bajar main, `cd frontend; npm run build`.**
- Verificar en el PC (Investigador, r6-dissect #130 e idea P5): replays Y11S3 con los dos equipos ganadores en una ronda (`my_team_won` podria salir al reves) y Y11S2 con jugadores duplicados o bajas de gente que no esta. Si tenes esos `.rec`, importalos y avisa. Nuevo (2026-11-03, idea P7): el parche Y11S3.3 de hoy aplica la privacidad del jugador al scoreboard; con un replay posterior, mira en Partidas o Rivales si algun rival sale con nick generico.
- Calibrar con la base real (umbrales solo probados con datos sinteticos): 30 rondas de Tendencias (39), 10 rondas por fila de Progreso (56, bajar `COMPARE_MIN_ROUNDS_FILA` a 8 si casi nada sale), records 6/20 (44), tramos de 45 s (52), 5 partidas para "habitual" (54), `CLUTCH_SITIO_MIN` (59) y `CLUTCH_OPERADOR_MIN` (61), 5 cada uno; cortes 30/90 s de "Cuándo llega la apertura" (63, `APERTURA_TEMPRANA`/`APERTURA_TARDIA`); 3 partidas por mapa para mejor y peor mapa del Inicio (64, `MIN_PARTIDAS_MAPA`, quiza 5).
- Tests dependientes del orden (preexistente): `python manage.py test tests.test_import_job tests.test_ajustes` da 4 fallos en `VigilanteTests`; la suite completa pasa. Candidato a ficha `tests`.
- Turnos con permisos negados (po 20261019T0325Z, release 20261020T0804Z y 20261024T0804Z): el clasificador nego correr `turno.sh`/`estado.sh`; si se repite, la rutina necesita permiso para `bash` sobre `scripts/equipo-dev/*.sh`.
- PRs abiertos que no son del equipo y no se tocan: #24, #22, #14, #11 y #1-#4. La rama `claude/bold-cori-6gcxh9` (sin PR) toca `aggregates.py` y `seed_demo.py`: si la mergeas, el choque lo resuelve el equipo (P3).
- CI remota: GitHub Actions no ejecuta pasos desde 2026-09-11. Lo que vale es `check.sh` local. (Aviso unico.)


## Para el equipo

(Escribe aca el humano. El equipo no borra ni edita este bloque; responde debajo con fecha.)

- 2026-10-28 (humano, respondido en una sesion de Claude Code): decisiones sobre las preguntas de `## Para el humano`.
  - Ficha 53 (teamkills): excluirlos de `kills`. Bajas, K/D, KPR, rating, 2K/3K y ACE cuentan solo rivales; los teamkills siguen en su metrica aparte (ficha 57). Va a ficha propia, con `recompute` y `metricas.md` al dia.
  - Ficha 50 / G7 (ultimo `.rec` faltante): `won=None` cuando el marcador final no cierra la partida segun `reglas_partida`; esas partidas salen de los winrates. Va a ficha propia.
  - Ficha 31 (1vX con `PLAYER_LEAVE`): si cuenta. El que se fue esta fuera de la ronda (como ya lo toma `clutch_vs`, ficha 55), asi que el ultimo vivo que gana suma su 1vX.
  - Ficha 49 (mapas rehechos): separar cada version en su propia fila ("Consulate (Y10)"), agrupando por `Match.map_id` como proponia la ficha, sin migracion. Va a ficha propia.
  - Ficha 38: sigue mandando la cabecera. Nada que cambiar.
  - Ficha 48: la frase de `CLAUDE.md` ya dice que todos los POST exigen `application/json` (PR #61, en dev). `/api/import/` sigue exigiendo JSON.
  - Release: dev promovido a main (PR #62, c9a2d6c). El `npm run build` y `release.ps1` los corre el humano en el PC.
- 2026-10-28 16:20 (dev 20261028T1607Z): leido. Son decisiones para fichas nuevas; las abre el PO en su proximo turno (el Dev no escribe fichas de funcionalidad). Nada de esto toca la 66.
- 2026-10-28 16:53 (revisor 20261028T1644Z): leido. La 66 (ahora `revisado`) no cambia por estas decisiones, salvo la fila "Mejor ronda" de `metricas.md`, que dice "teamkills incluidos": la ficha de teamkills tiene que corregirla (anotado en la 66 y en el Papel). Saque de `ESTADO.md` un bloque viejo duplicado que estaba desde 2026-10-15 entre `## Para el humano` y este bloque, con las preguntas que respondiste: `estado.sh` lo tomaba por `## Para el equipo` y no mostraba este. Las fichas nuevas las abre el PO en su proximo turno (regla 7).
- 2026-10-29 00:40 (po 20261029T0004Z): abiertas las fichas de tus decisiones: 67 (teamkills fuera de `kills`, prioridad 1), 68 (`won=None` con marcador que no cierra), 69 (1vX con `PLAYER_LEAVE`) y 70 (mapas por version, `map_id`, etiqueta "(Y10)"). Fichas 38 y 48: nada que abrir. La 49 queda descartada como bug (historia); la 70 la reemplaza como funcionalidad.
