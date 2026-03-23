import pytest
from django.urls import reverse
from rest_framework import status
from books.models import Genre, Book, UserBook
from common.enums import BookStatus

@pytest.mark.django_db
class TestBookViews:
    """Integration tests for Books."""

    def test_genre_list(self, api_client, user, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("genres")
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_genre_create(self, api_client, admin_user, tenant, faker):
        api_client.force_authenticate(user=admin_user)
        url = reverse("genres")
        name = faker.unique.word().capitalize()
        response = api_client.post(url, {"name": name}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_201_CREATED

    def test_genre_retrieve(self, api_client, user, genre, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("genre-detail", kwargs={"id": genre.id})
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_genre_delete(self, api_client, admin_user, genre, tenant):
        api_client.force_authenticate(user=admin_user)
        url = reverse("genre-detail", kwargs={"id": genre.id})
        response = api_client.delete(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_book_list(self, api_client, user, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("list")
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_book_create(self, api_client, user, genre, tenant, faker):
        api_client.force_authenticate(user=user)
        url = reverse("list")
        title = faker.sentence(nb_words=3)
        data = {
            "title": title,
            "author": faker.name(),
            "isbn": faker.isbn13().replace("-", ""),
            "published_year": faker.year(),
            "genres": [str(genre.id)],
        }
        response = api_client.post(url, data, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_201_CREATED

    def test_book_retrieve(self, api_client, user, book, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("book-detail", kwargs={"id": book.id})
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_book_delete(self, api_client, admin_user, book, tenant):
        api_client.force_authenticate(user=admin_user)
        url = reverse("book-detail", kwargs={"id": book.id})
        response = api_client.delete(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_userbook_add(self, api_client, user, book, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("user-books", kwargs={"user_id": user.id})
        response = api_client.post(url, {"book_id": book.id, "status": BookStatus.READING}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_201_CREATED

    def test_userbook_list(self, api_client, user, tenant):
        api_client.force_authenticate(user=user)
        url = reverse("user-books", kwargs={"user_id": user.id})
        response = api_client.get(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_userbook_update(self, api_client, user, book, tenant):
        api_client.force_authenticate(user=user)
        UserBook.objects.create(user=user, book=book, status=BookStatus.READING)
        url = reverse("user-book-detail", kwargs={"user_id": user.id, "book_id": book.id})
        response = api_client.patch(url, {"status": BookStatus.COMPLETED}, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_200_OK

    def test_userbook_remove(self, api_client, user, book, tenant):
        api_client.force_authenticate(user=user)
        UserBook.objects.create(user=user, book=book, status=BookStatus.READING)
        url = reverse("user-book-detail", kwargs={"user_id": user.id, "book_id": book.id})
        response = api_client.delete(url, HTTP_TENANT_ID=str(tenant.id))
        assert response.status_code == status.HTTP_204_NO_CONTENT
