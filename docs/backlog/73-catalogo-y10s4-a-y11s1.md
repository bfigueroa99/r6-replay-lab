# 73. Solid Snake, Fortress rehecho y las versiones Y10S4 e Y11S1 con nombre

estado: implementado
candado: -
rama: claude/equipo-dev/73-catalogo-y10s4-a-y11s1
tipo: funcionalidad
epica: datos-nuevos-del-parser
area: parser
prioridad: 2
fuente: idea P1 de `ALCANCE.md` (epica `sin entrega` en la linea `ROTACION` de `estado.sh`). Verificado por el PO el 2026-10-30 en el fork MIT de r6-dissect [ImAAhmad/r6-dissect](https://github.com/ImAAhmad/r6-dissect/tree/main/dissect), commit `1f0cc42` (2026-03-10, "Y11S1 SolidSnake, improved defuser detection"): `dissect/header.go` (`SolidSnake Operator = 444310693746`, `FortressY10 Map = 398899676157`), `dissect/operator_roles.go` (`444310693746: Attack`), `dissect/version.go` (`Y10S4 int = 9394857`, `Y11S1 int = 9578674`); [r6-dissect #130](https://github.com/redraskal/r6-dissect/issues/130). En `dev` 0fedc7b ninguno de los cuatro esta en `pydissect/constants.py` (`CODE_VERSIONS` termina en `Y10S3_1`)
archivos: backend/pydissect/constants.py, backend/tests/test_pydissect.py, backend/tests/test_retag.py, docs/formato-rec.md, README.md
turnos: po 20261030T1653Z, arquitecto 20261103T1604Z-cpkQba9, dev 20261104T0003Z-cmWzGBm

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Las partidas de las temporadas nuevas muestran a Solid Snake con su nombre
y su lado, y el Fortress rehecho sale como "Fortress (Y10)" y no como
`Unknown(398899676157)`: no hace falta etiquetarlos a mano en Datos. Lo ya
importado se corrige con `retag`, sin reimportar.

## Criterios de aceptacion

- [ ] `pydissect/constants.py`: `OPERATORS[444310693746]` es "Solid Snake",
      con lado de ataque en `OPERATOR_SIDES`; `operator_name(444310693746)`
      lo devuelve y ya no llama a `record_unknown`. Test en
      `backend/tests/test_pydissect.py`.
- [ ] `MAPS[398899676157]` es `("FortressY10", "Fortress")`: `map_name` da
      "Fortress", `map_slug` da "fortress" (comparte slug con la version
      vieja, como `ConsulateY10`) y `etiqueta_de_version` da "Fortress
      (Y10)", asi que Mapas lo separa como cualquier otra version (ficha
      70). Test en `test_pydissect.py`.
- [ ] `CODE_VERSIONS` suma `"Y10S4": 9394857` y `"Y11S1": 9578674`. Ninguna
      rama de lectura de `pydissect/events.py` cambia (todas comparan con
      Y9S4 o anteriores): la suite del parser sigue igual. Test de que las
      dos claves existen con esos valores.
- [ ] Lo ya importado: con una base sembrada con `factories` que tiene una
      partida en `map_id=398899676157` (`Unknown(...)`) y filas con
      `operator_id=444310693746` (`Unknown(...)` o el nombre que haya dejado
      la cabecera), `manage.py retag --dry-run` cuenta los cambios sin tocar
      la base, `retag` los aplica y una segunda corrida dice "Nada que
      reetiquetar". Test en `backend/tests/test_retag.py`.
- [ ] `docs/formato-rec.md` (donde dice que cada revamp cambia el
      `worldid` y cada temporada agrega operadores) nombra los cuatro IDs
      con la fuente, y `## Credito` del README suma el fork y el commit.
      Verificado solo en la nube con IDs sinteticos; con `.rec` reales va a
      `## Verificar en el PC` (`unknown_ids` deja de listar los dos IDs).

## Fuera de alcance

- El kill feed y los jugadores de Y11S2 (idea P5), DBNO (P3), el
  scoreboard Y10S4+ (P4) y los picks de preparacion (P6).
