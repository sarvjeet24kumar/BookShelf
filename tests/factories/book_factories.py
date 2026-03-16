import factory
from factory.django import DjangoModelFactory
from books.models import Genre, Book, BookGenre, UserBook
from common.enums import RequestStatus, BookStatus
from tests.factories.account_factories import TenantFactory, UserFactory
import random
import string

class GenreFactory(DjangoModelFactory):
    class Meta:
        model = Genre

    tenant = factory.SubFactory(TenantFactory)
    name = factory.Faker("lexify", text="Genre ??????????")


class BookFactory(DjangoModelFactory):
    class Meta:
        model = Book
        skip_postgeneration_save = True

    tenant = factory.SubFactory(TenantFactory)
    created_by = factory.SubFactory(UserFactory, tenant=factory.SelfAttribute('..tenant'))
    title = factory.Faker("sentence", nb_words=3)
    author = factory.Faker("name")
    published_year = factory.Faker("random_int", min=1900, max=2024)
    request_status = RequestStatus.APPROVED

    isbn = factory.Faker("numerify", text="#############") # 13 digits

    @factory.post_generation
    def genres(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for genre in extracted:
                BookGenre.objects.create(book=self, genre=genre)
        else:
            genre = GenreFactory(tenant=self.tenant)
            BookGenre.objects.create(book=self, genre=genre)

    class Params:
        pending = factory.Trait(request_status=RequestStatus.PENDING)
        rejected = factory.Trait(request_status=RequestStatus.REJECTED)


class UserBookFactory(DjangoModelFactory):
    class Meta:
        model = UserBook

    user = factory.SubFactory(UserFactory)
    book = factory.SubFactory(BookFactory, tenant=factory.SelfAttribute('..user.tenant'))
    status = BookStatus.READING

    class Params:
        completed = factory.Trait(status=BookStatus.COMPLETED)
        to_read = factory.Trait(status=BookStatus.TO_READ)
