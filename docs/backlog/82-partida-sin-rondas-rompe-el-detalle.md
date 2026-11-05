# 82. Una partida sin rondas rompe el detalle de partida

estado: propuesto
candado: arquitecto 2026-11-05T13:03Z
rama: -
tipo: bug
epica: -
area: frontend
prioridad: 3
fuente: QA 20261105T0256Z-cFRtPBc de la ficha 75 (anotado alli como "ficha 81"; el 81 lo tomo otra sesion a la vez). En dev 7a87ddc, `frontend/src/pages/MatchDetail.jsx:33`: `const round = rounds[Math.min(selected, rounds.length - 1)]` da `rounds[-1]` = `undefined` con 0 rondas, y `round.label` (`:124`) tira `TypeError`
archivos: frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js
turnos: qa 20261105T0256Z-cFRtPBc

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Una partida importada sin rondas (un `.rec` cortado o una carpeta a medias) hoy deja la pagina en blanco con un error en consola. Con el arreglo se ve la cabecera de la partida y un aviso "Esta partida no tiene rondas importadas", y el resto de la app sigue navegable.

## Criterios de aceptacion

- [ ] Repro de hoy: base con una partida sin rondas (`make_match` sin `make_round`), `runserver`, abrir `/partidas/<id>`: `TypeError: Cannot read properties of undefined (reading 'label')` y sin contenido. `GET /api/matches/<id>/` responde 200 con `rounds: []`.
- [ ] Con el arreglo, `/partidas/<id>` muestra la cabecera de la partida y un aviso de que no hay rondas, sin error en consola.
- [ ] Una partida con rondas se ve igual que antes (el e2e existente sigue verde).
- [ ] Test que lo cubre: e2e con ruta interceptada que devuelve `rounds: []`, o logica pura extraida y probada con vitest.

## Fuera de alcance

Evitar que el import guarde partidas sin rondas (es otra decision); el catch-all del SPA que responde HTML 200 a `/api/matches/foo/`.

## Diseno

## Implementacion

## Revision

## QA

## Verificar en el PC

## Pendiente

## Para el humano
