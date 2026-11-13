# 128. Repetir o cambiar el spawn tras perder

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: posicionamiento
area: fullstack
prioridad: 3
fuente: ALCANCE.md S3
archivos: -
turnos: po 20261113T1858Z-cxdASk3

## PR

## Que gana quien usa la app

En ataque, despues de perder una ronda, cuantas veces vuelves a salir del
mismo spawn y cuantas cambias, con el winrate de la ronda siguiente en cada
caso (y lo mismo tras ganar, como base). Dice si insistir con el spawn que
te acaba de costar la ronda te sale caro; es el gemelo de spawn de la 113
(operador).

## Criterios de aceptacion

- [ ] Un agregado nuevo arma pares de tus rondas de ataque consecutivas de
      la misma partida (`Round.number` siguiente, sin hueco de numeracion,
      las dos con `RoundPlayer.side` ataque y `RoundPlayer.spawn` no vacio)
      y devuelve, por resultado de la primera (`after_loss`, `after_win`) y
      caso (`repeat`, `switch`), `rounds`, `decided`, `won` y
      `winrate` de la segunda. Test: pierdes desde el spawn A, repites A dos
      veces (ganas una) y cambias a B una vez (ganas) -> repeat 2 rondas
      50 %, switch 1 ronda 100 %.
- [ ] Un par con una ronda sin spawn, de defensa o con hueco de numeracion
      no entra; una segunda sin ganador cuenta en `rounds` y no en el
      winrate. Test.
- [ ] Los filtros globales aplican; `site` y `operator` eligen la primera
      ronda del par (como la 113). Test con filtro de mapa.
- [ ] Se ve en la pagina donde vive "Salida del spawn" (Coach), con el aviso
      de muestra de la pagina (se avisa, no se oculta) y un texto sin pares;
      e2e de humo con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Repetir o cambiar el spawn tras perder").

## Fuera de alcance

- A que spawn cambias (el desglose por par, como la 126 para operadores).
- Defensa: el defensor no elige spawn como el atacante.
- Recomendar un spawn.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano

(nada)
