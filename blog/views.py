from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404
from blog.models import Post, Category, Comment
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from .forms import PostsForm, CommentsForm, ProfileForm

User = get_user_model()


def get_posts(post_objects):
    return post_objects.filter(
        pub_date__lte=timezone.now(),
        is_published=True,
        category__is_published=True
    ).annotate(comment_count=Count('comments'))

NUMBER_OF_PAGINATION_PAGES = 10

def get_paginator(request, query_set):
    paginator = Paginator(query_set, NUMBER_OF_PAGINATION_PAGES)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    template = 'blog/index.html'
    post_list = get_posts(Post.objects).order_by('-pub_date')
    page_obj = get_paginator(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def category_posts(request, category_slug):
    template = 'blog/category.html'
    category = get_object_or_404(
        Category,
        slug__exact=category_slug
    )
    if not category.is_published:
        raise Http404()
    post_list = get_posts(category.posts).order_by('-pub_date')
    page_obj = get_paginator(request, post_list)
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
    can_view = False
    if request.user == post.author:
        can_view = True
    elif (
        post.is_published
        and post.category.is_published
        and post.pub_date <= timezone.now()
    ):
        can_view = True
    if not can_view:
        raise Http404()
    comments = post.comments.select_related('author').all()
    context = {
        'post': post,
        'comments': comments,
        'form': CommentsForm(),
    }
    return render(request, template, context)


def profile(request, username):
    template = 'blog/profile.html'
    user = get_object_or_404(User, username=username)
    posts_list = (
        user.posts
        .annotate(comment_count=Count('comments'))
        .order_by('-pub_date')
    )
    page_obj = get_paginator(request, posts_list)
    context = {'profile': user, 'page_obj': page_obj}
    return render(request, template, context)


@login_required
def edit_profile(request):
    template = 'blog/user.html'
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', request.user)
    else:
        form = ProfileForm(instance=request.user)
    context = {'form': form}
    return render(request, template, context)


@login_required
def create_post(request):
    template = 'blog/create.html'
    form = PostsForm(
        request.POST or None,
        files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', request.user.username)
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def edit_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostsForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id)
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def delete_post(request, post_id):
    template = 'blog/create.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('blog:post_detail', post_id)
    form = PostsForm(request.POST or None, instance=post)
    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')
    context = {
        'form': form
    }
    return render(request, template, context)


@login_required
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentsForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', post_id)


@login_required
def edit_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id)

    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        form = CommentsForm(request.POST or None, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id)
    else:
        form = CommentsForm(instance=comment)
    context = {
        'form': form,
        'comment': comment
    }
    return render(request, template, context)


@login_required
def delete_comment(request, post_id, comment_id):
    template = 'blog/comment.html'
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user != comment.author:
        return redirect('blog:post_detail', post_id)
    if request.method == "POST":
        comment.delete()
        return redirect('blog:post_detail', post_id)
    context = {
        'comment': comment
    }
    return render(request, template, context)
