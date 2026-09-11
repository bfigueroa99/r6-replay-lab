"""Motor de insights: convierte los agregados en cosas concretas que corregir.

Reglas explicitas, con muestra minima en cada una para no sacar conclusiones de
tres rondas. Cada insight trae el numero, la referencia con la que se compara y
que hacer al respecto.
"""

from __future__ import annotations

from . import aggregates as agg

SEVERITY_ORDER = {"alta": 0, "media": 1, "baja": 2, "positivo": 3}


def _insight(
    key: str,
    severity: str,
    title: str,
    detail: str,
    action: str,
    *,
    metric: str = "",
    value=None,
    baseline=None,
    sample: int = 0,
    scope: str = "general",
) -> dict:
    return {
        "key": key,
        "severity": severity,
        "title": title,
        "detail": detail,
        "action": action,
        "metric": metric,
        "value": value,
        "baseline": baseline,
        "sample": sample,
        "scope": scope,
    }


def build_insights(**filters) -> dict:
    """Devuelve los insights ordenados por severidad."""
    over = agg.overview(**filters)
    overall = over["overall"]
    attack = over["attack"]
    defense = over["defense"]
    insights: list[dict] = []

    if (overall.get("rounds") or 0) < 20:
        return {
            "insights": [
                _insight(
                    "sin-datos",
                    "baja",
                    "Falta volumen para sacar conclusiones",
                    f"Tienes {overall.get('rounds') or 0} rondas importadas. "
                    "Con menos de 20 cualquier porcentaje es ruido.",
                    "Juega e importa unas cuantas partidas mas y vuelve a mirar esto.",
                    metric="rounds",
                    value=overall.get("rounds") or 0,
                    baseline=20,
                    sample=overall.get("rounds") or 0,
                )
            ],
            "totals": overall,
        }

    insights += _opening_duels(overall, attack, defense)
    insights += _trades(overall)
    insights += _early_deaths(attack, defense)
    insights += _sides(attack, defense)
    insights += _aim(overall)
    insights += _impact(overall)
    insights += _maps(overall, **filters)
    insights += _sites(overall, **filters)
    insights += _operators(overall, **filters)
    insights += _spawns(overall, **filters)
    insights += _round_flow(**filters)
    insights += _sesiones(**filters)
    insights += _momento_de_la_muerte(**filters)
    insights += _duelos_por_operador(**filters)
    insights += _nemesis(**filters)
    insights += _form(overall, **filters)

    insights.sort(key=lambda i: (SEVERITY_ORDER.get(i["severity"], 9), -(i["sample"] or 0)))
    return {"insights": insights, "totals": overall}


# --------------------------------------------------------------------- reglas


def _opening_duels(overall, attack, defense) -> list[dict]:
    out = []
    duels = overall.get("opening_duels") or 0
    wr = overall.get("opening_winrate")
    if duels >= 20 and wr is not None:
        if wr < 45:
            out.append(
                _insight(
                    "duelos-apertura",
                    "alta" if wr < 38 else "media",
                    f"Pierdes el {100 - wr:.0f}% de los duelos de apertura",
                    f"Ganaste {overall['opening_kills']} de {duels} primeros duelos. "
                    f"Cuando ganas la apertura la ronda se te va en "
                    f"{overall.get('winrate_after_opening_kill') or 0:.0f}% de victorias; "
                    f"cuando la pierdes, {overall.get('winrate_after_opening_death') or 0:.0f}%.",
                    "Deja de tomar el primer duelo sin apoyo: pide que alguien te siga a "
                    "distancia de trade, o cede el primer contacto y juega el refrag.",
                    metric="opening_winrate",
                    value=wr,
                    baseline=50,
                    sample=duels,
                )
            )
        elif wr >= 58:
            out.append(
                _insight(
                    "duelos-apertura-fuerte",
                    "positivo",
                    f"Ganas el {wr:.0f}% de los duelos de apertura",
                    f"{overall['opening_kills']} de {duels}. Es tu mejor herramienta.",
                    "Pide explicitamente el rol de entry/primer contacto y que te sigan "
                    "para tradear.",
                    metric="opening_winrate",
                    value=wr,
                    baseline=50,
                    sample=duels,
                )
            )

    for label, row in (("ataque", attack), ("defensa", defense)):
        d = row.get("opening_duels") or 0
        w = row.get("opening_winrate")
        if d >= 15 and w is not None and w < 40:
            out.append(
                _insight(
                    f"duelos-apertura-{label}",
                    "media",
                    f"En {label} los primeros duelos se te van ({w:.0f}%)",
                    f"{row['opening_kills']} de {d} duelos ganados en {label}.",
                    (
                        "En ataque: usa dron antes de cruzar y no pelees a la salida del spawn."
                        if label == "ataque"
                        else "En defensa: no hagas roam agresivo los primeros 20 segundos, "
                        "consolida y usa camara."
                    ),
                    metric="opening_winrate",
                    value=w,
                    baseline=50,
                    sample=d,
                    scope=label,
                )
            )
    return out


