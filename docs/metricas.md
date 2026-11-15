# Metricas: que significa cada numero

Todas se calculan en `backend/replays/analytics/metrics.py` (por ronda, al
importar) y se agregan en `aggregates.py`. Si un numero de la UI no te cuadra,
aca esta la definicion exacta.

## Base

| Metrica | Definicion |
|---|---|
| **Rondas** | Rondas tuyas importadas que pasan los filtros activos. |
| **Rondas ganadas (winrate)** | Rondas donde tu equipo gano / rondas jugadas. Es winrate **de rondas**, no de partidas: mide mejor porque una partida son 6-9 muestras. |
| **Partidas ganadas** | Partidas ganadas / partidas con ganador (`won` conocido). Empates e incompletas quedan fuera del denominador y se cuentan aparte ("sin resultado"). Las partidas las eligen los filtros menos el lado: un lado no parte una partida. Una partida queda incompleta (sin ganador, `won` nulo) cuando su marcador final no la cierra segun la regla de su tipo (`reglas_partida.py`: hoy solo Ranked desde Y9S4, primero a 4 con prorroga a 5); p. ej. 3-2 o 4-3 por un `.rec` faltante. Un tipo sin regla se decide por mas rondas. Lo importado antes se corrige con `manage.py recompute`. Limite: una rendicion antes de llegar a 4 tambien queda incompleta. |
| **Racha actual de partidas** | Partidas seguidas con el mismo resultado, contando hacia atras desde la mas reciente (orden `played_at`, `id`), sobre las partidas del filtro sin el lado (como Partidas ganadas). Las partidas sin resultado (empate o incompleta, `won` nulo) no cortan ni suman la racha. "Desde" es la fecha de la mas vieja de la racha. Con filtro de lado, la forma reciente (que si lo usa) puede no coincidir con la racha. Inicio, panel Últimas partidas. |
| **Rondas por partida** | Todas tus rondas importadas de esas partidas / partidas, con un decimal. La partida se lee entera: el operador o el sitio filtrado no recortan sus rondas. |
| **Mejor y peor mapa** | Winrate de partida por mapa (las variantes de temporada de un mapa cuentan juntas), entre los mapas con 3 o mas partidas con ganador. Desempata por mas partidas y despues por nombre. El peor solo aparece si esta por debajo del mejor: con un solo mapa o todos empatados queda vacio. |
| **Bajas / muertes** | Del kill feed. Una muerte es "moriste en esa ronda", no cuenta dos veces. Las bajas son solo a rivales: un teamkill o un suicidio registrado como baja no cuentan (una baja sobre un nick que no figura en la ronda si cuenta). Lo importado antes se corrige con `manage.py recompute`. |
| **K/D** | bajas / muertes. |
| **KPR** | bajas / rondas. Mas honesto que el K/D porque no premia esconderse. Referencia razonable en ranked: 0.7-0.9. |
| **HS%** | headshots / bajas. El replay marca el headshot en cada kill; solo cuentan los de bajas a rivales, asi que nunca pasa de 100. |
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

## Mitades y prorroga

En Tendencias, la partida se corta por mitades sin suponer cuantas rondas
tiene cada modo: la mitad se deduce del lado de cada ronda.

| Metrica | Definicion |
|---|---|
| **Primera / segunda mitad** | Rondas sin prorroga. Primera mitad: las jugadas en el lado inicial de la partida; segunda: las del otro lado. Las metricas (ganadas, rating, KPR, aperturas) son las de siempre sobre ese corte. Rondas sin lado, o de una partida sin lado inicial, no entran en ninguna. Si faltan los `.rec` de la primera mitad, la segunda se lee como primera. |
| **Prorroga** | Rondas con `overtimeRoundNumber > 0` en la cabecera del `.rec`. Sin prorroga la fila sale en 0 y con metricas vacias. **Prórroga por lado** (*Prórroga en ataque* / *en defensa*) parte esas mismas rondas por el lado de tu ronda de prorroga (`Round.my_side`), con las columnas de las mitades; las rondas de prorroga sin lado (`my_side` vacio) no entran en ninguna de las dos, asi que pueden sumar menos que la fila de arriba; los filtros globales aplican y con el de lado sale solo esa fila. Aviso de muestra con 30 rondas, como los cortes de Tendencias; sin rondas de prorroga, una nota y no ceros. |
| **Partidas a prórroga por lado** (columnas *Partidas* y *Partidas ganadas* de la tabla Prórroga por lado) | Partidas con al menos una ronda de prorroga (`overtime_number > 0`) entre tus rondas filtradas, partidas por el lado de tu primera ronda de prorroga (menor `overtime_number`, despues menor `number`; su `Round.my_side`). *Partidas ganadas* = ganadas sobre las que tienen resultado (`Match.won` no nulo): las incompletas cuentan en *Partidas* y no en el porcentaje. Se lee de la partida entera: el filtro de lado elige la fila, no cambia el lado con que arrancaste la prorroga. Lado vacio no entra en ninguna fila; un lado sin partidas muestra `—`. Aviso de varianza con menos de 10 partidas en un lado, como *Margen final*. No es el winrate de ronda de las columnas de la izquierda, que parten cada ronda por su propio lado. |
| **Lado inicial** | El lado de tu ronda de numero mas bajo sin prorroga. Se lee de la partida entera: el filtro de lado limita las rondas, no cambia con que lado arrancaste. Ganadas = partidas ganadas sobre las que tienen resultado; las incompletas cuentan en Partidas pero no en el porcentaje. |
| **Lado inicial por mapa** | El mismo lado inicial, separado por version de mapa (la misma etiqueta que Mapas: "Consulate (Y10)" no se mezcla con la vieja). Ganadas en ataque y en defensa = partidas ganadas sobre las que tienen resultado, solo con 3 o mas partidas con resultado en ese lado; con menos sale "—" y la fila dice "Poca muestra". Diferencia = ataque menos defensa, en puntos. Margen = 2 errores estandar con la proporcion de los dos lados juntos (no colapsa con 100 % o 0 %); si la diferencia no lo supera, "Dentro del ruido". |
| **Primera ronda de cada lado** | Ronda 1: tu ronda sin prorroga de numero mas bajo de la partida. Primera tras el cambio: la ronda sin prorroga de numero mas bajo cuyo lado no es el inicial (una partida que nunca cambio de lado no tiene). Resto: tus demas rondas sin prorroga con lado. La prorroga no entra en ninguna fila. Se lee de la partida entera: el filtro de lado limita las rondas, no cambia cual es la primera. Si faltan los `.rec` del arranque, la primera ronda que quedo se lee como "Ronda 1"; si falta el de la primera ronda del otro lado, la siguiente se lee como "Primera tras el cambio". |

## Modo de juego

En Tendencias, y como filtro "Modo" de la barra cuando la base tiene mas de un
modo o hay uno elegido (un enlace con `?gamemode=`).

| Metrica | Definicion |
|---|---|
| **Por modo** | Tus partidas agrupadas por el modo de la cabecera del `.rec` (Bomba, Rehén, Área segura, Bomba rápida; un id que el parser no conoce sale como `Unknown(<id>)`, y una partida sin modo como "Sin modo"). Partidas = partidas con alguna ronda tuya que pasa los filtros. Ganadas = partidas ganadas sobre las que tienen resultado; se lee de la partida entera, como "Lado inicial". Rondas ganadas, K/D y rating: las de siempre sobre las rondas de ese modo. |

## Contexto de la ronda

En Tendencias, cada ronda se corta tambien por lo que paso antes de ella en la
misma partida.

