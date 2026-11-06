from django.db import migrations, models

from replays.analytics.metrics import clutch_kills


def llenar(apps, schema_editor):
    """Calcula `clutch_kills` de lo ya importado con la misma regla del import.

    Sin esto todo clutch ganado quedaria en 0 y se veria silencioso. Corre en
    la base real al primer `runserver`: rondas sin jugadores o eventos sin
    nick no pueden tumbarla. Solo mira rondas con un intento de clutch: en el
    resto el valor es 0 por definicion.
    """
    RoundPlayer = apps.get_model("replays", "RoundPlayer")
    Event = apps.get_model("replays", "Event")

    rondas = (
        RoundPlayer.objects.filter(clutch_vs__gt=0)
        .values_list("round_id", flat=True)
        .distinct()
    )
    cambiados = []
    for round_id in list(rondas):
        jugadores = list(RoundPlayer.objects.filter(round_id=round_id))
        if not jugadores:
            continue
        team_of = {p.username: p.team_index for p in jugadores}
        eventos = [
            {"kind": kind, "actor": actor, "target": target}
            for kind, actor, target in Event.objects.filter(round_id=round_id)
            .order_by("order")
            .values_list("kind", "actor_name", "target_name")
        ]
        valores = clutch_kills(eventos, team_of)
        for p in jugadores:
            k = valores.get(p.username, 0)
            if p.clutch_kills != k:
                p.clutch_kills = k
                cambiados.append(p)
        if len(cambiados) >= 200:
            RoundPlayer.objects.bulk_update(cambiados, ["clutch_kills"])
            cambiados = []
    if cambiados:
        RoundPlayer.objects.bulk_update(cambiados, ["clutch_kills"])


class Migration(migrations.Migration):

    dependencies = [
        ("replays", "0004_roundplayer_opening_kill_traded"),
    ]

    operations = [
        migrations.AddField(
            model_name="roundplayer",
            name="clutch_kills",
            field=models.IntegerField(default=0),
        ),
        migrations.RunPython(llenar, migrations.RunPython.noop),
    ]
