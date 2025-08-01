# Generated by Django 5.2 on 2025-07-16 04:42

import django.core.validators
import django_jalali.db.models
import docpages.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='نام')),
                ('body', models.TextField(verbose_name='متن')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('approved', models.BooleanField(default=False, verbose_name='تایید شده')),
            ],
            options={
                'verbose_name': 'نظر',
                'verbose_name_plural': 'نظرات',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='MedicalLens',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='نام')),
                ('description', models.TextField(blank=True, verbose_name='توضیحات')),
                ('color', models.CharField(default='#3b82f6', max_length=7, verbose_name='رنگ تگ')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
            ],
            options={
                'verbose_name': 'لنز پزشکی',
                'verbose_name_plural': 'لنزهای پزشکی',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='عنوان')),
                ('content', models.TextField(verbose_name='محتوا')),
                ('media_type', models.CharField(choices=[('none', 'بدون رسانه'), ('image', 'تصویر'), ('video', 'ویدیو')], default='none', max_length=10, verbose_name='نوع رسانه')),
                ('image', models.ImageField(blank=True, null=True, upload_to='post_images/', validators=[docpages.models.validate_file_size, django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])], verbose_name='تصویر')),
                ('video', models.FileField(blank=True, null=True, upload_to='post_videos/', validators=[docpages.models.validate_file_size, django.core.validators.FileExtensionValidator(allowed_extensions=['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])], verbose_name='ویدیو')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', django_jalali.db.models.jDateTimeField(auto_now=True, verbose_name='تاریخ بروزرسانی')),
                ('likes_count', models.PositiveIntegerField(default=0, verbose_name='تعداد لایک\u200cها')),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('published', 'Published')], default='published', max_length=10, verbose_name='وضعیت')),
            ],
            options={
                'verbose_name': 'پست',
                'verbose_name_plural': 'پست\u200cها',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PostLike',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', django_jalali.db.models.jDateTimeField(auto_now_add=True, verbose_name='تاریخ لایک')),
            ],
            options={
                'verbose_name': 'لایک پست',
                'verbose_name_plural': 'لایک\u200cهای پست',
            },
        ),
    ]
