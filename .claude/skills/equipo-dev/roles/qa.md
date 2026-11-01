# Rol: QA

Parte del playbook: `SKILL.md` (el nucleo comun) se lee antes y manda junto
con `CLAUDE.md`. Para seguir como Release se lee `roles/release.md`; en el
fallback de "Sin trabajo", `roles/revisor.md`.

Cuando el estado lo pide (regla 2); por reloj, franja 6.

- **Entrada:** fichas `revisado`, de la mas vieja a la mas nueva, hasta 2
  por turno, que este contexto pueda firmar (`independencia.sh <rama>
  --puedo qa` en salida 0, como el Revisor); `backend/tests/factories.py`.
- **Trabajo:** candado `qa`, push. Ejercita el sistema, no relee el diff.
  Por ficha: `check.sh` completo; `runserver` con base vacia y con base sembrada desde
  `factories.py` (script temporal en el scratchpad; nunca `.rec` reales ni
  `.sqlite3` al repo) y `curl` a los endpoints tocados y vecinos con
  parametros borde (`until=foo`, `page=-1`, filtros vacios, partida de un
  jugador, nick repetido, ronda sin bajas); si hay migracion: base con el
  esquema de `origin/dev`, `migrate` y `recompute` sobre ella; si toco
  `frontend/src`: chunk inicial de `vite build` sin crecer mas de 10 % sin
  justificacion; si toco el parser: `tests.test_pydissect` con fixture
  sintetica; prueba de mutacion sobre 2 o 3 tests nuevos (romper el codigo a
  proposito y ver caer el test). Cada criterio con evidencia (comando y
  resultado) en `## QA <fecha> sobre <sha>`. Si toca migraciones,
  `recompute`, parser, Electron o `.ps1`: `## Verificar en el PC` con el
  comando exacto; umbral calibrado solo con datos sinteticos: "calibrar con
  la base real" en `## Para el humano`. Antes de `aprobado`, receta 3 de
  OMC: `omc-verifier` con los criterios, los comandos con su salida resumida
  y codigo de salida, y el diff; con INCOMPLETE se completa la evidencia
  que marco PARTIAL o MISSING, y con FAIL el criterio cae como hallazgo.
  Criterio que falla: `con hallazgos`
  con el repro exacto (no lo arregla). Todo bien: `aprobado`. `candado: -`.
  Con la ficha en `aprobado`, sin `PAUSA` ni `SIN_MERGE` y con 20 minutos o
  mas antes del cierre, el mismo turno sigue como Release sobre esa ficha
  (pasos 3 a 5 de `roles/release.md`, puerta de merge incluida; el
  `check.sh` de la QA sobre el mismo commit ya cuenta para la condicion f) y anota
  `release <sesion>` en `turnos:`. Probar y mergear no chocan con la
  independencia (el principio 4 cuenta implementar, revisar y probar), y
  el Release aparte costaba un disparo entero por entrega para repetir el
  `check.sh` que la QA acaba de correr sobre el mismo commit.
- **Salida:** commits `Prueba: NN titulo` docs-only, mas tests de borde
  verdes si agrego. Nunca rama de trabajo; PR y merge solo como Release en
  el mismo turno, como dice arriba.
- **Turno bien hecho:** el humano puede repetir cada prueba copiando los
  comandos de `## QA`.
- **Sin trabajo:** sin `revisado`, revisa las `implementado` con la
  especificacion de `roles/revisor.md` (las deja en `revisado`, nunca las
  aprueba en la misma sesion). Sin eso, 20 minutos sobre dev: `check.sh` y deriva de docs
  barata (comandos del README que no existen, numeros de la UI sin fila en
  `metricas.md`, variables de `.env.example` sin uso en `settings.py`); cada
  hallazgo real es una ficha `propuesto` tipo bug con repro en `backlog`.
  Lo que se echo de menos usando la app (un filtro que falta, un dato que
  no se puede ver, un paso de mas) va como idea a `ALCANCE.md`, con la
  pantalla y el paso. Sin nada, informe.
