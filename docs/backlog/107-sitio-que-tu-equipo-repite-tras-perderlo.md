# 107. Sitio que tu equipo repite tras perderlo

estado: propuesto
candado: arquitecto 2026-11-12T12:15Z
rama: -
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S4 (PO 20261105T1759Z-cCJ5erc)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py, frontend/src/pages/ (la pagina la elige el Arquitecto), docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz

## PR

## Que gana quien usa la app

Despues de perder una ronda defendiendo un sitio, la app dice cuantas veces
tu equipo vuelve a ese sitio en la siguiente ronda de defensa y cuantas
cambia, con el winrate de cada caso, en total y por mapa. Si el rival ya leyo
el sitio, repetir cuesta: es una decision de la defensa, o sea tuya y de tu
equipo, que ninguna tabla muestra hoy.

## Criterios de aceptacion

- [ ] Un agregado devuelve, para pares de rondas de defensa consecutivas de
      la misma partida (por `Round.number`, saltando las de ataque entre
      medio) donde la primera se perdio: `repeat` y `switch` con
      `rounds` y `winrate` de la segunda ronda, en total y por mapa. Test
      con una partida armada: perder en "2F Kitchen" y volver a "2F Kitchen"
      cuenta `repeat`; ir a "1F Bar" cuenta `switch`.
- [ ] Una ronda con `site=""` corta el par (no cuenta ni como primera ni
      como segunda) y el test lo afirma; los pares no cruzan partidas.
- [ ] Los filtros globales (mapa, tipo de partida, fechas, sesion) aplican;
      el de lado se ignora (solo hay pares de defensa) y el de sitio filtra
      por el sitio de la ronda perdida. Test del filtro de sitio.
- [ ] Se ve en la UI con los dos casos lado a lado y la muestra minima de
      `metricas.md` para winrates; sin pares, un texto vacio y no un error.
      El e2e de humo pasa por esa pagina con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir el sitio tras perderlo").

## Fuera de alcance

- El lado de ataque (S3, spawn tras perder): otra idea.
- Pares que siguen a una ronda ganada.
- Recomendar que sitio jugar: solo se cuenta.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
