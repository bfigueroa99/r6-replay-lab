# Estado del equipo de desarrollo autonomo

actualizado: 2026-10-28 20:40 UTC por qa + release (sesion 20261028T2004Z; motivo: por estado: 1 revisado; reloj: investigador, franja 7)
playbook: origin/dev@8802635 (pruebas: ok)
rutina: TURNOS_SIN_RASTRO=0 en 48 h | 7 de 43 en 7 dias; sin herramientas para comparar el prompt
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

Vacia. La 66 se mergeo a dev en este turno ([PR #63](https://github.com/bfigueroa99/r6-replay-lab/pull/63), c3597f4).

RELEASE=dev lleva 13 commits que main no tiene (promover: https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1)

COLA=0/4  TOTAL=0/6
RESUMEN propuesto=0 disenado=0 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=0 aprobado=0 entregado=0 espera_humano=0 cola=0 total=0 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=68 sin_merge=no pausa=no sin_rastro_48h=0

## Orden de merge sugerido

Nada abierto.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): DEV_7D=funcionalidad:10 (56-mapas-y-operadores-que-mejoran 57-teamkills 59-clutch-por-mapa-y-sitio 60-racha-de-rondas 61-clutch-por-operador 62-cuando-matas 63-cuando-llega-la-apertura 64-partidas-en-el-inicio 65-presencia-y-delta-por-operador 66-copiar-resumen-de-partida) otros:0 (fichas que llegaron a dev en 7 dias)
- Epicas en curso: exportar: H4 (66) en dev, H7 la reusa. paridad-referencia: R1 (64) en dev, R2-R5 idea. operadores: O6 (61) y O5 (65) en dev, O1 tramo siguiente.
- Papel: PAPEL_TIPOS=funcionalidad:0 otros:0 (propuesto y disenado). Cola: COLA_TIPOS=funcionalidad:0 de 0 ramas de trabajo.
- `ALCANCE.md`: 68 ideas libres (H4 marcada `en dev (PR #63)`).
- Investigacion: ultima entrada 2026-10-24. Proxima: 3, 5 y 6.
- Rotacion: ROTACION=saturadas (4 o mas de las ultimas 10): ninguna | sin entrega: exportar datos-nuevos-del-parser paridad-referencia
- Ciclo: CICLO=12h de reclamo a dev, mediana de las ultimas 10 funcionalidades (ficha:horas 66:4 65:6 64:8 63:12 62:8 61:32 59:12 57:12 56:12 60:44)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 49-mapas-rehechos-mezclan-lados | descartado (premisa falsa) | bug | temporada-y-modo | 2 | backend | - |

0 `propuesto`, 0 `disenado`. Proximo turno: PO (regla 7, papel vacio): abre las fichas de las decisiones del humano del 2026-10-28 (bloque de abajo: teamkills fuera de `kills`, `won=None` con marcador que no cierra, 1vX con `PLAYER_LEAVE`, mapas por version); la de teamkills corrige tambien la fila "Mejor ronda" de `metricas.md` que trajo la 66. Candidato a ficha chica: singular "1 baja / 1 muerte" en la linea de stats del resumen y aviso "Copiado" que no se borra (ficha 66, `## Para el humano`).

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-10-28 20:40 | (mismo turno que la QA) Entrega y mergea la 66: `aprobado` -> `entregado` -> [PR #63](https://github.com/bfigueroa99/r6-replay-lab/pull/63) -> dev c3597f4. Puerta a-f cumplida: dev, revisor y qa de tres sesiones, `check.sh` en verde sobre el head 5e506c5. Ficha recortada con `## PR`; espejo quitado de `backlog`, H4 `en dev`. `pruebas.sh`: PRUEBAS_OK (14). Borrar la rama: el clasificador nego `git push --delete` (queda en `BORRAR`). |
| dev | 2026-10-28 16:20 | Implementa 66 (`disenado` -> `implementado`, rama `claude/equipo-dev/66-copiar-resumen-de-partida`, f3a6e0e): `resumenPartida.js` puro (cinco lineas, 10 vitest), boton "Copiar resumen" con aviso en `MatchDetail.jsx`, e2e con portapapeles real, seccion nueva en `metricas.md`. Revision ciega: corregir dos (rondas sin ganador contaban como perdidas; numeros sin definicion); corregidos. `check.sh` en `Todo en verde.` (811 backend, 130 vitest, build, 53 e2e). |
| revisor | 2026-10-28 16:53 | Revisa 66 (funcionalidad, `implementado` -> `revisado`) sobre f3a6e0e, dev 2857aa6 ya incluido. `check.sh` en `Todo en verde.` antes y despues (811 backend, 130 vitest, build, 53 e2e). Revision a ciegas por el lider (sin herramienta de subagentes): aprobar. Contra la API real: `textoResumenPartida` sobre el detalle de las 29 partidas de `seed_demo`, sin `undefined`/`NaN` y con ganadas por lado y mejor ronda cuadrando. Mutacion: 4 de 5 caen; el test del singular de "Mejor ronda" pasaba con el bug ("1 bajas" contiene "1 baja"): el Revisor lo ajusto (compara la linea entera), 78ccd81. Menor anotado, no bloquea: la linea de stats dice "1 bajas / 1 muertes" (test exacto en la ficha). Limpieza de `ESTADO.md`: saco el bloque viejo duplicado que desde 2026-10-15 colgaba de una cabecera `## Para el equipo` rota (`estado.sh` lo leia como `## Para el equipo` y contaba mal `PARA_EL_HUMANO`); queda en `git log` (440e6a1). |
| qa | 2026-10-28 20:30 | Prueba 66 (funcionalidad, `revisado` -> `aprobado`) sobre 52e46d0 (dev 8802635 integrado). `check.sh` en `Todo en verde.` (811 backend, 130 vitest, build, 53 e2e); chunk inicial igual que dev. Base vacia y `seed_demo` con `runserver` y `curl`; Chromium copiando el resumen de las partidas 29, 1 y 15, cruzado con `/api/matches/<id>/`; portapapeles que rechaza, ausente y sin permiso: aviso en la pagina, consola limpia; el click no hace requests. Mutacion: tres, las tres caen. Friccion menor anotada en la ficha. |
| arquitecto | 2026-10-27 16:11 | Disena 64 (`matches_summary` en la vista de `/api/overview/`: partidas elegidas sin `side` como `by_margin`, `match_winrate` sobre `won` no nulo, `rounds_per_match`, mejor y peor mapa por `map_slug` con `MIN_PARTIDAS_MAPA = 3`, peor solo si esta por debajo del mejor; fila de cuatro `Stat3` en el Inicio), 65 (`presence_pct` y `winrate_delta` en `by_operator`, base del lado antes de `min_rounds`, delta nulo sin rondas con `my_team_won`, sin banda de ruido; columnas "Presencia" y "vs. tu lado") y 66 (`resumenPartida.js` puro con el texto exacto de cinco lineas, boton "Copiar resumen" con `navigator.clipboard`, e2e con `grantPermissions`). Numeros del e2e calculados sobre `seed_demo`. Sin arena, sin migracion, sin pushes de codigo. |
| investigador | 2026-10-24 20:12 | Familia 8, primera pasada de Replica contra r6-replay.com y Aurelix (recon completo de paginas publicas, sin cuenta ni capturas): `replica/recon.md`, `features.csv` (61 filas, 21 skip con motivo), `parity.md` (76.1 / 100, must 12 de 17), resenas 0 en 8 fuentes (`feedback.md`, `fixes.md`). Epica nueva `paridad-referencia` con R1-R4 (63 -> 67 libres). Sin pushes de codigo. |
| po | 2026-10-27 12:40 | Papel vacio: propone 64 (R1: partidas ganadas, rondas por partida y mejor y peor mapa en el Inicio), 65 (O5: presencia y delta de winrate contra tu lado en Operadores) y 66 (H4: copiar el resumen de una partida al portapapeles). `ALCANCE.md` reconciliado (61-63 en main), nuevas E12, O7, H7 y R5: 68 libres (67 al empezar). Sin pushes de codigo. |

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca. La lista larga anterior, con las preguntas que respondiste el 2026-10-28, esta en `git log` de este archivo: commit 440e6a1.)

- Ramas borrables (el proxy y el clasificador de la nube cortan `git push --delete`; pegar en tu PC): BORRAR: git push origin --delete claude/confident-feynman-dc9apf claude/equipo-dev/30-tests-ganador-de-ronda claude/equipo-dev/31-tests-stats-por-jugador claude/equipo-dev/32-days-enorme-da-500 claude/equipo-dev/33-fecha-con-zona-da-500 claude/equipo-dev/34-trade-kill-contado-doble claude/equipo-dev/35-tests-lado-de-los-equipos claude/equipo-dev/36-mitades-y-prorroga claude/equipo-dev/37-rivales-repetidos claude/equipo-dev/38-dos-ganadores-por-ronda claude/equipo-dev/39-inercia-entre-rondas claude/equipo-dev/40-hora-y-dia-de-la-semana claude/equipo-dev/41-ronda-segun-el-marcador claude/equipo-dev/42-como-se-cierran-tus-rondas claude/equipo-dev/43-match-point claude/equipo-dev/44-records-personales claude/equipo-dev/45-remontadas-y-derrumbes claude/equipo-dev/46-primero-de-tu-equipo-en-caer claude/equipo-dev/47-modos-desconocidos-en-datos claude/equipo-dev/48-posts-sin-json-desde-otra-pagina claude/equipo-dev/50-partidas-cerradas-y-holgadas claude/equipo-dev/51-matriz-de-duelos-de-la-partida claude/equipo-dev/52-rondas-cortas-y-largas claude/equipo-dev/53-multikills-por-tamano claude/equipo-dev/54-solo-duo-o-stack claude/equipo-dev/55-clutch-intentos-y-conversion claude/equipo-dev/56-mapas-y-operadores-que-mejoran claude/equipo-dev/57-teamkills claude/equipo-dev/58-primera-ronda-de-cada-mitad claude/equipo-dev/59-clutch-por-mapa-y-sitio claude/equipo-dev/60-racha-de-rondas claude/equipo-dev/61-clutch-por-operador claude/equipo-dev/62-cuando-matas claude/equipo-dev/63-cuando-llega-la-apertura claude/equipo-dev/64-partidas-en-el-inicio claude/equipo-dev/65-presencia-y-delta-por-operador claude/equipo-dev/66-copiar-resumen-de-partida
- PRs que esperan tu merge contra dev: ninguno. Promover a main cuando quieras: RELEASE=dev lleva 13 commits que main no tiene (https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1).
- Verificar en el PC (66): en Electron (`npm run desktop`), "Copiar resumen" en una partida y pegar.
- Entorno cloud (qa 20261026T2004Z): `check.sh` ya elige solo el Chromium de la imagen (`E2E_CHROMIUM`); correr `npx playwright test` suelto sin esa variable falla con `Executable doesn't exist`.
- Verificar en el PC (34, 38, 47, 55; traen migracion o tocan el parser, ya en main desde el PR #62): `manage.py backup`, `migrate`, `recompute --dry-run` (sin cambios de `clutch_vs`), `recompute`; para 38, `import_replays --force <carpeta>`; para 47, `unknown_ids` y `retag --dry-run`. Detalle en cada ficha. **Despues de bajar main, `cd frontend; npm run build`.**
- Verificar en el PC (Investigador, r6-dissect #130 e idea P5): replays Y11S3 con los dos equipos ganadores en una ronda (`my_team_won` podria salir al reves) y Y11S2 con jugadores duplicados o bajas de gente que no esta. Si tenes esos `.rec`, importalos y avisa.
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