def _trades(overall) -> list[dict]:
    deaths = overall.get("deaths") or 0
    untraded = overall.get("untraded_death_pct")
    if deaths >= 30 and untraded is not None and untraded > 65:
        return [
            _insight(
                "muertes-sin-trade",
                "alta" if untraded > 78 else "media",
                f"El {untraded:.0f}% de tus muertes no las venga nadie",
                f"{overall['untraded_deaths']} de {deaths} muertes quedaron sin trade. "
                "Eso significa que te mueres lejos del equipo o primero de todos.",
                "Juega a menos de 5 segundos de un compañero: si te matan, el que te sigue "
                "tiene que poder ver al asesino sin rotar medio mapa.",
                metric="untraded_death_pct",
                value=untraded,
                baseline=60,
                sample=deaths,
            )
        ]
    if deaths >= 30 and untraded is not None and untraded < 45:
        return [
            _insight(
                "muertes-tradeadas",
                "positivo",
                f"Solo el {untraded:.0f}% de tus muertes queda sin vengar",
                "Estas jugando pegado al equipo; tus muertes cuestan poco.",
                "Manten esa distancia y aprovechala para forzar duelos que te favorezcan.",
                metric="untraded_death_pct",
                value=untraded,
                baseline=60,
                sample=deaths,
            )
        ]
    return []


def _early_deaths(attack, defense) -> list[dict]:
    out = []
    for label, row, limit in (("ataque", attack, 50), ("defensa", defense, 45)):
        avg = row.get("avg_death_elapsed")
        deaths = row.get("deaths") or 0
        if deaths >= 20 and avg is not None and avg < limit:
            out.append(
                _insight(
                    f"muerte-temprana-{label}",
                    "media",
                    f"En {label} mueres a los {avg:.0f}s promedio",
                    f"Sobre {deaths} muertes. La ronda dura ~3 minutos: te estas quedando "
                    "fuera de la mayor parte de la ronda.",
                    (
                        "En ataque, gasta los primeros 40s en dronear y abrir paredes, no en "
                        "buscar pelea."
                        if label == "ataque"
                        else "En defensa, arma el sitio primero y sal a roamear despues de que "
                        "sepas de donde vienen."
                    ),
                    metric="avg_death_elapsed",
                    value=avg,
                    baseline=limit,
                    sample=deaths,
                    scope=label,
                )
            )
    return out


#: Con menos muertes de un lado, los porcentajes de la distribucion son ruido.
MUESTRA_MUERTES = 25


