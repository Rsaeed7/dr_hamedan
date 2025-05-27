from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from doctors.models import Doctor
from .models import Post, Comment, MedicalLens, PostLike
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
import json


def doctor_page(request, doctor_id):
    """Display a doctor's public page with their posts"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Filter by medical lenses if specified
    lens_filter = request.GET.get('lens')
    posts_list = Post.objects.filter(doctor=doctor, status='published')
    
    if lens_filter:
        try:
            lens = MedicalLens.objects.get(id=lens_filter)
            posts_list = posts_list.filter(medical_lenses=lens)
        except MedicalLens.DoesNotExist:
            pass
    
    # Search functionality
    search_query = request.GET.get('search', '').strip()
    if search_query:
        posts_list = posts_list.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(medical_lenses__name__icontains=search_query)
        ).distinct()
    
    paginator = Paginator(posts_list, 10)  # Show 10 posts per page
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    # Get all medical lenses for filter
    medical_lenses = MedicalLens.objects.all()
    
    context = {
        'doctor': doctor,
        'posts': posts,
        'medical_lenses': medical_lenses,
        'selected_lens': lens_filter,
        'search_query': search_query,
    }
    
    return render(request, 'docpages/doctor_page.html', context)

def post_detail(request, post_id):
    """Display a single post with comments"""
    post = get_object_or_404(Post, id=post_id)
    
    # If post is a draft and user is not the doctor, return 404
    if post.status == 'draft' and (not request.user.is_authenticated or not hasattr(request.user, 'doctor') or request.user.doctor != post.doctor):
        return HttpResponse("Post not found", status=404)
        
    comments = post.comments.filter(approved=True)
    
    # Check if current user liked this post
    user_liked = post.is_liked_by_user(request.user) if request.user.is_authenticated else False
    
    if request.method == 'POST':
        # Handle comment submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        body = request.POST.get('body')
        
        if name and email and body:
            Comment.objects.create(
                post=post,
                name=name,
                email=email,
                body=body,
                user=request.user if request.user.is_authenticated else None,
                approved=False  # Needs approval first
            )
            messages.success(request, 'نظر شما ثبت شد و پس از تایید نمایش داده خواهد شد.')
            return redirect('docpages:post_detail', post_id=post.id)
    
    context = {
        'post': post,
        'comments': comments,
        'user_liked': user_liked,
        'like_count': post.get_like_count(),
        'is_preview': False
    }
    
    return render(request, 'docpages/post_detail.html', context)

@login_required
def doctor_posts(request):
    """Display a doctor's posts dashboard"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')
    
    posts = Post.objects.filter(doctor=doctor)
    
    context = {
        'doctor': doctor,
        'posts': posts,
    }
    
    return render(request, 'docpages/doctor_posts.html', context)

