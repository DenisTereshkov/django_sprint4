from django.http import Http404
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.shortcuts import get_object_or_404, render, redirect
from django.db.models import Count
from django.db.models.functions import Now
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.views.generic import ListView, DetailView, UpdateView, DeleteView

from . forms import CreatePostForm, CommentForm
from blog.models import Post, Category, User, Comment


POSTS_ON_PAGE: int = 10

QUERY_SET_TEMPLATE = Post.objects.all(
).filter(
    is_published=True,
    category__is_published=True,
    pub_date__date__lt=Now()
).annotate(
    comment_count=Count('comments')
).order_by('-pub_date')


def paginator(request, posts):
    """Постраничный вывод"""
    paginator = Paginator(posts, POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


class OnlyAuthorMixin(UserPassesTestMixin):
    """Использование миксина дает доступ только для автора"""

    def test_func(self):
        object = self.get_object()
        return object.author == self.request.user

    def handle_no_permission(self):
        return redirect('blog:post_detail', self.kwargs['post_id'])


class PostUpdateView(OnlyAuthorMixin, UpdateView):
    """Изменение поста пользователя"""

    model = Post
    pk_url_kwarg = 'post_id'
    form_class = CreatePostForm
    template_name = 'blog/create.html'

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.id])


class PostDeleteView(OnlyAuthorMixin, DeleteView):
    """Удаление поста пользователя"""

    model = Post
    pk_url_kwarg = 'post_id'
    template_name = 'blog/create.html'
    success_url = reverse_lazy('blog:index')


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Изменение данных профиля пользователя"""

    template_name = 'blog/user.html'
    model = User
    fields = ('username', 'first_name', 'last_name', 'email')

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return reverse('blog:profile', args=[self.object.username])


def profile(request, username):
    """Функция описывающая профиль пользователя"""
    template_name = 'blog/profile.html'
    user = get_object_or_404(User, username=username)
    if request.user.username == username:
        posts = Post.objects.filter(
            author=user
        ).order_by('-pub_date').annotate(comment_count=Count('comments'))
    else:
        posts = QUERY_SET_TEMPLATE.filter(author=user)
    page_obj = paginator(request, posts)
    context = {
        'username': username,
        'profile': user,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


class IndexListView(ListView):
    """Отвечает за посты на главной странице"""

    template_name = 'blog/index.html'
    model = Post
    ordering = 'pub_date'
    paginate_by = POSTS_ON_PAGE

    def get_queryset(self):
        return QUERY_SET_TEMPLATE


class PostDetailView(DetailView):
    """Просмотр деталей поста"""

    model = Post
    template_name = 'blog/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object
        if post.author != self.request.user and (
            post.is_published is False
            or post.category.is_published is False
            or post.pub_date > timezone.now()
        ):
            raise Http404('Публикации не существует')
        context['form'] = CommentForm()
        context['comments'] = (
            self.object.comments.select_related('author')
        )
        return context


def category_posts(request, category_slug):
    """Функция категорий постов"""
    template_name = 'blog/category.html'
    category = get_object_or_404(
        Category.objects.all().filter(
            is_published=True,
        ),
        slug=category_slug
    )
    post_list = QUERY_SET_TEMPLATE.filter(
        category__slug=category_slug,
    )
    page_obj = paginator(request, post_list)
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


@login_required
def post_create(request):
    """Создание постов"""
    template_name = 'blog/create.html'
    form = CreatePostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('blog:profile', username=request.user)
    return render(request, template_name, {'form': form})


@login_required
def add_comment(request, post_id):
    """Добавление комментариев к посту"""
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = get_object_or_404(Post.objects, id=post_id)
        comment.author = request.user
        comment.save()
    return redirect('blog:post_detail', pk=post_id)


class CommentEditView(OnlyAuthorMixin, UpdateView):
    """Редактирование комментрия"""

    model = Comment
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm
    template_name = 'blog/comment.html'

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.id])


class CommentDeleteView(OnlyAuthorMixin, DeleteView):
    """Удаление комментария"""

    model = Comment
    pk_url_kwarg = 'comment_id'
    form_class = CommentForm
    template_name = 'blog/comment.html'
    success_url = reverse_lazy('blog:index')

    def get_success_url(self):
        return reverse('blog:post_detail', args=[self.object.id])
