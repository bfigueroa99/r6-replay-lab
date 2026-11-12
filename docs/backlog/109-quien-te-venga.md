# 109. Quien te venga

estado: disenado
candado: -
rama: -
tipo: funcionalidad
epica: escuadra
area: fullstack
prioridad: 3
fuente: ALCANCE.md C14 (primer tramo de C2 mirado desde ti)
archivos: backend/replays/models.py, backend/replays/migrations/0007_roundplayer_avenged_me.py, backend/replays/analytics/metrics.py (annotate_trades traded_by, quien_te_venga), backend/replays/ingest.py (_import_round), backend/replays/recompute.py, backend/replays/management/commands/recompute.py (help), backend/replays/analytics/aggregates.py (teammate_synergy), backend/replays/management/commands/seed_demo.py, backend/tests/test_quien_te_venga.py, backend/tests/test_seed_demo.py, frontend/src/quienTeVenga.js, frontend/src/quienTeVenga.test.js, frontend/src/pages/Teammates.jsx, frontend/e2e/humo.spec.js, docs/metricas.md
turnos: po 20261112T1127Z-cT8M5Vz, arquitecto 20261112T1603Z-cor3JBP

## PR

## Que gana quien usa la app

En Compañeros, por compañero habitual: cuantas de tus muertes vengo (mato a
tu asesino dentro de la ventana de trade) y cuantas veces estaba vivo y no lo
hizo. Dice con quien tus muertes no salen gratis, que el winrate por
compañero no separa.

## Criterios de aceptacion

- [ ] `/api/teammates/` devuelve por compañero (las mismas filas y muestra
      minima que `synergy`): `avenged` (tus muertes donde el fue quien mato
      a tu asesino dentro de `TRADE_WINDOW_SECONDS`), `alive_not_avenged`
      (tus muertes sin trade suyo con el vivo en ese momento) y la tasa.
      Test con una ronda armada: el compañero mata a tu asesino a 2 s cuenta
      `avenged`; a 5 s, con ventana 3, cuenta `alive_not_avenged`.
- [ ] Un compañero ya muerto cuando caiste no suma en ninguna columna; un
      trade hecho por otro compañero no le suma a el. Test.
- [ ] Usa la misma ventana que `was_traded` y no la duplica: cambiar
      `TRADE_WINDOW_SECONDS` y correr `recompute` mueve los dos numeros
      igual (test con `self.settings`, como `test_recompute`).
- [ ] La columna o tabla se ve en Compañeros; sin datos, un texto vacio y no
      un error. El e2e de humo pasa por Compañeros con la consola limpia.
- [ ] Fila nueva en `docs/metricas.md` ("Quien te venga").

## Fuera de alcance

- La matriz de trades de todo el equipo (C2).
- Tiempo de refrag (C6) y quien te venga a ti como rival (D*).

## Diseno

(arquitecto 20261112T1603Z-cor3JBP) Filtros duros: pasa (usa Kill, Death y
PlayerLeave del feed, `team_of` y la ventana de trade que ya existen; sin red,
sin dependencias, sin POST). Toca migracion y `recompute`: plan por consenso
en modo deliberado, 2 rondas (ronda 1: critic ITERATE, 3 MAJOR; ronda 2:
critic APPROVE, architect sin bloqueantes).

**Implementar despues de que #79 se mergee**: la migracion es
`0007_roundplayer_avenged_me` sobre `0006_match_excluded`, que solo existe en
la rama de la 79. Si al implementar otra ficha ya mergeo una 0007, renumerar a
0008 y rehacer `dependencies`.