@login_required
def create_post(request):
    """Create a new post"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        messages.error(request, 'فقط پزشکان می‌توانند پست ایجاد کنند.')
        return redirect('doctors:doctor_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        action = request.POST.get('action', 'publish')
        medical_lenses_ids = request.POST.getlist('medical_lenses')
        
        if title and content:
            # Create post with appropriate status
            status = 'draft' if action == 'save_draft' else 'published'
            post = Post(
                doctor=doctor,
                title=title,
                content=content,
                status=status
            )
            
            # Handle media upload (only one type allowed)
            if 'image' in request.FILES and 'video' in request.FILES:
                messages.error(request, 'فقط می‌توانید یک نوع رسانه (تصویر یا ویدیو) آپلود کنید.')
                return render(request, 'docpages/create_post.html', {
                    'doctor': doctor,
                    'form_data': request.POST,
                    'medical_lenses': MedicalLens.objects.all()
                })
            
            if 'image' in request.FILES:
                post.image = request.FILES['image']
            elif 'video' in request.FILES:
                post.video = request.FILES['video']
            
            try:
                post.save()
                
                # Add medical lenses
                if medical_lenses_ids:
                    post.medical_lenses.set(medical_lenses_ids)
                
                success_message = 'پیش‌نویس ذخیره شد.' if action == 'save_draft' else 'پست شما منتشر شد.'
                messages.success(request, success_message)
                return redirect('docpages:doctor_posts')
                
            except Exception as e:
                messages.error(request, f'خطا در ذخیره پست: {str(e)}')
        else:
            messages.error(request, 'عنوان و محتوا الزامی هستند.')
    
    context = {
        'doctor': doctor,
        'medical_lenses': MedicalLens.objects.all(),
    }
    
    return render(request, 'docpages/create_post.html', context)

@login_required
def edit_post(request, post_id):
    """Edit an existing post"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')
    
    post = get_object_or_404(Post, id=post_id, doctor=doctor)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        action = request.POST.get('action', 'publish')
        medical_lenses_ids = request.POST.getlist('medical_lenses')
        
        if title and content:
            # Update post
            post.title = title
            post.content = content
            
            # Update status if requested
            if action == 'save_draft':
                post.status = 'draft'
            elif action == 'publish':
                post.status = 'published'
            
            # Handle media update
            clear_image = request.POST.get('clear_image')
            clear_video = request.POST.get('clear_video')
            
            if clear_image:
                post.image = None
            if clear_video:
                post.video = None
            
            # Check for new media upload (only one type allowed)
            new_media_count = sum([
                bool(request.FILES.get('image')),
                bool(request.FILES.get('video'))
            ])
            
            if new_media_count > 1:
                messages.error(request, 'فقط می‌توانید یک نوع رسانه (تصویر یا ویدیو) آپلود کنید.')
                context = {
                    'doctor': doctor,
                    'post': post,
                    'medical_lenses': MedicalLens.objects.all(),
                    'form_data': request.POST
                }
                return render(request, 'docpages/edit_post.html', context)
            
            if 'image' in request.FILES:
                post.video = None  # Clear video if uploading image
                post.image = request.FILES['image']
            elif 'video' in request.FILES:
                post.image = None  # Clear image if uploading video
                post.video = request.FILES['video']
            
            try:
                post.save()
                
                # Update medical lenses
                post.medical_lenses.set(medical_lenses_ids)
                
                success_message = 'پیش‌نویس ذخیره شد.' if action == 'save_draft' else 'پست بروزرسانی شد.'
                messages.success(request, success_message)
                return redirect('docpages:doctor_posts')
                
            except Exception as e:
                messages.error(request, f'خطا در بروزرسانی پست: {str(e)}')
        else:
            messages.error(request, 'عنوان و محتوا الزامی هستند.')
    
    context = {
        'doctor': doctor,
        'post': post,
        'medical_lenses': MedicalLens.objects.all(),
    }
    
    return render(request, 'docpages/edit_post.html', context)

@login_required
def delete_post(request, post_id):
    """Delete a post"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')
    
    post = get_object_or_404(Post, id=post_id, doctor=doctor)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Your post has been deleted.')
        return redirect('docpages:doctor_posts')
    
    context = {
        'doctor': doctor,
        'post': post,
    }
    
    return render(request, 'docpages/delete_post.html', context)

@login_required
def manage_comments(request):
    """Manage comments on doctor's posts"""
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return redirect('doctors:doctor_list')
    
    # Get all comments for the doctor's posts
    comments = Comment.objects.filter(post__doctor=doctor)
    
    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        action = request.POST.get('action')
        
        if comment_id and action:
            comment = get_object_or_404(Comment, id=comment_id, post__doctor=doctor)
            
            if action == 'approve':
                comment.approved = True
                comment.save()
                messages.success(request, 'Comment approved.')
            elif action == 'delete':
                comment.delete()
                messages.success(request, 'Comment deleted.')
    
    context = {
        'doctor': doctor,
        'comments': comments,
    }
    
    return render(request, 'docpages/manage_comments.html', context)

@login_required
def toggle_like(request, post_id):
    """Toggle like status for a post"""
    if request.method != 'POST':
        return JsonResponse({'error': 'فقط درخواست POST مجاز است'}, status=405)
    
    post = get_object_or_404(Post, id=post_id)
    
    try:
        # Check if user already liked this post
        post_like = PostLike.objects.get(post=post, user=request.user)
        # User already liked, so unlike
        post_like.delete()
        liked = False
        message = 'لایک برداشته شد'
    except PostLike.DoesNotExist:
        # User hasn't liked, so like it
        PostLike.objects.create(post=post, user=request.user)
        liked = True
        message = 'لایک شد'
    
    # Update the cached like count
    post.likes_count = post.get_like_count()
    post.save(update_fields=['likes_count'])
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': post.likes_count,
        'message': message
    })

def search_medical_lenses(request):
    """AJAX endpoint for searching medical lenses"""
    if request.method != 'GET':
        return JsonResponse({'error': 'فقط درخواست GET مجاز است'}, status=405)
    
    query = request.GET.get('q', '').strip()
    
    if len(query) < 2:
        return JsonResponse({'results': []})
    
    # Search in medical lenses
    lenses = MedicalLens.objects.filter(
        Q(name__icontains=query) | Q(description__icontains=query)
    )[:10]  # Limit to 10 results
    
    results = []
    for lens in lenses:
        results.append({
            'id': lens.id,
            'name': lens.name,
            'description': lens.description,
            'color': lens.color
        })
    
    return JsonResponse({'results': results})
