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

## Rating

Un solo numero que resume cuanto aportaste en una ronda, para poder comparar
cortes entre si sin mirar ocho columnas.

**El 1.00 es tu propio promedio.** No hay un promedio global de jugadores en
este proyecto (solo existen tus replays), asi que la referencia eres tu: 1.20 en
un mapa significa que ahi rindes un 20% sobre tu ronda tipica. El promedio se
calcula sobre **todo** tu historial y no cambia con los filtros; si cambiara, el
rating de un mapa y el de un operador no serian comparables entre si.

### Como se calcula

Cada ronda suma puntos:

| Evento | Puntos | Por que |
|---|---|---|
| Base | **+1.0** | Piso, para que una ronda mala no termine en negativo. |
| Baja | **+1.0** | La unidad de la escala: todo lo demas se mide contra una baja. |
| Sobrevivir | **+0.3** | Vale, pero mucho menos que una baja: seguir vivo es poder retomar o cerrar. |
| Ganar la apertura | **+0.5** | El primer duelo es el que mas mueve la ronda. |
| Perder la apertura | **-0.5** | Simetrico. |
| Trade kill | **+0.3** | Es una baja que ademas deshace una perdida de tu equipo. |
| Muerte sin trade | **-0.4** | La mas cara: tu equipo queda con uno menos, gratis. |
| Clutch (1vX ganado) | **+0.7** | Cerrar la ronda solo es excepcional. |

```
rating = puntos promedio del corte / puntos promedio de todo tu historial
```

Una ronda tipica (una baja, muerte sin trade) son 1.6 puntos. La peor ronda
posible (perder la apertura y morir sin trade) son 0.1. Una ronda de 3 bajas con
apertura, trade y clutch, 5.8.

### Lo que hay que tener claro

- **Los pesos son un juicio, no una medicion.** Estan puestos por el impacto que
  cada evento tiene en ganar la ronda, y se dejan a la vista en
  `RATING_WEIGHTS` (`analytics/aggregates.py`) justamente para que se puedan
  discutir y cambiar. Si los cambias, los numeros historicos cambian con ellos.
- **No es el rating de nadie mas.** No es el de Siege.GG ni el de ningun sitio:
  se inspira en la idea, pero la formula y los pesos son de aca.
- **No compara jugadores.** Esta normalizado contra ti mismo, asi que el rating
  de otra persona calculado igual no seria comparable con el tuyo.
- **No incluye si la ronda se gano.** Es aporte individual: el resultado de la
  ronda depende de otras cuatro personas. Para eso esta el winrate, y mirar los
  dos juntos es lo interesante: rating alto con winrate bajo significa que estas
  rindiendo y perdiendo igual.
- **Como numero suelto no dice nada**: el rating de todo tu historial es 1.00 por
  definicion. Sirve en las tablas, comparando cortes.

## Sesiones

Una **sesion** es un bloque de juego seguido: se corta cuando pasan mas de
`SESSION_GAP_MINUTES` (120 por defecto) sin empezar una partida. El corte se
calcula sobre **todo** el historial, no sobre lo filtrado: si filtras por mapa,
esa partida sigue siendo la tercera de su noche.

| Metrica | Definicion |
|---|---|
| **Posicion en la sesion** | Si fue tu 1a, 2a, 3a... partida de ese bloque. De la 5a en adelante se juntan en un tramo: las sesiones largas son pocas y cada posicion suelta no junta muestra. |
| **Curva de la sesion** | Las metricas de siempre (winrate, KPR, aperturas, momento de la muerte) cortadas por posicion. Responde "juego peor despues de la tercera" con el numero. |
| **Caida de sesion** | Diferencia en puntos de winrate entre las 2 primeras partidas y de la 3a en adelante. El coach opina desde 30 rondas de cada lado y 10 puntos de diferencia. |

