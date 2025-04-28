from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from doctors.models import Doctor
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse





def doctor_page(request, doctor_id):
    """Display a doctor's public page with their posts"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    posts_list = Post.objects.filter(doctor=doctor, status='published')
    
    paginator = Paginator(posts_list, 10)  # Show 10 posts per page
    page = request.GET.get('page', 1)
    
    try:
        posts = paginator.page(page)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)
    
    context = {
        'doctor': doctor,
        'posts': posts,
    }
    
    return render(request, 'docpages/doctor_page.html', context)

def post_detail(request, post_id):
    """Display a single post with comments"""
    post = get_object_or_404(Post, id=post_id)
    
    # If post is a draft and user is not the doctor, return 404
    if post.status == 'draft' and (not request.user.is_authenticated or not hasattr(request.user, 'doctor') or request.user.doctor != post.doctor):
        return HttpResponse("Post not found", status=404)
        
    comments = post.comments.filter(approved=True)
    
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
                approved=False  # Needs approval first
            )
            messages.success(request, 'Your comment has been submitted and is awaiting approval.')
            return redirect('docpages:post_detail', post_id=post.id)
    
    context = {
        'post': post,
        'comments': comments,
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
        return redirect('doctors:doctor_list')
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        action = request.POST.get('action', 'publish')
        
        if title and content:
            # If preview action, don't save but show preview
            if action == 'preview':
                temp_post = Post(
                    doctor=doctor,
                    title=title,
                    content=content,
                    status='draft'
                )
                
                context = {
                    'doctor': doctor,
                    'post': temp_post,
                    'comments': [],
                    'is_preview': True,
                    'form_data': {
                        'title': title,
                        'content': content
                    }
                }
                
                return render(request, 'docpages/post_preview.html', context)
            
            # Create post with appropriate status
            status = 'draft' if action == 'save_draft' else 'published'
            post = Post(
                doctor=doctor,
                title=title,
                content=content,
                status=status
            )
            
            if 'image' in request.FILES:
                post.image = request.FILES['image']
                
            post.save()
            
            success_message = 'Your draft has been saved.' if action == 'save_draft' else 'Your post has been published.'
            messages.success(request, success_message)
            return redirect('docpages:doctor_posts')
        else:
            messages.error(request, 'Title and content are required.')
    
    context = {
        'doctor': doctor,
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
        
        if title and content:
            # If preview action, don't save but show preview
            if action == 'preview':
                temp_post = Post(
                    id=post.id,
                    doctor=doctor,
                    title=title,
                    content=content,
                    image=post.image,
                    created_at=post.created_at,
                    status=post.status
                )
                
                context = {
                    'doctor': doctor,
                    'post': temp_post,
                    'comments': [],
                    'is_preview': True,
                    'is_edit': True,
                    'form_data': {
                        'title': title,
                        'content': content
                    }
                }
                
                return render(request, 'docpages/post_preview.html', context)
                
            # Update post
            post.title = title
            post.content = content
            
            # Update status if requested
            if action == 'save_draft':
                post.status = 'draft'
            elif action == 'publish':
                post.status = 'published'
            
            if 'image' in request.FILES:
                post.image = request.FILES['image']
                
            post.save()
            
            success_message = 'Your draft has been saved.' if action == 'save_draft' else 'Your post has been updated.'
            messages.success(request, success_message)
            return redirect('docpages:doctor_posts')
        else:
            messages.error(request, 'Title and content are required.')
    
    context = {
        'doctor': doctor,
        'post': post,
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