| Metrica | Definicion |
|---|---|
| **Despues de ganar / perder** | Rondas cuya ronda anterior (la de numero `N - 1` en la misma partida) tu equipo gano o perdio. La anterior se lee de la partida entera: el filtro de lado o de operador limita las rondas que se cuentan, no cambia cual fue la anterior. La primera ronda, la que no tiene importada la anterior (falta su `.rec`) y la que tiene la anterior sin resultado van a "Sin ronda anterior". Las tres filas suman todas tus rondas. Las metricas (ganadas, rating, KPR, aperturas) son las de siempre sobre ese corte. |
| **Segun el marcador** | Rondas en que tu equipo llegaba adelante, empatado o atras: el marcador al empezar la ronda (`startingScore` de cada equipo en el `.rec`, guardado en `Round.score_before`), tu equipo contra el otro. No depende de a cuanto se gana el modo, asi que vale igual en ranked, unranked o rapida. Una ronda de una partida anterior a Y9S4 (el `.rec` no trae el marcador y se guarda 0-0), sin marcador o con un marcador que no es de dos equipos va a "Sin marcador", que solo se muestra si tiene rondas. Las cuatro filas suman todas tus rondas. |
| **Match point** | Rondas segun si alguien podia cerrar la partida ganandola, leido del marcador antes de la ronda (el mismo de "Segun el marcador"). *Tu match point*: tu equipo gana la partida si gana esa ronda; *match point rival*: al reves; *los dos a una ronda*: las dos cosas. Depende de a cuanto se gana cada tipo de partida, que sale de una tabla con fuente (`replays/analytics/reglas_partida.py`): hoy solo ranked (gana a 4; con 3-3 hay prorroga y gana el primero a 5, asi que 3-3 no es match point y 4-4 es de los dos). Unranked, rapida y custom no tienen regla confirmada y van a "Sin marcador o sin regla", junto con las rondas sin marcador o anteriores a Y9S4; esa fila solo se muestra si tiene rondas. Las cinco filas suman todas tus rondas. |
| **Como se cierran tus rondas** | Tus rondas de cada lado (ataque, defensa) segun como terminaron, de `Round.win_condition` y `Round.my_team_won`. *Por eliminacion*: el equipo perdedor termino con todos muertos (`KilledOpponents`). *Sin eliminacion*: hubo ganador sin que nadie quedara eliminado del todo (`ObjectiveOrTime`); el `.rec` de temporadas nuevas no dice si fue plant, defuse o tiempo, asi que es inferido del reloj y nunca se separa. Un plant seguido de la eliminacion de los atacantes y un defuse cuenta como eliminacion. *Sin dato*: ronda sin ganador o sin condicion. Los porcentajes son sobre tus ganadas (o perdidas) con dato, y entre parentesis va el conteo de rondas. Las cinco columnas de conteo suman todas tus rondas de ese lado; las rondas sin lado no entran. |
| **Duracion de la ronda** (panel "Rondas cortas y largas") | `Round.clock_start - Round.clock_end`: segundos absolutos de la fase de accion. Tramos fijos `0-45`, `45-90`, `90-135` y `135 o mas`, con el borde cerrado abajo (45 s exactos es `45-90`). Una ronda que llega al final del reloj termina con `clock_end = 1` y cae en el ultimo tramo: en ataque es derrota y en defensa victoria. *Posible plant* (`Round.possible_plant`) no entra en ningun tramo: va a su propia fila y solo se cuenta, sin winrate, rating ni promedios, porque no es una metrica de plant. Un plant que termina en barrida no se marca y entra a un tramo con la duracion hasta el plant; el `.rec` no deja separarlo. Reloj desconocido (`clock_start` o `clock_end` en 0) queda fuera de todas las filas y se cuenta aparte. Winrate (`RoundPlayer.won`), rating y KPR son los de siempre sobre las rondas del tramo. El lado es el de tu fila; *Total* incluye las rondas sin lado. **Cuanto tardas en ganar / perder**: promedio de la duracion de tus rondas ganadas / perdidas (`Round.my_team_won`) de los cuatro tramos, sin posible plant ni rondas sin ganador, con un decimal en la API y redondeado a segundos en la UI. Aviso de varianza con menos de 30 rondas en una celda. |

## Remontadas y derrumbes

Panel de Tendencias. Solo partidas desde Y9S4 (antes el `.rec` no trae el
marcador), con resultado, con todas sus rondas importadas y con el marcador legible
(dos equipos) en todas: una ronda que falta (tambien las primeras: la primera presente tiene que arrancar 0-0) o ilegible saca la partida entera. Si faltan las ultimas no se nota: el resultado de la partida sale del ultimo `.rec` importado, para este panel y para toda la app. Los filtros eligen
partidas y cada partida se lee entera, como en "Lado inicial".

| Metrica | Definicion |
|---|---|
| **Desventaja / ventaja maxima** | El peor (o mejor) `tus rondas - las del rival` del marcador antes de cada ronda (`Round.score_before`, leido con tu `team_index`). Cuenta el marcador antes de la ultima ronda, no el final: perder 3-4 desde 3-2 es ventaja maxima 1. |
| **Remontada** | Partida ganada con desventaja maxima de 2 o mas rondas. El corte de 2 es fijo: con 1 entraria toda partida que perdiste la primera ronda. Se listan las 20 de mayor desventaja (a igual, la mas reciente) y se cuentan todas. |
| **Derrumbe** | Partida perdida con ventaja maxima de 2 o mas rondas. Mismo tope y orden que las remontadas. |
| **Winrate segun la diferencia al cambio de lado** | Partidas y winrate de partida segun `tus rondas - las del rival` antes de la primera ronda de la segunda mitad: la primera ronda sin prorroga cuyo lado es distinto del de la ronda mas baja sin prorroga (la misma frontera que "Mitades y prorroga"). Tramos `+2 o mas`, `+1`, `Empatado`, `-1`, `-2 o menos`; las cinco filas se muestran aunque esten en 0. Una partida sin ronda de segunda mitad importada no entra. |
| **Margen final** (panel "Partidas cerradas y holgadas") | Partidas, ganadas y winrate de partida segun `abs(Match.my_score - Match.opponent_score)`, el marcador final. Tramos `Prorroga` (alguna ronda con `overtime_number > 0`; gana a cualquier margen), `1 ronda`, `2 rondas`, `3 o mas`; las cuatro filas se muestran aunque esten en 0. Corte propio, mas laxo que el de arriba: basta con que la partida sea Y9S4 o posterior y tenga resultado; no exige todas las rondas. Pre-Y9S4, empates y sin resultado quedan fuera y se cuentan aparte. `side` se ignora (no parte una partida). Rating y KPR del tramo sobre todas tus rondas de esas partidas, sin recortar por operador ni sitio. Aviso de varianza con menos de 10 partidas en un tramo. |

## Sesiones

Una **sesion** es un bloque de juego seguido: se corta cuando pasan mas de
`SESSION_GAP_MINUTES` (120 por defecto) sin empezar una partida. El corte se
calcula sobre **todo** el historial, no sobre lo filtrado: si filtras por mapa,
esa partida sigue siendo la tercera de su noche.

| Metrica | Definicion |
|---|---|
| **Posicion en la sesion** | Si fue tu 1a, 2a, 3a... partida de ese bloque. De la 5a en adelante se juntan en un tramo: las sesiones largas son pocas y cada posicion suelta no junta muestra. |
| **Curva de la sesion** | Las metricas de siempre (winrate, KPR, aperturas, momento de la muerte) cortadas por posicion. Responde "juego peor despues de la tercera" con el numero. |
| **Después de perder seguido** (panel de Tendencias) | Winrate de **partida** (no de rondas) de la partida siguiente segun cuantas derrotas seguidas llevabas en la sesion: filas *Sin derrotas antes*, *Tras 1 derrota*, *Tras 2 derrotas* y *Tras 3 o más*. Las sesiones son las de "Sesion" (corte de `SESSION_GAP_MINUTES`, sobre **todas** las partidas) y se recorren en orden de `played_at` con un contador que arranca en 0: la partida se anota en la fila `min(racha, 3)` y despues una derrota suma 1, una victoria lo vuelve a 0, y empate o incompleta (`match_result`) no lo tocan. La racha se mide sin filtros (un filtro de mapa no inventa ni borra rachas); los filtros de mapa, tipo, modo, fechas y sesion eligen que partidas se cuentan, y lado, operador y sitio se ignoran como en `match_queryset`. *Partidas* las cuenta todas; *Decididas* (el `n`) solo victorias y derrotas, y *Ganadas* = victorias / decididas. Las cuatro filas salen siempre; sin partidas, una nota y no ceros. Aviso de varianza con menos de 10 partidas decididas en una fila, como *Margen final*. `GET /api/sessions/`, clave `by_losing_streak`. |
| **Resultado de la sesion** | Partidas ganadas y perdidas de la sesion (`1G 0P`), solo las que cumplen los filtros. Las que no tienen resultado (empate o partida sin cerrar, `won` nulo) no son ni una ni otra: en el texto copiado salen como "N sin resultado". |
| **Mejor / peor partida de la sesion** | La de mayor y menor rating de tus rondas en esa partida, entre las que cumplen los filtros y tienen rating. Solo con dos partidas o mas; si todas tienen el mismo rating no hay peor. Empate: la jugada antes. Se ve en las columnas Mejor y Peor de la tabla Sesiones de Tendencias (cada una enlaza a su partida; sin partida, `—`) y en el texto del boton "Copiar". |
| **Caida de sesion** | Diferencia en puntos de winrate entre las 2 primeras partidas y de la 3a en adelante. El coach opina desde 30 rondas de cada lado y 10 puntos de diferencia. |

