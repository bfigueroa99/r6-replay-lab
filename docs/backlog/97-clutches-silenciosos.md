# 97. Clutches silenciosos

estado: propuesto
candado: arquitecto 2026-11-06 02:20 UTC
rama: -
tipo: funcionalidad
epica: impacto
area: fullstack
prioridad: 3
fuente: K11 de ALCANCE.md; [Siege.GG, rating rebalance](https://siege.gg/blog/946-player-rating-rebalance) (2026-08-11: "It also allows for 'quiet' clutches to have an impact on rating"); investigador 2026-11-03
archivos: -
turnos: po 20261106T0041Z-cSxDY1g

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

La tabla de clutches de Compañeros (intentos y ganados por 1vX, ficha 55)
no distingue un 1v2 ganado matando a los dos de uno ganado sin disparar
(aguantando el reloj en defensa, o esperando el plant/defuse). Con esto se
ve cuantos de tus clutches ganados fueron "silenciosos", por lado y por
condicion de victoria: si cuando quedas solo ganas peleando o ganas
escondiendote.

## Criterios de aceptacion

- [ ] Al importar, cada `RoundPlayer` con `clutch_vs > 0` guarda cuantas
      bajas hizo desde el instante en que quedo como unico vivo de su equipo
      (columna nueva, p. ej. `clutch_kills`, calculada en
      `analytics/metrics.py` con la misma recorrida del feed que
      `clutch_vs`; los teamkills no cuentan, como en `kills` desde la
      ficha 67). `recompute` la llena en la base existente. Tests de
      `metrics.py`: un 1v2 ganado con dos bajas da 2, un 1v1 ganado por
      tiempo da 0, una baja hecha antes de quedar solo no cuenta.
- [ ] La API que ya sirve `clutch_conversion` agrega, por cada fila 1vX y
      por lado, los ganados silenciosos (ganados con `clutch_kills = 0`) y
      el total de ganados silenciosos por condicion de victoria
      (`Round.win_condition`, con las inferidas del reloj marcadas aparte,
      como dice `docs/formato-rec.md`). Test de Django con datos sinteticos.
- [ ] La tabla de clutches de `Teammates.jsx` muestra la columna
      "Silenciosos" (cantidad y % de los ganados) y una nota con el reparto
      por condicion de victoria; con muestra chica se marca como las otras
      filas.
- [ ] `docs/metricas.md` tiene la fila de "Clutch silencioso" con su
      definicion exacta (que cuenta como baja, desde que instante).
- [ ] El e2e ve la columna en la pagina de Compañeros con los datos de
      `seed_demo` sin errores en la consola (si `seed_demo` necesita un
      clutch silencioso, se agrega y se ajustan los numeros que afirme el e2e).

## Fuera de alcance

- Tocar el Rating: la Siege.GG premia el clutch silencioso, pero cambiar la
  formula del Rating que ya se muestra es una decision del humano (P10). Si
  el diseno lo cree util, va a `## Para el humano` como pregunta.
- Señal del Coach sobre clutches (es K9, otra idea).
- Clutches perdidos: un 1vX perdido sin bajas no es "silencioso", es perdido.

## Diseno

(Arquitecto) Agrega migracion y `recompute`: va a "Verificar en el PC".

## Implementacion

## Para el humano

(Nada por ahora.)
