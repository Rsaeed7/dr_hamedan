from django.db import models


class Contact(models.Model):
    phone_number = models.CharField(max_length=11,verbose_name='شماره تلفن')
    email = models.EmailField(verbose_name='ایمیل')
    address = models.TextField(verbose_name='آدرس')
    whatsapp = models.CharField(max_length=100,verbose_name='واتساپ')
    telegram = models.CharField(max_length=100,verbose_name='تلگرام')
    instagram = models.CharField(max_length=100,verbose_name='اینستاگرام')
    eitaa = models.CharField(max_length=100,verbose_name='ایتا')

    def __str__(self):
        return self.email
    class Meta:
        verbose_name='اطلاعات تماس'
        verbose_name_plural='اطلاعات تماس'


class ContactUs(models.Model):
    name = models.CharField(max_length=50,verbose_name='نام')
    email = models.EmailField(verbose_name='ایمیل')
    subject = models.CharField(max_length=100,verbose_name='موضوع')
    message = models.TextField(verbose_name='پیام')

    def __str__(self):
        return f'{self.name} - {self.subject}'

    class Meta:
        verbose_name='پیام کاربر'
        verbose_name_plural='پیام کاربران'

class Message(models.Model):
    message = models.CharField(max_length=65,verbose_name='اعلامیه')
    published = models.BooleanField(default=False,verbose_name='نمایش داده شود')

    def __str__(self):
        return f'{self.message}'
    class Meta:
        verbose_name='اعلامیه'
        verbose_name_plural='اعلامیه ها'
# Create your models here.
