from django import forms

from .models import Post, Comment


class CreatePostForm(forms.ModelForm):
    """Класс формы поста"""

    class Meta:
        model = Post
        exclude = ('author', 'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }


class CommentForm(forms.ModelForm):
    """Класс формы комментариев"""

    class Meta:
        model = Comment
        fields = ('text',)
