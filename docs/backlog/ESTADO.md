# Estado del equipo de desarrollo autonomo

actualizado: 2026-11-18 13:01 UTC por qa, release, revisor, dev, arquitecto (sesion 20261118T1211Z-cMNRUxv; motivo: por estado: 1 revisado; sigue: por estado: 1 implementado; sigue: por estado: 2 disenado, lugar en cola; sigue: por estado: 6 propuesto, 2 disenado de 3)
playbook: origin/dev@2611d85
rutina: TURNOS_SIN_RASTRO=11 en 48 h (~11-16T15:13Z ~11-16T19:13Z ~11-16T23:14Z ~11-17T03:14Z ~11-17T07:14Z ~11-17T11:14Z ~11-17T15:14Z ~11-17T19:14Z ~11-17T23:14Z ~11-18T03:14Z ~11-18T07:14Z) | 25 de 42 en 7 dias
en vacio: TURNOS_EN_VACIO=0 de 0 en 48 h | 0 de 17 en 7 dias (turnos que no dejaron otro commit que ESTADO.md)
issues: ISSUES=bfigueroa99/r6-replay-lab: 0 abiertos | pedidos 0 | en curso 0 | esperando a una persona 0 | para cerrar o verificar 0 | ignorados 0 | sin confianza 0; triados en este turno: ninguno
pausa: no

## Cola (items con codigo, esperando al humano o en trabajo)