Bloqueo: migracion 0007 sobre 0006_match_excluded; Implementar despues de que #79 se mergee (estado.sh frena la ficha hasta entonces).
Objetivo: en Companeros, por companero habitual (mismas filas y muestra minima que synergy): cuantas de tus muertes vengo, cuantas estaba vivo y no, y la tasa. Misma ventana y regla que was_traded.
RALPLAN-DR: principios: una regla de trade (annotate_trades); calcular al importar; recompute rehace lo que depende de la ventana; sin deps ni tocar firma de analyse_round; seed deterministico. Drivers: no duplicar ventana; /api/teammates/ barato; migracion y recompute seguros. Opciones: A (elegida) dos booleanos en fila del companero avenged_me, alive_not_avenged_me con Count(filter); B avenged_by en tu fila + vivo al consultar (viola a medias); C todo al consultar (viola, duplica ventana).
Regla (en metricas.md): tu muerte = primer Kill (orden del feed) con victima vos. Solo cuenta si su autor es rival segun team_of; Death sin autor, teamkill, autor fuera de team_of o sin Kill tuyo: nadie suma. Vivo = companero (mismo team_of, distinto de vos) sin Kill como victima, Death ni PlayerLeave en posicion anterior a tu muerte. Si ese Kill tiene traded_by y es un companero vivo, suma avenged_me; los demas vivos alive_not_avenged_me. El que tambien mato a tu asesino pero sin el trade (break de annotate_trades asigna el primer vengador) queda alive_not; documentado. Diferencia con was_traded (que vale con cualquier Kill tuyo tradeado, incluido teamkill vengado) documentada. Tasa avenged/(avenged+alive_not), null si 0.
Pasos:
1 metrics.py: annotate_trades resetea e["traded_by"]="" con traded y al marcar pone e["traded_by"]=later["actor"]. Funcion pura quien_te_venga(eventos, team_of, yo) -> {nick: "avenged"|"alive_not"}; lee kind, actor, target, traded_by con .get; orden = posicion en la lista (llamadores ordenan por order). Docstring "Unica implementacion: import, recompute y la migracion 0007; su firma no cambia". analyse_round no se toca.
2 ingest.py _import_round: despues del loop de jugadores y antes del bulk_create: yo = username del RoundPlayer is_me (si no hay, {}); team_of = {p["username"]: p.get("teamIndex",0) for p in round_data["players"]}; quien_te_venga(analysis["events"], team_of, yo) (eventos ya traen traded_by porque kill_events son los mismos dicts); fija los booleanos.
3 recompute.py: planos agrega clock y traded; kill_events = [p for p in planos if kind==KILL] (mismos dicts); claves inicializadas en False en metrics para todos; tras annotate_trades yo = jugador is_me (o None -> nada), quien_te_venga(planos, team_of, yo); CAMPOS suma las dos columnas; docstring y help de recompute.
4 models.py RoundPlayer: avenged_me, alive_not_avenged_me BooleanField(default=False). migrations/0007_roundplayer_avenged_me.py: AddField x2 + RunPython(llenar, noop): solo rondas is_me=True died=True, salta rondas sin jugadores; eventos values_list por order. traded_by se reconstruye desde Event sin llamar a annotate_trades: si tu Kill tiene traded=True, traded_by = autor del primer Kill posterior de un companero sobre tu asesino. Por que: como la 0004, copia la marca que sostiene el was_traded visible (ventana del import o ultimo recompute) en vez de recalcular con la vigente. Con relojes no monotonos el vengador puede diferir; recompute corrige. Luego quien_te_venga y bulk_update en lotes de 200.
5 aggregates.teammate_synergy suma avenged=Count(filter avenged_me), alive_not_avenged=Count(filter alive_not_avenged_me), avenge_rate=_pct(...) o None. Vista sin cambios.
6 seed_demo.py llena columnas sin eventos (convencion was_traded): si murio, companero vivo = not died o death_elapsed > muerte; si tradeado el primer vivo por indice avenged, resto alive_not; si no, todos los vivos alive_not. Toda ronda tradeada (indice%12 en {4,8}) tiene un vivo. Numeros del e2e se calculan con seed_demo real en base temporal. Nota en metricas.md: recompute sobre el seed deja avenged en 0 (igual que was_traded). Frontend: frontend/src/quienTeVenga.js filasQuienTeVenga(synergy) filtra avenged+alive_not>0, ordena por tasa desc y nick; quienTeVenga.test.js; Panel "Quién te venga" debajo de Sinergia en Teammates.jsx con el mismo minRounds; columnas Compañero, Vengó, Vivo y no vengó, %; vacio "Ningún compañero estaba vivo cuando caíste con estos filtros."; npm run build. metricas.md fila con la regla. e2e humo.spec.js "Compañeros muestra quién te venga" junto a Companeros (687-724).
Tests unit test_quien_te_venga.py: vengar_a_los_2_segundos_suma_vengo; 5_segundos_con_ventana_3_cuenta_vivo_y_no_vengo; companero_ya_muerto_no_suma_nada; companero_que_se_fue_antes_no_cuenta_vivo; el_trade_de_otro_companero_deja_al_resto_vivo_y_no_vengo; el_que_tambien_mato_pero_sin_el_trade_queda_vivo_y_no_vengo; sin_muerte_tuya_nadie_suma; muerte_sin_autor_nadie_suma; teamkill_nadie_suma; traded_by_es_el_autor_del_kill_vengador; traded_by_se_resetea_al_achicar_la_ventana. Integracion: api_companeros_trae_vengo_y_tasa; tasa_nula_sin_muertes_con_companeros_vivos; cambiar_la_ventana_y_recompute_mueve_vengo_igual_que_was_traded; import_y_recompute_dan_lo_mismo; recompute_llena_lo_importado; migracion_0007_reconstruye_desde_event_sin_recalcular_ventana; migracion_0007_no_se_cae_con_ronda_sin_jugadores_ni_eventos. Seed: vengo_del_seed_suma_lo_mismo_que_tus_rondas_tradeadas. Vitest.
Pre-mortem: 1 ventana vigente distinta a la del import (0007 copia Event.traded; recompute rehace ambas; test de migracion con ventana cambiada). 2 migracion lenta o rota (filtros, .get, lotes, test ronda rota). 3 seed rompe e2e (solo columnas nuevas; check completo).
Puede romperse: KeyError en recompute sin claves; planos y kill_events dejan de ser los mismos dicts -> traded_by se pierde; e2e de Companeros que cuentan paneles por posicion (687-797).
Preguntas al humano (no bloqueantes): teamkill vengado o muerte sin autor, contar? (hoy no); el que mato a tu asesino sin el trade cuenta como no vengo?

