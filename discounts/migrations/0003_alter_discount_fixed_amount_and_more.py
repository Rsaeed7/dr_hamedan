# Generated by Django 5.2 on 2025-07-29 16:42

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('discounts', '0002_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='discount',
            name='fixed_amount',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='مبلغ ثابت تخفیف'),
        ),
        migrations.AlterField(
            model_name='discount',
            name='max_discount_amount',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='حداکثر مبلغ تخفیف'),
        ),
        migrations.AlterField(
            model_name='discount',
            name='min_amount',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MinValueValidator(0)], verbose_name='حداقل مبلغ سفارش'),
        ),
        migrations.AlterField(
            model_name='discountreport',
            name='total_discount_amount',
            field=models.IntegerField(default=0, verbose_name='مبلغ کل تخفیف'),
        ),
        migrations.AlterField(
            model_name='discountreport',
            name='total_revenue_impact',
            field=models.IntegerField(default=0, verbose_name='تأثیر بر درآمد'),
        ),
        migrations.AlterField(
            model_name='discountusage',
            name='discount_amount',
            field=models.IntegerField(verbose_name='مبلغ تخفیف'),
        ),
        migrations.AlterField(
            model_name='discountusage',
            name='final_amount',
            field=models.IntegerField(verbose_name='مبلغ نهایی'),
        ),
        migrations.AlterField(
            model_name='discountusage',
            name='original_amount',
            field=models.IntegerField(verbose_name='مبلغ اصلی'),
        ),
    ]
