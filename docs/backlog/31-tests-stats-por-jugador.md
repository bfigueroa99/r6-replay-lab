# 31. Tests de stats por jugador: 1vX, headshots y agregado por partida

estado: entregado
candado: -
rama: claude/equipo-dev/31-tests-stats-por-jugador
area: parser
prioridad: 3
fuente: hueco de tests en pydissect: `stats.player_round_stats` (incluido el calculo de 1vX) y `stats.player_match_stats` no tienen ningun test unitario (main dc0188b)
archivos: backend/tests/test_player_stats.py
turnos: po 20261008T0302Z, arquitecto 20261008T0602Z, dev 20261008T0902Z, revisor 20261008T1202Z, qa 20261008T1802Z, release 20261009T0002Z

## PR

**Titulo:** `[equipo-dev][tests] Tests de stats por jugador: 1vX, headshots y agregado por partida`

### Que cambia

Agrega `backend/tests/test_player_stats.py`: 12 tests sin `.rec` sobre
`stats.player_round_stats` y `stats.player_match_stats`. Los clutch (1vX),
kills, muertes y % de headshots del Resumen, Operadores y la pagina de jugador
salen de ahi, y el 1vX es la logica mas enredada del parser; ahora un cambio
no puede inflar ni borrar clutches sin que la suite lo note. No cambia codigo
de la app.

### Por que esto y no otra cosa

Ficha 31 (hueco de tests en `pydissect/`). El lector falso no se comparte con
la ficha 30 a proposito (~15 lineas) para que se puedan mergear en cualquier
orden.

### Como se probo

- `./scripts/check.sh` sobre la rama fusionada con main: `Todo en verde.`
  (ruff ok, 378 tests backend, 53 vitest, build ok, 17 e2e).
- 1vX: ultimo vivo que gana suma sus kills y los rivales vivos; 1v1 ganado
  vale 1; ganador sin bajas no tiene 1vX; el ultimo del ganador que muere
  igual cobra; las kills antes de quedar solo (o con un companero vivo) no
  cuentan; un companero muerto sin asesino tambien deja solo al clutcher.
- Headshots: 50.0 por ronda; 0 kills no divide por cero; el agregado es hs%
  sobre el total (25.0), no promedio de rondas.
- Agregado de muertes y asistencias; asistencias salen del marcador.
- Mutaciones del Dev, del Revisor y de QA sobre `stats.py`: todas caen.

### Riesgos y lo que no entra

Sin migraciones, sin `recompute`, sin frontend: solo un archivo de test. No
se toca `pydissect/`. La rama `PLAYER_LEAVE` del 1vX queda sin test a
proposito (caso dudoso abajo).

### Como probarlo en 2 minutos

```
cd backend
python manage.py test tests.test_player_stats -v 2   # 12 tests ok
```

### Para el humano

Aviso, no bloquea: si un companero del ganador sale de la partida
(`PLAYER_LEAVE`) y despues el ultimo vivo gana un 1v1, hoy queda con
`1vX == 0` porque el que salio no cuenta como muerto. Si eso debe contar como
clutch es decision de producto; candidato a ficha aparte.

### Candidatos descubiertos

Ninguno en `propuesto` todavia (el caso de arriba queda para el PO).

## Que gana quien usa la app

Los clutch, kills, muertes y hs% que muestra la app quedan cubiertos por
tests: un cambio en el parser no puede romperlos en silencio.

## Criterios de aceptacion

- [x] Ultimo vivo que gana: `1vX == 5`, `kills == 3`, vivo.
- [x] 1v1 ganado -> `1vX == 1` (escenario del diseno; el de la PO era ambiguo).
- [x] Ganador sin bajas -> nadie con 1vX.
- [x] Ultimo del ganador que muere al final -> igual cobra el 1vX.
- [x] hs% por ronda 50.0; 0 kills -> 0.0 sin dividir por cero.
- [x] Agregado por partida (rondas, kills, headshots, hs%, muertes, asistencias).

## Implementacion, Revision y QA (resumen; el detalle esta en `git log`)

- Dev 20261008T0902Z (a39852f, e6e030e): `LectorFalso` + 10 tests; desvios
  justificados (agregado con dos rondas distintas -> 25.0; test de kills antes
  de quedar solo).
- Revisor 20261008T1202Z sobre c7cd309: aprobar. Hallazgo corregido con
  `test_la_kill_con_un_companero_vivo_no_cuenta_para_el_1vx`.
- QA 20261008T1802Z sobre 10126b8: aprobado. 10 mutaciones propias; agrego
  `test_un_companero_muerto_sin_asesino_tambien_deja_solo_al_clutcher`.
- Release 20261009T0002Z: `check.sh` en verde sobre la rama con main dc0188b.

## Verificar en el PC

No hace falta: solo agrega tests.

## Para el humano

- (Arquitecto, aviso) Caso dudoso del 1vX con `PLAYER_LEAVE` (ver `## PR`).
  Candidato a ficha aparte.