def _momento_de_la_muerte(**filters) -> list[dict]:
    """Los dos extremos de la distribucion: salir temprano y quedarse sin tiempo.

    Son problemas distintos con arreglos opuestos, y el promedio de
    `avg_death_elapsed` los tapa a los dos: quien muere mitad a los 20 y mitad a
    los 170 tiene el mismo promedio que quien muere siempre a los 95.
    """
    timing = agg.death_timing(**filters)
    out = []

    for clave, label in (("attack", "ataque"), ("defense", "defensa")):
        fila = timing[clave]
        if fila["deaths"] < MUESTRA_MUERTES:
            continue

        # un sexto de la ronda son los primeros 30s: mas de un cuarto de las
        # muertes ahi es concentracion, no reparto normal
        if (fila["first30_pct"] or 0) >= 25:
            out.append(
                _insight(
                    f"muertes-tempranas-{label}",
                    "media",
                    f"En {label} el {fila['first30_pct']:.0f}% de tus muertes es en los "
                    "primeros 30s",
                    f"{fila['first30']} de {fila['deaths']} muertes en {label} pasan antes de que "
                    "la ronda se arme. Mueres con informacion de nadie y con el equipo todavia "
                    "agrupado.",
                    (
                        "En ataque: dronea antes de cruzar y no pelees el spawnpeek."
                        if label == "ataque"
                        else "En defensa: no salgas a roamear en los primeros segundos; consolida "
                        "el sitio y sal cuando sepas de donde vienen."
                    ),
                    metric="first30_pct",
                    value=fila["first30_pct"],
                    baseline=25,
                    sample=fila["deaths"],
                    scope=label,
                )
            )

    ataque = timing["attack"]
    if ataque["deaths"] >= MUESTRA_MUERTES and (ataque["last30_pct"] or 0) >= 25:
        out.append(
            _insight(
                "sin-tiempo-ataque",
                "media",
                f"En ataque mueres con el reloj casi agotado el "
                f"{ataque['last30_pct']:.0f}% de las veces",
                f"{ataque['last30']} de {ataque['deaths']} muertes en ataque pasan con menos de "
                f"{agg.CLOCK_TAIL} segundos de reloj. A esa altura la ronda ya no da para plantar: "
                "la ejecucion nunca llego a empezar.",
                "Ponle hora al ataque: dronea y abre los primeros 60 segundos, pero entra antes "
                "del minuto y medio aunque la informacion no este completa. Llegar tarde al sitio "
                "es perder la ronda sin pelearla.",
                metric="last30_pct",
                value=ataque["last30_pct"],
                baseline=25,
                sample=ataque["deaths"],
                scope="ataque",
            )
        )
    return out


def _sides(attack, defense) -> list[dict]:
    a, d = attack.get("winrate"), defense.get("winrate")
    ar, dr = attack.get("rounds") or 0, defense.get("rounds") or 0
    if a is None or d is None or min(ar, dr) < 25:
        return []
    gap = a - d
    if abs(gap) < 12:
        return []
    weak, strong = ("ataque", "defensa") if gap < 0 else ("defensa", "ataque")
    weak_wr, strong_wr = (a, d) if gap < 0 else (d, a)
    return [
        _insight(
            "desbalance-lados",
            "media",
            f"Tu {weak} rinde {abs(gap):.0f} puntos menos que tu {strong}",
            f"{weak}: {weak_wr:.0f}% de rondas ganadas · {strong}: {strong_wr:.0f}%.",
            (
                "Dedica una sesion a revisar ejecuciones de ataque: sitios donde entras, "
                "quien abre, quien tradea."
                if weak == "ataque"
                else "Revisa tus setups de defensa: refuerzos, angulos y donde te paras "
                "en los sitios que mas juegas."
            ),
            metric="winrate",
            value=weak_wr,
            baseline=strong_wr,
            sample=min(ar, dr),
            scope=weak,
        )
    ]