El corte de la 3a partida esta fijo a proposito: probar varios cortes y quedarse
con el que mas conviene es la forma barata de encontrar patrones que no existen.

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

Un trade es que **mataron a tu asesino dentro de la ventana** de tu muerte, y que
quien lo mato era de tu equipo. La ventana son 3 segundos por defecto, igual que
r6-dissect, y se cambia con `TRADE_WINDOW_SECONDS` en el `.env`; las planillas de
Pro League usan hasta 10.

El numero mueve bastante: sobre el historial de prueba, pasar de 3 a 10 segundos
baja las muertes sin trade de 97.3% a 91.2% y sube el KST de 45.5% a 49.1%. Como
los trades se guardan calculados al importar, despues de cambiarlo hay que correr
`manage.py recompute`, que no vuelve a leer los `.rec`. La app dice siempre con
que ventana estan calculados los numeros que muestra.

| Metrica | Definicion |
|---|---|
| **Muerte tradeada** | Alguien vengo tu muerte en la ventana. Tu muerte costo poco: intercambiaste. |
| **Muerte sin trade** | Moriste y nadie te vengo. Es la muerte que realmente pierde rondas: tu equipo queda 4v5 gratis. Un porcentaje sobre 65% casi siempre significa que juegas muy separado o muy adelantado. |
| **Trade kills** | Veces que **tu** mataste al asesino de un compañero dentro de la ventana. |

## Duelos

Un duelo es una baja entre tu y alguien del **equipo contrario**, en cualquiera
de las dos direcciones. Sale del kill feed, no del scoreboard.

| Metrica | Definicion |
|---|---|
| **Duelo** | Una baja tuya sobre un rival, o de un rival sobre ti. Los teamkills no cuentan: se descartan comparando el equipo de los dos en esa ronda, porque la misma persona puede ser companero en unas rondas y rival en otras. |
| **Duelos ganados %** | Bajas a favor / duelos. No es lo mismo que el K/D: aca no entran las muertes sin asesino registrado. |
| **Balance** | Bajas a favor menos bajas en contra, contra ese rival u operador. |
| **Duelo de apertura** | El duelo fue la primera baja de la ronda. Perder siempre el primer contacto contra la misma persona es un problema distinto a perder duelos en general. |
| **Operador rival** | El operador que tenia el rival **en esa ronda**, sacado de su fila del scoreboard: el kill feed del `.rec` no trae el operador dentro del evento. |

En ranked solo los rivales casi no se repiten, asi que la tabla por persona es
anecdota antes que patron: el coach solo opina desde 8 duelos contra la misma
persona. La tabla por operador si junta muestra rapido, y es la que suele
mostrar algo util.

## Impacto

| Metrica | Definicion |
|---|---|
| **KST** | Rondas donde mataste, sobreviviste o tu muerte se tradeo, sobre el total. Es el clasico KOST **sin la O** de objetivo, porque los eventos de plant/defuse no estan disponibles (ver `formato-rec.md`). Bajo 65% significa que hay muchas rondas donde tu equipo jugo con uno menos. |
| **1vX (clutch)** | Rondas donde quedaste ultimo de tu equipo y ganaste. El `X` es la cantidad de rivales vivos cuando quedaste solo. Se calcula con la misma logica que r6-dissect. |
| **Multikill** | Rondas con 2 o mas bajas. |
| **Cuando mueres** | La distribucion completa, en tramos de 30 segundos y separada por lado. El promedio esconde la forma: morir siempre a los 100s no es lo mismo que morir mitad a los 20 y mitad a los 170, y las dos cosas se arreglan distinto. |
| **Sales muy temprano** | Muertes en los primeros 30 **segundos jugados**. La ronda todavia no se arma: mueres sin informacion. El coach opina desde 25 muertes del lado y un 25% concentrado ahi (el reparto uniforme daria 17%). |
| **Te quedas sin tiempo** | Muertes con menos de 30 segundos **de reloj**. Es otro eje: no importa cuanto jugaste, importa que la ronda ya estaba decidida. En ataque significa que la ejecucion nunca llego a empezar. |
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
| **Sesion** | Bloque de juego seguido, y posicion de la partida dentro de el. Ver la seccion Sesiones. |
| **Rating** | Aporte por ronda contra tu propio promedio. Aparece en casi todas las tablas. Ver la seccion Rating. |
| **Rival** | Duelos contra una persona o contra un operador rival. Ver la seccion Duelos. |
| **Con y sin** | Tus numeros en las rondas que compartiste con alguien, contra el resto de tu historial. Es la unica forma de ver si con esa persona rindes distinto, pero el lado "sin" suele tener poca muestra: la app lo avisa bajo 20 rondas. |
| **Compañero** | Winrate de las rondas que esa persona jugo **en tu equipo**, no su winrate por separado. Se agrupa por jugador (profileID), asi que un cambio de nick no parte el historial. Con menos de 25 rondas compartidas es varianza. |