- Calypso Casino, Noor y el Dokkaebi rehecho: ningun parser abierto publica
  sus IDs; salen de `unknown_ids` en el PC.
- Temporada como dimension (A3): esta ficha solo deja las versiones en la
  tabla.
- Cambiar que gana entre las constantes y `data/overrides.json`: hoy ganan
  las constantes (`header.py`, `operator_name` y `_map_entry`) y sigue asi.

## Diseno

Diseno 2026-11-03 sobre `dev` ec263c3. Una sola forma obvia (cuatro entradas
de tabla): sin arena ni consenso.

**Riesgo que la ficha no veia: `test_retag.py` ya usa estos dos IDs como
"desconocidos".** `MAPA_NUEVO = 398899676157` y `OPERADOR_NUEVO =
444310693746` (lineas 20-21; `test_unknowns.py` los importa de ahi) son la
base de los tests que suponen `Unknown(...)` y que el override les da el
nombre ("Nighthaven Labs", "Denari"). Al catalogarlos, las constantes ganan
al override y fallan 8 (spike en el scratchpad sobre ec263c3:
`test_sin_overrides_no_cambia_nada`,
`test_aplica_el_nombre_*`, `UnknownIdsCommandTests`, el POST de
`test_unknowns.py`); con el arreglo, la suite entera del backend queda
verde. Arreglo: **cambiar solo el valor** de las dos
constantes del test a IDs sinteticos que ningun catalogo va a usar,
`MAPA_NUEVO = 999000000001` y `OPERADOR_NUEVO = 999000000002`, con un
comentario de por que (los IDs reales se catalogan con el tiempo). Ningun
test se borra, salta ni cambia de asercion: es el mismo test sobre un ID
que sigue siendo desconocido. Los IDs reales pasan a tener sus propios
tests (abajo).

### Archivos

- `backend/pydissect/constants.py`:
  - `CODE_VERSIONS`: `"Y10S4": 9394857` y `"Y11S1": 9578674` al final, en
    orden. No se agregan constantes sueltas (`Y10S4 = ...`): ninguna rama
    de `events.py`/`header.py` las compara hoy (todas son `<= Y9S4`), y una
    constante sin uso es ruido para el lint.
  - `MAPS`: `398899676157: ("FortressY10", "Fortress"),` despues de
    `ConsulateY10`, en la tabla principal (viene del fork, no de
    observacion: no va a `MAPS_EXTRA`).
  - `OPERATORS`: `444310693746: "Solid Snake",` despues de `Denari`, con
    `OPERATOR_SIDES["Solid Snake"] = ATTACK`. Comentario de una linea arriba
    de las dos entradas nuevas con la fuente (fork ImAAhmad/r6-dissect
    `1f0cc42`), como hace el docstring con r6-dissect.
- `backend/tests/test_pydissect.py`, tests nuevos:
  - `NameTests.test_solid_snake_tiene_nombre_y_lado_de_ataque`:
    `operator_name(444310693746) == "Solid Snake"`,
    `operator_side(444310693746) == "Attack"`.
  - `NameTests.test_solid_snake_no_se_anota_como_desconocido`: con
    `unittest.mock.patch("pydissect.header.record_unknown")`,
    `operator_name(444310693746)` no lo llama (y `operator_name(1)` si, como
    control).
  - `NameTests.test_el_catalogo_gana_al_rolename_de_la_cabecera`:
    `operator_label({"operator": 444310693746, "roleName": "SOLIDSNAKE"}) ==
    "Solid Snake"` (sin el catalogo daria "Solidsnake").
  - `NameTests.test_fortress_rehecho_comparte_slug_con_el_viejo`:
    `map_name(398899676157) == "Fortress"`, `map_slug(398899676157) ==
    map_slug(126196841359) == "fortress"`.
  - `EtiquetaDeVersionTests.test_fortress_rehecho_lleva_y10`:
    `etiqueta_de_version(398899676157) == "Fortress (Y10)"` y
    `etiqueta_de_version(126196841359) == "Fortress"`.
  - `test_las_versiones_y10s4_e_y11s1_estan_en_orden`: los dos valores
    exactos y que `list(CODE_VERSIONS.values())` siga estrictamente
    creciente (protege el orden de toda la tabla, no solo de las nuevas).
    En la clase que mejor calce (`HeaderTests`) o una nueva
    `CodeVersionsTests(SimpleTestCase)`.