El corte de la 3a partida esta fijo a proposito: probar varios cortes y quedarse
con el que mas conviene es la forma barata de encontrar patrones que no existen.

## Records

El panel **Tus récords** del Resumen. Se calculan con los filtros activos. En
todos, a igual valor gana la partida (o el dia) mas reciente: igualar un record
lo mueve a la partida nueva. Sin candidato el record no aparece; nunca se
muestra un 0 inventado.
Cada record enlaza a su partida; los de ronda (mas bajas en una ronda, clutch
mas grande y racha de rondas) abren el detalle parado en esa ronda
(`/partidas/<id>#ronda-<n>`, la ronda donde empieza la racha).

| Metrica | Definicion |
|---|---|
| **Mejor partida** | El rating de partida mas alto (el de "Rating") entre las partidas con al menos 6 rondas tuyas (`RECORD_MIN_RONDAS_PARTIDA`). |
| **Mas bajas en una partida** | La suma de tus bajas mas alta en una partida. Sin ninguna baja, no hay record. |
| **Mas bajas en una ronda** | El maximo de bajas tuyas en una ronda, con la etiqueta de la ronda (`R1`, `R2`...). A igual valor y misma partida, la ronda mas tardia. |
| **Clutch mas grande** | El 1vX ganado de X mas alto (`one_vx` de una ronda que tu equipo gano). Sin clutches ganados, no hay record. |
| **Racha de rondas** | Las rondas ganadas seguidas mas largas de una partida, con la etiqueta de la ronda donde empieza. Se mide sobre todas las rondas de la partida, prorroga incluida: el filtro elige partidas, no rondas (con un filtro de lado no habria rachas, porque los lados alternan). La cortan una ronda perdida, una ronda sin resultado y un hueco en la numeracion (falta un `.rec`). En el encabezado del detalle de partida se muestran tambien las perdidas seguidas, con la misma regla; ahi, a igual largo, queda la primera racha de la partida. |
| **Mejor dia** | El winrate de rondas mas alto en un dia con al menos 20 rondas tuyas (`RECORD_MIN_RONDAS_DIA`); empata a favor de mas rondas ganadas y despues del dia mas reciente. No enlaza a una partida. Los dos minimos son a ojo. |

## Cuando juegas

En Tendencias, tus rondas cortadas por el momento en que empezo la partida. La
hora es la que guardo tu PC al grabar el replay, tal cual (sin zona horaria ni
conversion). Una partida cuenta entera en la franja y el dia en que empezo,
aunque termine pasada la medianoche. Las filas son fijas: una franja sin rondas
sale en 0, y cada lista suma todas tus rondas. Las metricas (ganadas, rating,
KPR, aperturas) son las de siempre sobre ese corte, con el aviso de muestra
minima de abajo.

| Metrica | Definicion |
|---|---|
| **Por hora del dia** | Ocho franjas de 3 horas (0–3, 3–6, ..., 21–24) segun la hora de inicio de la partida. El borde es la hora en punto: una partida de las 2:59 cae en 0–3 y una de las 3:00 en 3–6. |
| **Por dia de la semana** | Lunes a domingo segun el dia de inicio de la partida. |

## Duelos de apertura

La **primera baja de la ronda** define el duelo de apertura. Quien mata lo gana,
quien muere lo pierde. Si la primera muerte no tiene asesino registrado (evento
`Death` suelto), cuenta como apertura perdida para quien murio.