def _aim(overall) -> list[dict]:
    kills = overall.get("kills") or 0
    hs = overall.get("hs_pct")
    if kills < 40 or hs is None:
        return []
    if hs < 25:
        return [
            _insight(
                "headshots",
                "media",
                f"Solo {hs:.0f}% de tus bajas son headshot",
                f"{overall['headshots']} de {kills} bajas. En Siege la cabeza mata de un tiro: "
                "un hs% bajo suele ser crosshair placement, no puntería.",
                "Apunta a la altura de cabeza mientras te mueves y haz 10 minutos de "
                "campo de tiro antes de jugar ranked.",
                metric="hs_pct",
                value=hs,
                baseline=30,
                sample=kills,
            )
        ]
    if hs >= 45:
        return [
            _insight(
                "headshots-fuerte",
                "positivo",
                f"{hs:.0f}% de headshots",
                f"{overall['headshots']} de {kills} bajas. Tu mecanica no es el problema.",
                "Si el winrate no acompaña, el trabajo esta en decisiones y posicion, no en aim.",
                metric="hs_pct",
                value=hs,
                baseline=30,
                sample=kills,
            )
        ]
    return []


def _impact(overall) -> list[dict]:
    out = []
    rounds = overall.get("rounds") or 0
    kst = overall.get("kst_pct")
    if rounds >= 40 and kst is not None and kst < 65:
        out.append(
            _insight(
                "kst",
                "alta" if kst < 55 else "media",
                f"Aportas algo en solo el {kst:.0f}% de las rondas",
                f"KST = rondas donde matas, sobrevives o tu muerte se tradea. "
                f"{overall['kst_rounds']} de {rounds}. El resto son rondas en las que el "
                "equipo jugo con uno menos.",
                "Antes que buscar mas kills, apunta a no morir gratis: sobrevivir ya cuenta.",
                metric="kst_pct",
                value=kst,
                baseline=70,
                sample=rounds,
            )
        )
    clutch = overall.get("clutch_rounds") or 0
    if rounds >= 40 and clutch == 0:
        out.append(
            _insight(
                "sin-clutches",
                "baja",
                "No tienes rondas 1vX ganadas",
                f"En {rounds} rondas no cerraste ninguna quedandote solo.",
                "Cuando quedes ultimo, juega el reloj y separa los duelos: uno a la vez, "
                "nunca dos angulos abiertos.",
                metric="clutch_rounds",
                value=0,
                baseline=1,
                sample=rounds,
            )
        )
    return out


def _maps(overall, **filters) -> list[dict]:
    base = overall.get("winrate")
    if base is None:
        return []
    rows = [r for r in agg.by_map(min_rounds=15, **filters) if r.get("winrate") is not None]
    if len(rows) < 2:
        return []
    out = []
    worst = min(rows, key=lambda r: r["winrate"])
    if worst["winrate"] < base - 10:
        out.append(
            _insight(
                "mapa-debil",
                "media",
                f"{worst['map']} es tu peor mapa ({worst['winrate']:.0f}%)",
                f"{worst['rounds']} rondas jugadas, contra un {base:.0f}% general. "
                f"Ataque {worst.get('attack_winrate') or 0:.0f}% · "
                f"defensa {worst.get('defense_winrate') or 0:.0f}%.",
                f"Elige un solo sitio de {worst['map']} y aprendetelo completo: refuerzos, "
                "rotaciones y dos angulos de defensa. Es mas rentable que estudiar el mapa entero.",
                metric="winrate",
                value=worst["winrate"],
                baseline=base,
                sample=worst["rounds"],
                scope=worst["map"],
            )
        )
    best = max(rows, key=lambda r: r["winrate"])
    if best["winrate"] > base + 10:
        out.append(
            _insight(
                "mapa-fuerte",
                "positivo",
                f"{best['map']} es tu mapa ({best['winrate']:.0f}%)",
                f"{best['rounds']} rondas, {best['winrate'] - base:+.0f} puntos sobre tu promedio.",
                "Cuando puedas votar o banear, empuja para jugar este mapa.",
                metric="winrate",
                value=best["winrate"],
                baseline=base,
                sample=best["rounds"],
                scope=best["map"],
            )
        )
    return out


