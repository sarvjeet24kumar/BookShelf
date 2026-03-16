import factory
from factory.django import DjangoModelFactory
from django.contrib.auth import get_user_model
from tenants.models import Tenant
from common.enums import UserRole
import random
import string

User = get_user_model()


class TenantFactory(DjangoModelFactory):
    class Meta:
        model = Tenant

    name = factory.Faker("company")
    slug = factory.Faker("slug")


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    tenant = factory.SubFactory(TenantFactory)
    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
    role = UserRole.USER

    @factory.post_generation
    def password(obj, create, extracted, **kwargs):
        pw = extracted if extracted else "Password@123"
        obj.set_password(pw)
        if create:
            obj.save()
    is_active = True
    is_email_verified = True

    username = factory.LazyAttribute(lambda o: factory.Faker("lexify", text="u?????????").evaluate(None, None, {'locale': None}).lower())

    phone_no = factory.Faker("numerify", text="+91##########")

    class Params:
        is_admin = factory.Trait(
            role=UserRole.ADMIN,
            username=factory.LazyAttribute(lambda o: ("a" + o.first_name.lower() + "adm")[:30])
        )
        is_super_admin = factory.Trait(
            role=UserRole.SUPER_ADMIN,
            tenant=None,
            is_email_verified=True,
            username=factory.LazyAttribute(lambda o: ("s" + o.first_name.lower() + "sup")[:30])
        )
        unverified = factory.Trait(is_email_verified=False)
        suspended = factory.Trait(is_active=False)

