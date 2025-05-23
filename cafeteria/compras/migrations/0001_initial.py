# Generated by Django 5.1.7 on 2025-04-17 20:11

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Proveedor",
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
                ("nombre", models.CharField(max_length=100)),
                ("telefono", models.CharField(blank=True, max_length=20, null=True)),
                ("email", models.EmailField(blank=True, max_length=254, null=True)),
                ("direccion", models.TextField(blank=True, null=True)),
                ("notas", models.TextField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "Proveedor",
                "verbose_name_plural": "Proveedores",
                "ordering": ["nombre"],
            },
        ),
        migrations.CreateModel(
            name="Compra",
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
                ("fecha", models.DateField(default=django.utils.timezone.now)),
                (
                    "tipo_documento",
                    models.CharField(
                        choices=[
                            ("boleta", "Boleta"),
                            ("factura", "Factura"),
                            ("sin_documento", "Sin Documento"),
                            ("transferencia", "Transferencia"),
                            ("otro", "Otro"),
                        ],
                        default="boleta",
                        max_length=20,
                    ),
                ),
                (
                    "numero_documento",
                    models.CharField(
                        blank=True,
                        help_text="Número de boleta, factura o transferencia",
                        max_length=30,
                        null=True,
                    ),
                ),
                (
                    "destino",
                    models.CharField(
                        help_text="Área o departamento de destino", max_length=100
                    ),
                ),
                (
                    "detalle",
                    models.TextField(help_text="Descripción de artículos comprados"),
                ),
                ("total", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "comprobante",
                    models.FileField(
                        blank=True,
                        help_text="Imagen o PDF del comprobante",
                        null=True,
                        upload_to="comprobantes/",
                    ),
                ),
                ("notas_adicionales", models.TextField(blank=True, null=True)),
                (
                    "proveedor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="compras",
                        to="compras.proveedor",
                    ),
                ),
            ],
            options={
                "verbose_name": "Compra",
                "verbose_name_plural": "Compras",
                "ordering": ["-fecha"],
            },
        ),
    ]
