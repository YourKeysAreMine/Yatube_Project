import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост1',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.user)

    def test_create_post(self):
        """Валидная форма PostForm создаёт запись в Post"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост2',
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile",
                              kwargs={"username": PostCreateFormTests.user})
        )
        added_post = Post.objects.get(text=form_data['text'])
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(added_post.text, form_data['text'])
        self.assertEqual(added_post.group, PostCreateFormTests.group)

    def test_post_edit(self):
        """Валидная форма PostForm изменяет запись в Post"""
        form_data = {
            'text': 'Новый текст поста',
            'group': PostCreateFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={"post_id": PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse("posts:post_detail",
                              kwargs={"post_id": PostCreateFormTests.post.id})
        )
        edited_post = Post.objects.get(text=form_data['text'])
        self.assertTrue(Post.objects.filter(text=form_data['text']).exists())
        self.assertEqual(edited_post.id, PostCreateFormTests.post.id)

    def test_post_with_image_create(self):
        """Валидная форма PostForm создаёт пост с картинкой в БД"""
        form_data = {
            'text': 'Тестовый пост3',
            'group': PostCreateFormTests.group.id,
            'image': 'posts/small.gif'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse("posts:profile",
                              kwargs={"username": PostCreateFormTests.user})
        )
        self.assertTrue(Post.objects.filter(image=form_data['image']).exists())

    def test_post_comment(self):
        """Валидная форма CommentForm создаёт комментарий под постом"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    kwargs={"post_id": PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse("posts:post_detail",
                              kwargs={"post_id": PostCreateFormTests.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count + 1)

    def test_post_unathorized_comment(self):
        """Комментировать посты может только авторизованный пользователь"""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.client.post(
            reverse('posts:add_comment',
                    kwargs={"post_id": PostCreateFormTests.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F')
        self.assertEqual(Comment.objects.count(), comments_count)
