# 73. Solid Snake, Fortress rehecho y las versiones Y10S4 e Y11S1 con nombre

estado: entregado
candado: -
rama: claude/equipo-dev/73-catalogo-y10s4-a-y11s1
tipo: funcionalidad
epica: datos-nuevos-del-parser
area: parser
prioridad: 2
fuente: idea P1 de `ALCANCE.md` (epica `sin entrega` en la linea `ROTACION` de `estado.sh`). Verificado por el PO el 2026-10-30 en el fork MIT de r6-dissect [ImAAhmad/r6-dissect](https://github.com/ImAAhmad/r6-dissect/tree/main/dissect), commit `1f0cc42` (2026-03-10, "Y11S1 SolidSnake, improved defuser detection"): `dissect/header.go` (`SolidSnake Operator = 444310693746`, `FortressY10 Map = 398899676157`), `dissect/operator_roles.go` (`444310693746: Attack`), `dissect/version.go` (`Y10S4 int = 9394857`, `Y11S1 int = 9578674`); [r6-dissect #130](https://github.com/redraskal/r6-dissect/issues/130). En `dev` 0fedc7b ninguno de los cuatro esta en `pydissect/constants.py` (`CODE_VERSIONS` termina en `Y10S3_1`)
archivos: backend/pydissect/constants.py, backend/tests/test_pydissect.py, backend/tests/test_retag.py, docs/formato-rec.md, README.md
turnos: po 20261030T1653Z, arquitecto 20261103T1604Z-cpkQba9, dev 20261104T0003Z-cmWzGBm, revisor 20261104T0403Z-cMkuzSY, qa 20261104T0804Z-cwJxvZj, release 20261104T0804Z-cwJxvZj

## PR

Titulo: `[equipo-dev][parser] Solid Snake, Fortress rehecho y las versiones Y10S4 e Y11S1 con nombre`

### Que cambia

Las partidas de las temporadas nuevas muestran a Solid Snake con su nombre y su lado (ataque), y el Fortress rehecho sale como "Fortress (Y10)" en vez de `Unknown(398899676157)`. Lo ya importado se corrige con `manage.py retag`, sin reimportar. `CODE_VERSIONS` suma Y10S4 e Y11S1.

### Por que esto y no otra cosa

Ficha 73, idea P1 de `ALCANCE.md` (epica `datos-nuevos-del-parser`, sin entregas). Los IDs salen del fork MIT ImAAhmad/r6-dissect (`1f0cc42`). Descartado: dejarlos en `overrides.json` (cada usuario tendria que etiquetarlos a mano) y constantes sueltas `Y10S4 = ...` sin uso (ruido para el lint).

### Como se probo

- `check.sh` (con `verificar.sh`): VERDE sobre el commit de entrega, 882 tests backend, 153 vitest, 54 e2e (QA: VERDE bcc1edd97 con los mismos conteos).
- Tests nuevos: `NameTests` (`test_solid_snake_tiene_nombre_y_lado_de_ataque`, `test_solid_snake_no_se_anota_como_desconocido`, `test_el_catalogo_gana_al_rolename_de_la_cabecera`, `test_fortress_rehecho_comparte_slug_con_el_viejo`), `EtiquetaDeVersionTests.test_fortress_rehecho_lleva_y10`, `CodeVersionsTests.test_las_versiones_y10s4_e_y11s1_estan_en_orden`, `RetagCatalogoNuevoTests` (dry-run, aplicacion, segunda corrida y comando).
- `test_retag.py`: `MAPA_NUEVO`/`OPERADOR_NUEVO` pasan a IDs sinteticos (`999000000001`/`999000000002`) porque los reales ahora estan catalogados; ninguna asercion cambio.
- Manual (QA): `retag --dry-run`/`retag`/`unknown_ids` sobre base sembrada; `runserver` con `/api/filters/` mostrando "Fortress (Y10)" y "Solid Snake"; 4 mutaciones, cada una tumba su test.
- OMC: diseno plan=— · implementacion revisión=1 hallazgo (1 arreglado) · revision revisión=0 hallazgos · QA verificación=PASS.

### Riesgos y lo que no entra

Sin migracion ni `recompute`; `retag` es la via para lo ya importado. Si el fork se equivocara en el lado de Solid Snake, sus rondas saldrian con lados cruzados: lo confirma el PC. Fuera: kill feed Y11S2, DBNO, scoreboard Y10S4+, Calypso Casino/Noor/Dokkaebi rehecho (sin IDs publicos).

### Como probarlo en 2 minutos

```bash
cd backend
python manage.py test tests.test_pydissect tests.test_retag tests.test_unknowns
python manage.py shell -c "from pydissect.constants import *; print(OPERATORS[444310693746], OPERATOR_SIDES['Solid Snake'], MAPS[398899676157])"
# Solid Snake Attack ('FortressY10', 'Fortress')
```

Verificar en el PC: ver `## Verificar en el PC` de la ficha (`retag --dry-run`, `retag`, `unknown_ids`).

### Para el humano

Aviso, no bloquea: si ya nombraste alguno de estos IDs en Datos, tras `retag` gana el catalogo ("Solid Snake", "Fortress").

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Las partidas de las temporadas nuevas muestran a Solid Snake con su nombre
y su lado, y el Fortress rehecho sale como "Fortress (Y10)" y no como
`Unknown(398899676157)`: no hace falta etiquetarlos a mano en Datos. Lo ya
importado se corrige con `retag`, sin reimportar.

## Criterios de aceptacion

- [x] `pydissect/constants.py`: `OPERATORS[444310693746]` es "Solid Snake",
      con lado de ataque en `OPERATOR_SIDES`; `operator_name(444310693746)`
      lo devuelve y ya no llama a `record_unknown`. Test en
      `backend/tests/test_pydissect.py`.
- [x] `MAPS[398899676157]` es `("FortressY10", "Fortress")`: `map_name` da
      "Fortress", `map_slug` da "fortress" (comparte slug con la version
      vieja, como `ConsulateY10`) y `etiqueta_de_version` da "Fortress
      (Y10)", asi que Mapas lo separa como cualquier otra version (ficha
      70). Test en `test_pydissect.py`.
