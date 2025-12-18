from django.db import models
from django.contrib.auth.models import User
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def compress_image(image_field, quality=70, max_width=1920):
    if not image_field:
        return image_field
    
    try:
        img = Image.open(image_field)
        
        if img.mode != 'RGB':
            img = img.convert('RGB')

        if img.width > max_width:
            output_size = (max_width, int(img.height * (max_width / img.width)))
            img.thumbnail(output_size)
            
        output = BytesIO()
        img.save(output, format='JPEG', quality=quality)
        output.seek(0)
        
        return InMemoryUploadedFile(
            output,
            'ImageField',
            f"{image_field.name.split('.')[0]}.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
    except Exception as e:
        print(f"Error compressing image: {e}")
        return image_field


class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_image = models.ImageField(upload_to='client_images', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")

    def save(self, *args, **kwargs):
        if self.profile_image and isinstance(self.profile_image.file, InMemoryUploadedFile):
             self.profile_image = compress_image(self.profile_image, quality=60, max_width=800)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Client: {self.user.username}"


class PhotographerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    short_intro = models.CharField(max_length=250)
    bio = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    
    SPECIALIZATION_CHOICES = [
        ('wedding', 'Свадьба'),
        ('portrait', 'Портрет'),
        ('reportage', 'Репортаж'),
        ('lovestory', 'Love Story'),
        ('fashion', 'Fashion'),
    ]
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, default='wedding')
    
    price = models.IntegerField(default=0, help_text="Стоимость часа работы в RUB")
    
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='ru')
    
    profile_image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)

    def save(self, *args, **kwargs):
        if self.profile_image and not self.id:
             pass

        if self.profile_image:
             if hasattr(self.profile_image, 'file') and not isinstance(self.profile_image.file, InMemoryUploadedFile):
                 pass

             if isinstance(self.profile_image.file, InMemoryUploadedFile):
                 self.profile_image = compress_image(self.profile_image, quality=60, max_width=800)

        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username


class Photo(models.Model):
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photographs')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image and isinstance(self.image.file, InMemoryUploadedFile):
             self.image = compress_image(self.image, quality=70, max_width=1600)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Photo by {self.photographer.user.username}"


class BookingRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Выполнена'),
        ('cancelled', 'Отменена'),
    ]
    
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings_made')
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name='bookings_received')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    message = models.TextField(verbose_name="Сообщение")
    contact_phone = models.CharField(max_length=20, verbose_name="Телефон для связи")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_deleted_by_client = models.BooleanField(default=False)
    is_deleted_by_photographer = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.id} from {self.client.username}"


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photographer')

    def __str__(self):
        return f"{self.user.username} likes {self.photographer.user.username}"


class News(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    image = models.ImageField(upload_to='news_images', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