def _sites(overall, **filters) -> list[dict]:
    base = overall.get("winrate")
    rows = [r for r in agg.by_site(min_rounds=8, **filters) if r.get("winrate") is not None]
    if base is None or not rows:
        return []
    worst = min(rows, key=lambda r: r["winrate"])
    if worst["winrate"] >= base - 15:
        return []
    return [
        _insight(
            "sitio-debil",
            "media",
            f"{worst['site']} en {worst['map']}: {worst['winrate']:.0f}% de rondas ganadas",
            f"{worst['rounds']} rondas en ese sitio, {base - worst['winrate']:.0f} puntos bajo "
            "tu promedio.",
            "Anota que hacen distinto los equipos que te ganan ahi: por donde entran y que "
            "pared abren primero. Es el sitio con mas retorno para estudiar.",
            metric="winrate",
            value=worst["winrate"],
            baseline=base,
            sample=worst["rounds"],
            scope=f"{worst['map']} · {worst['site']}",
        )
    ]


def _operators(overall, **filters) -> list[dict]:
    base_wr = overall.get("winrate")
    base_kpr = overall.get("kpr")
    rows = [r for r in agg.by_operator(min_rounds=12, **filters) if r.get("winrate") is not None]
    if base_wr is None or not rows:
        return []
    out = []
    bad = [
        r
        for r in rows
        if r["winrate"] < base_wr - 12 or (base_kpr and (r.get("kpr") or 0) < base_kpr * 0.7)
    ]
    if bad:
        worst = min(bad, key=lambda r: r["winrate"])
        out.append(
            _insight(
                "operador-debil",
                "media",
                f"Con {worst['operator']} rindes por debajo de tu promedio",
                f"{worst['rounds']} rondas · {worst['winrate']:.0f}% ganadas · "
                f"{worst.get('kpr') or 0:.2f} kills por ronda (tu promedio: {base_kpr:.2f}).",
                f"O te dedicas a aprender {worst['operator']} de verdad (utilidad incluida) o "
                "lo saltas y te quedas con tu pool corto.",
                metric="winrate",
                value=worst["winrate"],
                baseline=base_wr,
                sample=worst["rounds"],
                scope=worst["operator"],
            )
        )
    good = [r for r in rows if r["winrate"] > base_wr + 10]
    if good:
        best = max(good, key=lambda r: r["winrate"])
        out.append(
            _insight(
                "operador-fuerte",
                "positivo",
                f"{best['operator']} es tu mejor operador ({best['winrate']:.0f}%)",
                f"{best['rounds']} rondas · {best.get('kpr') or 0:.2f} kills por ronda.",
                "Priorizalo en el pick y arma tu pool alrededor de ese rol.",
                metric="winrate",
                value=best["winrate"],
                baseline=base_wr,
                sample=best["rounds"],
                scope=best["operator"],
            )
        )
    return out


def _spawns(overall, **filters) -> list[dict]:
    rows = [r for r in agg.by_spawn(min_rounds=8, **filters) if r.get("winrate") is not None]
    if len(rows) < 3:
        return []
    base = overall.get("winrate") or 0
    worst = min(rows, key=lambda r: r["winrate"])
    if worst["winrate"] >= base - 18:
        return []
    return [
        _insight(
            "spawn-debil",
            "baja",
            f"Atacando desde {worst['spawn']} ({worst['map']}) ganas {worst['winrate']:.0f}%",
            f"{worst['rounds']} rondas desde ese spawn.",
            "Cambia la ruta de entrada desde ese spawn: si siempre vas por el mismo lado, "
            "la defensa ya lo tiene resuelto.",
            metric="winrate",
            value=worst["winrate"],
            baseline=base,
            sample=worst["rounds"],
            scope=f"{worst['map']} · {worst['spawn']}",
        )
    ]


