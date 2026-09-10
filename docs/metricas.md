# Metricas: que significa cada numero

Todas se calculan en `backend/replays/analytics/metrics.py` (por ronda, al
importar) y se agregan en `aggregates.py`. Si un numero de la UI no te cuadra,
aca esta la definicion exacta.

## Base

| Metrica | Definicion |
|---|---|
| **Rondas** | Rondas tuyas importadas que pasan los filtros activos. |
| **Rondas ganadas (winrate)** | Rondas donde tu equipo gano / rondas jugadas. Es winrate **de rondas**, no de partidas: mide mejor porque una partida son 6-9 muestras. |
| **Bajas / muertes** | Del kill feed. Una muerte es "moriste en esa ronda", no cuenta dos veces. |
| **K/D** | bajas / muertes. |
| **KPR** | bajas / rondas. Mas honesto que el K/D porque no premia esconderse. Referencia razonable en ranked: 0.7-0.9. |
| **HS%** | headshots / bajas. El replay marca el headshot en cada kill. |
| **Sobrevives** | Rondas donde no moriste / rondas jugadas. |

## Duelos de apertura

La **primera baja de la ronda** define el duelo de apertura. Quien mata lo gana,
quien muere lo pierde. Si la primera muerte no tiene asesino registrado (evento
`Death` suelto), cuenta como apertura perdida para quien murio.

| Metrica | Definicion |
|---|---|
| **Duelos de apertura** | Aperturas ganadas + perdidas. Solo cuenta las rondas donde estuviste en el primer contacto. |
| **Aperturas ganadas %** | ganadas / (ganadas + perdidas). |
| **Winrate tras ganar la apertura** | Rondas ganadas entre las rondas donde te llevaste la primera baja. En Siege esta arriba del 70% para casi cualquier jugador: por eso el primer duelo importa tanto. |
| **Winrate tras perder la apertura** | Lo mismo del otro lado. |
| **Entry kill** | La primera baja **de tu equipo** en la ronda (distinto de la primera de la ronda: si el rival abrio, tu entry sigue estando en juego). |

## Trades

Un trade es que **mataron a tu asesino dentro de 3 segundos** de tu muerte, y que
quien lo mato era de tu equipo. La ventana de 3 s es la misma que usa r6-dissect.

| Metrica | Definicion |
|---|---|
| **Muerte tradeada** | Alguien vengo tu muerte en la ventana. Tu muerte costo poco: intercambiaste. |
| **Muerte sin trade** | Moriste y nadie te vengo. Es la muerte que realmente pierde rondas: tu equipo queda 4v5 gratis. Un porcentaje sobre 65% casi siempre significa que juegas muy separado o muy adelantado. |
| **Trade kills** | Veces que **tu** mataste al asesino de un compañero dentro de la ventana. |

## Impacto

| Metrica | Definicion |
|---|---|
| **KST** | Rondas donde mataste, sobreviviste o tu muerte se tradeo, sobre el total. Es el clasico KOST **sin la O** de objetivo, porque los eventos de plant/defuse no estan disponibles (ver `formato-rec.md`). Bajo 65% significa que hay muchas rondas donde tu equipo jugo con uno menos. |
| **1vX (clutch)** | Rondas donde quedaste ultimo de tu equipo y ganaste. El `X` es la cantidad de rivales vivos cuando quedaste solo. Se calcula con la misma logica que r6-dissect. |
| **Multikill** | Rondas con 2 o mas bajas. |
| **Mueres a los** | Promedio de segundos de la fase de accion hasta tu muerte. Se saca del reloj de la ronda: `reloj_inicial - reloj_de_tu_muerte`. Un promedio bajo (menos de 45-50 s) significa que te estas perdiendo la mayor parte de la ronda. |

## Cortes

| Dimension | Nota |
|---|---|
| **Lado** | Ataque o defensa. Se deduce de los operadores de cada equipo, no de un campo del replay. |
| **Mapa** | Las variantes por temporada del mismo mapa (Border, BorderY10, ...) colapsan al mismo `slug`, asi que el historial no se parte cuando Ubisoft revampea un mapa. |
| **Sitio** | El sitio de bomba, tal como lo nombra el juego (`2F Gym, 2F Bedroom`). En defensa es tu setup; en ataque es lo que estas atacando. |
| **Spawn** | Solo tiene sentido en ataque: es la posicion exterior desde donde arrancaste. En defensa el replay pone el sitio en ese campo. |
| **Operador** | El operador con el que terminaste la ronda (si hiciste swap en preparacion, queda el ultimo). |
| **Numero de ronda** | Para ver si te caes en las rondas finales. |

## Sobre el mapa de calor

El `.rec` **no expone coordenadas** de las bajas, asi que no hay heatmap de
posiciones sobre el minimapa. El "mapa de calor" de la app es una matriz
mapa x sitio (y mapa x spawn) coloreada por winrate, que es la granularidad
espacial real que entrega el formato.

## Muestra minima

Los agregados de la UI filtran por `min_rounds` y el coach exige muestra antes de
opinar:

| Regla | Muestra minima |
|---|---|
| Cualquier insight | 20 rondas totales |
| Duelos de apertura | 20 duelos (15 por lado) |
| Trades / KST / aim | 30 muertes / 40 rondas / 40 bajas |
| Mapa | 15 rondas en ese mapa |
| Operador | 12 rondas con ese operador |
| Sitio / spawn | 8 rondas |

Con 3 partidas importadas el coach te va a decir que faltan datos. Es a proposito.
