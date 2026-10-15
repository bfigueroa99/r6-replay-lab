# 48. POST de etiquetas y de Ubisoft aceptan formularios de otra pagina

estado: propuesto
candado: arquitecto 2026-10-15T12:12Z
rama: -
tipo: bug
epica: -
area: backend
prioridad: 2
fuente: QA 20261015T1012Z probando la ficha 47: `curl -X POST -H "Content-Type: text/plain" --data '{"gamemodes": {"999": "Ataque nuevo"}}' localhost:8766/api/overrides/` -> 200 y reetiqueta 2 partidas. `save_overrides` (views.py:587 en main 17f0ae1) y `player_ubisoft` (views.py:264) no llaman a `_es_json`; `app_settings` y `make_backup` si.
archivos: -
turnos: qa 20261015T1012Z

## PR

(La escribe el Release manager al final.)

## Que gana quien usa la app

Hoy cualquier pagina abierta en el navegador puede mandar un formulario a
`127.0.0.1` que reescribe `overrides.json` y renombra partidas ya
importadas (sin vuelta atras), o que dispara la consulta a Ubisoft sin el
clic del usuario. Con esto esos dos POST piden `application/json`, como ya
lo hacen Ajustes y Respaldo (`_es_json`, views.py:111), y esa puerta se
cierra sin tokens ni sesiones.

## Criterios de aceptacion

- [ ] `POST /api/overrides/` con `Content-Type: text/plain` (o
      `application/x-www-form-urlencoded`) devuelve 415 y no escribe
      `overrides.json` ni toca `Match`. Test.
- [ ] `POST /api/players/<id>/ubisoft/` sin `application/json` devuelve 415
      y no llama a `perfil_externo.abrir` (reemplazado en el test). Test.
- [ ] Con `application/json` los dos siguen igual (tests existentes en
      verde).
- [ ] La UI sigue funcionando: Datos ya manda JSON; `PerfilUbisoft.jsx`
      llama `post(...)` sin cuerpo, asi que no manda `Content-Type`: pasa
      a mandar `{}`. El e2e del perfil o de Datos sigue en verde.
- [ ] `CLAUDE.md` ya dice que los POST que cambian configuracion exigen
      JSON; el docstring de `_es_json` nombra tambien estos dos (sin tocar
      `CLAUDE.md`).

## Fuera de alcance

- `POST /api/import/` (solo relee la carpeta configurada; no escribe nada
  que el usuario no pidiera). Si el Arquitecto lo ve barato, puede sumarlo
  con su test; si no, queda anotado.
- Tokens CSRF o sesiones: la app es local y sin cuentas.

## Diseno

## Implementacion

## Revision

## QA

## Para el humano
