import shutil
import tempfile

from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Follow
from posts.views import NUMBER_OF_POSTS

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        for i in range(11):
            cls.post = Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
            )
        cls.post_without_group = Post.objects.create(
            author=cls.user,
            text='Тестовый пост без группы',
        )
        cls.templates_page_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': PostPagesTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': PostPagesTest.user}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': PostPagesTest.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': PostPagesTest.post.id}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(PostPagesTest.user)

    def test_pages_uses_correts_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for reverse_name, template in self.templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context_page_one(self):
        """Шаблон index сформирован с правильным контекстом, страница 1"""
        response = self.client.get(reverse("posts:index"))
        self.assertEqual(len(response.context["page_obj"]), NUMBER_OF_POSTS)

    def test_index_show_correct_context_page_two(self):
        """Шаблон index сформирован с правильным контекстом, страница 2"""
        response = self.client.get(reverse("posts:index") + '?page=2')
        self.assertEqual(len(response.context["page_obj"]),
                         Post.objects.count() - NUMBER_OF_POSTS)

    def test_group_list_show_correct_context_page_one(self):
        """Шаблон group_list сформирован с правильным контекстом, страница 1"""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': PostPagesTest.group.slug}))
        self.assertEqual(len(response.context["page_obj"]), NUMBER_OF_POSTS)

    def test_group_list_show_correct_context_page_two(self):
        """Шаблон group_list сформирован с правильным контекстом, страница 2"""
        response = self.client.get(reverse(
            'posts:group_list', kwargs={'slug': PostPagesTest.group.slug})
            + '?page=2')
        self.assertEqual(len(response.context["page_obj"]),
                         Post.objects.filter(group=PostPagesTest.group).count()
                         - NUMBER_OF_POSTS)

    def test_profile_show_correct_context_page_one(self):
        """Шаблон profile сформирован с правильным контекстом, страница 1"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': PostPagesTest.user}))
        self.assertEqual(len(response.context["page_obj"]), NUMBER_OF_POSTS)

    def test_profile_show_correct_context_page_two(self):
        """Шаблон group_list сформирован с правильным контекстом, страница 2"""
        response = self.client.get(reverse(
            'posts:profile', kwargs={'username': PostPagesTest.user})
            + '?page=2')
        self.assertEqual(len(response.context["page_obj"]),
                         Post.objects.count() - NUMBER_OF_POSTS)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом"""
        response = self.client.get(reverse(
            'posts:post_detail', kwargs={'post_id': PostPagesTest.post.id}))
        self.assertEqual(response.context['post'].author, PostPagesTest.user)
        self.assertEqual(
            response.context['post'].text, PostPagesTest.post.text)
        self.assertEqual(
            response.context['post'].group, PostPagesTest.post.group)
        self.assertEqual(
            response.context['post'].id, PostPagesTest.post.id)

    def test_create_post_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': PostPagesTest.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_check_created_post_exist_deisred_location(self):
        """Проверка размещения поста на страницах"""
        latest_post_with_group = Post.objects.filter(
            group=PostPagesTest.group).latest('id')
        form_fields = {
            reverse('posts:index'):
            latest_post_with_group,
            reverse(
                'posts:group_list', kwargs={'slug': PostPagesTest.group.slug}
            ): latest_post_with_group,
            reverse(
                'posts:profile', kwargs={'username': PostPagesTest.user}
            ): latest_post_with_group,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertIn(expected, form_field)

    def test_check_post_not_in_wrong_group_list(self):
        """Проверяем чтобы созданный Пост с группой не попал в чужую группу."""
        form_fields = {
            reverse(
                "posts:group_list", kwargs={"slug": self.group.slug}
            ): Post.objects.get(group=None),
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                response = self.authorized_client.get(value)
                form_field = response.context["page_obj"]
                self.assertNotIn(expected, form_field)

    def test_profile_follow(self):
        """Авторизованный пользователь может подписываться
        на других пользователей и удалять их из подписок"""
        response = self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostPagesTest.user})
        )
        self.assertRedirects(
            response, reverse('posts:follow_index')
        )
        self.assertTrue(Follow.objects.filter(
            author=PostPagesTest.user).exists())
        response = self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': PostPagesTest.user})
        )
        self.assertRedirects(
            response, reverse('posts:follow_index')
        )
        self.assertFalse(Follow.objects.filter(
            author=PostPagesTest.user).exists())


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super(PostImageTest, cls).setUpClass()
        cls.user = User.objects.create_user(username="auth")
        cls.group = Group.objects.create(
            title="Test group",
            slug="test_group_slug",
            description="Test group description",
        )
        cls.small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x02\x00"
            b"\x01\x00\x80\x00\x00\x00\x00\x00"
            b"\xFF\xFF\xFF\x21\xF9\x04\x00\x00"
            b"\x00\x00\x00\x2C\x00\x00\x00\x00"
            b"\x02\x00\x01\x00\x00\x02\x02\x0C"
            b"\x0A\x00\x3B"
        )
        cls.uploaded = SimpleUploadedFile(
            name="small.gif", content=cls.small_gif, content_type="image/gif"
        )
        cls.post = Post.objects.create(
            author=cls.user, text="Тестовый текст",
            group=cls.group,
            image=cls.uploaded
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = self.client
        self.authorized_client.force_login(PostImageTest.user)

    def test_check_image_in_context_index(self):
        """Проверяем, что картинка отображается на главной странице"""
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(
            response.context['page_obj'][0].image,
            PostImageTest.post.image
        )

    def test_check_image_in_context_post_detail(self):
        """Проверяем, что картинка отображается в деталях поста"""
        response = self.client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostImageTest.post.id}))
        self.assertEqual(response.context['post'].image,
                         PostImageTest.post.image)

    def test_check_image_in_context_group_list(self):
        """Проверяем, что картинка отображается в постах группы"""
        response = self.client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostImageTest.group.slug}))
        self.assertEqual(
            response.context['page_obj'][0].image,
            PostImageTest.post.image
        )

    def test_check_image_in_context_profile(self):
        """Проверяем, что картинка отображается в профайле"""
        response = self.client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostImageTest.post.author}))
        self.assertEqual(
            response.context['page_obj'][0].image,
            PostImageTest.post.image
        )

    def test_cache(self):
        """Проверяем, что кэш работает"""
        response_1 = self.client.get(reverse("posts:index")).content
        Post.objects.all().delete
        response_2 = self.client.get(reverse("posts:index")).content
        self.assertEqual(response_1, response_2)
        Post.objects.all().delete
        cache.clear()
        response_3 = self.client.get(reverse("posts:index")).content
        self.assertNotEqual(response_1, response_3)

    def test_follow_index_subscribed_users(self):
        """Проверяем, что новая запись пользователя появляется
        в ленте тех, кто на него подписан"""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': PostImageTest.user})
        )
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_follow_index_unsubscribed_users(self):
        """Проверяем, что новая запись пользователя не появляется
        в ленте тех, кто на него подписан"""
        response = self.authorized_client.get(reverse("posts:follow_index"))
        self.assertEqual(len(response.context['page_obj']), 0)
