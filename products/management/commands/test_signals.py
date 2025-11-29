from django.core.management.base import BaseCommand
from products.models import Product
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = "Test product signals"

    def handle(self, *args, **options):
        print("🧪 Testing product signals...")

        # Создаем тестового пользователя если нет
        user, created = User.objects.get_or_create(
            email="test@test.com", defaults={"is_active": True, "email_verified": True}
        )

        # Создаем тестовый товар
        product, created = Product.objects.get_or_create(
            title="Test Product for Signals",
            master=user,
            defaults={
                "description": "Test description",
                "price": 1000,
                "is_approved": False,
            },
        )

        print(f"📦 Test product: {product.pk}, Approved: {product.is_approved}")

        # Меняем статус одобрения
        print("🔄 Changing approval status from False to True...")
        product.is_approved = True
        product.save()

        print("✅ Test completed")
