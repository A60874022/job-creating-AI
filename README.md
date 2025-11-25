# HandmadeMarket - Маркетплейс товаров ручной работы

![Django](https://img.shields.io/badge/Django-5.2.7-green)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![WebSocket](https://img.shields.io/badge/WebSocket-Enabled-orange)
![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16.2-blue)
![Redis](https://img.shields.io/badge/Redis-7.2-red)
![Django Channels](https://img.shields.io/badge/Django_Channels-4.0-lightblue)
![Celery](https://img.shields.io/badge/Celery-5.3-green)

## 📖 О проекте

**HandmadeMarket** - это современная онлайн-платформа для покупки и продажи уникальных товаров ручной работы. Один аккаунт - две роли: вы можете быть как покупателем, так и продавцом!

### 🌟 Особенности платформы

- 🎭 **Один аккаунт - две роли** - Покупайте и продавайте без переключения между аккаунтами
- 💬 **Чат в реальном времени** - Общайтесь с другими пользователями мгновенно
- 🛍️ **Умный каталог** - Поиск и фильтрация по категориям, названию
- 🔔 **Умные уведомления** - Не пропускайте важные события
- 📱 **Адаптивный дизайн** - Удобно на любом устройстве

## 🛠 Технологический стек


- **Python 3.10** - основной язык программирования
- **Django 5.2.7** - веб-фреймворк
- **Django Channels** - для обработки WebSocket-соединений
- **PostgreSQL 16** - основная реляционная база данных
- **Redis 7.2** -  брокер для Channels
- **HTML5/CSS3** - семантическая разметка и стили
- **Bootstrap 5.3** - CSS-фреймворк для адаптивного дизайна
- **JavaScript (ES6+)** - интерактивность на стороне клиента




## 🚀 Быстрый старт

### Для пользователей

📱 **Посетите сайт:** [https://your-domain.com](https://your-domain.com)

### Для разработчиков

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/your-username/handmade-marketplace.git
cd handmade-marketplace

# 2. Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate    # Windows

# 3. Установите зависимости
pip install -r requirements.txt

# 4. Настройте базу данных
python manage.py migrate
python manage.py createsuperuser

# 5. Запустите Redis (для чатов и уведомлений)
redis-server

# 6. Запустите сервер
python manage.py runserver