| Metrica | Definicion |
|---|---|
| **Duelos de apertura** | Aperturas ganadas + perdidas. Solo cuenta las rondas donde estuviste en el primer contacto. La apertura es la primera baja de la ronda, aunque sea un teamkill (no cuenta en Bajas, si aca). |
| **Aperturas ganadas %** | ganadas / (ganadas + perdidas). |
| **Winrate tras ganar la apertura** | Rondas ganadas entre las rondas donde te llevaste la primera baja. En Siege esta arriba del 70% para casi cualquier jugador: por eso el primer duelo importa tanto. |
| **Winrate tras perder la apertura** | Lo mismo del otro lado. |
| **Aperturas limpias, devueltas y vengadas** | Las aperturas partidas por trade, con el winrate de ronda de cada grupo. *Ganada devuelta*: ganaste la apertura y esa baja quedo tradeada (el equipo de tu victima te mato dentro de la ventana de trade; justo en el borde cuenta, igual que *Muertes tradeadas*); es la misma marca "tradeada" del timeline. *Ganada limpia*: el resto de tus aperturas ganadas; tambien queda limpia si moriste enseguida por un teamkill, por un `Death` sin autor o si la victima no figura entre los jugadores. *Perdida vengada*: perdiste la apertura y un compañero vengo tu muerte en la ventana (`was_traded`). *Perdida sin vengar*: el resto, incluido el `Death` sin autor. Ganada limpia + devuelta = aperturas ganadas y vengada + sin vengar = perdidas. Se calcula al importar (`opening_kill_traded`); cambiar la ventana se aplica con `manage.py recompute`. Sin muestra el winrate queda vacio. El Rating no cambia. Página Resumen, panel *Aperturas que pesan*. |
| **Entry kill** | La primera baja **de tu equipo** en la ronda (distinto de la primera de la ronda: si el rival abrio, tu entry sigue estando en juego). |
| **Primero de tu equipo en caer** | En cada ronda tuya, quien de tu equipo tiene la menor hora de muerte (`death_elapsed`). Es la primera baja **de tu equipo**, no de la ronda: si antes cayó un rival, sigue contando (distinto de la apertura perdida de *Duelos de apertura*). Si nadie de tu equipo tiene hora de muerte (no perdió a nadie, o el feed no la registró), la ronda va a *Sin bajas*. Empate en el mismo segundo, o una hora en 0 (evento sin reloj): cae primero quien aparece antes en el feed; si falta el evento de alguno, la ronda cuenta para el compañero. Página Compañeros, panel *Primero en caer*, por lado y total. El % junto a *Caíste primero* y *Cayó un compañero* es sobre todas las rondas del lado, incluidas las *Sin bajas*. |
| **Rondas que tu equipo ganó sin ti** | Tus rondas con `died=True` y ganador conocido (`Round.my_team_won` no nulo). *Ganadas*: las que gano tu equipo; *% ganadas* = ganadas / rondas en que caiste, por el lado de tu fila y total; con filtro de lado sale ese lado y el total. *Quién la sostiene*: por compañero habitual (la regla de *Clutches de tus compañeros*: 5 partidas en tu equipo, todo el historial, por `Player`), de esas rondas ganadas con el en tu equipo (`team_index` de tu fila), en cuantas seguia vivo al final (`survived` en su fila) y que % es. Seguir vivo no es haber hecho las bajas. Un * marca menos de 5 rondas (`GANADA_SIN_TI_MIN`): sale igual. Filtros de la barra sobre tu fila. Página Compañeros, panel *Rondas que tu equipo ganó sin ti*. |
| **Winrate cuando caes primero / cuando cae un compañero / sin bajas** | Rondas ganadas sobre rondas de cada grupo de la fila anterior. El lado es el de tu fila de la ronda. |
| **Cuando llega la apertura** | El segundo de fase de accion (`Event.elapsed`) del primer `Kill` o `Death` de la ronda por `order`, el mismo evento que define el duelo de apertura, sea de quien sea. Tramos: *Temprano* < 30 s, *Medio* 30 a 90 s (29.9 es temprano, 30 es medio), *Tarde* >= 90 s, y *Sin bajas* si la ronda no tiene ningun evento de baja. Un evento sin reloj (`elapsed` 0) cae en *Temprano*. Por lado (el de tu fila de la ronda), *Winrate* = rondas ganadas / rondas del tramo; *Primera baja tuya* = rondas donde algun jugador de tu equipo tiene `opening_kill` / rondas del tramo (cuadra con *Duelos de apertura*). En *Sin bajas* no hay primera baja y la columna queda vacia. Rondas sin ganador conocido quedan afuera. Página Tendencias, tabla *Cuándo llega la apertura*; los cortes 30 y 90 son `APERTURA_TEMPRANA` y `APERTURA_TARDIA` en `aggregates.py`. |

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
| **Fuera de posición** | Rondas en que moriste, sin bajas y sin que nadie te vengara / rondas jugadas. Es "te agarraron mal parado": morir peleando (con una baja) o morir y que te venguen no cuenta. Sale en todo agregado y en los CSV (`caught_out_rounds`, `caught_out_pct`). |
| **Muertes tempranas por spawn** | Panel "Salida del spawn" del Coach: rondas de ataque con ese spawn (y mapa, con su version) en que moriste con `0 < death_elapsed < 15` segundos jugados de la fase de accion / rondas de ataque con ese spawn. Los 15 s (`SALIDA_SPAWN_SEGUNDOS`) son la mitad del primer tramo de "Sales muy temprano": a esa altura el atacante todavia sale del spawn o esta en el runout. Un reloj en 0 es "sin reloj" (`metrics.py` escribe 0 cuando el feed no lo trae) y no cuenta, igual que una muerte sin reloj. Las rondas de defensa y las sin spawn no entran. Se compara contra el resto de tu ataque con la misma banda que "Dónde quedas fuera de posición" (`POSICION_BANDAS` errores estandar de la proporcion combinada): *Caes temprano* si la diferencia pasa el margen, *Sales bien* si queda por debajo de menos el margen, *Sin señal* si no. El total del ataque (la nota del panel) se arma antes de la muestra minima. |
| **Repetir el sitio tras perderlo** | Panel del Coach (`/api/positioning/site-after-loss/`). Pares de rondas de defensa consecutivas de la misma partida (por `Round.number`, saltando las de ataque entre medio) cuya primera tu equipo perdio; una sin ganador no es derrota y no abre par. El par se corta si entre las dos falta un numero (ronda sin `.rec` o sin fila tuya) o si alguna no tiene lado o sitio. *Repite* si la segunda es en el mismo sitio, *cambia* si no. Winrate de la segunda ronda sobre las que tienen ganador (una sin ganador cuenta en las rondas, no en el winrate). En total y por mapa (con su version). Mapa, tipo, modo, fechas y sesion aplican; lado y operador no; el filtro de sitio elige el sitio de la ronda perdida. Muestra minima 8 pares por caso (`REPETIR_SITIO_MIN_RONDAS`), en el total y en cada mapa: debajo se avisa "pocas rondas" junto al winrate, no se oculta. |
| **Repetir o cambiar el spawn** | Panel del Coach (`/api/positioning/spawn-after-result/`). Pares de tus rondas de ataque consecutivas de la misma partida (por `Round.number`, saltando las de defensa entre medio), cortados por un numero faltante, una ronda sin lado o una de ataque sin spawn. Separados por el resultado de la primera (*Tras perder*, *Tras ganar*; una primera sin ganador no abre par). *Repite* si la segunda sale del mismo spawn (`RoundPlayer.spawn`), *cambia* si no. Winrate de la segunda sobre las que tienen ganador (una sin ganador cuenta en las rondas, no en el winrate). Mapa, tipo, modo, fechas y sesion aplican; lado no (es siempre ataque); operador y sitio eligen la primera ronda del par. Muestra minima 8 rondas por caso (`REPETIR_SITIO_MIN_RONDAS`, la de la 107): debajo se avisa "pocas rondas" junto al winrate, no se oculta. |
| **Bajas tempranas por spawn** | Tus bajas a rivales con `0 < Event.elapsed < 15` en las rondas de ataque con ese spawn. Los teamkills no cuentan; un reloj en 0 tampoco. |
| **Trade kills** | Veces que **tu** mataste al asesino de un compañero dentro de la ventana. Cuenta bajas, no compañeros vengados: si el rival habia matado a dos y lo matas, es un trade kill (y las dos muertes cuentan como tradeadas). |
| **Trades por equipo** | En el detalle de una partida, por equipo: muertes, tradeadas, sin trade, % sin trade (sobre las muertes de ese equipo; `—` sin muertes) y trade kills. El equipo se toma ronda a ronda (el `team_index` de tu fila; sin tu fila, el de la partida). Misma ventana `TRADE_WINDOW_SECONDS` y mismas columnas que el scoreboard, que ya se guardan al importar; nada se recalcula al consultar. Con tu `team_index` fijo toda la partida (lo normal) es la suma de las filas *Trades* y *Sin trade* de cada equipo del scoreboard; si cambiara en alguna ronda, el panel sigue a tu equipo ronda a ronda y el scoreboard, que agrupa por indice, no. Una muerte por teamkill o sin autor cuenta como sin trade, igual que en el scoreboard. Se resalta el equipo con menos muertes sin trade, menor % sin trade y mas trade kills. |
| **Fases de la ronda** | En el detalle de una partida, las bajas de cada equipo segun los segundos jugados de la fase de accion (`Event.elapsed`): temprano `< 30`, medio `30–120`, tarde `>= 120`. 30 es el mismo corte de "Sales muy temprano" y de la apertura temprana; 120 deja el ultimo minuto de los 180 s como cierre. No usa el 90 de "Cuando llega la apertura" a proposito: ese corte habla de cuando cae la primera baja, no de en que momento de la ronda se pelea. Teamkills (y suicidios), bajas sin reloj (`elapsed` en 0) y bajas de un jugador sin fila en la ronda no van a ningun equipo; las dos ultimas se avisan debajo de la tabla. "Rondas que dominaste": rondas con resultado conocido en que tu equipo saco mas bajas que el rival en esa fase, y cuantas de ellas ganaste (`—` sin rondas); "que dominó el rival" es el espejo; los empates y las fases sin bajas no cuentan en ninguna. El equipo se lee ronda a ronda, como en "Trades por equipo". Agrega lo que dejo el import (`Event.elapsed`, `team_index`, `my_team_won`), sin columnas nuevas ni queries extra, igual que "Trades por equipo". |

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
| **Operadores que te abren** | La apertura es la primera baja de la ronda (`Kill` o `Death` por `order`, la misma de *Duelos de apertura*); cuenta solo si es una baja entre rivales: un teamkill o una muerte sin asesino que abre la ronda no suma a ningun operador. *Te abre*: esa baja fue del rival con ese operador (su fila del scoreboard de la ronda) sobre ti; *Le abres*: tuya sobre el. Una fila por operador y por tu lado de la ronda (`Round.my_side`); los filtros globales aplican y el de lado deja solo ese. *Ganas*: Le abres / (Te abre + Le abres). *De tus aperturas perdidas*: Te abre / todas tus muertes de apertura contra rivales de ese lado, incluidas las de operador vacio o `Unknown(...)`, que no tienen fila (por eso un lado puede sumar menos de 100). Muestra minima: aperturas (Te abre + Le abres) >= la *Muestra minima* de la pagina (3 por defecto). Orden: Te abre descendente. Pagina Duelos, panel *Operadores que te abren*. |
| **Rondas contra un operador** | Rondas tuyas (con los filtros) en que ese operador estuvo en el equipo contrario, haya habido duelo o no. El equipo se lee ronda por ronda comparando `team_index`. Desde 10 rondas. |
| **Mueres (contra un operador)** | Rondas en que moriste / rondas contra ese operador. |
| **Ganas la ronda (contra un operador)** | Rondas ganadas / rondas contra ese operador. |
| **vs. promedio** | Puntos de diferencia entre la tasa contra ese operador y la misma tasa sobre **todas** tus rondas filtradas. En "Mueres" es mejor negativo; en "Ganas" es mejor positivo. No trae banda de ruido: con 10 a 30 rondas, 10 o 15 puntos todavia pueden ser azar. |
| **Rival repetido** | Persona (por profileID, no por nick) que estuvo en el equipo contrario en al menos una de tus rondas filtradas de N partidas distintas. Desde 2 partidas. Un rival que solo aparece en rondas que los filtros por ronda (`side`, `site`, `operator`) dejan afuera no cuenta en esa partida. *Última vez*: la fecha de la partida mas reciente de las que cuenta la fila (con los filtros aplicados). |
| **Récord contra un rival** | Partidas ganadas-perdidas de esas N. El winrate se calcula sobre las que tienen resultado: una partida sin resultado cuenta en Partidas y no en el winrate. Es tu record contra esa persona, no su nivel. |
| **Revanchas esa noche** | En *Rivales repetidos*, cuantas de las partidas filtradas contra ese rival cayeron en una sesion (la de "Sesiones": corte de `SESSION_GAP_MINUTES` sin jugar, calculada sobre todas las partidas) en la que ya lo habias enfrentado antes; la primera partida de cada sesion contra el no cuenta (a igual fecha, la de menor id). Entre parentesis, ganadas-perdidas de esas revanchas; las partidas sin resultado cuentan en el total y no en el record. Es un conteo, sin winrate: con 1 a 3 revanchas por rival un porcentaje seria ruido. `—` sin revanchas (0 en el CSV). Página Duelos. |
| **Stack rival repetido** | Grupo de 2 o mas personas (por profileID) que estuvieron juntas en el equipo contrario en una misma ronda tuya filtrada, en N partidas distintas, desde 2. Un rival que se fue y el que entro en su lugar no forman grupo; una ronda con mas de 10 rivales (dato raro) no arma grupos. Se muestra el grupo mas grande con esas partidas: si A, B y C se repiten juntos, no salen tambien A+B, A+C y B+C con las mismas partidas; un grupo mas chico sale aparte solo si suma alguna partida que el grande no tiene. *Juntos* es cuantas personas tiene el grupo y *Partidas* es N. Record y winrate como en **Récord contra un rival**. El `.rec` no trae nombre de equipo ni de clan: el grupo es solo coincidencia de personas. *Última vez*: la fecha de la partida mas reciente de las que cuenta la fila (con los filtros aplicados). Página Duelos, panel *Stacks rivales que se repiten*. |
| **Stack rival en la partida** | Los **Stacks rivales repetidos** (misma definicion, mismo record) calculados sobre **todo** tu historial, sin los filtros globales, que jugaron en esta partida. Si un grupo esta contenido en otro que tambien jugo esta partida, sale solo el mas grande (A+B no sale si en esta partida estuvieron A, B y C y ese trio tambien se repite). El record cuenta esta partida y es el mismo numero que la fila de Duelos sin filtros (con un filtro global activo, Duelos puede mostrar otro record o no mostrar el grupo); las partidas sin resultado se avisan aparte. Sin grupos no se muestra nada. Detalle de la partida, aviso arriba de las rondas. |
| **Estado al morir** | Panel de Duelos (`/api/duels/death-state/`). Por cada ronda en que moriste, los vivos de tu equipo (contandote) y los rivales justo antes del primer evento del feed que te mata (`Kill` sobre vos o `Death` tuyo, la misma eleccion que `died`). Un `PlayerLeave` y un teamkill anteriores ya restaron su vivo. Una muerte sin evento en el feed, o despues de haberte ido, no entra (se informa cuantas). *Con ventaja* si tu equipo tenia mas vivos, *en paridad* si igual, *en desventaja* si menos. Winrate de esas rondas sobre las que tienen ganador. Sin normalizar a 5v5: partidas con menos jugadores dan estados como 4v4. Todos los filtros globales aplican. Muestra minima 30 muertes por fila: no se oculta, se avisa. |
| **Estado al matar** | Panel de Duelos (`/api/duels/kill-state/`). Por cada baja tuya a un rival, los vivos de tu equipo (contandote) y los rivales justo antes de ese `Kill`. Un `PlayerLeave` y un teamkill anteriores ya restaron su vivo; un teamkill tuyo no es baja. Sin agrupar por segundo: en un trade cada baja ve el estado que dejo la anterior. *Con ventaja*, *en paridad*, *en desventaja* como en Estado al morir. *Bajas* por fila; *Rondas* y winrate sobre rondas distintas de la fila (dos bajas tuyas con ventaja en la misma ronda son una ronda del grupo), sobre las que tienen ganador. Las bajas que el feed te atribuye despues de tu caida o de que te fuiste (trampas, gadgets, o un intercambio del mismo instante que el feed ordena con tu muerte primero; cuentan en *Bajas* del Resumen) no tienen estado tuyo y se informan aparte; las de tu fila que el feed no ubica de ninguna forma, tambien aparte. Sin normalizar a 5v5. Todos los filtros globales aplican. Muestra minima 30 rondas por fila: no se oculta, se avisa. |
| **Ventaja numérica tirada** | Panel de Duelos (`/api/duels/thrown-advantage/`). Rondas en que, despues de alguna baja o abandono del feed, tu equipo tuvo mas vivos que el rival (contandote; una diferencia de arranque sin bajas no cuenta). *Tiradas*: las de esas que tu equipo perdio. % tiradas = tiradas / rondas con ventaja; rondas sin ganador no entran. Se separa la ventaja maxima de la ronda: uno, dos o mas. Un `PlayerLeave` y un teamkill restan su vivo. Las bajas del mismo segundo de reloj se miden juntas (un trade simultaneo no deja a nadie con uno mas), salvo las del ultimo reloj de la ronda, que se miden de a una: tras el plant el juego deja de emitir el reloj y todo el post-plant lleva el mismo valor. Y la diferencia que deja a un equipo sin vivos no cuenta: una ronda ganada por eliminacion entra solo si antes de la ultima baja ya ibas arriba, y un clutch ganado no es ventaja. Una ronda que arranca 5v4 cuenta desde la primera salida (si cae un rival, +2). Por lado y por mapa son cuentas de rondas, no promedios de partidas. Todos los filtros globales aplican sobre tu fila. Lista: las 20 tiradas mas recientes, cada una con enlace a la partida parada en esa ronda. Muestra minima 30 rondas con ventaja por fila: no se oculta, se avisa. |
| **Matriz de duelos (partida)** | En el detalle de una partida: bajas del feed entre jugadores de equipos distintos, por par autor -> victima, con cuantas fueron headshot. El equipo de cada nick se lee de los jugadores de esa misma ronda; teamkills, bajas sin autor o sin victima y nicks sin fila en la ronda no cuentan. El lado (tu equipo o el rival) se decide ronda por ronda con tu `team_index` de esa ronda. Con "Solo aperturas", solo la apertura de cada ronda, la misma de **Duelos de apertura** y de la columna Aperturas del scoreboard: la primera muerte de la ronda (`Kill` o `Death`). Si esa muerte no es una baja entre rivales (una muerte sin asesino, un teamkill), la ronda no suma nada a la matriz. Conteos crudos, sin rating. |
| **Teamkills** | Baja del feed (`Kill`) con autor y victima en tu equipo esa ronda, leido ronda por ronda con el `team_index` de cada uno; un suicidio no cuenta. *Hechos*: tuyas sobre un compañero; *Sufridos*: de un compañero sobre ti. *Rondas con teamkill*: tus rondas filtradas con al menos un teamkill de tu equipo (tambien entre otros dos compañeros) y su winrate contra el de las demas, con el mismo `won` que **Winrate** (una ronda sin ganador conocido cuenta como no ganada). La tabla por compañero (profileID) solo suma los que te involucran. No cuentan en Bajas, HS%, KPR ni multikills. Un teamkill que abre la ronda sigue contando como apertura y entry del autor (y con eso en Duelos de apertura y en el Rating) hasta que otra ficha lo cambie. Página Compañeros, panel *Teamkills*. |

