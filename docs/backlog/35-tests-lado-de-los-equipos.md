# 35. Tests de como el parser decide que equipo ataca

estado: entregado
candado: -
rama: claude/equipo-dev/35-tests-lado-de-los-equipos
tipo: tests
epica: -
area: tests
prioridad: 3
fuente: hueco de tests en `pydissect/header.py`: `derive_team_roles` solo la ejercitaba `RealReplayTests`, que se salta sin `R6_TEST_REPLAY` (en la nube y en `check.sh` siempre).
archivos: backend/tests/test_pydissect.py
turnos: po 20261010T0301Z, arquitecto 20261010T0602Z, dev 20261010T1501Z, revisor 20261012T1202Z, dev 20261012T1503Z, revisor 20261012T1640Z (QA sin revisado en cola), dev 20261012T2101Z, revisor 20261013T0002Z, qa 20261013T0302Z, release 20261013T0413Z

## PR

**Titulo:** `[equipo-dev][tests] Tests de como el parser decide que equipo ataca`

### Que cambia

Doce tests nuevos para `derive_team_roles`, la funcion que decide que equipo ataca y cual defiende. Hoy ningun test que corre la cubria; baja el riesgo de que un cambio en el parser, o una temporada con operadores nuevos, invierta ataque y defensa (y con eso todo lo que se filtra por lado) sin que nada avise.

### Por que esto y no otra cosa

Ficha 35: hueco de tests visto en `pydissect/header.py`. Se descarto usar `.rec` reales o fixtures binarias: un lector falso (`SimpleNamespace`) alcanza y corre en todos lados. No cambia codigo de `pydissect/`.

### Como se probo

- `./scripts/check.sh`: 468 tests backend (4 saltados), 65 vitest, build ok, 23 e2e. `Todo en verde.`
- Tests nuevos (`LadoDeLosEquiposTests` en `backend/tests/test_pydissect.py`):
  - `test_el_equipo_con_operadores_de_ataque_ataca`, `test_el_atacante_puede_ser_el_equipo_1`: lado por mayoria, con el atacante en cualquiera de los dos `teamIndex`.
  - `test_gana_la_mayoria_aunque_cada_equipo_tenga_de_los_dos_lados`, `test_los_defensores_de_mas_restan_aunque_empaten_en_atacantes`, `test_los_defensores_de_mas_del_equipo_1_tambien_restan`, `test_los_atacantes_de_mas_suman_aunque_empaten_en_defensores`: el puntaje es ataque menos defensa y votan los dos equipos.
  - `test_el_jugador_con_operador_0_se_descarta`: sale de `players` y del `scoreboard`.
  - `test_operador_con_nombre_y_sin_lado_hereda_el_de_su_equipo`, `test_el_recluta_no_se_anota_como_operador_nuevo`, `test_un_id_sin_nombre_se_anota_como_unknown`: `inferredOperatorSides`.
  - `test_sin_operadores_conocidos_no_hay_lado_y_avisa`: sin `role` y con `log.warning`.
  - `test_el_tear_down_vacia_el_registro_de_ids_desconocidos`: los tests no dejan IDs en `overrides.unknown_ids()`.
- Mutaciones sobre `header.py` (revision y QA): caen todas salvo `>=` por `>` en el desempate, fuera de alcance a proposito.

### Riesgos y lo que no entra

Sin migraciones, sin `recompute`, sin frontend, sin cambios de parser. Fuera: la regla de desempate (`score0 >= score1`), `read_header` y `gamemode_name`.

### Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_pydissect.LadoDeLosEquiposTests -v 2   # 12 tests OK
python manage.py test tests.test_pydissect --reverse                    # sin estado entre tests
```

### Para el humano

Dos avisos, no bloquean: (1) `inferredOperatorSides` anota tambien los IDs sin nombre como `"Unknown(<id>)"`; el test lo documenta tal cual. (2) Si los dos equipos empatan en puntaje ataca el equipo 0; no se testea para no fijarlo. Cualquiera de los dos, si queres cambiarlo, es otra ficha.

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Trabajo interno: el lado de cada equipo, y todo lo que se filtra por ataque y defensa, depende de esta funcion. Ahora un test avisa si se invierte.

## Criterios de aceptacion

- [x] Mayoria de operadores de ataque conocidos -> `Attack`, tambien con el atacante en `teamIndex` 1.
- [x] Jugador con operador 0 fuera de `header["players"]` y del `scoreboard`.
- [x] Operador con nombre y sin lado hereda el de su equipo en `inferredOperatorSides`; el Recluta no; un ID sin nombre se anota como `Unknown(<id>)` (criterio ajustado en el diseno a lo que hace main).
- [x] Sin operadores con lado conocido: sin `role`, sin excepcion, con `log.warning`.
- [x] Los tests no dejan estado en `overrides.unknown_ids()`.

## Fuera de alcance

Cambiar el desempate; `.rec` reales o fixtures binarias; otras funciones de `header.py`.

## Diseno, implementacion y revision (resumen; detalle en `git log`)

- Diseno (arquitecto 20261010T0602Z): solo `test_pydissect.py`, lector falso, overrides en JSON temporal con recarga en `finally`, `reset_unknown()` en `setUp`/`tearDown`.
- Implementacion en tres pasadas de dev; tres revisiones. Hallazgos corregidos: el operador sin lado se movio al equipo defensor (si no, `ATTACK` fijo pasaba); tests de mayoria mixta para que voten los dos equipos y pesen ataque y defensa; rename del test del `tearDown`; el revisor agrego `test_los_defensores_de_mas_del_equipo_1_tambien_restan`. Veredicto final: **aprobar**.

## QA 2026-10-13 sobre 76a476f

(QA 20261013T0302Z.) `check.sh` en verde (468 backend, 65 vitest, build, 23 e2e). Cada criterio con una mutacion que cae; `--reverse` y `--shuffle 7` OK; humo de `runserver` con base vacia y `seed_demo`: `/api/overview/?side=Attack|Defense|foo`, `/api/operators/?page=-1`, `/api/coach/?until=foo` -> 200. Veredicto: **aprobado**.

## Para el humano

Los dos avisos del PR (Unknown en `inferredOperatorSides`, desempate al equipo 0). Informativos.
