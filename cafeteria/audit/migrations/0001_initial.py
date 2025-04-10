# Generated by Django 5.1.7 on 2025-03-24 15:34

from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="LogActividad",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("fecha_hora", models.DateTimeField(auto_now_add=True)),
                ("accion", models.CharField(max_length=255)),
                ("modelo", models.CharField(max_length=100)),
                ("objeto_id", models.IntegerField()),
                ("detalles", models.JSONField(default=dict)),
            ],
            options={
                "verbose_name": "Log de Actividad",
                "verbose_name_plural": "Logs de Actividad",
                "ordering": ["-fecha_hora"],
            },
        ),
    ]
