# Generated by Django 5.2 on 2025-07-16 04:42

import django.db.models.deletion
import django_jalali.db.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('phone_number', models.CharField(max_length=20, verbose_name='شماره تلفن')),
                ('message', models.TextField(verbose_name='متن پیام')),
                ('success', models.BooleanField(verbose_name='موفق')),
                ('response_data', models.JSONField(blank=True, null=True, verbose_name='داده\u200cهای پاسخ')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='پیام خطا')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='زمان ارسال')),
            ],
            options={
                'verbose_name': 'لاگ پیامک',
                'verbose_name_plural': 'لاگ\u200cهای پیامک',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='SMSReminderSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_24h_enabled', models.BooleanField(default=True, verbose_name='یادآوری ۲۴ ساعته فعال')),
                ('reminder_2h_enabled', models.BooleanField(default=True, verbose_name='یادآوری ۲ ساعته فعال')),
                ('confirmation_sms_enabled', models.BooleanField(default=True, verbose_name='پیامک تایید فعال')),
                ('cancellation_sms_enabled', models.BooleanField(default=True, verbose_name='پیامک لغو فعال')),
                ('working_hour_start', models.TimeField(default='08:00', verbose_name='شروع ساعات کاری')),
                ('working_hour_end', models.TimeField(default='20:00', verbose_name='پایان ساعات کاری')),
                ('max_retry_attempts', models.PositiveIntegerField(default=3, verbose_name='حداکثر تلاش مجدد')),
                ('retry_interval_minutes', models.PositiveIntegerField(default=30, verbose_name='فاصله تلاش مجدد (دقیقه)')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', django_jalali.db.models.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
            ],
            options={
                'verbose_name': 'تنظیمات یادآوری پیامکی',
                'verbose_name_plural': 'تنظیمات یادآوری پیامکی',
            },
        ),
        migrations.CreateModel(
            name='SMSReminderTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='نام قالب')),
                ('reminder_type', models.CharField(choices=[('confirmation', 'تایید نوبت'), ('reminder_24h', 'یادآوری ۲۴ ساعته'), ('reminder_2h', 'یادآوری ۲ ساعته'), ('cancellation', 'لغو نوبت'), ('custom', 'پیام سفارشی')], max_length=20, verbose_name='نوع یادآوری')),
                ('template', models.TextField(help_text='از متغیرهای زیر استفاده کنید: {patient_name}, {doctor_name}, {appointment_date}, {appointment_time}, {clinic_name}, {clinic_address}', verbose_name='قالب پیام')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', django_jalali.db.models.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
            ],
            options={
                'verbose_name': 'قالب یادآوری پیامکی',
                'verbose_name_plural': 'قالب\u200cهای یادآوری پیامکی',
            },
        ),
        migrations.CreateModel(
            name='SMSReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reminder_type', models.CharField(choices=[('confirmation', 'تایید نوبت'), ('reminder_24h', 'یادآوری ۲۴ ساعته'), ('reminder_2h', 'یادآوری ۲ ساعته'), ('cancellation', 'لغو نوبت'), ('custom', 'پیام سفارشی')], max_length=20, verbose_name='نوع یادآوری')),
                ('phone_number', models.CharField(max_length=20, verbose_name='شماره تلفن')),
                ('message', models.TextField(verbose_name='متن پیام')),
                ('scheduled_time', django_jalali.db.models.jDateTimeField(verbose_name='زمان برنامه\u200cریزی شده')),
                ('sent_time', django_jalali.db.models.jDateTimeField(blank=True, null=True, verbose_name='زمان ارسال')),
                ('status', models.CharField(choices=[('pending', 'در انتظار ارسال'), ('sent', 'ارسال شده'), ('failed', 'ناموفق'), ('cancelled', 'لغو شده')], default='pending', max_length=20, verbose_name='وضعیت')),
                ('attempts', models.PositiveIntegerField(default=0, verbose_name='تعداد تلاش')),
                ('max_attempts', models.PositiveIntegerField(default=3, verbose_name='حداکثر تلاش')),
                ('sms_response', models.JSONField(blank=True, null=True, verbose_name='پاسخ سرویس پیامک')),
                ('error_message', models.TextField(blank=True, null=True, verbose_name='پیام خطا')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', django_jalali.db.models.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('reservation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sms_reminders', to='reservations.reservation', verbose_name='رزرو')),
            ],
            options={
                'verbose_name': 'یادآوری پیامکی',
                'verbose_name_plural': 'یادآوری\u200cهای پیامکی',
                'ordering': ['-created_at'],
            },
        ),
    ]
