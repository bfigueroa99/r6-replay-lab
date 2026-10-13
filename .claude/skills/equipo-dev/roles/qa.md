# Rol: QA

Parte del playbook del equipo. Lo comun a todos los roles (principios,
arranque, turnos, prioridades, fichas, cierre) esta en
`.claude/skills/equipo-dev/SKILL.md`; este archivo es solo la especificacion
de este rol. Se lee de `$EQUIPO_REF` con `git show`, nunca del checkout.

Cuando el estado lo pide (regla 2); por reloj, franja 6.

- **Entrada:** fichas `revisado`, de la mas vieja a la mas nueva, hasta 2
  por turno; `backend/tests/factories.py`.
- **Antes de candar:** `puerta.sh <rama> --solo b` en `PUERTA b OK`: esta
  sesion no implemento ni reviso esa ficha.
- **Trabajo:** candado `qa`, push. Ejercita el sistema, no relee el diff.
  Por ficha: `check.sh` completo; `runserver` con base vacia y con base sembrada desde
  `factories.py` (script temporal en el scratchpad; nunca `.rec` reales ni
  `.sqlite3` al repo) y `curl` a los endpoints tocados y vecinos con
  parametros borde (`until=foo`, `page=-1`, filtros vacios, partida de un
  jugador, nick repetido, ronda sin bajas); si hay migracion: base con el
  esquema de `origin/main`, `migrate` y `recompute` sobre ella; si toco
  `frontend/src`: chunk inicial de `vite build` sin crecer mas de 10 % sin
  justificacion; si toco el parser: `tests.test_pydissect` con fixture
  sintetica; prueba de mutacion sobre 2 o 3 tests nuevos (romper el codigo a
  proposito y ver caer el test). Cada criterio con evidencia (comando y
  resultado) en `## QA <fecha> sobre <sha>`. Si toca migraciones,
  `recompute`, parser, Electron o `.ps1`: `## Verificar en el PC` con el
  comando exacto; umbral calibrado solo con datos sinteticos: "calibrar con
  la base real" en `## Para el humano`. Criterio que falla: `con hallazgos`
  con el repro exacto (no lo arregla). Todo bien: `aprobado`. `candado: -`.
- **Salida:** commits `Prueba: NN titulo` docs-only, mas tests de borde
  verdes si agrego. Nunca PR, nunca rama de trabajo.
- **Turno bien hecho:** el humano puede repetir cada prueba copiando los
  comandos de `## QA`.
- **Sin trabajo:** sin `revisado`, revisa las `implementado` con la
  especificacion del Revisor (`roles/revisor.md`; las deja en `revisado`, nunca las aprueba en la
  misma sesion). Sin eso, 20 minutos sobre main: `check.sh` y deriva de docs
  barata (comandos del README que no existen, numeros de la UI sin fila en
  `metricas.md`, variables de `.env.example` sin uso en `settings.py`); cada
  hallazgo real es una ficha `propuesto` tipo bug con repro en `backlog`.
  Lo que se echo de menos usando la app (un filtro que falta, un dato que
  no se puede ver, un paso de mas) va como idea a `ALCANCE.md`, con la
  pantalla y el paso. Sin nada, informe.

