# 66. Copiar el resumen de una partida como texto

estado: propuesto
candado: -
rama: -
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H4
archivos: -
turnos: po 20261027T1205Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Despues de una partida uno quiere pasarle al equipo como fue sin mandar
capturas. Un boton en el detalle de partida copia al portapapeles un resumen
en texto plano (mapa, marcador, resultado, tu linea de stats, rondas ganadas
por lado y tu mejor ronda) listo para pegar en el chat. No sube nada: es el
portapapeles del navegador.

## Criterios de aceptacion

- [ ] Una funcion pura (`frontend/src/`, sin React) arma el texto desde el
      payload de `/api/matches/<id>/`: primera linea `<mapa> · <marcador> ·
      <resultado>` con fecha y tipo de partida; despues bajas/muertes, K/D, HS%,
      aperturas y KST tuyos; rondas ganadas en ataque y en defensa (`n de m`);
      y la ronda con mas bajas tuyas (numero y bajas; si hay empate, la primera).
      Tests vitest con un payload armado a mano.
- [ ] Casos borde con test: partida sin bajas tuyas (no inventa "mejor
      ronda": la linea no sale), partida sin rondas de un lado, resultado
      "incompleta", nick con caracteres raros. El texto no lleva HTML ni
      markdown.
- [ ] `MatchDetail.jsx` muestra un boton "Copiar resumen" en la cabecera que
      llama a `navigator.clipboard.writeText` y avisa "Copiado" en la UI; si el
      portapapeles no esta disponible o rechaza, muestra un aviso y no tira error
      a la consola.
- [ ] El e2e abre una partida de `seed_demo`, aprieta el boton (con permiso de
      portapapeles en Chromium) y afirma que el texto copiado empieza con el mapa
      y el marcador de esa partida.
- [ ] Ninguna request nueva: el resumen sale del payload que la pagina ya
      tiene.

## Fuera de alcance

- Compartir por red, enlaces o imagenes.
- Resumen de los 10 jugadores o de la matriz de duelos (idea H5).
- Copiar señales del Coach (idea H6): otro item.

## Para el humano

(Nada por ahora.)