En ranked solo los rivales casi no se repiten, asi que la tabla por persona es
anecdota antes que patron: el coach solo opina desde 8 duelos contra la misma
persona. La tabla por operador si junta muestra rapido, y es la que suele
mostrar algo util. La de rondas contra cada operador responde otra pregunta:
la de duelos habla de los tiroteos que ya pasaron, la de rondas de como te
condiciona ese operador aunque nunca lo enfrentes de frente.

## Impacto

| Metrica | Definicion |
|---|---|
| **KST** | Rondas donde mataste, sobreviviste o tu muerte se tradeo, sobre el total. Es el clasico KOST **sin la O** de objetivo, porque los eventos de plant/defuse no estan disponibles (ver `formato-rec.md`). Bajo 65% significa que hay muchas rondas donde tu equipo jugo con uno menos. |
| **1vX (clutch)** | Rondas donde quedaste ultimo de tu equipo y ganaste. El `X` se cuenta como en r6-dissect, desde el final de la ronda: tus bajas desde que quedaste solo mas los rivales que siguen en la ronda al terminar. Una diferencia con r6-dissect: quien se fue de la partida (`PlayerLeave`), compañero o rival, esta fuera de la ronda (`metrics.one_vx`); un compañero que se fue no te quita el clutch y un rival que se fue no suma al `X`, aunque se haya ido con vos ya solo (ahi el `X` puede quedar por debajo del de Clutch: intentos y conversion). Sin ganador conocido cuenta el primer equipo, como en r6-dissect. Lo importado antes se corrige con `manage.py recompute`. Limite: el `.rec` trae `PlayerLeave` solo antes de Y9S1; desde ahi un abandono no deja rastro y el que se fue sigue contando como vivo. |
| **Clutch: intentos y conversión** | Intento = ronda en la que quedaste como unico vivo de tu equipo con al menos un rival vivo, ganes o pierdas (`clutch_vs`, calculado al importar desde el feed; `Kill`, `Death` y `PlayerLeave` cuentan como muerte). `X` = rivales vivos en ese instante (si tu equipo arranca la ronda con uno solo, el intento empieza en el primer segundo); 5 o mas se agrupan en `1v5+`. Ganado = intento en una ronda que tu equipo gano; las rondas sin ganador conocido (`.rec` cortado) no cuentan como intento. Conversion = ganados / intentos, total y por lado. Difiere del `1vX` de arriba en que cuenta tambien los perdidos, y su `X` puede no coincidir con el de `one_vx`, que se calcula desde el final de la ronda. Partidas importadas antes se llenan con la migracion o con `manage.py recompute`. La columna Silenciosos se define en Clutch silencioso. |
| **Clutch silencioso** | Clutch ganado (intento de la fila de arriba en una ronda que tu equipo gano) sin ninguna baja tuya desde que quedaste solo (`clutch_kills = 0`). `clutch_kills` se calcula al importar desde el feed (`metrics.clutch_kills`): cuenta las bajas a rivales (la regla de `kills`: sin teamkills ni suicidios; una victima sin nick conocido cuenta) de los eventos posteriores al que te dejo como unico vivo de tu equipo, el mismo instante de `clutch_vs` (no desde el final de la ronda como `one_vx`: con abandonos el X y estas bajas pueden no cuadrar con el 1vX); la baja que hiciste antes de quedar solo no cuenta, y si tu equipo arranca la ronda con uno solo cuenta desde el primer segundo. Un clutch perdido sin bajas no es silencioso; uno ganado en el que moriste despues de quedar solo (plantaste y la defensa no desactivo) si, si no hiciste bajas. Columna Silenciosos = cantidad y % sobre los ganados de esa fila (`—` sin ganados); un `*` marca menos de 5 ganados (`CLUTCH_SILENCIOSO_MIN`; a diferencia de las tablas por sitio y por operador, el corte es sobre ganados, no sobre intentos). La nota reparte los silenciosos por condicion de victoria de la ronda (`Round.win_condition`): por eliminacion (`KilledOpponents`: los rivales cayeron sin bajas tuyas, por caidas, sus gadgets o teamkills), sin eliminacion (`ObjectiveOrTime`: plant, defuse o tiempo, inferido del reloj en temporadas nuevas y nunca separado) y sin dato; en temporadas nuevas casi todo silencioso cae en sin eliminacion. No entra al Rating. Partidas importadas antes se llenan con la migracion o con `manage.py recompute`. Respeta los filtros de la barra. |
| **Clutch por mapa y sitio** | Mismo intento y ganado que la fila de arriba, agrupados por mapa (`Match.map_slug`) y sitio de bomba de la ronda (`Round.site`). Por mapa hay una fila Total (suma de sus sitios) y una por sitio, ordenadas por intentos; las rondas sin sitio van a "Sin sitio", ultima del mapa. Conversion = ganados / intentos. Un `*` marca una fila con menos de 5 intentos (`CLUTCH_SITIO_MIN`): sale igual, pero ese % es muestra chica. Respeta los filtros de la barra. |
| **Clutch por operador** | Mismo intento y ganado que la conversion de clutch, agrupados por operador (`RoundPlayer.operator`) y lado; una fila por par, ordenadas por intentos. Las rondas sin operador o sin lado no salen en ninguna fila, por eso la suma de intentos puede quedar por debajo de la de la conversion. Conversion = ganados / intentos. Un `*` marca una fila con menos de 5 intentos (`CLUTCH_OPERADOR_MIN`): sale igual, pero ese % es muestra chica. Respeta los filtros de la barra. |
| **Clutches de tus compañeros** | En Compañeros, panel Clutches (clave `teammate_clutches` de `/api/teammates/`). Por compañero habitual (5 partidas o mas en tu equipo, todo el historial, sin filtros: `MIN_PARTIDAS_HABITUAL`), las rondas en que quedo ultimo vivo de tu equipo con rivales vivos (`clutch_vs > 0` en su fila, el mismo algoritmo que el tuyo) y cuantas gano tu equipo. Agrupado por `Player`: un cambio de nick no parte la fila. Las rondas sin ganador no cuentan. Conversion = ganados / intentos. La fila Tú es tu conversion total con los mismos filtros. Un `*` marca menos de 5 intentos (`CLUTCH_COMPANERO_MIN`): sale igual. Respeta los filtros de la barra, aplicados a tu fila de esa ronda. |
| **Multikill (2K, 3K, 4K, ace)** | Rondas con exactamente 2, 3 y 4 bajas, y ace = 5 o mas (un modo con respawn la puede pasar de 5). Las bajas son las de la columna Bajas: solo a rivales, los teamkills no cuentan. El scoreboard de la partida las muestra como `2×2K · 1×ACE` (rondas × tamaño, solo los tamaños con alguna ronda) y ordena por el total de rondas con 2 o mas; el Resumen y el perfil de un jugador muestran el mismo texto sobre las rondas filtradas. `multikill_pct` (rondas con 2 o mas / rondas) no cambia. |
| **Cuando matas** | Tus bajas a rivales en tramos de 30 segundos de la fase de accion (`Event.elapsed` del evento Kill con tu nick como autor y la victima del otro equipo en esa ronda; **teamkills afuera**), el ultimo tramo abierto en 150s+, separadas por tu lado en la ronda. Tramos sin bajas no salen. La suma de todos los tramos es la de la columna Bajas con los mismos filtros, salvo una baja sobre un nick sin fila en la ronda, que Bajas cuenta y aca no (no se sabe de que equipo es). Un evento sin reloj trae 0 s y cae en 0-30s, igual que en Cuando mueres. Dice si tu impacto esta en la apertura o en el cierre de la ronda. |
| **Cuando mueres** | La distribucion completa, en tramos de 30 segundos y separada por lado. El promedio esconde la forma: morir siempre a los 100s no es lo mismo que morir mitad a los 20 y mitad a los 170, y las dos cosas se arreglan distinto. |
| **Sales muy temprano** | Muertes en los primeros 30 **segundos jugados**. La ronda todavia no se arma: mueres sin informacion. El coach opina desde 25 muertes del lado y un 25% concentrado ahi (el reparto uniforme daria 17%). |
| **Te quedas sin tiempo** | Muertes con menos de 30 segundos **de reloj**. Es otro eje: no importa cuanto jugaste, importa que la ronda ya estaba decidida. En ataque significa que la ejecucion nunca llego a empezar. |
| **Mueres a los** | Promedio de segundos de la fase de accion hasta tu muerte. Se saca del reloj de la ronda: `reloj_inicial - reloj_de_tu_muerte`. Un promedio bajo (menos de 45-50 s) significa que te estas perdiendo la mayor parte de la ronda. |

