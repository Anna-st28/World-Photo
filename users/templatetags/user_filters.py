from django import template
from users.models import PhotographerProfile, ClientProfile

register = template.Library()

@register.filter
def get_avatar_url(user):
    # Check for photographer profile
    try:
        if hasattr(user, 'photographerprofile'):
            profile = user.photographerprofile
            if profile.profile_image:
                return profile.profile_image.url
    except Exception:
        pass

    # Check for client profile
    try:
        if hasattr(user, 'clientprofile'):
            profile = user.clientprofile
            if profile.profile_image:
                return profile.profile_image.url
    except Exception:
        pass
        
    name = user.get_full_name() or user.username
    return f"https://ui-avatars.com/api/?name={name}&background=e0bbd8&color=fff"
