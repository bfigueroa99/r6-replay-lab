# 35. Tests de como el parser decide que equipo ataca

estado: implementado
candado: -
rama: claude/equipo-dev/35-tests-lado-de-los-equipos
area: tests
prioridad: 3
fuente: hueco de tests en `pydissect/header.py`: `derive_team_roles` (decide el lado de cada equipo por mayoria de operadores, descarta jugadores con operador 0 y anota el lado inferido de los operadores nuevos en `inferredOperatorSides`) solo lo ejercita `RealReplayTests` de `tests/test_pydissect.py`, que se salta sin `R6_TEST_REPLAY` (en la nube y en `check.sh` siempre). Es justo el codigo que tiene que aguantar una temporada nueva con operadores desconocidos.
archivos: backend/tests/test_pydissect.py
turnos: po 20261010T0301Z, arquitecto 20261010T0602Z, dev 20261010T1501Z

## PR

(La escribe el Release manager al final: titulo `[equipo-dev][area] Titulo`,
cuerpo segun `.claude/skills/equipo-dev/plantilla-pr.md` y una seccion
"Como probarlo en 2 minutos" con comandos exactos.)

## Que gana quien usa la app

Trabajo interno: si una temporada nueva trae operadores que la app no conoce,
el lado de cada equipo (y con el todo lo que se filtra por ataque y defensa)
depende de esta funcion, y hoy ningun test que corre la cubre. Baja el riesgo
de que un cambio en el parser invierta ataque y defensa sin que nada avise.

## Criterios de aceptacion

- [ ] Con un lector falso (`header`, `players`, `teams`, sin `.rec`), un equipo con mayoria de operadores de ataque conocidos queda `Attack` y el otro `Defense`, tambien cuando el equipo atacante es el `teamIndex` 1 (test en `tests/test_pydissect.py`).
- [ ] Un jugador con operador 0 sale de `header["players"]` y del `scoreboard` (test).
- [ ] Un operador con nombre conocido pero sin lado en `OPERATOR_SIDES` (el caso de un operador nuevo etiquetado en overrides) hereda el lado de su equipo en `header["inferredOperatorSides"]`; un Recluta no se anota ahi, y un ID sin nombre tampoco (test).
- [ ] Si ningun operador tiene lado conocido, los equipos quedan sin `role` y la funcion no revienta (test que afirma tambien el `log.warning`).
- [ ] Los tests no dejan estado: `operator_name` anota los IDs sin nombre en el registro en memoria de `overrides.record_unknown`, asi que cada test que use un ID desconocido llama a `reset_unknown()` al terminar, y `unknown_ids()` queda vacio despues de la clase (test).

## Fuera de alcance

- Cambiar la regla de desempate (`score0 >= score1` hace atacar al equipo 0): si el diseno ve que el empate da un resultado dudoso, va a `## Para el humano`, no se cambia en esta ficha.
- Tests con `.rec` reales o fixtures binarias.
- Otras funciones de `header.py` sin test directo (`read_header`, `gamemode_name`).

## Diseno

(Arquitecto 20261010T0602Z, sobre main 0b547d7.) Solo tests: no cambia codigo
de `pydissect/`. Spike en el scratchpad con un lector falso confirmo el
comportamiento actual, con **un ajuste al criterio 3** (ver abajo).

