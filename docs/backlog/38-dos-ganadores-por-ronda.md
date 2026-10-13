# 38. Una ronda de Y9S4+ con defuse del perdedor queda con dos ganadores

estado: entregado
candado: -
rama: claude/equipo-dev/38-dos-ganadores-por-ronda
tipo: bug
epica: -
area: parser
prioridad: 2
fuente: aviso de la ficha 30 (`## Para el humano`, ya en main) y de `ESTADO.md`; `round_end` en `backend/pydissect/events.py:378`
archivos: backend/pydissect/events.py, backend/tests/test_round_end.py, docs/formato-rec.md
turnos: po 20261013T0511Z, arquitecto 20261013T0611Z, dev 20261013T1111Z, revisor 20261013T1213Z, qa 20261013T1312Z, release 20261013T1411Z

## PR

Titulo: `[equipo-dev][parser] Una ronda de Y9S4+ con defuse del perdedor ya no queda con dos ganadores`

### Que cambia

Desde Y9S4 una ronda con defuse (o plant) del equipo que perdio podia quedar
con **dos** ganadores en el parser, y `analyse_round` se quedaba con el
ultimo: la ronda sumaba como ganada aunque el marcador de la partida dijera
lo contrario. Ahora en Y9S4+ el ganador sale solo de la cabecera (la misma
fuente que el marcador) y el kill feed solo aporta la condicion si apunta al
ganador; winrate de ronda, condicion de victoria y todo lo que cuelga de
`my_team_won` dejan de contradecir al marcador.

### Por que esto y no otra cosa

Ficha 38, del aviso que dejo la ficha 30 en `## Para el humano`. Se descarto
"manda el feed y se corrige el marcador": mas invasivo y contradice el
comentario de `round_end`, que trata a la cabecera como la verdad desde Y9S4.
Se descarto agregar un aviso nuevo en el parser: no llegaria a ninguna
pantalla, y `analyse_round` ya marca `win_condition_certain=False` en lo que
no es eliminacion.

### Como se probo

- `./scripts/check.sh` (release, sobre 2a2d8eb con `origin/main` fusionado):
  `Todo en verde.` con 484 tests backend, 65 frontend, build ok, 24 e2e.
- Tests nuevos en `backend/tests/test_round_end.py`:
  - `test_y9s4_un_defuse_del_perdedor_no_crea_un_segundo_ganador`
  - `test_y9s4_un_plant_del_perdedor_no_crea_un_segundo_ganador`
  - `test_y9s4_sin_coincidencia_y_con_eliminacion_la_condicion_es_eliminacion`
  - `test_y9s4_defuse_del_ganador_da_la_condicion_desactivar`
  - `test_y9s4_plant_del_ganador_da_la_condicion_bomba`
  - `test_previo_y9s4_el_defuse_sigue_decidiendo_el_ganador`
  Los dos "del perdedor" fallan sobre main y pasan con el cambio; los 14
  previos no se tocaron.
- Revision independiente: aprobar (un hallazgo menor sin efecto en datos).
- QA independiente: propiedad sobre 3456 combinaciones (siempre un ganador,
  el de la cabecera, en Y9S4), importacion sintetica de punta a punta con
  `my_team_won` coincidiendo con el marcador, y mutacion de 3 variantes del
  arreglo que hacen caer los tests.

### Riesgos y lo que no entra

Sin migraciones ni frontend. Las rondas ya importadas no cambian solas:
`recompute` no reparsea, hay que reimportar (ver abajo). Fuera: el caso de
`PLAYER_LEAVE` en 1vX y la inferencia de plant por reloj. Menor sin efecto:
en Y9S4+ con plant del perdedor y ronda sin defuse ni eliminacion, el
`winCondition` del parser queda en `TIME`, pero ese campo no se guarda ni se
lee en `replays/`.

### Como probarlo en 2 minutos

```powershell
cd backend; python manage.py test tests.test_round_end -v 2   # 20 OK
cd backend; python manage.py test tests                       # suite completa en verde
```

### Verificar en el PC

Toca el parser: confirmar con `.rec` reales de Y9S4+ que el ganador de cada
ronda coincide con el marcador.

```powershell
cd backend; python manage.py backup
cd backend; python manage.py import_replays --force <carpeta de replays>
$env:R6_TEST_REPLAY="<ruta a un .rec Y9S4+>"; cd backend; python manage.py test tests.test_pydissect
```

### Para el humano

Nada que decidir. Aviso: se eligio que **manda la cabecera**; si preferis que
mande el feed y se corrija el marcador, pedilo en `## Para el equipo`.

### Candidatos descubiertos

Ninguno.

## Criterios de aceptacion

- [x] Y9S4+, cabecera al equipo 0 y `DEFUSER_DISABLE_COMPLETE` del equipo 1:
      un solo ganador, el de la cabecera.
- [x] Lo mismo con `DEFUSER_PLANT_COMPLETE`.
- [x] Feed y cabecera coinciden: la condicion sale del feed; 14 tests previos verdes.
- [x] No coinciden: condicion inferida (`KILLED_OPPONENTS`/`TIME`); la
      incertidumbre la pone `analyse_round`.
- [x] Antes de Y9S4 el comportamiento no cambia.
- [x] `docs/formato-rec.md` dice que desde Y9S4 la cabecera manda.

## Diseno e implementacion

(Arquitecto 20261013T0611Z, Dev 20261013T1111Z) En Y9S4+ `round_end` ya no
escribe `won` desde el feed: el loop guarda `disabler` y `planter`, y despues
del loop la condicion es `DISABLED_DEFUSER`/`DEFUSED_BOMB` solo si apuntan al
ganador de la cabecera; si no, la inferencia de bomba de siempre. Antes de
Y9S4, el `return` temprano del defuse y el bloque del plant siguen igual.
Desvio: `recompute` no reparsea; las rondas ya importadas se corrigen con
`import_replays --force`.

## Revision 2026-10-13 sobre 0b96635

(Revisor 20261013T1213Z) Veredicto: aprobar. Un hallazgo menor no
bloqueante: `winCondition = TIME` tras plant del perdedor en Y9S4+; ese campo
de pydissect no se guarda ni se lee en `replays/`.

## QA 2026-10-13 sobre a6febeb

(QA 20261013T1312Z) Veredicto: aprobado. `check.sh` verde; propiedad sobre
3456 combinaciones; importacion sintetica de punta a punta; mutacion de 3
variantes. Detalle en `git log` (commit 3251eec).

## Verificar en el PC

`cd backend; python manage.py backup` y despues
`python manage.py import_replays --force <carpeta>`; con `.rec` Y9S4+,
`$env:R6_TEST_REPLAY="<ruta>"; python manage.py test tests.test_pydissect`.

## Para el humano

Aviso, sin pregunta abierta: manda la cabecera (variante conservadora). Si
preferis que mande el feed y se corrija el marcador, pedilo en `## Para el equipo`.
