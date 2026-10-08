# 32. Un ?days= enorme da 500 en nueve endpoints

estado: en curso 2026-10-08
candado: dev 2026-10-08 15:10 UTC
rama: claude/equipo-dev/32-days-enorme-da-500
area: backend
prioridad: 2
fuente: bug reproducido en main dc0188b con `seed_demo`: `GET /api/overview/?days=1000000` responde 500 (`OverflowError: date value out of range` en `replays/views.py:_filters`, que solo atrapa `ValueError`). Lo mismo en coach, operators, trends, teammates, duels, sessions, compare y players/<id>.
archivos: backend/replays/views.py, backend/tests/test_api.py
turnos: dev 20261008T1502Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Un enlace con un filtro de dias absurdo (escrito a mano en la URL, o compartido
con un numero mal tipeado) ya no tumba la pagina con un error de servidor: se
ignora el filtro como cualquier otro valor invalido. Baja el riesgo de que un
valor de la query string vuelva a dar 500, que `ParametrosInvalidosTests` ya
declara como regla.

## Criterios de aceptacion

- [ ] `GET /api/overview/?days=1000000` responde 200 (test).
- [ ] `GET /api/overview/?days=99999999999` responde 200 en los nueve endpoints que usan `_filters` (test con subTest).
- [ ] Un `days` desbordado se ignora: la respuesta es igual a la que se obtiene sin `days` (test).
- [ ] `days=7` sigue filtrando como antes (test existente o nuevo).

## Fuera de alcance

- Cambiar que significa un `days` negativo (hoy deja un `since` en el futuro y la respuesta sale vacia, sin 500).
- Validar el resto de filtros de texto (`map`, `operator`): ya no dan 500.

## Diseno

(Dev, bug encontrado en el turno.) En `_filters`, atrapar
`(ValueError, OverflowError)` alrededor de `int(days)` + `timedelta` +
la resta: `timedelta(days=10**11)` desborda en el constructor y
`datetime.now() - timedelta(days=10**6)` en la resta. Tests nuevos en
`ParametrosInvalidosTests` de `backend/tests/test_api.py`. Sin migracion,
sin recompute, sin frontend.
