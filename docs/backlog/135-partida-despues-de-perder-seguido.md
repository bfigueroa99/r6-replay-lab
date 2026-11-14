# 135. Partida despues de perder seguido

estado: propuesto
candado: arquitecto 2026-11-14T00:41Z
rama: -
tipo: funcionalidad
epica: progreso
area: backend
prioridad: 3
fuente: ALCANCE.md E6; el Coach ya aconseja "si son tres derrotas seguidas, corta la sesión" (`coach.py`, `_form`) sin mostrar el dato que lo respalda
archivos: -
turnos: po 20261113T1954Z-cfZTvvE

## PR

## Que gana quien usa la app

En Tendencias, tu winrate en la partida siguiente segun cuantas derrotas
seguidas llevabas en la sesion (0, 1, 2, 3 o mas): saber con tus propios
numeros si conviene cortar despues de dos derrotas, que hoy el Coach dice
como regla general.

## Criterios de aceptacion

- [ ] Un agregado ordena las partidas de cada sesion (el corte de sesion
      que ya usan `sessions` y `by_session_position`) y devuelve, por
      derrotas seguidas previas en esa sesion (0, 1, 2, 3+), `matches`,
      `wins` y `winrate` de la partida siguiente. La primera partida de la
      sesion cae en 0. Test con una sesion D, D, V, D.
- [ ] Una partida con `won` nulo o empatada no suma ni corta la racha y
      no entra al winrate de su fila (como `match_result`). Test.
- [ ] Los filtros globales aplican a la partida que se cuenta; la racha
      previa se mide sobre todas las partidas de la sesion, sin filtros
      (si no, un filtro de mapa inventaria rachas). Test con filtro de mapa.
- [ ] Panel en Tendencias cerca de "Curva de la sesión", con su `n` por
      fila y aviso de muestra chica; sin sesiones, un texto y no un error;
      e2e con `seed_demo` y consola limpia. Fila nueva en `docs/metricas.md`.

## Fuera de alcance

- Minutos desde la partida anterior (otro tramo).
- Rachas entre sesiones (E13 mira los dias de descanso).
- Cambiar la señal del Coach para que use este dato.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
