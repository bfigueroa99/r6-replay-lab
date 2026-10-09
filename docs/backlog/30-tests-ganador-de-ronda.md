# 30. Tests de quien gana la ronda y por que

estado: entregado
candado: -
rama: claude/equipo-dev/30-tests-ganador-de-ronda
area: parser
prioridad: 2
fuente: hueco de tests en pydissect: `events.round_end` y `events.read_defuser_timer` no tienen ningun test (main dc0188b; el unico que los ejercita es `RealReplayTests`, que se salta sin `R6_TEST_REPLAY`)
archivos: backend/tests/test_round_end.py
turnos: po 20261008T0302Z, arquitecto 20261008T0602Z, dev 20261008T0902Z, revisor 20261008T1202Z, qa 20261008T1802Z, release 20261009T0002Z

## PR

**Titulo:** `[equipo-dev][tests] Tests de quien gana la ronda y por que`

### Que cambia

Agrega `backend/tests/test_round_end.py`: 14 tests sin `.rec` sobre
`events.round_end` y `events.read_defuser_timer`, de donde salen el winrate,
la condicion de victoria de cada ronda y las rondas por tiempo. Hasta ahora un
cambio ahi pasaba la suite en verde; ahora un refactor del parser o una
temporada nueva no puede romper el ganador de la ronda en silencio. No cambia
codigo de la app.

### Por que esto y no otra cosa

Ficha 30 (hueco de tests en `pydissect/`). Se descarto una fixture binaria:
un lector falso que toma los accesos del `Reader` real ejercita la misma
logica sin archivos.

### Como se probo

- `./scripts/check.sh` sobre la rama fusionada con main: `Todo en verde.`
  (ruff ok, 380 tests backend, 53 vitest, build ok, 17 e2e).
- Antes de Y9S4: eliminacion por KILL y por DEATH, plant sin desactivar,
  desactivar despues del plant, defensa por tiempo con los dos ordenes de roles.
- Y9S4+: el marcador decide (aunque el feed diga lo contrario), se compara
  contra el marcador inicial de la ronda, gana el equipo 1 si el 0 no sube,
  condicion por eliminacion o por tiempo, fuera de bomba no inventa condicion.
- Reloj del defuser: plant y despues desactivar; id desconocido no agrega eventos.
- Autor de la KILL corregido por el marcador.
- Mutaciones del Dev, del Revisor y de QA (19 en total) sobre `events.py`:
  todas caen salvo un mutante equivalente documentado.

### Riesgos y lo que no entra

Sin migraciones, sin `recompute`, sin frontend: solo un archivo de test. No
se toca `pydissect/`. El bug de Y9S4 con `DEFUSER_DISABLE_COMPLETE` (abajo)
queda sin test a proposito: afirmarlo lo congelaria.

### Como probarlo en 2 minutos

```
cd backend
python manage.py test tests.test_round_end -v 2   # 14 tests ok
```

### Para el humano

Aviso, no bloquea: en Y9S4+, con la cabecera dando la ronda al equipo 0 y un
`DEFUSER_DISABLE_COMPLETE` de un jugador del 1, `round_end` deja a los dos
equipos con `won=True`. Hay que decidir si manda la cabecera o el feed; es
candidato a ficha aparte.

### Candidatos descubiertos

Ninguno en `propuesto` todavia (el bug de arriba queda para el PO).

## Que gana quien usa la app

El winrate, la condicion de victoria y las rondas "por tiempo" salen de
`round_end`; con estos tests un cambio en el parser no puede romperlos en
silencio.

## Criterios de aceptacion

- [x] Previo a Y9S4, 5 muertes (KILL o DEATH) -> el rival gana con `KilledOpponents`.
- [x] Plant sin desactivar -> `DefusedBomb`; desactivado -> `DisabledDefuser`.
- [x] Sin muertes ni defuser -> gana la defensa con `Time`.
- [x] Y9S4+ en bomba: el marcador decide; condicion por eliminacion o tiempo.
- [x] `read_defuser_timer` agrega START/COMPLETE de plant y de disable.
- [x] KILL con `usernameFromScoreboard` queda con el autor corregido.

## Implementacion, Revision y QA (resumen; el detalle esta en `git log`)

- Dev 20261008T0902Z (a63d828, a65069c): `LectorFalso` + 11 tests; tests de
  Y9S4 rehechos tras la revision ciega para que solo los pase el marcador.
- Revisor 20261008T1202Z sobre 0de3a3c: aprobar. Hallazgo corregido con 2
  tests (marcador contra el inicial de la ronda; gana el 1 si el 0 no sube).
- QA 20261008T1802Z sobre 6e48e43: aprobado. 10 mutaciones propias; agrego
  `test_y9s4_fuera_de_bomba_el_marcador_decide_sin_inventar_condicion`.
- Release 20261009T0002Z: `check.sh` en verde sobre la rama con main dc0188b.

## Verificar en el PC

No hace falta: solo agrega tests.

## Para el humano

- (Arquitecto, aviso) Bug de Y9S4+ con `DEFUSER_DISABLE_COMPLETE`: los dos
  equipos quedan `won=True` (ver `## PR`). Candidato a ficha aparte.
