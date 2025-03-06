from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from .models import MagArticle, Category
# from product.models import Product
import time

class MagView(ListView):
    model = MagArticle
    paginate_by = 3
    queryset = MagArticle.objects.filter(published=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = Category.objects.all()
        context['articles_last'] = MagArticle.objects.filter(published=True).order_by("-date")[:3]
        return context



def article(request,slug):
    object = get_object_or_404(MagArticle, slug=slug)
    # if request.method == "POST":
    #     parent_id = request.POST.get('parent_id')
    #     name = request.POST.get('name')
    #     text = request.POST.get('text')
    #     if not name or text:
    #         messages.error(request,'لطفا نام و متن کامنت را به درستی وارد کنید')
    #     if parent_id:
    #         is_reply = True
    #         messages.success(request, "پاسخ شما با موفقیت ثبت شد و پس از تایید نمایش داده میشود...")
    #     else:
    #         is_reply = False
    #         messages.success(request, "پیام شما با موفقیت ثبت شد و پس از تایید نمایش داده میشود...")
    #     Comment.objects.create(article=object, text=text , parent_id=parent_id , name=name , is_reply=is_reply , user=request.user)
    #     return redirect(get_object_or_404(MagArticle, slug=slug))
    #
    # comments = Comment.objects.filter(article=object, status='confirmed')
    context = {
        "object": object,
        # "comments": comments,
        'articles_last': MagArticle.objects.filter(published=True).order_by("-date")[:3],
        'category':Category.objects.all()
    }

    return render(request, "mag/article_detail.html", context)

# @login_required()
# def comments_delete(request,id):
#     try:
#         comment = get_object_or_404(Comment,id=id)
#         comment.delete()
#         time.sleep(2)
#         return redirect('account:comment_list')
#     except:
#         return redirect('account:comment_list')