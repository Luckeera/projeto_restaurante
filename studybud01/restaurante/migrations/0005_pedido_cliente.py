# Generated by Django 5.2 on 2025-05-02 18:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurante', '0004_remove_pedido_prato_remove_pedido_quantidade_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='pedido',
            name='cliente',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, related_name='meus_pedidos', to=settings.AUTH_USER_MODEL),
            preserve_default=False,
        ),
    ]
