from itertools import chain

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm

NUMBER_OF_POSTS: int = 10


def get_pagination(request, quaryset):
    paginator = Paginator(quaryset, NUMBER_OF_POSTS)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    page_obj = get_pagination(request, Post.objects.all())
    return render(request, 'posts/index.html', {'page_obj': page_obj})


def group_posts(request, slug):
    some_group = get_object_or_404(Group, slug=slug)
    posts = some_group.posts.all()
    page_obj = get_pagination(request, posts)
    context = {
        'page_obj': page_obj,
        'group': some_group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    requested_author = get_object_or_404(User, username=username)
    posts = requested_author.posts.all()
    page_obj = get_pagination(request, posts)
    quaryset = Follow.objects.filter(author=requested_author)
    if quaryset.exists and len(quaryset) > 0:
        following = True
    else:
        following = False
    context = {
        'page_obj': page_obj,
        'author': requested_author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:post_detail', post.id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    subscriptions = Follow.objects.filter(
        user=request.user).values_list('author_id', flat=True)
    result_quary = []
    for subscription in subscriptions:
        quaryset = Post.objects.filter(author_id=subscription)
        result_quary = list(chain(result_quary, quaryset))
    page_obj = get_pagination(request, result_quary)
    return render(request, 'posts/follow.html', {'page_obj': page_obj})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get(user=request.user, author=author).delete()
    return redirect('posts:follow_index')
