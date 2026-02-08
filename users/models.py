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
            
        # Resize if width > max_width
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
        if self.profile_image:
            try:
                if isinstance(self.profile_image.file, InMemoryUploadedFile):
                     self.profile_image = compress_image(self.profile_image, quality=60, max_width=800)
            except (FileNotFoundError, ValueError, OSError):
                pass
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Client: {self.user.username}"


SPECIALIZATION_CHOICES = [
    ('wedding', 'Свадьба'),
    ('portrait', 'Портрет'),
    ('reportage', 'Репортаж'),
    ('lovestory', 'Love Story'),
    ('fashion', 'Fashion'),
]

class PhotographerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    short_intro = models.CharField(max_length=250)
    bio = models.TextField()
    city = models.CharField(max_length=100, blank=True, null=True)
    
    specialization = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, default='wedding')
    
    price = models.IntegerField(default=0, help_text="Стоимость часа работы в RUB")
    
    LANGUAGE_CHOICES = [
        ('ru', 'Русский'),
        ('en', 'English'),
    ]
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='ru')
    
    profile_image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    views_count = models.PositiveIntegerField(default=0)
    
    # New fields for contact info
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Номер телефона")
    social_vk = models.URLField(blank=True, null=True, verbose_name="Ссылка на ВКонтакте")
    social_telegram = models.CharField(max_length=50, blank=True, null=True, verbose_name="Telegram (username)")
    website = models.URLField(blank=True, null=True, verbose_name="Личный сайт")

    def save(self, *args, **kwargs):
        if self.profile_image and not self.id: # Only compress on initial upload or handle update logic carefully
             # Simple check: if image is being updated. 
             # Ideally we compare with old instance, but for simplicity in this homework, 
             # we can just compress. However, compressing already compressed image might degrade quality repeatedly.
             # Better approach: check if it's a new file.
             pass
             
        # For simplicity, we will apply compression if it looks like a raw upload (has file path)
        # In a real app, we'd check if self.pk is None or if 'profile_image' in changed_fields
        if self.profile_image:
             # This is a bit risky without state tracking, but acceptable for a prototype if we don't save repeatedly.
             # Actually, let's just do it. The user wants the feature.
             # To avoid re-compression, we could check a flag or just assume new uploads.
             # We will try to compress.
             if hasattr(self.profile_image, 'file') and not isinstance(self.profile_image.file, InMemoryUploadedFile):
                 # It might be a file from disk (management command) or fresh upload
                 pass
             
             # Let's rely on the fact that forms send InMemoryUploadedFile.
             # If we just save, we might re-compress.
             # Safe bet: Compress if no ID (create) or if we implement a check in View.
             # Let's put the logic here but only if it is an InMemoryUploadedFile (fresh upload).
             if self.profile_image:
                 try:
                     if isinstance(self.profile_image.file, InMemoryUploadedFile):
                         self.profile_image = compress_image(self.profile_image, quality=60, max_width=800)
                 except (FileNotFoundError, ValueError, OSError):
                     pass

        super().save(*args, **kwargs)

    def __str__(self):
        return self.user.username

class ProfileView(models.Model):
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name='profile_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=40, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['photographer', 'user']),
            models.Index(fields=['photographer', 'session_key']),
        ]

    def __str__(self):
        viewer = self.user.username if self.user else f"Anonymous ({self.session_key})"
        return f"{viewer} viewed {self.photographer.user.username}"

class Photo(models.Model):
    photographer = models.ForeignKey(PhotographerProfile, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='photographs')
    category = models.CharField(max_length=50, choices=SPECIALIZATION_CHOICES, default='wedding', verbose_name="Категория")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.image:
            try:
                if isinstance(self.image.file, InMemoryUploadedFile):
                     self.image = compress_image(self.image, quality=70, max_width=1600)
            except (FileNotFoundError, ValueError, OSError):
                pass
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

class PhotoLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='photo_likes')
    photo = models.ForeignKey(Photo, on_delete=models.CASCADE, related_name='likes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'photo')

    def __str__(self):
        return f"{self.user.username} likes photo {self.photo.id}"

class SupportRequest(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новый'),
        ('in_progress', 'В работе'),
        ('resolved', 'Решен'),
        ('closed', 'Закрыт'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='support_requests')
    subject = models.CharField(max_length=200, default='Вопрос в поддержку', verbose_name="Тема")
    message = models.TextField(verbose_name="Сообщение")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    admin_response = models.TextField(blank=True, null=True, verbose_name="Ответ администратора")

    def __str__(self):
        return f"{self.subject} - {self.user.username}"
