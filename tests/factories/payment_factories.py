import factory
from factory.django import DjangoModelFactory
from payments.models import Subscription, Payment
from common.enums import SubscriptionPlan, PaymentStatus, SubscriptionStatus
from tests.factories.account_factories import TenantFactory, UserFactory
import random
import string


class SubscriptionFactory(DjangoModelFactory):
    class Meta:
        model = Subscription

    tenant = factory.SubFactory(TenantFactory)
    status = SubscriptionStatus.CREATED

    class Params:
        premium = factory.Trait(status=SubscriptionStatus.ACTIVE)


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = Payment

    tenant = factory.SubFactory(TenantFactory)
    subscription = factory.SubFactory(
        SubscriptionFactory, tenant=factory.SelfAttribute("..tenant")
    )
    initiated_by = factory.SubFactory(
        UserFactory, tenant=factory.SelfAttribute("..tenant")
    )
    amount = 50000
    status = PaymentStatus.CREATED

    razorpay_order_id = factory.Faker("numerify", text="order_##############")

    class Params:
        completed = factory.Trait(
            status=PaymentStatus.PAID,
            razorpay_payment_id=factory.Faker("numerify", text="pay_##############"),
            razorpay_signature=factory.Faker("lexify", text="?" * 64),
        )
        failed = factory.Trait(status=PaymentStatus.FAILED)
