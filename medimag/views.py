from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView

from .forms import CommentForm
from .models import MagArticle, Category , Comment
# from product.models import Product
import time
from django.db.models import Q
class MagView(ListView):
    model = MagArticle
    paginate_by = 3

    def get_queryset(self):
        queryset = MagArticle.objects.filter(published=True)

        # جستجو
        search_query = self.request.GET.get('query', '')
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )

        # فیلتر بر اساس نام دسته‌بندی
        category_name = self.request.GET.get('category', None)
        if category_name:
            queryset = queryset.filter(category__name=category_name)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = Category.objects.all()
        context['articles_last'] = MagArticle.objects.filter(published=True).order_by("-date")[:3]
        context['search_query'] = self.request.GET.get('query', '')
        context['selected_category'] = self.request.GET.get('category', '')
        return context

def article(request, slug):
    object = get_object_or_404(MagArticle, slug=slug)
    comments = Comment.objects.filter(article=object, status='confirmed')

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.article = object  # ارتباط کامنت با مقاله
            comment.status = 'checking'  # وضعیت پیش‌فرض کامنت
            comment.user = request.user if request.user.is_authenticated else None
            comment.save()
            messages.success(request,
                             'نظر شما با موفقیت ثبت شد و پس از تایید نمایش داده خواهد شد!')
            return redirect(object.get_absolute_url())  # بازگشت به صفحه مقاله
    else:
        form = CommentForm()

    context = {
        "object": object,
        "comments": comments,
        "form": form,  # نمایش فرم در قالب
        'articles_last': MagArticle.objects.filter(published=True).order_by("-date")[:3],
        'category': Category.objects.all(),
    }

    return render(request, "medimag/article_detail.html", context)





# @login_required()
# def comments_delete(request,id):
#     try:
#         comment = get_object_or_404(Comment,id=id)
#         comment.delete()
#         time.sleep(2)
#         return redirect('account:comment_list')
#     except:
#         return redirect('account:comment_list')