def _round_flow(**filters) -> list[dict]:
    rows = [r for r in agg.by_round_number(**filters) if (r.get("rounds") or 0) >= 8]
    if len(rows) < 4:
        return []
    early = [r for r in rows if r["round_number"] < 3]
    late = [r for r in rows if r["round_number"] >= 6]
    if not early or not late:
        return []
    al_inicio = sum(r["rounds_won"] for r in early) / max(sum(r["rounds"] for r in early), 1) * 100
    al_final = sum(r["rounds_won"] for r in late) / max(sum(r["rounds"] for r in late), 1) * 100
    sample = sum(r["rounds"] for r in late)
    if al_inicio - al_final < 15:
        return []
    return [
        _insight(
            "rondas-finales",
            "media",
            f"Te caes en las rondas finales ({al_final:.0f}% vs {al_inicio:.0f}% al principio)",
            f"Primeras 3 rondas: {al_inicio:.0f}% ganadas. Ronda 7 en adelante: "
            f"{al_final:.0f}% ({sample} rondas).",
            "Cuando el marcador esta apretado, simplifica: menos jugadas nuevas, mas "
            "ejecucion del setup que ya te funciono en la primera mitad.",
            metric="winrate",
            value=round(al_final, 1),
            baseline=round(al_inicio, 1),
            sample=sample,
        )
    ]


#: Desde que partida de la sesion se considera "tarde". Es la pregunta natural
#: ("me quedo una mas?"), y fijarla evita salir a buscar el corte que mas
#: conviene entre varios, que es una forma barata de encontrar patrones falsos.
CORTE_SESION = 3


def _sesiones(**filters) -> list[dict]:
    """Compara el arranque de la sesion contra la parte tardia."""
    rows = agg.by_session_position(**filters)
    if len(rows) < CORTE_SESION:
        return []

    temprano = [r for r in rows if r["position"] < CORTE_SESION]
    tarde = [r for r in rows if r["position"] >= CORTE_SESION]
    if not temprano or not tarde:
        return []

    def resumen(filas):
        rondas = sum(r["rounds"] for r in filas)
        ganadas = sum(r["rounds_won"] for r in filas)
        kills = sum(r["kills"] for r in filas)
        return rondas, (ganadas / rondas * 100 if rondas else 0), (kills / rondas if rondas else 0)

    rondas_temprano, wr_temprano, kpr_temprano = resumen(temprano)
    rondas_tarde, wr_tarde, kpr_tarde = resumen(tarde)
    if min(rondas_temprano, rondas_tarde) < 30:
        return []

    caida = wr_temprano - wr_tarde
    if caida < 10:
        return []

    kpr = ""
    if kpr_temprano and kpr_tarde < kpr_temprano * 0.8:
        kpr = f" Tus bajas por ronda tambien bajan, de {kpr_temprano:.2f} a {kpr_tarde:.2f}."

    return [
        _insight(
            "fatiga-sesion",
            "media" if caida >= 15 else "baja",
            f"De la {CORTE_SESION}a partida en adelante ganas {caida:.0f} puntos menos",
            f"Primeras {CORTE_SESION - 1} partidas de cada sesion: {wr_temprano:.0f}% de rondas "
            f"ganadas sobre {rondas_temprano} rondas. De la {CORTE_SESION}a en adelante: "
            f"{wr_tarde:.0f}% sobre {rondas_tarde}.{kpr}",
            f"Fijate un tope de {CORTE_SESION - 1} partidas por sesion, o corta cuando notes que "
            "la segunda derrota seguida vino sin que pasara nada raro. Seguir jugando cansado "
            "cuesta mas MMR que cualquier error mecanico.",
            metric="winrate",
            value=round(wr_tarde, 1),
            baseline=round(wr_temprano, 1),
            sample=rondas_tarde,
        )
    ]


