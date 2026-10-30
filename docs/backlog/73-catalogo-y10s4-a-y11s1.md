# 73. Solid Snake, Fortress rehecho y las versiones Y10S4 e Y11S1 con nombre

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: datos-nuevos-del-parser
area: parser
prioridad: 2
fuente: idea P1 de `ALCANCE.md` (epica `sin entrega` en la linea `ROTACION` de `estado.sh`). Verificado por el PO el 2026-10-30 en el fork MIT de r6-dissect [ImAAhmad/r6-dissect](https://github.com/ImAAhmad/r6-dissect/tree/main/dissect), commit `1f0cc42` (2026-03-10, "Y11S1 SolidSnake, improved defuser detection"): `dissect/header.go` (`SolidSnake Operator = 444310693746`, `FortressY10 Map = 398899676157`), `dissect/operator_roles.go` (`444310693746: Attack`), `dissect/version.go` (`Y10S4 int = 9394857`, `Y11S1 int = 9578674`); [r6-dissect #130](https://github.com/redraskal/r6-dissect/issues/130). En `dev` 0fedc7b ninguno de los cuatro esta en `pydissect/constants.py` (`CODE_VERSIONS` termina en `Y10S3_1`)
archivos: -
turnos: po 20261030T1653Z

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

## Implementacion

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
