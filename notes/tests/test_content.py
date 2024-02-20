from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContentNote(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.user)
        cls.not_author = User.objects.create(username='Не автор')
        cls.not_author_client = Client()
        cls.not_author_client.force_login(cls.not_author)
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug='note_slug',
            author=cls.user,
        )

    def test_notes_list_for_different_users(self):
        users = (
            (self.author_client, True),
            (self.not_author_client, False),
        )
        url = reverse('notes:list')
        for user, note_in_list in users:
            with self.subTest(user=user):
                response = user.get(url)
                object_list = response.context['object_list']
                self.assertEqual(self.note in object_list, note_in_list)

    def test_pages_contains_form(self):
        adress = (
            ('notes:add', None),
            ('notes:edit', (self.note.slug,))
        )
        for adres, args in adress:
            with self.subTest(adres=adres):
                url = reverse(adres, args=args)
                response = self.author_client.get(url)
                self.assertIn('form', response.context)
                self.assertIsInstance(response.context['form'], NoteForm)
