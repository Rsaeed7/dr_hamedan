# Generated by Django 5.2 on 2025-07-29 16:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('homecare', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='service',
            name='estimated_price',
            field=models.IntegerField(verbose_name='هزینه حدودی (تومان)'),
        ),
    ]
