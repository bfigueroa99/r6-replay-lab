# 66. Copiar el resumen de una partida como texto

estado: entregado
candado: -
rama: claude/equipo-dev/66-copiar-resumen-de-partida
tipo: funcionalidad
epica: exportar
area: frontend
prioridad: 3
fuente: ALCANCE.md H4
archivos: frontend/src/resumenPartida.js, frontend/src/resumenPartida.test.js, frontend/src/pages/MatchDetail.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261027T1205Z, arquitecto 20261027T1605Z, dev 20261028T1607Z, revisor 20261028T1644Z, qa 20261028T2004Z, release 20261028T2004Z

## PR

Titulo: `[equipo-dev][frontend] Detalle de partida: copiar el resumen como texto`

### Que cambia

El detalle de partida tiene un boton **Copiar resumen** que deja en el
portapapeles cinco lineas de texto plano: mapa, marcador y resultado; fecha y
tipo; tu linea de stats (bajas/muertes, K/D, HS, aperturas, KST); rondas
ganadas en ataque y en defensa; y tu mejor ronda. Listo para pegar en el chat
del equipo, sin capturas. No sale nada a la red: es el portapapeles del
navegador, y el texto sale del payload que la pagina ya tiene.

### Por que esto y no otra cosa

Ficha 66, primer tramo de la epica `exportar` (H4 de `ALCANCE.md`). Texto
plano y no markdown ni imagen: pega igual en Discord, WhatsApp o un editor.
Las rondas con ganador desconocido (`.rec` cortado) no cuentan en `n de m`,
como en las metricas por lado.

### Como se probo

- `./scripts/check.sh`: 811 tests backend, 130 frontend, build ok, 53 e2e.
- `frontend/src/resumenPartida.test.js` (10): texto exacto de las cinco
  lineas, sin bajas no hay mejor ronda, lado sin rondas, incompleta, nick con
  `<b>Ñandú_*|` literal, sin rondas ni fila tuya, K/D nulo con raya, empate de
  bajas, singular de "1 baja", ronda sin ganador fuera de las ganadas.
- e2e `el detalle de partida copia el resumen` (`seed_demo`, permiso de
  portapapeles en Chromium).
- QA: texto copiado en Chromium para tres partidas de `seed_demo`, cruzado con
  `/api/matches/<id>/`; portapapeles que rechaza, ausente o sin permiso:
  aviso en la pagina y consola limpia; el click no hace requests; tres
  mutaciones, las tres caen; chunk inicial igual que dev.

### Riesgos y lo que no entra

Solo frontend: sin migracion, sin `recompute`, sin parser. Fuera: resumen de
los 10 jugadores o de la matriz de duelos (H5), copiar señales del Coach (H6),
compartir por red o imagen.

### Como probarlo en 2 minutos

```powershell
cd frontend; npm run build; cd ..\backend
..\.venv\Scripts\python.exe manage.py runserver
```

Abrir `http://localhost:8000/partidas`, entrar a una partida, apretar
"Copiar resumen": aparece "Copiado". Pegar en un editor: cinco lineas (cuatro
si no hiciste bajas), la primera `<mapa> · <marcador> · <resultado>`.

### Verificar en el PC

- Electron (`npm run desktop`): "Copiar resumen" y pegar. No se verifica en la nube.

### Para el humano

Aviso, no bloquea: la linea de stats dice "1 bajas / 1 muertes" con una sola
baja o muerte, y "Copiado" queda puesto hasta salir de la pagina (abajo).

### Candidatos descubiertos

Ninguno.

## Que gana quien usa la app

Pasarle al equipo como fue una partida sin mandar capturas: un boton copia un
resumen en texto plano listo para pegar.

## Criterios de aceptacion

- [x] Funcion pura `textoResumenPartida` con las cinco lineas, con vitest.
- [x] Casos borde con test: sin bajas, lado sin rondas, incompleta, nick raro;
      sin HTML ni markdown.
- [x] Boton en `MatchDetail.jsx` con aviso "Copiado" o de error, sin consola.
- [x] e2e con permiso de portapapeles afirma mapa y marcador.
- [x] Ninguna request nueva.

## Diseno

(Arquitecto 20261027T1605Z.) Funcion pura `resumenPartida.js` sobre el payload
de `/api/matches/<id>/`, boton y estado `copia` en la cabecera, e2e con
`grantPermissions`. Skills: no aplica; sin arena.

## Implementacion

(Dev 20261028T1607Z.) Todo el diseno. Desvios: rondas con ganador desconocido
fuera de `n de m`; fila `## Copiar resumen de la partida` en
`docs/metricas.md`; el aviso a la izquierda del boton.

## Revision 2026-10-28 sobre f3a6e0e

(Revisor 20261028T1644Z.) Aprobar. Corrigio el test del singular de "Mejor
ronda" (pasaba con el bug). Hallazgo menor abierto: singular en la linea de
stats.

## QA 2026-10-28 sobre 52e46d0

(QA 20261028T2004Z.) Aprobado. Los cinco criterios con Chromium y `curl` sobre
base sembrada y vacia; detalle en `git log` (commit `Prueba: 66`).

## Para el humano

- Aviso, no bloquea (Revisor y QA): la linea de stats del resumen dice "1 bajas
  / 1 muertes" con una sola baja o muerte (con `seed_demo`, la partida del
  2026-08-02 08:00), y el aviso "Copiado" no se borra hasta salir de la
  pagina. Caben en una ficha chica; el test exacto del singular esta en la
  Revision de `git log`.
- Aviso: la fila "Mejor ronda" de `metricas.md` dice "teamkills incluidos";
  la ficha que saque los teamkills de `kills` tiene que corregirla.
