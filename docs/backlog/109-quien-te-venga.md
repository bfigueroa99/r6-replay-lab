# 109. Quien te venga

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C14 (primer tramo de C2 mirado desde ti)
archivos: backend/replays/analytics/aggregates.py, backend/replays/views.py (teammates), frontend/src/pages/Teammates.jsx, docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz

## PR

## Que gana quien usa la app

En Compañeros, por compañero habitual: cuantas de tus muertes vengo (mato a
tu asesino dentro de la ventana de trade) y cuantas veces estaba vivo y no lo
hizo. Dice con quien tus muertes no salen gratis, que el winrate por
compañero no separa.

## Criterios de aceptacion

- [ ] `/api/teammates/` devuelve por compañero (las mismas filas y muestra
      minima que `synergy`): `avenged` (tus muertes donde el fue quien mato
      a tu asesino dentro de `TRADE_WINDOW_SECONDS`), `alive_not_avenged`
      (tus muertes sin trade suyo con el vivo en ese momento) y la tasa.
      Test con una ronda armada: el compañero mata a tu asesino a 2 s cuenta
      `avenged`; a 5 s, con ventana 3, cuenta `alive_not_avenged`.
- [ ] Un compañero ya muerto cuando caiste no suma en ninguna columna; un
      trade hecho por otro compañero no le suma a el. Test.
- [ ] Usa la misma ventana que `was_traded` y no la duplica: cambiar
      `TRADE_WINDOW_SECONDS` y correr `recompute` mueve los dos numeros
      igual (test con `self.settings`, como `test_recompute`).
- [ ] La columna o tabla se ve en Compañeros; sin datos, un texto vacio y no
      un error. El e2e de humo pasa por Compañeros con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Quien te venga").

## Fuera de alcance

- La matriz de trades de todo el equipo (C2).
- Tiempo de refrag (C6) y quien te venga a ti como rival (D*).

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
