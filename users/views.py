from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from blog.models import Post
from blog.views import (
    annotate_comment_count,
    filter_published_posts,
    get_paginator,
)
from .forms import RegistrationForm, ProfileEditForm


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'registration/registration_form.html',
                  {'form': form})


@login_required
def profile_edit(request):
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('users:profile',
                            username=request.user.username)
    else:
        form = ProfileEditForm(instance=request.user)
    return render(request, 'users/profile_edit.html', {'form': form})


def profile_view(request, username):
    user = get_object_or_404(User, username=username)

    if request.user == user:
        posts = Post.objects.filter(author=user)
    else:
        posts = Post.objects.filter(author=user)
        posts = filter_published_posts(posts)

    posts = annotate_comment_count(
        posts.select_related('category', 'location', 'author')
    )

    page_obj = get_paginator(request, posts, 10)

    return render(request, 'users/profile.html', {
        'profile_user': user,
        'page_obj': page_obj,
    })