Ajustes del consenso para el Dev (MINOR de la ronda 2):
1. Docstring de la 0007: congela firma y semantica de `quien_te_venga`; si la
   regla cambia, se corrige con `recompute`, nunca editando la 0007 (precedente
   0005). El vengador se reconstruye por posicion, sin reloj: equivale a
   `annotate_trades` porque un asesino muere una sola vez; test de la
   migracion con un reloj no monotono que documente la diferencia.
2. El caso del `break` (otro compañero tambien mata a tu asesino sin el trade)
   es casi teorico: el test se mantiene, `metricas.md` no lo presenta como
   frecuente.
3. `planos` y `kill_events` de `recompute.py` salen los dos de `eventos` ya
   ordenado por `order` (recompute.py:63), para no romper el
   `zip(strict=True)`.
4. Tasa nula se muestra "—" en la columna %, como los demas paneles.
5. El e2e ubica el panel con `section.panel` + heading "Quién te venga", no
   por posicion (no romper los `nth()` de las tablas de clutch).
6. `test_vengo_del_seed_suma_lo_mismo_que_tus_rondas_tradeadas` afirma el
   total exacto, no solo > 0.
7. Test de la migracion llamando a `llenar` directo, como
   `tests/test_aperturas_trade.py:220`.

**Verificacion manual (y `## Verificar en el PC` de QA).** `manage.py backup`,
`migrate` (0007), `recompute --dry-run` (las filas que cambian por las dos
columnas nuevas solo si cambiaste la ventana), `recompute`; en Compañeros, el
panel con tasas creibles (no 0 % ni 100 % en todos).

Skills: no aplica (tabla en una pagina existente y migracion con precedentes 0004 y 0005).
OMC: plan=APPROVE (2 rondas) · revisión=— · verificación=—

## Para el humano

Preguntas no bloqueantes (variante conservadora en el diseno): (1) una muerte
tuya por teamkill vengado o sin autor, ¿deberia contar? Hoy no suma a nadie.
(2) El compañero que mato a tu asesino pero se quedo sin el trade (otro lo
mato antes en la ventana), ¿es "no vengó"? Hoy si.

## Implementacion

## Revision

## QA
