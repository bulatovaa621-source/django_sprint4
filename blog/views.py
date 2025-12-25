from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from blog.models import Post, Category, Comment
from django.utils import timezone 
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from .forms import CommentsForm, PostsForm, CommentEditForm


def get_paginator(request, query_set, per_page=10):
    paginator = Paginator(query_set, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'blog/index.html'
    post_list = filter_published_posts(Post.objects.all())
    
    print(f"Всего постов до фильтрации: {Post.objects.count()}")
    print(f"Постов после фильтрации: {post_list.count()}")
    
    for post in post_list:
        print(f"  - {post.title}: published={post.is_published}, "
              f"category_published={post.category.is_published}, "
              f"date={post.pub_date}")
    post_list = annotate_comment_count(post_list)
    page_obj = get_paginator(request, post_list, 10)

    context = {'page_obj': page_obj}
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    post_list = Post.objects.filter(category=category)
    post_list = filter_published_posts(post_list)

    post_list = annotate_comment_count(
        post_list.select_related('category', 'location', 'author')
    )
    page_obj = get_paginator(request, post_list, 10)
    context = {
        'page_obj': page_obj,
        'category': category,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'blog/detail.html'
    post = get_object_or_404(
        Post.objects.select_related('author', 'category', 'location'),
        pk=post_id
    )
    if request.user != post.author:
        if (not post.is_published or not post.category.is_published
                or post.pub_date > timezone.now()):
            raise Http404("Пост не найден")

    comments = post.comments.filter(is_published=True)

    form = None
    if request.user.is_authenticated:
        if request.method == 'POST':
            form = CommentsForm(request.POST)
            if form.is_valid():
                comment = form.save(commit=False)
                comment.post = post
                comment.author = request.user
                comment.save()
                return redirect('blog:post_detail', post_id=post.id)
        else:
            form = CommentsForm()
    context = {
        'post': post,
        'comments': comments,
        'form': form,
    }
    return render(request, template, context)


def annotate_comment_count(query_set):
    return query_set.annotate(
        comment_count=Count('comments', filter=Q(comments__is_published=True))
    ).order_by('-pub_date')


def filter_published_posts(query_set):
    return query_set.filter(
        is_published=True,
        category__is_published=True,
        pub_date__lte=timezone.now()
    )


@login_required
def create_post(request):
    template = 'blog/create.html'
    if request.method == 'POST':
        form = PostsForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('users:profile', username=request.user.username)
    else:
        form = PostsForm()
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def edit_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        form = PostsForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostsForm(instance=post)
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def delete_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == 'POST':
        post.delete()
        return redirect('users:profile', username=request.user.username)
    form = PostsForm(instance=post)
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == 'POST':
        form = CommentsForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect('blog:post_detail', post_id=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == "POST":
        form = CommentEditForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentEditForm(instance=comment)
    context = {
        'form': form,
        'post': post,
        'comment': comment
        
    }
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    post = get_object_or_404(Post, id=post_id)
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id=post.id)
    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id=post.id)
    context = {
        'post': post,
        'comment': comment
    }
    return render(request, template, context)