**Ajuste al criterio 3.** El criterio dice que "un ID sin nombre tampoco" se
anota en `inferredOperatorSides`. En main **si** se anota: `operator_name`
devuelve `"Unknown(<id>)"` (no vacio) para un ID que no esta ni en
`OPERATORS` ni en overrides, y queda `{"Unknown(123)": "Attack"}`. Es
coherente con el comentario del codigo ("quedan registrados para
aprenderlos") y nadie consume ese dict fuera de `match.py:144`, que lo copia al
dict de la ronda. Como la ficha es de tests y cambiar el comportamiento esta
fuera de alcance, el test **documenta lo que hace main**: el ID sin nombre se
anota con la clave `"Unknown(<id>)"`. Si el humano prefiere que no se anote,
es otra ficha (ver `## Para el humano`).

**Archivo y por que**

- `backend/tests/test_pydissect.py`: ahi viven `NameTests` y
  `CompatTradeTests`, que ya usan lectores falsos (`FakeReader`). Clase nueva
  `LadoDeLosEquiposTests(SimpleTestCase)` despues de `NameTests`. Import nuevo:
  `derive_team_roles` desde `pydissect.header`; `overrides` desde `pydissect`
  (`from pydissect import overrides`), `ATTACK`, `DEFENSE`, `RECRUIT` desde
  `pydissect.constants`.

Nada mas. `archivos:` = ese archivo.

**Lector falso**

`derive_team_roles(r)` solo usa `r.players` (lista de dicts con `username`,
`teamIndex`, `operator`), `r.header` (dict), `r.teams` (lista de 2 dicts) y
escribe `r.scoreboard`. Helper de modulo:

```python
def _lector(jugadores):
    """Lo minimo que `derive_team_roles` lee y escribe, sin .rec."""
    return SimpleNamespace(header={}, players=jugadores, teams=[{}, {}], scoreboard=None)
```

IDs a usar (estan en `constants.OPERATORS` y ya los usa `NameTests`): Ash
`92270642656` (ataque), Mute `92270642318` (defensa). Para un segundo atacante
y defensor, el Dev toma dos IDs cualquiera de `OPERATORS` con lado conocido y
los nombra en una constante con comentario (`THERMITE = ...  # ataque`). ID
desconocido: `999` (no esta en `OPERATORS`; si lo estuviera el test lo
detecta porque falla).

**Tests** (nombres en espanol, sin tildes)

1. `test_el_equipo_con_operadores_de_ataque_ataca`: equipo 0 con 2 atacantes,
   equipo 1 con 2 defensores -> `teams[0]["role"] == ATTACK`,
   `teams[1]["role"] == DEFENSE`.
2. `test_el_atacante_puede_ser_el_equipo_1`: lo mismo invertido ->
   `teams[1]["role"] == ATTACK`.
3. `test_el_jugador_con_operador_0_se_descarta`: 3 jugadores, uno con
   `operator: 0` -> `header["players"]` tiene 2 y no contiene a ese
   `username`; `len(scoreboard) == 2`.
4. `test_operador_con_nombre_y_sin_lado_hereda_el_de_su_equipo`: overrides
   apuntando a un JSON temporal con `{"operators": {"999": "Nuevo"}}`; equipo 0
   con Ash y el `999`, equipo 1 con Mute ->
   `header["inferredOperatorSides"] == {"Nuevo": ATTACK}`. Mecanica (para que
   no quede cache sucio): `tempfile.TemporaryDirectory()`, escribir el JSON,
   `with mock.patch.dict(os.environ, {overrides.ENV_VAR: ruta}):`
   `overrides.load(force=True)` y llamar a `derive_team_roles`; fuera del
   `with`, en un `finally`, `overrides.load(force=True)` otra vez para que el
   cache vuelva al estado sin overrides. `os` ya esta importado; agregar
   `tempfile`, `from types import SimpleNamespace`, `from unittest import mock`.
5. `test_el_recluta_no_se_anota_como_operador_nuevo`: equipo 0 con Ash y
   `RECRUIT`, equipo 1 con Mute -> `"inferredOperatorSides" not in header`.
6. `test_un_id_sin_nombre_se_anota_como_unknown`: equipo 0 con Ash y `999`
   (sin overrides), equipo 1 con Mute ->
   `header["inferredOperatorSides"] == {"Unknown(999)": ATTACK}` y
   `999 in overrides.unknown_ids()["operators"]`. (Criterio 3 ajustado.)
7. `test_sin_operadores_conocidos_no_hay_lado_y_avisa`: todos con `999` ->
   `with self.assertLogs("pydissect.header", level="WARNING")`; afirma que
   ningun `teams[i]` tiene `"role"` y que `header["players"]` sigue armado.
8. `test_los_ids_desconocidos_no_quedan_registrados_entre_tests`: con 6 y 7 en
   la clase, `setUp` y `tearDown` llaman a `overrides.reset_unknown()`; este
   test afirma `overrides.unknown_ids() == {}` al empezar (prueba que el
   `tearDown` del anterior limpio, sea cual sea el orden). Ademas
   `tearDownClass` llama a `reset_unknown()` por las dudas.

`self.assertNoLogs` no hace falta en el resto: el warning solo sale en 7.

**Orden**

1. Helper `_lector` y tests 1 a 3.
2. 5, 6 y 7 con el `setUp`/`tearDown` de `reset_unknown`.
3. 4 (overrides temporal), y el 8 al final.
4. `python manage.py test tests.test_pydissect` y despues `check.sh`.

Prueba de mutacion sugerida para QA: cambiar `score0 >= score1` por
`score0 <= score1` hace caer 1 y 2; sacar el `p.get("operator") != RECRUIT`
hace caer 5.

**Que puede romperse**

- El cache de overrides es global de modulo: si el test 4 no lo recarga en el
  `finally`, otros tests que dependan de nombres (`NameTests`) podrian ver
  `"Nuevo"`. Por eso el `finally`.
- `record_unknown` es estado global: si un test olvida limpiar, cualquier test
  posterior que mire `overrides.unknown_ids()` ve IDs ajenos. El `tearDown` lo
  cubre.
- Sin migracion, sin frontend, sin cambios de parser. `RealReplayTests` no se
  toca.

**Verificacion manual:** `cd backend && python manage.py test
tests.test_pydissect -v 2` muestra los 8 tests nuevos.

**Choques:** ninguno. La rama abierta (#33) toca `replays/views.py` y
`tests/test_dates.py`; la ficha 34 (disenada en este turno) toca
`analytics/metrics.py` y otros tests.

**Desempate:** `score0 >= score1` hace atacar al equipo 0 si los puntajes
empatan (por ejemplo, equipo 0 con un atacante y un defensor conocidos y
equipo 1 sin ninguno conocido). Fuera de alcance; no se testea el empate para
no fijar un comportamiento dudoso. Va como aviso a `## Para el humano`.

## Implementacion

(Dev 20261010T1501Z.) Solo `backend/tests/test_pydissect.py`: clase
`LadoDeLosEquiposTests` despues de `NameTests`, con helpers de modulo
`_lector` y `_jugador` y constantes `ASH`, `THERMITE`, `MUTE`, `JAGER`,
`DESCONOCIDO = 999`. Los 8 tests del diseno, uno por criterio:

| criterio | test |
|---|---|
| 1 | `test_el_equipo_con_operadores_de_ataque_ataca`, `test_el_atacante_puede_ser_el_equipo_1` |
| 2 | `test_el_jugador_con_operador_0_se_descarta` |
| 3 (ajustado) | `test_operador_con_nombre_y_sin_lado_hereda_el_de_su_equipo`, `test_el_recluta_no_se_anota_como_operador_nuevo`, `test_un_id_sin_nombre_se_anota_como_unknown` |
| 4 | `test_sin_operadores_conocidos_no_hay_lado_y_avisa` |
| 5 | `test_los_ids_desconocidos_no_quedan_registrados_entre_tests` |

Desvios del diseno:

- Test 8: tal como estaba disenado (afirmar `unknown_ids() == {}` al
  empezar) pasaba aunque se borrara el `tearDown`, porque el `setUp` ya
  limpia (hallazgo de la revision ciega). Ahora el test anota un ID
  desconocido, llama a `self.tearDown()` y afirma que el registro quedo
  vacio. Mutacion: con el `tearDown` vacio, cae exactamente ese test.
- Sin `tearDownClass`: con `tearDown` en cada test sobraba.
- El test 4 afirma ademas `unknown_ids() == {}`: con el override el `999`
  tiene nombre y no se registra como desconocido.

Revision ciega (`revision.md`): un hallazgo (el del test 8), corregido.
Sin cambios en `pydissect/`. `check.sh` en verde.

## Revision <fecha> sobre <sha>

(Revisor) Formato de `revision.md`. Veredicto al final.

## QA <fecha> sobre <sha>

(QA) Un comando y un resultado por criterio de aceptacion.

## Verificar en el PC

(QA, solo si toca migraciones, recompute, parser, Electron o `.ps1`.)

## Pendiente

(Solo si alguien dejo trabajo a medias: que falta y donde se trabo.)

## Para el humano

(Arquitecto 20261010T0602Z, avisos; no bloquean la ficha.)

- `derive_team_roles` anota en `inferredOperatorSides` tambien los IDs sin
  nombre, como `"Unknown(<id>)"`. Esta ficha lo deja documentado en un test tal
  como esta. Si preferis que solo se anoten operadores con nombre, decilo y el
  PO abre una ficha aparte.
- Desempate: si los dos equipos suman el mismo puntaje de ataque menos
  defensa, ataca el equipo 0 (`score0 >= score1`). No se testea para no fijar
  algo dudoso; si queres otra regla, es otra ficha.
