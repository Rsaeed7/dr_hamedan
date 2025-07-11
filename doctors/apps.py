from django.apps import AppConfig


class DoctorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doctors'
    
    def ready(self):
        import doctors.signals
    verbose_name = 'پزشکان'

    def ready(self):
        """بارگذاری سیگنال‌ها هنگام آماده شدن اپلیکیشن"""
        import doctors.signals
