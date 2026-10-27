# 65. Presencia y delta de winrate por operador

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: operadores
area: fullstack
prioridad: 3
fuente: ALCANCE.md O5 (replica/features.csv fila 26, must, clone partial; [r6tv](https://r6tv.online/how-it-works), [aurelix](https://aurelix.app/blog/how-to-analyse-r6-siege-replays))
archivos: -
turnos: po 20261027T1205Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

En Operadores hoy se ve el winrate de cada operador, pero no si es mejor o
peor que tu winrate normal en ese lado ni cuanto lo juegas. Con dos columnas
nuevas, presencia (% de tus rondas de ese lado jugadas con el) y delta
(su winrate menos tu winrate base del lado), queda claro que operador te sube
y cual te baja, y si el numero se apoya en muchas rondas o en pocas.

## Criterios de aceptacion

- [ ] Cada fila de `GET /api/operators/` trae `presence_pct` = rondas con ese
      operador en ese lado / tus rondas de ese lado (con los mismos filtros), y
      `winrate_delta` = winrate del operador - winrate base del lado, en puntos.
      Test: 10 rondas de ataque, 4 con Ash (3 ganadas) y 6 con otro (3 ganadas):
      Ash con 40 % de presencia y +25 puntos (75 - 50).
- [ ] El winrate base del lado sale de todas tus rondas de ese lado con los
      filtros activos, aunque `min_rounds` oculte filas: ocultar un operador no
      mueve el delta de los demas. Test con `min_rounds`.
- [ ] Con filtro de operador o de lado (`side=Defense`), presencia y delta
      siguen definidos sobre las rondas que el filtro deja; una fila sin rondas
      ganadas ni perdidas (todas sin ganador) da `winrate_delta: null`. Base
      vacia: lista vacia, 200.
- [ ] La tabla de `Operators.jsx` muestra las columnas "Presencia" y "vs. tu
      lado" (con signo, +/-), ordenables, con ayuda que dice como se calculan,
      y el CSV de la tabla las incluye. El e2e afirma que la columna aparece.
- [ ] Filas en `docs/metricas.md` para las dos columnas; si el delta va con
      banda de ruido (`_ruido` de `aggregates.py`), la fila lo dice.

## Fuera de alcance

- El corte por mapa y sitio (idea O1): va despues, como su propio tramo.
- Cambiar la señal del Coach que ya compara operador contra tu promedio.
- Rating relativo al operador (idea O3).

## Para el humano

(Nada por ahora.)
