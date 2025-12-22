from django import forms
from .models import Comment, Post
from django.contrib.auth import get_user_model

User = get_user_model()


class PostsForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('title',
                  'text',
                  'pub_date',
                  'location',
                  'category',
                  'image',
                  'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class CommentsForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')
