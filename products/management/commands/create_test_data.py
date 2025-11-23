from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from orders.models import Order, OrderItem
from products.models import Category, Favorite, Product
from users.models import Profile

User = get_user_model()


class Command(BaseCommand):
    help = "Setup complete test data for handmade marketplace"

    def handle(self, *args, **options):
        self.stdout.write("🚀 Setting up complete test data...")

        # 1. Создаем суперпользователя
        self.stdout.write("1. Creating superuser...")
        admin, created = User.objects.get_or_create(
            email="admin@example.com",
            defaults={"is_superuser": True, "is_staff": True, "is_active": True},
        )
        if created:
            admin.set_password("admin123")
            admin.save()
            self.stdout.write("   ✓ Superuser created: admin@example.com / admin123")
        else:
            self.stdout.write("   ✓ Superuser already exists")

        # 2. Создаем категории
        self.stdout.write("2. Creating categories...")
        categories_data = [
            ("Вышивка", "embroidery"),
            ("Вязание и кружево", "knitting-crochet"),
            ("Керамика и гончарное дело", "pottery-ceramics"),
            ("Украшения", "jewelry"),
            ("Декор для дома", "home-decor"),
            ("Мыловарение", "soap-making"),
            ("Свечи", "candles"),
            ("Деревообработка", "woodworking"),
        ]

        categories = {}
        for name, slug in categories_data:
            category, created = Category.objects.get_or_create(
                slug=slug, defaults={"name": name}
            )
            categories[name] = category
            if created:
                self.stdout.write(f"   ✓ Category created: {name}")
            else:
                self.stdout.write(f"   ✓ Category already exists: {name}")

        # 3. Создаем пользователей и профили
        self.stdout.write("3. Creating users and profiles...")

        users_data = [
            {
                "email": "master_anna@example.com",
                "is_master": True,
                "bio": "Профессиональная вышивальщица с 10-летним опытом",
                "city": "Москва",
            },
            {
                "email": "master_peter@example.com",
                "is_master": True,
                "bio": "Керамист, специализируюсь на ручной лепке",
                "city": "Санкт-Петербург",
            },
            {
                "email": "customer_maria@example.com",
                "is_master": False,
                "bio": "Люблю handmade товары",
                "city": "Казань",
            },
            {
                "email": "customer_alex@example.com",
                "is_master": False,
                "bio": "Коллекционирую уникальные вещи",
                "city": "Екатеринбург",
            },
        ]

        users = {}
        for user_data in users_data:
            user, created = User.objects.get_or_create(
                email=user_data["email"],
                defaults={"is_master": user_data["is_master"], "is_active": True},
            )
            if created:
                user.set_password("test123")
                user.save()
                self.stdout.write(f'   ✓ User created: {user_data["email"]}')
            else:
                self.stdout.write(f'   ✓ User already exists: {user_data["email"]}')

            # Создаем или обновляем профиль
            profile, profile_created = Profile.objects.get_or_create(
                user=user, defaults={"bio": user_data["bio"], "city": user_data["city"]}
            )
            if not profile_created:
                # Если профиль уже существует, обновляем его
                profile.bio = user_data["bio"]
                profile.city = user_data["city"]
                profile.save()
                self.stdout.write(f'   ✓ Profile updated: {user_data["email"]}')
            else:
                self.stdout.write(f'   ✓ Profile created: {user_data["email"]}')

            users[user_data["email"]] = user

        # 4. Создаем товары
        self.stdout.write("4. Creating products...")
        products_data = [
            (
                users["master_anna@example.com"],
                categories["Вышивка"],
                'Вышитая картина "Лесная фея"',
                "Ручная вышивка мулине на хлопковом полотне. Размер 30x40 см.",
                4500,
            ),
            (
                users["master_anna@example.com"],
                categories["Вышивка"],
                'Вышитые серьги "Цветочные"',
                "Нежные серьги с вышитыми цветами. Легкие и удобные.",
                1200,
            ),
            (
                users["master_peter@example.com"],
                categories["Керамика и гончарное дело"],
                'Керамическая кружка "Утро"',
                "Ручная лепка, уникальная глазурь. Объем 350 мл.",
                1800,
            ),
            (
                users["master_peter@example.com"],
                categories["Керамика и гончарное дело"],
                'Набор тарелок "Геометрия"',
                "Набор из 4-х тарелок разного диаметра. Ручная роспись.",
                3200,
            ),
            (
                users["master_anna@example.com"],
                categories["Вязание и кружево"],
                'Вязаный свитер "Северный"',
                "Теплый свитер из натуральной шерсти. Размер M.",
                5200,
            ),
            (
                users["master_peter@example.com"],
                categories["Украшения"],
                'Керамическое колье "Луна"',
                "Подвеска из керамики ручной работы на кожаном шнурке.",
                1500,
            ),
            (
                users["master_anna@example.com"],
                categories["Декор для дома"],
                'Вышитая подушка "Винтаж"',
                "Декоративная подушка с ручной вышивкой.",
                2800,
            ),
        ]

        products = []
        for master, category, title, description, price in products_data:
            product, created = Product.objects.get_or_create(
                title=title,
                master=master,
                defaults={
                    "category": category,
                    "description": description,
                    "price": price,
                    "created_at": timezone.now(),
                },
            )
            products.append(product)
            if created:
                self.stdout.write(f"   ✓ Product created: {title} - {price} руб.")
            else:
                self.stdout.write(f"   ✓ Product already exists: {title}")

        # 5. Создаем заказы
        self.stdout.write("5. Creating orders...")

        # Удаляем старые заказы для чистоты тестовых данных
        Order.objects.filter(
            customer__in=[
                users["customer_maria@example.com"],
                users["customer_alex@example.com"],
            ]
        ).delete()

        order1, created = Order.objects.get_or_create(
            customer=users["customer_maria@example.com"], status="оформлен"
        )
        if created:
            OrderItem.objects.get_or_create(
                order=order1,
                product=products[0],
                defaults={"quantity": 1, "price_at_moment": products[0].price},
            )
            self.stdout.write("   ✓ Order 1 created: customer_maria → Вышитая картина")
        else:
            self.stdout.write("   ✓ Order 1 already exists")

        order2, created = Order.objects.get_or_create(
            customer=users["customer_alex@example.com"], status="в_работе"
        )
        if created:
            OrderItem.objects.get_or_create(
                order=order2,
                product=products[2],
                defaults={"quantity": 1, "price_at_moment": products[2].price},
            )
            OrderItem.objects.get_or_create(
                order=order2,
                product=products[5],
                defaults={"quantity": 1, "price_at_moment": products[5].price},
            )
            self.stdout.write("   ✓ Order 2 created: customer_alex → Кружка + Колье")
        else:
            self.stdout.write("   ✓ Order 2 already exists")

        # 6. Создаем избранное
        self.stdout.write("6. Creating favorites...")

        # Удаляем старые избранные для чистоты тестовых данных
        Favorite.objects.filter(
            user__in=[
                users["customer_maria@example.com"],
                users["customer_alex@example.com"],
            ]
        ).delete()

        Favorite.objects.get_or_create(
            user=users["customer_maria@example.com"], product=products[1]
        )
        Favorite.objects.get_or_create(
            user=users["customer_maria@example.com"], product=products[4]
        )
        Favorite.objects.get_or_create(
            user=users["customer_alex@example.com"], product=products[3]
        )
        self.stdout.write("   ✓ Favorites created/updated")

        self.stdout.write(
            self.style.SUCCESS("\n🎉 SUCCESS! Test data setup completed!")
        )

        self.stdout.write("\n📊 SUMMARY:")
        self.stdout.write(f"   • Categories: {Category.objects.count()}")
        self.stdout.write(f"   • Users: {User.objects.count()}")
        self.stdout.write(f"   • Products: {Product.objects.count()}")
        self.stdout.write(f"   • Orders: {Order.objects.count()}")
        self.stdout.write(f"   • Favorites: {Favorite.objects.count()}")

        self.stdout.write("\n🔐 TEST ACCOUNTS:")
        self.stdout.write("   👑 Admin:     admin@example.com / admin123")
        self.stdout.write("   👩‍🎨 Master 1:  master_anna@example.com / test123")
        self.stdout.write("   👨‍🎨 Master 2:  master_peter@example.com / test123")
        self.stdout.write("   👩 Customer 1: customer_maria@example.com / test123")
        self.stdout.write("   👨 Customer 2: customer_alex@example.com / test123")

        self.stdout.write("\n🌐 TEST URLS:")
        self.stdout.write("   • Catalog:    http://127.0.0.1:8000/catalog/")
        self.stdout.write("   • Admin:      http://127.0.0.1:8000/admin/")
        self.stdout.write("   • Add product: http://127.0.0.1:8000/catalog/add/")
