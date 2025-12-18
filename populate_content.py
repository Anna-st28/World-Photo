import os
import django
import random
import requests
from django.core.files.base import ContentFile
from io import BytesIO

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from users.models import PhotographerProfile, Photo, News


def download_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return ContentFile(response.content)
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None


def create_news():
    print("Creating News...")
    news_data = [
        {
            "title": "Новая выставка 'Городские ритмы'",
            "content": "В центре современного искусства открылась выставка, посвященная ритму большого города. Лучшие фотографы представили свои работы, запечатлевшие мгновения городской суеты и тишины.",
            "image_url": "https://images.unsplash.com/photo-1449824913929-2b3a640fd856?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
        },
        {
            "title": "Мастер-класс по портретной съемке",
            "content": "Известный фотограф Анна Смирнова проведет мастер-класс по основам портретной фотографии. Участники узнают о работе со светом, композиции и психологии работы с моделью.",
            "image_url": "https://images.unsplash.com/photo-1542038784456-1ea8e935640e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
        },
        {
            "title": "Лучшие камеры 2024 года",
            "content": "Обзор новинок фототехники. Мы протестировали флагманские модели от Canon, Sony и Nikon, чтобы помочь вам сделать правильный выбор.",
            "image_url": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
        },
        {
            "title": "Фотоконкурс 'Природа родного края'",
            "content": "Приглашаем всех желающих принять участие в ежегодном фотоконкурсе. Главный приз - профессиональный объектив!",
            "image_url": "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
        }
    ]

    for item in news_data:
        if not News.objects.filter(title=item["title"]).exists():
            news = News(title=item["title"], content=item["content"])
            img_content = download_image(item["image_url"])
            if img_content:
                news.image.save(f"news_{random.randint(1000,9999)}.jpg", img_content, save=True)
            news.save()
            print(f"  Created news: {news.title}")
        else:
            print(f"  News already exists: {item['title']}")


def create_photographers():
    print("Creating Photographers...")
    photographers_data = [
        {
            "username": "alex_photo",
            "email": "alex@example.com",
            "short_intro": "Профессиональный свадебный фотограф",
            "bio": "Привет! Меня зовут Александр. Я занимаюсь фотографией уже более 10 лет. Моя страсть - запечатлевать самые счастливые моменты вашей жизни. Работаю в Москве и области.",
            "city": "Москва",
            "profile_url": "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?ixlib=rb-1.2.1&auto=format&fit=crop&w=200&q=80",
            "portfolio_urls": [
                "https://images.unsplash.com/photo-1519741497674-611481863552?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1511285560982-1351cdeb9821?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1515934751635-c81c6bc9a2d8?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
            ]
        },
        {
            "username": "maria_art",
            "email": "maria@example.com",
            "short_intro": "Художественная портретная съемка",
            "bio": "Я вижу красоту в каждом человеке. Мои фотографии - это не просто снимки, это истории. Люблю экспериментировать со светом и цветом.",
            "city": "Санкт-Петербург",
            "profile_url": "https://images.unsplash.com/photo-1494790108377-be9c29b29330?ixlib=rb-1.2.1&auto=format&fit=crop&w=200&q=80",
            "portfolio_urls": [
                "https://images.unsplash.com/photo-1531746020798-e6953c6e8e04?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1534528741775-53994a69daeb?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1526080652727-5b77f74eacd2?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
            ]
        },
        {
            "username": "dmitry_landscape",
            "email": "dmitry@example.com",
            "short_intro": "Пейзажная и travel-фотография",
            "bio": "Путешествую по миру и снимаю самые красивые уголки нашей планеты. Открыт для сотрудничества с журналами и тревел-агентствами.",
            "city": "Сочи",
            "profile_url": "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?ixlib=rb-1.2.1&auto=format&fit=crop&w=200&q=80",
            "portfolio_urls": [
                "https://images.unsplash.com/photo-1472214103451-9374bd1c798e?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1447752875215-b2761acb3c5d?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80",
                "https://images.unsplash.com/photo-1470071459604-3b5ec3a7fe05?ixlib=rb-1.2.1&auto=format&fit=crop&w=800&q=80"
            ]
        }
    ]

    for data in photographers_data:
        if not User.objects.filter(username=data["username"]).exists():
            user = User.objects.create_user(username=data["username"], email=data["email"], password="password123")
            
            profile = PhotographerProfile(
                user=user,
                short_intro=data["short_intro"],
                bio=data["bio"],
                city=data["city"]
            )
            
            # Profile Image
            img_content = download_image(data["profile_url"])
            if img_content:
                profile.profile_image.save(f"profile_{data['username']}.jpg", img_content, save=True)
            profile.save()
            
            # Portfolio Photos
            for url in data["portfolio_urls"]:
                photo_content = download_image(url)
                if photo_content:
                    photo = Photo(photographer=profile)
                    photo.image.save(f"portfolio_{random.randint(10000,99999)}.jpg", photo_content, save=True)
                    photo.save()
            
            print(f"  Created photographer: {data['username']}")
        else:
            print(f"  User already exists: {data['username']}")


if __name__ == "__main__":
    create_news()
    create_photographers()
    print("Done!")