- `backend/tests/test_retag.py`:
  - Cambio de valor de `MAPA_NUEVO`/`OPERADOR_NUEVO` (ver arriba).
  - Clase nueva `RetagCatalogoNuevoTests(OverridesTestCase)` (overrides
    vacios: asi se ve que el nombre sale de las constantes). `setUp`: una
    partida `map_name="Unknown(398899676157)"`, `map_slug=
    "unknown-398899676157"`, `map_id=398899676157`; dos `RoundPlayer` con
    `operator_id=444310693746`, uno `operator="Unknown(444310693746)"` y
    otro `operator="Solidsnake"` (lo que dejaba la cabecera).
    - `test_dry_run_cuenta_mapa_y_operador_sin_tocar_la_base`:
      `retag(dry_run=True)` da `matches == 1`, `round_players == 2`, y la
      base sigue igual.
    - `test_retag_pone_el_nombre_del_catalogo`: tras `retag()`,
      `map_name == "Fortress"`, `map_slug == "fortress"`, los dos
      operadores `"Solid Snake"`.
    - `test_la_segunda_corrida_no_tiene_nada_que_hacer`: segunda
      `retag()` con `changed is False`; y por comando
      (`call_command("retag", stdout=...)`) la salida dice "Nada que
      reetiquetar" (copiar el texto exacto de
      `RetagCommandTests.test_sin_cambios_lo_dice`).
- `docs/formato-rec.md`, seccion "IDs de mapas y operadores" (linea ~162):
  un parrafo corto despues de los dos mecanismos: "Catalogados desde el
  fork MIT ImAAhmad/r6-dissect (commit `1f0cc42`): Solid Snake
  `444310693746` (ataque), Fortress rehecho `398899676157` (`FortressY10`),
  versiones `Y10S4 = 9394857` e `Y11S1 = 9578674`. Calypso Casino, Noor
  y el Dokkaebi rehecho siguen saliendo de `unknown_ids`."
