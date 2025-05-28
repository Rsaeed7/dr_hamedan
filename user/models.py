from django.utils import timezone
from django.utils import timezone
from django.db import models
from django_jalali.db import models as jmodels
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,BaseUserManager

from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        """
        ایجاد کاربر عادی با شماره تلفن و پسورد
        """
        if not phone:
            raise ValueError("شماره تلفن باید وارد شود")

        user = self.model(
            phone=phone,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        """
        ایجاد سوپر کاربر با دسترسی ادمین
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('first_name', 'مدیر')
        extra_fields.setdefault('last_name', 'سیستم')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('سوپر کاربر باید is_staff=True باشد.')
        if extra_fields.get('is_admin') is not True:
            raise ValueError('سوپر کاربر باید is_admin=True باشد.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('سوپر کاربر باید is_superuser=True باشد.')

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^09\d{9}$',
        message="شماره تلفن باید با 09 شروع شود و 11 رقم باشد"
    )


    email = models.EmailField(
        verbose_name="آدرس ایمیل",
        max_length=255,
        blank=True,
        null=True,
        unique=True,
    )

    first_name = models.CharField(max_length=100, verbose_name="نام")
    last_name = models.CharField(max_length=100, verbose_name="نام خانوادگی")

    phone = models.CharField(
        max_length=11,
        verbose_name="شماره تلفن",
        unique=True,
        validators=[phone_regex]
    )

    is_active = models.BooleanField(default=True, verbose_name="کاربر فعال")
    is_admin = models.BooleanField(default=False, verbose_name="ادمین")
    is_staff = models.BooleanField(default=False, verbose_name="کارمند")
    is_admin_chat = models.BooleanField(default=False, verbose_name="اوپراتور پشتیبانی چت")

    date_joined = jmodels.jDateTimeField(auto_now_add=True, verbose_name="تاریخ عضویت")
    last_login = jmodels.jDateTimeField(auto_now=True, verbose_name="آخرین ورود")

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربرها"

    def __str__(self):
        return f"{self.phone} - {self.get_full_name()}"

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def name(self):
        return f"{self.phone} - {self.get_full_name()}"


class Otp(models.Model):
    token = models.CharField(max_length=100, null=True)
    phone = models.CharField(max_length=12)
    code = models.SmallIntegerField()
    expires = jmodels.jDateTimeField(auto_now_add=True)  # افزودن فیلد زمان ایجاد

    def is_expired(self):
        expiration_time = timezone.now() - timezone.timedelta(minutes=3)  # مدت زمان انقضا
        return self.expires < expiration_time

    def __str__(self):
        return self.phone

    class Meta:
        verbose_name = "رمز یک بار مصرف"
        verbose_name_plural = "رمز های یک بار مصرف"


