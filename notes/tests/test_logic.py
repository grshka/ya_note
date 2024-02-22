from http import HTTPStatus

from django.contrib.auth import get_user_model, get_user
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()
TITLE = 'Заголовок'
TEXT = 'Текст'
SLUG = 'not_slug'


class Testfixtures(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url_done = reverse('notes:success')
        cls.url_add = reverse('notes:add')
        cls.url_login = reverse('users:login')
        cls.user = User.objects.create(username='Мимо Крокодил')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.not_author = User.objects.create(username='Не автор')
        cls.user_not_author = Client()
        cls.user_not_author.force_login(cls.not_author)
        cls.form_data = {'text': TEXT,
                         'title': TITLE,
                         'slug': SLUG,
                         }


class TestNoteCreation(Testfixtures):

    def test_user_can_create_note(self):
        note_count_start = Note.objects.count()
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        note_count = Note.objects.count()
        self.assertEqual(note_count, (note_count_start + 1))
        last_note = Note.objects.last()
        self.assertEqual(last_note.title, self.form_data['title'])
        self.assertEqual(last_note.text, self.form_data['text'])
        self.assertEqual(last_note.slug, self.form_data['slug'])
        self.assertEqual(last_note.author, self.user)

    def test_anonymous_user_cant_create_note(self):
        note_count_start = Note.objects.count()
        response = self.client.post(self.url_add, data=self.form_data)
        expected_url = f'{self.url_login}?next={self.url_add}'
        self.assertRedirects(response, expected_url)
        self.assertEqual(Note.objects.count(), note_count_start)

    def test_empty_slug(self):
        note_count_start = Note.objects.count()
        self.form_data.pop('slug')
        response = self.auth_client.post(self.url_add, data=self.form_data)
        self.assertRedirects(response, self.url_done)
        self.assertEqual(Note.objects.count(), (note_count_start + 1))
        new_note = Note.objects.last()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestSlug(Testfixtures):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.note = Note.objects.create(
            title='Заголовок',
            text='Текст заметки',
            slug=SLUG,
            author=cls.user,
        )
        cls.url_edit = reverse('notes:edit', args=(cls.note.slug,))
        cls.url_delete = reverse('notes:delete', args=(cls.note.slug,))

    def test_not_unique_slug(self):
        note_count_start = Note.objects.count()
        self.form_data['slug'] = self.note.slug
        response = self.auth_client.post(
            self.url_add,
            data=self.form_data
        )
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.note.slug + WARNING)
        )
        self.assertEqual(Note.objects.count(), note_count_start)

    def test_author_can_edit_note(self):
        response = self.auth_client.post(self.url_edit, self.form_data)
        self.assertRedirects(response, self.url_done)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.form_data['title'])
        self.assertEqual(self.note.text, self.form_data['text'])
        self.assertEqual(self.note.slug, self.form_data['slug'])
        self.assertEqual(self.note.author, self.user)

    def test_other_user_cant_edit_note(self):
        response = self.user_not_author.post(self.url_edit, self.form_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        note_from_db = Note.objects.get(id=self.note.id,)
        self.assertEqual(self.note.title, note_from_db.title)
        self.assertEqual(self.note.text, note_from_db.text)
        self.assertEqual(self.note.slug, note_from_db.slug)
        self.assertEqual(self.note.author, note_from_db.author)

    def test_author_can_delete_note(self):
        note_count_start = Note.objects.count()
        response = self.auth_client.post(self.url_delete)
        self.assertRedirects(response, self.url_done)
        self.assertEqual(Note.objects.count(), (note_count_start - 1))

    def test_other_user_cant_delete_note(self):
        note_count_start = Note.objects.count()
        response = self.user_not_author.post(self.url_delete)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertEqual(Note.objects.count(), note_count_start)