- `README.md`, `## Credito`: una frase que suma el fork
  ([ImAAhmad/r6-dissect](https://github.com/ImAAhmad/r6-dissect), MIT) como
  fuente de los IDs de Y10S4/Y11S1.

`archivos:` sin frontend: la etiqueta "(Y10)" ya la arma
`etiqueta_de_version` (ficha 70) y la UI la muestra sola. Sin migracion,
sin `metricas.md` (no hay numero nuevo), sin pagina nueva (sin e2e nuevo).
`seed_demo` no usa estos IDs: los numeros del e2e no cambian.

### Orden de implementacion

1. Cambiar `MAPA_NUEVO`/`OPERADOR_NUEVO` en `test_retag.py` y correr
   `test_retag test_unknowns`: tiene que quedar verde igual que antes.
2. Constantes en `constants.py`.
3. Tests nuevos de `test_pydissect.py` y `RetagCatalogoNuevoTests`.
4. Docs (`formato-rec.md`, README).
5. `verificar.sh`.

### Que puede romperse

- Si se hace el paso 2 sin el 1: 8 tests de retag/unknowns en rojo. Es
  la senal de que falta el paso 1, no de un bug.
- `operator_side` / `derive_team_roles`: "Solid Snake" pasa a ser operador
  conocido de ataque y vota en la mayoria del equipo. Es lo correcto; si el
  fork se equivocara de lado, la ronda saldria con lados cruzados. Lo
  confirma el PC (abajo).
- Base del humano: segun `docs/roadmap.md` (linea ~98), el humano ya nombro
  `Unknown(398899676157)` en Datos en su base real. Tras `retag` queda
  "Fortress"; si lo habia nombrado con otro mapa, ese mapa estaba mal o el
  fork esta mal: lo resuelve el PC. Ya avisado en `## Para el humano`.
- Nombre con espacio: ningun archivo de `frontend/src` mapea nombres de
  operador a iconos o slugs (`git grep` de Tubarao/Denari/Rauora en
  `frontend/src` vacio), asi que "Solid Snake" no rompe nada visual.

### Verificacion manual (para el `## Verificar en el PC` de QA)

En el PC, con la base real: `manage.py retag --dry-run` lista
`Unknown(398899676157) -> Fortress` (o el nombre que hubiera puesto el
override) y las filas de Solid Snake; `retag`; `manage.py unknown_ids` ya
no muestra ninguno de los dos IDs; Mapas muestra "Fortress (Y10)"
separado de "Fortress"; en una partida con Solid Snake, su equipo sale
atacando en las rondas de ataque.

Skills: no aplica (ningun dominio nuevo: entradas de tabla y tests del
patron de `test_pydissect.py`/`test_retag.py`).
OMC: plan=— · revisión=— · verificación=—

## Implementacion

2026-11-04 (dev 20261104T0003Z-cmWzGBm) sobre `dev` ec263c3. Diseno completo, sin desvios de fondo:

- `constants.py`: `CODE_VERSIONS` suma `Y10S4`/`Y11S1`; `MAPS[398899676157] = ("FortressY10", "Fortress")`
  despues de `ConsulateY10`; `OPERATORS[444310693746] = "Solid Snake"` y su lado `ATTACK`. Comentario
  con la fuente (fork `1f0cc42`) arriba de cada entrada.
- `test_retag.py`: `MAPA_NUEVO`/`OPERADOR_NUEVO` pasan a `999000000001`/`999000000002` con
  comentario de por que (paso 1 del diseno; ningun test cambio de asercion). Clase nueva
  `RetagCatalogoNuevoTests` sin overrides: `test_dry_run_cuenta_mapa_y_operador_sin_tocar_la_base`,
  `test_retag_pone_el_nombre_del_catalogo`, `test_la_segunda_corrida_no_tiene_nada_que_hacer`
  (este ultimo tambien por `call_command("retag")`, "Nada que reetiquetar").
- `test_pydissect.py`: en `NameTests`, `test_solid_snake_tiene_nombre_y_lado_de_ataque`,
  `test_solid_snake_no_se_anota_como_desconocido` (con control `operator_name(1)`),
  `test_el_catalogo_gana_al_rolename_de_la_cabecera`, `test_fortress_rehecho_comparte_slug_con_el_viejo`;
  en `EtiquetaDeVersionTests`, `test_fortress_rehecho_lleva_y10`; clase nueva `CodeVersionsTests`
  con `test_las_versiones_y10s4_e_y11s1_estan_en_orden`.
- `docs/formato-rec.md` (seccion IDs de mapas y operadores) y `README.md` (`## Credito`, archivo CRLF:
  se mantuvieron los finales de linea).

Criterios -> tests: los cinco criterios tienen test con nombre arriba, salvo el de docs (verificable
leyendo el diff) y la parte de `.rec` reales, que va a `## Verificar en el PC` (la escribe QA desde
el diseno).

Revision previa (omc-code-reviewer via general-purpose, el tipo omc no existe en el checkout): 1 LOW
real, el comentario del test de orden decia que las ramas de lectura comparan contra
`CODE_VERSIONS`, pero la tabla no la lee nadie (comparan las constantes sueltas). Corregido.

verificar.sh: VERDE cb26bbf12 (882 tests backend, 153 vitest, 54 e2e).

Skills: no aplica (entradas de tabla y tests del patron existente).
OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision <fecha> sobre <sha>

## QA <fecha> sobre <sha>

## Verificar en el PC

## Pendiente

## Para el humano

Aviso, no bloquea: si ya nombraste alguno de estos IDs en Datos, despues de
`retag` queda el nombre del catalogo ("Solid Snake", "Fortress (Y10)"),
porque las constantes ganan a `overrides.json` desde siempre. El nombre del
operador sale del fork (`SolidSnake`) y de la pagina de temporada de
Ubisoft (Silent Hunt); si un `.rec` real dice otra cosa, se cambia una
linea y se corre `retag`.
