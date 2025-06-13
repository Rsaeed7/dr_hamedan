# from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.db import models
from user.models import User
from django.urls.base import reverse
import jdatetime
from django_jalali.db import models as jmodels
from ckeditor.fields import RichTextField


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True , verbose_name="نام دسته بندی")
    slug = models.SlugField(unique=True , allow_unicode=True , verbose_name='اسلاگ')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'دسته بندی'
        verbose_name_plural = 'دسته بندی'

class MagArticle(models.Model):
    STATUS_CHOICES = (("False", "پیش نویس"), ("True", "انتشار"))
    title = models.CharField(max_length=100, verbose_name='عنوان')
    description = RichTextField(verbose_name='متن مقاله', blank=True)
    image = models.ImageField(upload_to='blog', verbose_name='تصویر')
    date = jmodels.jDateTimeField(verbose_name='زمان', auto_now_add=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,verbose_name='دسته بندی' ,related_name='category' , null=True , blank=True)
    writer = models.ForeignKey(User, on_delete=models.CASCADE , verbose_name='نویسنده')
    slug = models.SlugField(unique=True, allow_unicode=True , verbose_name='اسلاگ', blank=True)
    published = models.BooleanField(default=True, verbose_name='منتشر شود')

    def __str__(self):
        return self.title



    def get_absolute_url(self):
        return reverse('mag:article',kwargs={'slug': self.slug})

    # def get_comments(self):
    #     return Comment.objects.filter(content_type=ContentType.objects.get_for_model(self), object_id=self.id)

    class Meta:
        verbose_name = 'مقاله'
        verbose_name_plural = 'مقالات'

#
class Comment(models.Model):
    STATUS_CHOICES = (('checking','در حال بررسی'),('confirmed','تایید شده'))
    GENDER_CHOICES = [
        ('M', 'آقا'),
        ('F', 'خانم'),
    ]
    article = models.ForeignKey(MagArticle , on_delete=models.CASCADE , verbose_name='مقاله', related_name='comments')
    name = models.CharField(max_length=100, verbose_name='نام کاربر')
    text = models.TextField(verbose_name='متن کامنت')
    parent = models.ForeignKey("self", on_delete=models.CASCADE , verbose_name='کامنت والد', related_name='related_comments', null=True, blank=True)
    date = jmodels.jDateTimeField(verbose_name='تاریخ ثبت', auto_now_add=True)
    is_reply = models.BooleanField(default=False, verbose_name="آیا این یک پاسخ است؟")
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="checking", verbose_name="وضعیت"
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, default="M", verbose_name="جنسیت",blank=True,null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='کاربر', related_name='blog_comments', null=True, blank=True)
    def status_display(self):
        if self.status == 'checking':
            return 'در حال بررسی'
        else:
            return 'تایید شده'

    class Meta:
        ordering = ("date",)
        verbose_name = "کامنت"
        verbose_name_plural = "کامنت ها"

    # def JaliliDatepublished(self):
    #     return jdatetime.date.fromgregorian(
    #         day=self.date.day,
    #         month=self.date.month,
    #         year=self.date.year,
    #     )

    def __str__(self):
        repl = "reply" if self.is_reply else "comment"
        return f'{repl} from "{self.name}" to "{self.article}"'