## Resumen de la ronda

El detalle de cada partida trae dos o tres frases por ronda, generadas de los
eventos. No hay nada inventado: cada frase se escribe solo si su dato existe, y
si no existe simplemente no aparece. Lo que puede decir:

| Frase | De donde sale |
|---|---|
| Quien se llevo el primer duelo y cuando | Primer evento de baja de la ronda. Si no trae asesino (evento `Death` suelto) lo dice en vez de suponer uno. |
| Si esa muerte se vengo, y con cuanto margen | El flag `traded` del evento y la baja que la vengo dentro de la ventana de trade. |
| **Segundos jugados en inferioridad** | Se recorre el feed llevando la cuenta de vivos por equipo. Es el numero que explica por que se pierde una ronda sin que nadie juegue mal despues del 4v5. |
| Que hiciste tu | Tu fila del scoreboard de esa ronda: bajas, trades, clutch, si moriste y cuando. |
| Como se cerro | `win_condition`. Si el replay no lo expone (temporadas nuevas), lo dice asi, con el plant marcado como probable. |

No se guarda en la base: es texto derivado y cambia si cambian las metricas.

## Sobre el mapa de calor

El `.rec` **no expone coordenadas** de las bajas, asi que no hay heatmap de
posiciones sobre el minimapa. El "mapa de calor" de la app es una matriz
mapa x sitio (y mapa x spawn) coloreada por winrate, que es la granularidad
espacial real que entrega el formato.

## Progreso

Comparar lo reciente contra lo inmediatamente anterior es la unica forma honesta
de decir "mejore". Dos modos: por **partidas** (las ultimas N contra las N
anteriores, que siempre tiene muestra de los dos lados si jugaste 2N) y por
**dias**.

| Metrica | Definicion |
|---|---|
| **Cambio** | La diferencia entre los dos periodos, en puntos o en la unidad de la metrica. |
| **Banda de ruido** | Error estandar de la diferencia entre las dos proporciones: `sqrt(p1(1-p1)/n1 + p2(1-p2)/n2)`. Es **cuanto se mueve sola** una metrica con esa cantidad de rondas. Si el cambio no pasa la banda, la app lo marca como ruido y no como mejora ni empeora. |

Un ejemplo real de por que hace falta: 10 partidas contra las 10 anteriores dio
un winrate 9.3 puntos mas bajo. Suena a bajon, pero con ~50 rondas por lado la
banda es de 9.6 puntos: ese cambio no existe. En la misma comparacion, KST bajo
15.2 con banda de 9.6, y ese si.

La banda solo se calcula para porcentajes. En K/D, KPR, rating y "mueres a los"
no se puede con esta informacion, asi que la flecha muestra la direccion pero no
afirma que el cambio sea real.

**"Mueres a los" no se juzga**: subir puede ser que sobrevivas mas o que llegues
tarde a todo, asi que se muestra sin flecha de bueno o malo.

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