def _duelos_por_operador(**filters) -> list[dict]:
    """Operadores rivales contra los que pierdes mucho mas que tu promedio.

    Es la unica lectura por rival con muestra decente en ranked solo: la gente
    no se repite, los operadores si.
    """
    totals = agg.duel_totals(**filters)
    base = totals.get("winrate")
    if base is None or totals["duels"] < 60:
        return []
    rows = [
        r
        for r in agg.duels_by_operator(min_duels=8, **filters)
        if r.get("winrate") is not None and r["winrate"] <= base - 15
    ]
    if not rows:
        return []
    peor = min(rows, key=lambda r: (r["winrate"], -r["duels"]))
    return [
        _insight(
            "operador-rival",
            "media",
            f"Contra {peor['operator']} pierdes {peor['deaths']} de {peor['duels']} duelos",
            f"Ganas el {peor['winrate']:.0f}% de los duelos contra {peor['operator']}, "
            f"cuando tu promedio contra cualquiera es {base:.0f}%.",
            f"Revisa esas muertes: si te mata la utilidad de {peor['operator']} el problema es "
            "no limpiarla antes de entrar; si es duelo directo, es el angulo desde el que "
            "tomas el contacto.",
            metric="winrate",
            value=peor["winrate"],
            baseline=base,
            sample=peor["duels"],
            scope=peor["operator"],
        )
    ]


def _nemesis(**filters) -> list[dict]:
    """Un rival puntual que te gana siempre. En ranked solo casi nunca aplica."""
    totals = agg.duel_totals(**filters)
    base = totals.get("winrate")
    if base is None:
        return []
    rows = [
        r
        for r in agg.nemesis(min_duels=8, **filters)
        if r.get("winrate") is not None and r["winrate"] <= 25
    ]
    if not rows:
        return []
    peor = min(rows, key=lambda r: (r["winrate"], -r["duels"]))
    aperturas = ""
    if (peor["opening_duels"] or 0) >= 3 and (peor["opening_winrate"] or 0) < 50:
        aperturas = (
            f" {peor['opening_deaths']} de esos {peor['opening_duels']} fueron el primer "
            "duelo de la ronda."
        )
    return [
        _insight(
            "nemesis",
            "baja",
            f"{peor['username']} te gana {peor['deaths']} de {peor['duels']} duelos",
            f"Tu promedio contra cualquiera es {base:.0f}%; contra esta persona, "
            f"{peor['winrate']:.0f}%.{aperturas}",
            "Si te lo vuelves a cruzar, no tomes el primer contacto contra el: deja que "
            "alguien mas abra y juega el trade.",
            metric="winrate",
            value=peor["winrate"],
            baseline=base,
            sample=peor["duels"],
            scope=peor["username"],
        )
    ]


def _form(overall, **filters) -> list[dict]:
    series = agg.trend_by_match(limit=10, **filters)
    if len(series) < 6:
        return []
    recent = series[-5:]
    rounds = sum(r["rounds"] for r in recent)
    won = sum(r["rounds_won"] for r in recent)
    if not rounds:
        return []
    wr = won / rounds * 100
    base = overall.get("winrate") or 0
    if wr < base - 12:
        return [
            _insight(
                "bajon",
                "baja",
                f"Ultimas 5 partidas: {wr:.0f}% de rondas ganadas",
                f"Tu promedio historico es {base:.0f}%. Puede ser varianza o puede ser cansancio.",
                "Si son tres derrotas seguidas, corta la sesion. El tilt cuesta mas MMR que "
                "cualquier error mecanico.",
                metric="winrate",
                value=round(wr, 1),
                baseline=base,
                sample=rounds,
            )
        ]
    if wr > base + 12:
        return [
            _insight(
                "racha",
                "positivo",
                f"Ultimas 5 partidas: {wr:.0f}% de rondas ganadas",
                f"Vas {wr - base:+.0f} puntos sobre tu promedio.",
                "Aprovecha la racha, pero fijate un tope de partidas para no devolverlo todo.",
                metric="winrate",
                value=round(wr, 1),
                baseline=base,
                sample=rounds,
            )
        ]
    return []