## Cortes

| Dimension | Nota |
|---|---|
| **Lado** | Ataque o defensa. Se deduce de los operadores de cada equipo, no de un campo del replay. |
| **Mapa** | Cada version de un mapa (`Match.map_id` dentro del mismo `map_slug`) es su propia fila en las tablas de mapas, sitios y spawns (CSV de `/api/export/`) y en las señales del Coach de mapa, sitio y spawn. Partidas, el detalle de la partida y su resumen copiado dicen la version con la misma etiqueta. La etiqueta sale del sufijo `Y<n>` del identificador interno en `MAPS` ("Consulate (Y7)", "Consulate (Y10)"); la version sin sufijo y los mapas de una sola version llevan el nombre a secas. El filtro de mapa por slug junta todas las versiones, y elegir una version en el selector filtra por `map_id`. **Mejor y peor mapa** del Inicio (con su muestra minima contada por version), **Clutch por mapa y sitio** y el progreso por mapa de Tendencias (Mapas que mejoran y empeoran) tambien separan por version con la misma etiqueta, y el CSV de partidas (`table=matches`) trae la columna `map_version` al final. Lo unico que sigue juntando versiones por slug es la lista de mapas de cada rival en Duelos. |
| **Sitio** | El sitio de bomba, tal como lo nombra el juego (`2F Gym, 2F Bedroom`). En defensa es tu setup; en ataque es lo que estas atacando. |
| **Spawn** | Solo tiene sentido en ataque: es la posicion exterior desde donde arrancaste. En defensa el replay pone el sitio en ese campo. |
| **Operador** | El operador con el que terminaste la ronda (si hiciste swap en preparacion, queda el ultimo). |
| **Presencia** | Rondas con ese operador en ese lado / todas tus rondas de ese lado, con los filtros activos. La base se cuenta antes del minimo de rondas: ocultar una fila no mueve las demas y las presencias de un lado suman 100 %. Con filtro de operador en `/api/operators/`, ese operador queda en 100 %; la pagina Operadores pide sus tablas por lado sin ese filtro y resalta la fila elegida, asi que ahi la Presencia no cambia. |
| **vs. tu lado** | Winrate con ese operador menos tu winrate de todas las rondas de ese lado (la misma base que Presencia), en puntos. Vacio si la fila o el lado no tienen ninguna ronda con ganador conocido. Con filtro de operador en `/api/operators/` da 0 (la pagina Operadores no se lo pasa: ver Presencia). No lleva banda de ruido: la fila es parte de la base y no una muestra independiente, asi que el error estandar de dos proporciones no aplica; lo que dice cuanto pesa el numero es la Presencia. |
| **Operador por sitio** | En Operadores, panel Por sitio (`/api/operators/sites/`). Winrate con un operador en un sitio contra el winrate del resto de tus operadores ahi: mismo mapa (por version), sitio y lado, otro operador; no contra el total del sitio, que contiene al operador. Solo rondas con ganador conocido y con sitio, lado y operador: una ronda sin ganador no cuenta ni como ganada ni como perdida. Fila solo con al menos 10 rondas del operador y 10 del resto (`OPERADOR_SITIO_MIN_RONDAS`; `min_rounds` en la API). Margen: 2 errores estandar de la diferencia con proporcion combinada (operador + resto), como **Fuera de posición**; veredicto *Te rinde* / *Te hunde* si la diferencia pasa el margen, *Sin señal* si no. El filtro de operador recorta las filas, no el resto. Orden por la diferencia absoluta. |
| **Pool de operadores** | En Operadores, panel Tu pool (`/api/operators/pool/`). Por lado, operadores distintos (sin `Unknown(...)` ni vacios) en tus ultimas 20 partidas (`POOL_PARTIDAS_RECIENTES`; menos si no hay 20) y en todo lo filtrado. *Sin jugar*: jugado alguna vez y no en los 30 dias (`POOL_DIAS_SIN_JUGAR`) anteriores a tu partida mas nueva con los filtros, no a hoy; con la fecha de la ultima vez y sus rondas. *Nunca jugados*: catalogo del lado (tabla del parser mas los vistos en la base) sin rondas tuyas. Mapa, tipo, modo, fechas y sesion aplican; lado, operador y sitio no (el lado solo elige que bloque se muestra; con sitio, todo lo no jugado ahi pasaria por nunca jugado). |
| **Repetir o cambiar de operador** | En Operadores, panel Repetir o cambiar tras perder (`/api/operators/after-result/`). Pares de rondas tuyas consecutivas del mismo lado en la misma partida (por numero de ronda, saltando las del otro lado), cortados por un numero faltante, una ronda sin lado o un operador vacio o `Unknown(...)`. Se separan por el resultado de la primera (*Tras perder*, *Tras ganar*; una primera sin ganador no abre par). *Repite* si la segunda es con el mismo operador, *Cambia* si no. Winrate de la segunda sobre las que tienen ganador (una segunda sin ganador cuenta en las rondas, no en el winrate). *Total* suma los dos lados. Mapa, tipo, modo, fechas y sesion aplican; el lado elige el bloque; operador y sitio eligen la primera ronda del par (filtrar las filas dejaria solo los pares que repiten). Muestra minima 12 rondas por caso (`OPERADOR_TRAS_RESULTADO_MIN_RONDAS`): se avisa *pocas rondas*, no se oculta. |
| **A qué operador cambias tras perder** | Debajo del panel Repetir o cambiar tras perder (clave `switches` de `/api/operators/after-result/`). Los pares *Tras perder · Cambia* de esa fila, partidos por operador de la primera ronda (*Perdiste con*), operador de la segunda (*Cambiaste a*) y lado. Winrate de la segunda sobre las que tienen ganador. Por lado, la suma de las filas es el *Cambia* de *Tras perder*. Mismos filtros que el panel. Muestra minima 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`): se avisa *pocas rondas*, no se oculta. |
| **Numero de ronda** | Para ver si te caes en las rondas finales. |
| **Sesion** | Bloque de juego seguido, y posicion de la partida dentro de el. Ver la seccion Sesiones. |
| **Rating** | Aporte por ronda contra tu propio promedio. Aparece en casi todas las tablas. Ver la seccion Rating. |
| **Rival** | Duelos contra una persona o contra un operador rival. Ver la seccion Duelos. |
| **Con y sin** | Tus numeros en las rondas que compartiste con alguien, contra el resto de tu historial. Es la unica forma de ver si con esa persona rindes distinto, pero el lado "sin" suele tener poca muestra: la app lo avisa bajo 20 rondas. |
| **Compañero** | Winrate de las rondas que esa persona jugo **en tu equipo**, no su winrate por separado. Se agrupa por jugador (profileID), asi que un cambio de nick no parte el historial. Con menos de 25 rondas compartidas es varianza. |
| **Tamaño del grupo** (panel "Solo, en dúo o en stack") | Habitual = un jugador (por `profileID`, asi que un cambio de nick no lo parte) que jugo en tu equipo (`team_index` igual al tuyo en la misma ronda) en 5 o mas partidas distintas de **todo** tu historial. Se mide sin filtros a proposito: un filtro de mapa o de fecha no cambia con quien jugas. Cada partida cae en una sola fila por los habituales distintos que estuvieron en tu equipo en cualquiera de sus rondas: *Solo* 0, *Dúo* 1, *Trío* 2, *Stack* 3 o mas (3 o 4 en un stack completo; mas solo si alguien entro por abandono). Los filtros eligen que partidas y que rondas entran, pero no cambian quien es habitual ni la fila de una partida. *Winrate partida*: sobre el resultado entero de la partida, sin las que no tienen ganador (empates e incompletas, `Match.won` nulo). *Rondas*, *Winrate rondas* y *Rating*: los de siempre sobre tus rondas filtradas de esas partidas. Distinto del minimo de Sinergia, que cuenta rondas filtradas y se ajusta en la UI. Aviso de varianza con menos de 10 partidas en un grupo. |

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

## Copiar resumen de la partida

El boton **Copiar resumen** del detalle de partida copia al portapapeles un
texto plano armado con los numeros que la pagina ya muestra (marcador,
resultado y tu linea de Bajas, Muertes, K/D, HS%, Duelos de apertura y KST de
la partida). Suma dos numeros propios; una linea sin datos no sale:

| Linea | Definicion |
|---|---|
| **Rondas ganadas: ataque n de m · defensa n de m** | Por lado, `m` = rondas de la partida en que jugaste ese lado con ganador conocido y `n` = las que gano tu equipo. Una ronda sin ganador (`.rec` cortado) no cuenta en ninguno de los dos. Un lado sin rondas no aparece. |
| **Mejor ronda** | La ronda con mas bajas tuyas (las de la columna Bajas, solo a rivales); en empate, la primera. No sale si no hiciste ninguna baja. El nick es el de tu fila en la ultima ronda de la partida. |

No se guarda ni sale a la red: es el portapapeles del navegador.

## Comparar partidas

**Comparar con…** en el detalle lleva a `/comparar/<a>/<b>`, que pone dos
partidas lado a lado con los numeros del detalle (`my_totals`) de cada una.
No calcula metricas nuevas; solo suma la columna **Diferencia**:

| Fila | Definicion |
|---|---|
| **Rondas en ataque / defensa: n de m** | Por lado, `m` = rondas de la partida en que jugaste ese lado y `n` = las que gano tu equipo. Una ronda sin ganador cuenta en `m` y no en `n`. Sin rondas en ese lado: `—`. |
| **Diferencia de los lados** | Winrate del lado en A menos el de B, en puntos (`-33 pts`), redondeado a entero: se compara el winrate y no el conteo, porque 4 de 6 no es mejor que 3 de 3. |
| **Diferencia de Bajas, Muertes, Aperturas, Muertes sin trade, KST y Rating** | A menos B, con signo, sobre lo que muestra la celda ya redondeado (KST en puntos, rating con dos decimales). En verde si A sale mejor y en rojo si sale mejor B; para Muertes, Aperturas perdidas y Muertes sin trade sale mejor quien tiene menos. Diferencia 0 no marca a nadie. |

Una partida sin tu fila (no jugaste ninguna ronda) o un rating sin dato dan
`—` y la diferencia queda vacia.

## Sobre la granularidad espacial

El `.rec` **no expone coordenadas** de las bajas, asi que no hay heatmap de
posiciones sobre el minimapa. Lo mas fino que entrega el formato es sitio de
bomba y spawn de ataque: con eso trabajan el Coach y las tablas `maps`, `sites`
y `spawns` de la exportacion CSV.

La tabla **Dónde quedas fuera de posición** del Coach usa esa granularidad:
compara el % fuera de posición de cada sitio contra el **resto** de tus rondas
y el de cada spawn contra el resto de tu **ataque** (el spawn solo existe en
ataque, y en ataque se queda fuera de posición mas seguido: contra todo, el
spawn saldria marcado por el lado). No se compara contra el total porque la
zona esta dentro de el. El veredicto (*Te agarran más*, *Te sostienes*) solo
habla si la diferencia pasa el **margen**, dos errores estandar de la
diferencia, calculados con la proporcion combinada (zona + resto: con la de cada
muestra, una zona en 0 % o 100 % tendria margen casi nulo). Con una fila por sitio y spawn (20 o mas
en un historial real), con uno solo un tercio de las zonas saldria marcado por
azar. El filtro Lado deja el resto del mismo lado.

## Progreso

Comparar lo reciente contra lo inmediatamente anterior es la unica forma honesta
de decir "mejore". Dos modos: por **partidas** (las ultimas N contra las N
anteriores, que siempre tiene muestra de los dos lados si jugaste 2N) y por
**dias**.

| Metrica | Definicion |
|---|---|
| **Cambio** | La diferencia entre los dos periodos, en puntos o en la unidad de la metrica. |
| **Banda de ruido** | Error estandar de la diferencia entre las dos proporciones: `sqrt(p1(1-p1)/n1 + p2(1-p2)/n2)`. Es **cuanto se mueve sola** una metrica con esa cantidad de rondas. Si el cambio no pasa la banda, la app lo marca como ruido y no como mejora ni empeora. |
| **Cambio por mapa y operador** | Los mismos dos periodos partidos por mapa y por operador + lado. Una fila aparece solo si tiene al menos **10 rondas en cada periodo** (`COMPARE_MIN_ROUNDS_FILA`, mas baja que las 20 del total porque un operador rara vez junta 20 rondas de un lado en 10 partidas). El cambio es de winrate de ronda; la banda es la misma formula con las rondas de esa fila, y el veredicto (mejor, peor o ruido) sale igual que en el total. El rating de cada periodo se muestra sin banda. Las filas van de la que mas subio a la que mas cayo. |
| **Forma contra tu historial** | Panel del Inicio: tus ultimas 10 partidas contra **todas las anteriores** (no las 10 anteriores), con los filtros activos salvo fechas y sesion (el periodo lo define la comparacion). Sin filtro de fecha ni de sesion, las 10 son las mismas de "Ultimas partidas"; con alguno de esos, "Ultimas partidas" los respeta y este panel no. Muestra Rondas ganadas, Rating, KST y Muertes sin trade con el mismo cambio, banda de ruido y veredicto que Progreso; el `n` de la banda son las rondas de cada lado (las muertes, en Muertes sin trade), asi que con un historial largo la domina el lado de las 10. Con 10 partidas o menos no hay resto y no se compara; con menos de 20 rondas de algun lado (`COMPARE_MIN_ROUNDS`) se muestra con aviso de muestra chica. `GET /api/compare/?against=rest`. |
| **Puesto en el lobby** | Panel de Tendencias (`lobby_rank` en `/api/trends/`). En cada partida, el rating de cada jugador es el promedio de sus puntos por ronda (los de **Rating**) en las rondas que dejan los filtros; los de ronda (lado, operador, sitio) recortan las mismas rondas para todos. *Mejor de la partida*: ningun otro jugador tiene mas; *Último de la partida*: ninguno tiene menos; empatar cuenta (con dos empatados sos mejor y ultimo). *Mejor de tu equipo*: ningun compañero (estuvo en tu equipo en alguna de esas rondas) tiene mas. Porcentaje sobre las partidas con al menos otro jugador (con al menos un compañero, en el de equipo); una partida con solo tu fila no cuenta. Partidas con menos de 10 jugadores entran con los que hay. Muestra minima 10 partidas: no se oculta, se avisa. |

Un ejemplo real de por que hace falta: 10 partidas contra las 10 anteriores dio
un winrate 9.3 puntos mas bajo. Suena a bajon, pero con ~50 rondas por lado la
banda es de 9.6 puntos: ese cambio no existe. En la misma comparacion, KST bajo
15.2 con banda de 9.6, y ese si.

La banda solo se calcula para porcentajes. En K/D, KPR, rating y "mueres a los"
no se puede con esta informacion, asi que la flecha muestra la direccion pero no
afirma que el cambio sea real.

**"Mueres a los" no se juzga**: subir puede ser que sobrevivas mas o que llegues
tarde a todo, asi que se muestra sin flecha de bueno o malo.

## Temporada en Ubisoft

El panel del perfil de un jugador. **No sale de tus replays**: es lo que
devuelve la API de Ubisoft (`full_profiles`, la misma que leen stats.cc y R6
Tracker) para la temporada actual de PC, guardado con la fecha de la consulta.
Cubre todas sus partidas, no solo las que jugo contigo.

| Metrica | Definicion |
|---|---|
| **Rango** | El rango actual en Ranked, por su id en la tabla de Ranked 2.0 (Cobre 5 ... Diamante 1, Campeones). |
| **MMR** | `rank_points` de Ranked: los puntos que ves en el juego. |
| **Maximo de la temporada** | El rango y los puntos mas altos que alcanzo esta temporada. |
| **K/D** | bajas / muertes de la temporada en esa playlist. Sin muertes no hay K/D. |
| **Partidas ganadas** | ganadas / (ganadas + perdidas). Los abandonos cuentan como partida jugada pero no entran al porcentaje. |
| **Partidas** | ganadas + perdidas + abandonos. Una playlist sin partidas no se muestra. |
| **Nivel** | Nivel de la cuenta (`rewards/public_profile`). Si Ubisoft no lo devuelve, sale `—`. |
| **Horas jugadas** | `PTotalTimePlayed` en horas, redondeado. Incluye todos los modos de la cuenta. |

## Datos

En la pagina Datos, panel Importación.

| Metrica | Definicion |
|---|---|
| **Partidas por versión del juego** | Clave `versions` de `/api/import/status/`. Partidas importadas agrupadas por `Match.game_version` tal como viene del replay, con la fecha de la primera y la última. Orden: la versión con `code_version` más alto primero (a igual código, la usada más tarde); las partidas sin versión, en la fila "Sin versión", al final. Sin filtros de la barra y con todas las partidas importadas, también las que se excluyan de los agregados: es el inventario de lo importado, no una métrica de rendimiento. |

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
| Zona fuera de posición | 5 rondas en la tabla, 8 para la señal del Coach |
| Salida del spawn | 5 rondas de ataque por spawn (`POSICION_MIN_RONDAS`) |
| Repetir el sitio tras perderlo | 8 pares por caso (`REPETIR_SITIO_MIN_RONDAS`): no se oculta, se avisa |
| Repetir o cambiar el spawn | 8 rondas por caso (`REPETIR_SITIO_MIN_RONDAS`): no se oculta, se avisa |
| Cortes de Tendencias (ronda anterior, marcador, como se cierran, hora, dia) | 30 rondas por fila: no se oculta, se avisa |
| Repetir o cambiar de operador | 12 rondas por caso (`OPERADOR_TRAS_RESULTADO_MIN_RONDAS`): no se oculta, se avisa |
| A qué operador cambias tras perder | 5 rondas por par (`OPERADOR_CAMBIO_MIN_RONDAS`): no se oculta, se avisa |
| Estado al morir | 30 muertes por fila: no se oculta, se avisa |
| Estado al matar | 30 rondas por fila: no se oculta, se avisa |
| Ventaja numérica tirada | 30 rondas con ventaja por fila: no se oculta, se avisa |
| Puesto en el lobby | 10 partidas con otro jugador (`MUESTRA_PARTIDAS`): no se oculta, se avisa |
| Clutches de tus compañeros | habitual (5 partidas juntas) para salir; 5 intentos por fila (`CLUTCH_COMPANERO_MIN`): no se oculta, se avisa con * |
| Quién la sostiene (ganadas sin ti) | habitual (5 partidas juntas) para salir; 5 rondas por fila (`GANADA_SIN_TI_MIN`): no se oculta, se avisa con * |

Con 3 partidas importadas el coach te va a decir que faltan datos. Es a proposito.

**Ver esas rondas** (señales del Coach): abre el Resumen con los filtros que
definen la señal (lado, mapa por slug, operador con su lado, mapa y sitio),
sumados a los de la barra; los de la señal pisan a los de la barra. No hay
filtro de spawn: una señal de spawn abre su mapa en ataque. Las señales de
rival (operador rival, nemesis) abren Duelos con los filtros de la barra, y
las generales no tienen enlace. El mapa va por slug: en un mapa rehecho el
enlace junta las dos versiones, salvo que la barra ya tenga un mapa (o una
version), que la señal respeta. Un sitio que llega por el enlace aparece en
la barra aunque la pagina no tenga selector de sitio, para poder quitarlo.
