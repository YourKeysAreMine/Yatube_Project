from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group


User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostURLTests.user}/': 'posts/profile.html',
            f'/posts/{PostURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.templates = (
            '/',
            f'/group/{PostURLTests.group.slug}/',
            f'/posts/{PostURLTests.post.id}/',
            f'/profile/{PostURLTests.user}/',
        )

    def setUp(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(PostURLTests.user)

    def test_home_page_exists_at_desired_location(self):
        """Общедоступные страницы доступны любому пользователю."""
        for address in self.templates:
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_page_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def tets_page_not_exists(self):
        """Страница /unexisting_page/ не существует"""
        response = self.client.get('/unexisting-page/')
        self.assertNotEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_create_post_page_exists_at_desired_location(self):
        """Страница /edit/ доступна автору поста."""
        self.guest_client = Client()
        author = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(author)
        response = self.authorized_client.get(f'/posts/'
                                              f'{PostURLTests.post.id}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_uses_correct_template(self):
        """Проверка, что URL адрес использует правильный шаблон"""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
