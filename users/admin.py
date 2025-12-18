from django.contrib import admin
from .models import PhotographerProfile, Photo, News

admin.site.register(PhotographerProfile)
admin.site.register(Photo)
admin.site.register(News)