- [x] `CODE_VERSIONS` suma `"Y10S4": 9394857` y `"Y11S1": 9578674`. Ninguna
      rama de lectura de `pydissect/events.py` cambia (todas comparan con
      Y9S4 o anteriores): la suite del parser sigue igual. Test de que las
      dos claves existen con esos valores.
- [x] Lo ya importado: con una base sembrada con `factories` que tiene una
      partida en `map_id=398899676157` (`Unknown(...)`) y filas con
      `operator_id=444310693746` (`Unknown(...)` o el nombre que haya dejado
      la cabecera), `manage.py retag --dry-run` cuenta los cambios sin tocar
      la base, `retag` los aplica y una segunda corrida dice "Nada que
      reetiquetar". Test en `backend/tests/test_retag.py`.
- [x] `docs/formato-rec.md` (donde dice que cada revamp cambia el
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

Diseno 2026-11-03 sobre `dev` ec263c3 (arquitecto 20261103T1604Z-cpkQba9): cuatro entradas de tabla en `constants.py` (`CODE_VERSIONS` Y10S4/Y11S1, `MAPS[398899676157] = ("FortressY10", "Fortress")`, `OPERATORS[444310693746] = "Solid Snake"` con lado `ATTACK`). Riesgo detectado: `test_retag.py` usaba estos dos IDs como "desconocidos"; se cambia solo el valor de `MAPA_NUEVO`/`OPERADOR_NUEVO` a IDs sinteticos. Sin frontend, sin migracion, sin `metricas.md`, sin e2e nuevo (`seed_demo` no usa estos IDs). Detalle completo en `git log` de esta ficha.

OMC: plan=— · revisión=— · verificación=—

## Implementacion

2026-11-04 (dev 20261104T0003Z-cmWzGBm) sobre `dev` ec263c3, sin desvios del diseno. Revision previa: 1 LOW (comentario del test de orden) corregido. verificar.sh: VERDE cb26bbf12 (882/153/54).

OMC: plan=— · revisión=1 hallazgo (1 arreglado) · verificación=—

## Revision 2026-11-04 sobre e4785f1

Revisor 20261104T0403Z-cMkuzSY. Revision a ciegas sin hallazgos; los cinco criterios con test. Veredicto: aprobar -> `revisado`.

OMC: plan=— · revisión=0 hallazgos (0 arreglados) · verificación=—

## QA 2026-11-04 sobre bcc1edd

QA 20261104T0804Z-cwJxvZj. Ejercita el sistema con bases sinteticas en el scratchpad (`DATA_DIR`/`SQLITE_PATH` fuera del repo).

- `verificar.sh` (check.sh completo): VERDE bcc1edd97 en 145 s, 882 tests backend, 153 vitest, 54 e2e.
- Base sembrada con `factories` (Fortress rehecho como `Unknown`, Solid Snake como `Unknown` y como `Solidsnake`): `retag --dry-run` cuenta 1 partida y 2 filas sin tocar la base; `retag` las nombra; la segunda corrida y `unknown_ids` no tienen nada que hacer.
- `runserver` sobre esa base: `/api/filters/` da `fortress` con versiones `126196841359 "Fortress"` y `398899676157 "Fortress (Y10)"`, y "Solid Snake" entre los operadores; `/api/matches/1/` dice "Fortress (Y10)"; `overview/`, `overview/?map=fortress`, `operators/?map=fortress&until=foo`, `matches/?page=-1`, `matches/?map=` y `unknown/` en 200, sin traceback.
- Base vacia: los mismos endpoints en 200, `matches/999/` 404; `/api/operators/catalog/` trae `{"name": "Solid Snake", "side": "Attack"}`; `retag` y `unknown_ids` sin nada que hacer.
- Mutaciones (revertidas): Solid Snake en `DEFENSE` -> cae `test_solid_snake_tiene_nombre_y_lado_de_ataque`; sin la entrada `FortressY10` -> caen 4 (slug, "(Y10)", dry-run y aplicacion del retag); `Y11S1 = 9000000` -> cae `test_las_versiones_y10s4_e_y11s1_estan_en_orden`; sin Solid Snake en `OPERATORS` -> caen 5.
- Sin `frontend/src`, sin migracion: no aplica el chunk de `vite build` ni `migrate` sobre esquema viejo.
- Observacion fuera de alcance (ya estaba en `dev`): `retag` imprime por cada nombre viejo las filas del ID entero ("Solidsnake -> Solid Snake (2 filas)" con una sola fila de ese nombre); el total final es correcto.

Criterios: los cinco cumplidos (verifier PASS en los cinco; lo de `.rec` reales va abajo).

Veredicto: `aprobado`.

Skills: no aplica.
OMC: plan=— · revisión=— · verificación=PASS

## Verificar en el PC

Con la base real, desde `backend/`:

```powershell
..\.venv\Scripts\python.exe manage.py retag --dry-run   # lista Unknown(398899676157) -> Fortress y las filas de Solid Snake
..\.venv\Scripts\python.exe manage.py retag
..\.venv\Scripts\python.exe manage.py unknown_ids        # ya no muestra 398899676157 ni 444310693746
```

En la app: Mapas muestra "Fortress (Y10)" aparte de "Fortress"; en una partida con Solid Snake su equipo sale atacando en las rondas de ataque.

## Pendiente

## Para el humano

Aviso, no bloquea: si ya nombraste alguno de estos IDs en Datos, despues de
`retag` queda el nombre del catalogo ("Solid Snake", "Fortress (Y10)"),
porque las constantes ganan a `overrides.json` desde siempre. El nombre del
operador sale del fork (`SolidSnake`) y de la pagina de temporada de
Ubisoft (Silent Hunt); si un `.rec` real dice otra cosa, se cambia una
linea y se corre `retag`.