| rama | ficha | estado | horas sin commits | PR / compare |
|---|---|---|---|---|
| claude/equipo-dev/136-prorroga-marcada-en-el-detalle | docs/backlog/136-prorroga-marcada-en-el-detalle.md | con hallazgos | 82 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/136-prorroga-marcada-en-el-detalle?expand=1) |
| claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa | docs/backlog/138-el-sitio-con-el-que-abres-la-defensa.md | revisado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa?expand=1) |
| claude/equipo-dev/139-rondas-perdidas-sobreviviendo | docs/backlog/139-rondas-perdidas-sobreviviendo.md | implementado | 0 | [compare](https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/139-rondas-perdidas-sobreviviendo?expand=1) |
| claude/equipo-dev/79-excluir-una-partida-de-los-agregados | docs/backlog/79-excluir-una-partida-de-los-agregados.md | entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano) | 110 | [PR #81](https://github.com/bfigueroa99/r6-replay-lab/pull/81) |

COLA=4 (tope 4)  TOTAL=4 (tope 6)
RESUMEN propuesto=4 disenado=3 en_curso=0 huerfanas=0 implementado=0 revisado=0 con_hallazgos=1 aprobado=0 entregado=0 espera_humano=1 cola=4 total=4 tope_cola=4 tope_total=6 tope_propuesto=6 tope_disenado=3 ideas_libres=103 sin_merge=no pausa=no sin_rastro_48h=11 bloqueadas=2 pedidos=0

(`implementado=0` y `revisado=0` porque este contexto implemento la 139 y reviso la 138: las cuenta `bloqueadas=2`; para la proxima sesion son tomables.)

## Orden de merge sugerido

`git merge-tree --write-tree` por pares entre 136, 138, 139 y 79, y de cada una con `origin/dev` 2611d85 (con la 137): sin conflictos (todas salen 0).

1. `claude/equipo-dev/138-el-sitio-con-el-que-abres-la-defensa` (revisado, falta QA de otra sesion).
2. `claude/equipo-dev/139-rondas-perdidas-sobreviviendo` (implementado, falta revision de otra sesion).
3. `claude/equipo-dev/136-prorroga-marcada-en-el-detalle` (con hallazgos: un Major de contraste en la marca de prorroga; lo arregla un Dev de otra sesion). Libera la 140.
4. `claude/equipo-dev/79-excluir-una-partida-de-los-agregados` (PR #81, lo mergea el humano: toca `CLAUDE.md`). Libera la 83 y la 109.

## Alcance

- Funcionalidades que llegaron a `dev` en los ultimos 7 dias (`DEV_7D`): DEV_7D=funcionalidad:28 (102-pool-de-operadores-por-lado 107-sitio-que-tu-equipo-repite-tras-perderlo 110-tu-forma-contra-tu-historial 111-copiar-las-senales-del-coach 112-saltar-a-la-ronda-desde-los-records 113-repetir-o-cambiar-de-operador-tras-perder 114-que-operadores-te-abren 115-prorroga-por-lado 116-en-que-estado-de-vivos-mueres 118-ver-esas-rondas-desde-el-coach 119-mejor-y-peor-partida-de-cada-sesion 120-puesto-en-el-lobby 121-copiar-una-ronda-como-texto 122-cuando-te-toco-por-ultima-vez 123-clutches-de-tus-companeros 124-partidas-por-version-del-juego 125-teamkill-marcado-en-la-timeline 126-a-que-operador-cambias-tras-perder 127-partidas-que-van-a-prorroga 128-repetir-o-cambiar-el-spawn-tras-perder 129-filtro-de-operador-en-operadores 130-saltar-a-la-siguiente-ronda-perdida 131-rondas-que-el-equipo-gano-sin-ti 132-rivales-que-se-repiten-en-la-misma-noche 133-ventaja-numerica-tirada 134-en-que-estado-de-vivos-matas 135-partida-despues-de-perder-seguido 137-cuantas-de-tus-muertes-son-headshot) otros:3 (fichas que llegaron a dev en 7 dias)
- Epicas en curso: rivales: 137 en dev (PR #140), 147 disenado (tramo 2). impacto: 134 en dev, 143 disenado. revision-de-rondas: 139 implementado, 136 con hallazgos, 140 disenado (frenada por 136). posicionamiento: 138 revisado. escuadra: 141 disenado, 109 disenado (frenada), 144 propuesto. progreso: 146 propuesto. lado-y-marcador: 145 propuesto. operadores: 142 propuesto. datos: 79 entregado (PR #81), 83 disenado (frenada).
- Papel: PAPEL_TIPOS=funcionalidad:10 otros:0 (propuesto y disenado; la directiva pide 3 funcionalidades antes de tests sueltos). Cola: COLA_TIPOS=funcionalidad:4 de 4 ramas de trabajo
- `ALCANCE.md`: ALCANCE=backlog, ideas libres: 103. Ideas nuevas de este turno: D21 (Tú contra tus compañeros en puntos, en Muertes por headshot) y T10 (encabezado de fila en las tablas, `idea (deuda)`), las dos de la QA de la 137.
- Investigacion: INVESTIGACION=backlog, ultima entrada: 2026-11-09.
- Rotacion: ROTACION=saturadas (4 o mas de las ultimas 10): pagina Duelos.jsx | sin entrega: ninguna. `Duelos.jsx` quedo saturada con la 137: el PO no suma tarjetas ahi hasta que rote (la 143 y la 147 ya venian propuestas con Duelos).
- Ciclo: CICLO=0h de reclamo a dev, mediana de las ultimas 10 funcionalidades (ficha:horas 137:105 134:26 135:0 132:0 131:0 128:0 129:4 133:1 127:0 130:2)

## Papel (rama backlog)

| ficha | estado | tipo | epica | prioridad | area | candado |
|---|---|---|---|---|---|---|
| 109-quien-te-venga | disenado | funcionalidad | escuadra | 3 | - | - |
| 136-prorroga-marcada-en-el-detalle | con hallazgos | funcionalidad | revision-de-rondas | 3 | - | - |
| 138-el-sitio-con-el-que-abres-la-defensa | revisado | funcionalidad | posicionamiento | 3 | fullstack | - |
| 139-rondas-perdidas-sobreviviendo | implementado | funcionalidad | revision-de-rondas | 3 | fullstack | - |
| 140-ventaja-tirada-marcada-en-el-detalle | disenado | funcionalidad | revision-de-rondas | 3 | - | - |
| 141-companeros-que-pierden-vivos | disenado | funcionalidad | escuadra | 3 | fullstack | - |
| 142-operadores-con-los-que-mueres-solo | propuesto | funcionalidad | operadores | 3 | - | - |
| 143-quien-cierra-la-ronda | disenado | funcionalidad | impacto | 3 | fullstack | - |
| 144-companeros-por-lado | propuesto | funcionalidad | escuadra | 3 | - | - |
| 145-ultima-ronda-antes-del-cambio-de-lado | propuesto | funcionalidad | lado-y-marcador | 3 | - | - |
| 146-que-mapas-te-tocan | propuesto | funcionalidad | progreso | 3 | - | - |
| 147-headshots-que-recibes-por-operador-rival | disenado | funcionalidad | rivales | 3 | fullstack | - |
| 79-excluir-una-partida-de-los-agregados | entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano) | funcionalidad | datos | 3 | - | - |
| 83-partidas-excluidas-en-partidas-y-datos | disenado | funcionalidad | datos | 3 | - | - |

FRENADAS=3 (la 109 espera a la 79; la 140 espera a la 136; la 83 espera a la 79) | disenado que esperan a una ficha que no esta en dev: no cuentan en disenado= de RESUMEN

Espejos: 137 sale del papel (en dev, PR #140); 138 (revisado) y 139 (implementado) al dia en este turno; 79 vive en su rama, que manda.

## Ultimo turno de cada rol

| rol | fecha-hora UTC | que hizo |
|---|---|---|
| release | 2026-11-18 12:30 | (release 20261118T1211Z-cMNRUxv, siguiendo como QA) 137: ficha recortada con `## PR`, `Entrega: 137`, VERDE 04e408687 (1404, 459, 122) sobre el commit exacto con dev fusionado (el primer intento cayo con `That port is already in use` en el e2e, contencion del contenedor compartido; repetido, verde), [PR #140](https://github.com/bfigueroa99/r6-replay-lab/pull/140) abierto, comentario de CI respondido y mergeado (2611d85). Borrado de la rama: cortado por el proxy, sale en BORRAR. |
| qa | 2026-11-18 12:22 | (qa 20261118T1211Z-cMNRUxv, por estado: 1 revisado) 137 `revisado` -> `aprobado`: VERDE ede9b1244 (1404, 459, 122), base sembrada desde `factories.py` (teamkills, rival sobre rival, victima sin fila, partida de un jugador, nick repetido, muerte sin dato), Tú total 7/5/4 y compañeros ataque 5/4/2 recalculados en SQL iguales a la API, 25 bordes en 200, Playwright sin Critical ni Major, 4 mutaciones caen, verificacion PASS (fallback del lider). Ideas D21 y T10. |
| revisor | 2026-11-18 12:40 | (revisor 20261118T1211Z-cMNRUxv, sigue) 138 `implementado` -> `revisado`: merge de dev (con la 137) sin conflicto, VERDE 1f3455da2 (1417, 463, 123); sondas de prorroga y de bordes de la API, 3 mutaciones que caen; sin hallazgos. Sin subagentes: revision del lider. |
| dev | 2026-11-18 12:55 | (dev 20261118T1211Z-cMNRUxv, sigue) 139 `disenado` -> `implementado`: `lost_alive` en `/api/rounds/lost-alive/` (3 consultas fijas), panel "Rondas perdidas sobreviviendo" en Tendencias con tabla por lado, por mapa y las 10 mas recientes con enlace a la ronda; 11 tests Django + 4 vitest + 1 e2e, TDD con rojo visto, 2 mutaciones que caen; VERDE cdd077c56 (1415, 463, 123). Sin subagente para la revision ciega del Dev. |
| arquitecto | 2026-11-18 13:00 | (arquitecto 20261118T1211Z-cMNRUxv, sigue) Disena 147 (`headshot_deaths_by_operator` en `/api/duels/`, tabla "Por operador rival" dentro del panel de la 137, con `diff` contra tu total; consulta probada sobre `seed_demo`: 6 operadores, Rook 28 %, +3) y 143 (`closing_kills` en `/api/duels/closing/`, ultima baja del feed por ronda, `unknown` aparte; componente propio para no pisar a la 147 en `Duelos.jsx`; clasificacion probada sobre `seed_demo`). |
| investigador | 2026-11-09 20:40 | (investigador 20261109T2004Z-cQbf8yt, reloj) Familias 1, 2, 4 y 7 con cuatro subagentes. Siete ideas nuevas con fuente abierta (B21, K13, D15, D16, F20, F21, P8) y fuentes nuevas en P3 y P5; nueve descartadas con motivo. Senal fuerte: el fork prestonwillis10 de r6-dissect decodifica arma, loadout y dano (pregunta al humano). Sin pushes de codigo. |
| po | 2026-11-14 03:44 | (po 20261114T0316Z-cwWsU9i, sigue) Propone 147 (headshots que recibes por operador rival, D20, tramo de la 137: implementar despues de #137). Reconcilia D13, E6 y F24 en dev y los espejos de 134 y 137. Ideas nuevas K16 (estado al matar de tus compañeros) y E23 (muertes por headshot en el tiempo). |

## Para el humano

(Solo lo que el humano tiene que decidir o hacer, bajo el tope de `PARA_EL_HUMANO`. Un aviso que no bloquea de una ficha ya en `dev` queda en la ficha, no aca.)

- DESTRABA: ficha 79, entregado (PR pendiente de merge: toca CLAUDE.md, lo mergea el humano), 110 h sin commits | frena a: 109 83 | https://github.com/bfigueroa99/r6-replay-lab/compare/dev...claude/equipo-dev/79-excluir-una-partida-de-los-agregados?expand=1
- Release: RELEASE=dev lleva 32 commits que main no tiene (promover: https://github.com/bfigueroa99/r6-replay-lab/compare/main...dev?expand=1). Al publicar: en el PC `cd frontend; npm run build`, la lista "Verificar en el PC" de abajo y `.\scripts\release.ps1`.
- Ramas borrables (el proxy de la nube corta `git push --delete`; en este turno tambien la de la 137): BORRAR: git push origin --delete claude/confident-feynman-dc9apf claude/equipo-dev/30-tests-ganador-de-ronda claude/equipo-dev/31-tests-stats-por-jugador claude/equipo-dev/32-days-enorme-da-500 claude/equipo-dev/33-fecha-con-zona-da-500 claude/equipo-dev/34-trade-kill-contado-doble claude/equipo-dev/35-tests-lado-de-los-equipos claude/equipo-dev/36-mitades-y-prorroga claude/equipo-dev/37-rivales-repetidos claude/equipo-dev/38-dos-ganadores-por-ronda claude/equipo-dev/39-inercia-entre-rondas claude/equipo-dev/40-hora-y-dia-de-la-semana claude/equipo-dev/41-ronda-segun-el-marcador claude/equipo-dev/42-como-se-cierran-tus-rondas claude/equipo-dev/43-match-point claude/equipo-dev/44-records-personales claude/equipo-dev/45-remontadas-y-derrumbes claude/equipo-dev/46-primero-de-tu-equipo-en-caer claude/equipo-dev/47-modos-desconocidos-en-datos claude/equipo-dev/48-posts-sin-json-desde-otra-pagina claude/equipo-dev/50-partidas-cerradas-y-holgadas claude/equipo-dev/51-matriz-de-duelos-de-la-partida claude/equipo-dev/52-rondas-cortas-y-largas claude/equipo-dev/53-multikills-por-tamano claude/equipo-dev/54-solo-duo-o-stack claude/equipo-dev/55-clutch-intentos-y-conversion claude/equipo-dev/56-mapas-y-operadores-que-mejoran claude/equipo-dev/57-teamkills claude/equipo-dev/58-primera-ronda-de-cada-mitad claude/equipo-dev/59-clutch-por-mapa-y-sitio claude/equipo-dev/60-racha-de-rondas claude/equipo-dev/61-clutch-por-operador claude/equipo-dev/62-cuando-matas claude/equipo-dev/63-cuando-llega-la-apertura claude/equipo-dev/64-partidas-en-el-inicio claude/equipo-dev/65-presencia-y-delta-por-operador claude/equipo-dev/66-copiar-resumen-de-partida claude/equipo-dev/67-teamkills-fuera-de-las-bajas claude/equipo-dev/68-partidas-sin-cerrar-sin-resultado claude/equipo-dev/69-clutch-cuenta-con-abandonos claude/equipo-dev/70-mapas-por-version claude/equipo-dev/71-version-del-mapa-en-la-partida claude/equipo-dev/72-apertura-marcada-en-la-timeline claude/equipo-dev/73-catalogo-y10s4-a-y11s1 claude/equipo-dev/74-version-del-mapa-en-el-resto-de-pantallas claude/equipo-dev/75-trades-de-los-dos-equipos claude/equipo-dev/76-aperturas-sin-trade claude/equipo-dev/77-selector-de-tipo-de-partida claude/equipo-dev/78-filtros-en-el-listado-de-partidas claude/equipo-dev/80-donde-quedas-fuera-de-posicion claude/equipo-dev/81-textos-de-la-ui-sin-tildes claude/equipo-dev/82-partida-sin-rondas-rompe-el-detalle claude/equipo-dev/84-enlace-a-partida-inexistente-culpa-a-django claude/equipo-dev/85-filtro-sin-rondas-esconde-la-barra claude/equipo-dev/86-duelos-dice-0-rondas-con-rondas-sin-duelos claude/equipo-dev/87-readme-con-conteos-de-tests-viejos claude/equipo-dev/88-textos-del-backend-sin-tildes claude/equipo-dev/89-salida-del-spawn-por-mapa claude/equipo-dev/90-stacks-rivales-repetidos claude/equipo-dev/91-fases-de-la-ronda-en-la-partida claude/equipo-dev/92-stack-rival-en-la-partida claude/equipo-dev/93-operador-por-sitio claude/equipo-dev/94-racha-actual-de-partidas claude/equipo-dev/95-partida-anterior-y-siguiente claude/equipo-dev/96-filtros-en-la-url claude/equipo-dev/97-clutches-silenciosos claude/equipo-dev/98-lado-inicial-por-mapa claude/equipo-dev/99-copiar-resumen-de-sesion claude/equipo-dev/100-modo-de-juego-como-dimension claude/equipo-dev/101-dos-partidas-lado-a-lado claude/equipo-dev/102-pool-de-operadores-por-lado claude/equipo-dev/103-tira-de-rondas-en-partidas claude/equipo-dev/104-hilo-de-importacion-ensucia-otros-tests claude/equipo-dev/105-url-con-byte-nulo-tumba-la-spa claude/equipo-dev/106-ruta-unc-en-la-spa claude/equipo-dev/107-sitio-que-tu-equipo-repite-tras-perderlo claude/equipo-dev/110-tu-forma-contra-tu-historial claude/equipo-dev/111-copiar-las-senales-del-coach claude/equipo-dev/112-saltar-a-la-ronda-desde-los-records claude/equipo-dev/113-repetir-o-cambiar-de-operador-tras-perder claude/equipo-dev/114-que-operadores-te-abren claude/equipo-dev/115-prorroga-por-lado claude/equipo-dev/116-en-que-estado-de-vivos-mueres claude/equipo-dev/117-hotfix-graficos-punteados claude/equipo-dev/118-ver-esas-rondas-desde-el-coach claude/equipo-dev/119-mejor-y-peor-partida-de-cada-sesion claude/equipo-dev/120-puesto-en-el-lobby claude/equipo-dev/121-copiar-una-ronda-como-texto claude/equipo-dev/122-cuando-te-toco-por-ultima-vez claude/equipo-dev/123-clutches-de-tus-companeros claude/equipo-dev/124-partidas-por-version-del-juego claude/equipo-dev/125-teamkill-marcado-en-la-timeline claude/equipo-dev/126-a-que-operador-cambias-tras-perder claude/equipo-dev/127-partidas-que-van-a-prorroga claude/equipo-dev/128-repetir-o-cambiar-el-spawn-tras-perder claude/equipo-dev/129-filtro-de-operador-en-operadores claude/equipo-dev/130-saltar-a-la-siguiente-ronda-perdida claude/equipo-dev/131-rondas-que-el-equipo-gano-sin-ti claude/equipo-dev/132-rivales-que-se-repiten-en-la-misma-noche claude/equipo-dev/133-ventaja-numerica-tirada claude/equipo-dev/134-en-que-estado-de-vivos-matas claude/equipo-dev/135-partida-despues-de-perder-seguido claude/equipo-dev/137-cuantas-de-tus-muertes-son-headshot
- Verificar en el PC (97): `manage.py backup`, `migrate` (0005_roundplayer_clutch_kills), `recompute --dry-run` sin filas nuevas por `clutch_kills`; en Compañeros, Silenciosos con numeros creibles (no 100 % en todas las filas).
- Calibrar con la base real (138, revisada): el corte de 5 partidas por apertura de defensa (`APERTURA_DEFENSA_MIN_PARTIDAS`), puesto con datos sinteticos.
- Rutina: 11 disparos sin rastro en 48 h (~11-16T15:13Z a ~11-18T07:14Z, cada 4 h); revisar el historial de la Routine del equipo (la que lleva `r6-replay-lab` en el nombre). Este turno lo lanzo una sesion de orquestacion, no la Routine.
- CI remota: GitHub Actions no ejecuta pasos (los jobs mueren en segundos, tambien en el PR #140). Lo que vale es `check.sh` local. (Aviso unico; no se repite por turno.)

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
- 2026-11-05 (humano, respondido en su sesion de Claude Code; llego en el disparo del PO): respuestas a `## Para el humano`.
  1. Ficha 76: "apertura devuelta" = (a), el trade del evento (lo ya disenado). No cambia nada del diseno.
  2. POST nuevos: se permiten los tres. E2 (metas personales), F2 (notas por ronda) y G2 (excluir una partida de los agregados) pasan a `idea`; cada POST entra a la lista de POST permitidos de `CLAUDE.md` cuando su ficha se disene, con las mismas reglas (local, exige `application/json`).
  3. PRs #1, #2, #3, #4, #11, #14, #22 y #24 contra `main`: cerrados sin merge, con comentario. Sus ideas vuelven a `idea` (incluidas Posicionamiento del #1 y spawn peeks del #22). Las ramas no se borraron.
  4. Promocion `dev` -> `main`: autorizada. La abre y la fusiona la sesion del humano al cerrar la tanda (~04:15 UTC); el equipo no la toca.
- 2026-11-05 02:40 (po 20261105T0230Z-c8Ahepa): registrado. (1) Ficha 76: respuesta en `## Para el humano` del espejo y de su rama (7e6415c, solo docs; la 76 ya estaba `implementado` y sin candado). (2) `ALCANCE.md`: E2, F2 y G2 en `idea`; G2 ya es la ficha 79, que pide sumar su POST a `CLAUDE.md`. (3) Ideas de los PRs cerrados en `ALCANCE.md`: A10 filtros en la URL, E14 racha actual, F15 "Ver esas rondas" desde las señales, F16 filtros en Partidas (ficha 78), F17 partida anterior/siguiente y flechas, S1 fuera de posicion (ficha 80) y S2 salida del spawn con enlace a peekabooR6; vigia e pick rate ya estaban cubiertos (I2, O5); los `mercado/*` ya estaban; #11 y #24 eran maquinaria. (4) Notas de la release y "Verificar en el PC" listos en `## Para el humano`.
