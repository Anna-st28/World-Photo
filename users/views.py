from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, PhotographerProfileForm, PhotoUploadForm, BookingRequestForm, ClientProfileForm
from .models import PhotographerProfile, Photo, News, BookingRequest, Favorite, ClientProfile
import random
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


def home(request):
    all_photos = list(Photo.objects.all())
    best_photos = random.sample(all_photos, min(len(all_photos), 6))
    
    specializations = PhotographerProfile.SPECIALIZATION_CHOICES
    
    return render(request, 'users/home.html', {
        'best_photos': best_photos,
        'specializations': specializations
    })


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()

            if form.cleaned_data['is_photographer']:
                PhotographerProfile.objects.create(
                    user=user, 
                    short_intro="Начинающий фотограф", 
                    bio="Расскажите о себе..."
                )
            else:
                ClientProfile.objects.create(user=user)
            
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def dashboard(request):
    try:
        profile = request.user.photographerprofile
        is_photographer = True
        client_profile = None
    except PhotographerProfile.DoesNotExist:
        profile = None
        is_photographer = False
        client_profile, created = ClientProfile.objects.get_or_create(user=request.user)

    password_form = PasswordChangeForm(request.user)

    p_form = None
    photo_form = None
    photos = []
    received_active_bookings = []
    received_completed_bookings = []

    client_form = None

    if is_photographer:
        p_form = PhotographerProfileForm(instance=profile)
        photo_form = PhotoUploadForm()
        photos = profile.photos.all().order_by('-uploaded_at')
        all_received = BookingRequest.objects.filter(photographer=profile, is_deleted_by_photographer=False).order_by('-created_at')
        received_active_bookings = all_received.exclude(status='completed')
        received_completed_bookings = all_received.filter(status='completed')
    else:
        client_form = ClientProfileForm(instance=client_profile)

    all_sent = BookingRequest.objects.filter(client=request.user, is_deleted_by_client=False).order_by('-created_at')
    sent_active_bookings = all_sent.exclude(status='completed')
    sent_completed_bookings = all_sent.filter(status='completed')
    
    favorites = Favorite.objects.filter(user=request.user)

    if request.method == 'POST':
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, 'Ваш пароль был успешно обновлен!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')

        elif 'update_settings' in request.POST:
             messages.success(request, 'Настройки сохранены!')
             return redirect('dashboard')

        elif 'send_question' in request.POST:
            messages.success(request, 'Ваш вопрос отправлен в поддержку. Мы ответим в ближайшее время.')
            return redirect('dashboard')

        elif 'delete_account' in request.POST:
            user = request.user
    
            user.delete()
            logout(request)
            messages.success(request, 'Ваш аккаунт был успешно удален.')
            return redirect('home')

        elif 'update_booking_status' in request.POST:
            booking_id = request.POST.get('booking_id')
            new_status = request.POST.get('status')
            booking = get_object_or_404(BookingRequest, id=booking_id, photographer=profile)
            booking.status = new_status
            booking.save()
            messages.success(request, 'Статус заявки обновлен.')
            return redirect('dashboard')

        elif 'cancel_booking' in request.POST:
            booking_id = request.POST.get('booking_id')
            try:
                if is_photographer:
                    booking = BookingRequest.objects.get(id=booking_id, photographer=profile)

                    if booking.status == 'completed' or booking.status == 'cancelled':
                         booking.is_deleted_by_photographer = True
                         booking.save()

                         if booking.is_deleted_by_client and booking.is_deleted_by_photographer:
                             booking.delete()
                             
                         messages.success(request, 'Заявка удалена из вашего списка.')
                         return redirect('dashboard')

                    if booking.status != 'cancelled' and booking.status != 'completed':
                        booking.status = 'cancelled'
                        booking.save()
                        messages.success(request, 'Заявка отменена. Клиент получит уведомление.')
                        return redirect('dashboard')
                        
                else:
                    booking = BookingRequest.objects.get(id=booking_id, client=request.user)

                    if booking.status == 'completed' or booking.status == 'cancelled':
                         booking.is_deleted_by_client = True
                         booking.save()

                         if booking.is_deleted_by_client and booking.is_deleted_by_photographer:
                             booking.delete()
                             
                         messages.success(request, 'Заявка удалена из вашего списка.')
                         return redirect('dashboard')
                    
                    pass

            except BookingRequest.DoesNotExist:
                booking = get_object_or_404(BookingRequest, Q(id=booking_id) & (Q(client=request.user) | Q(photographer__user=request.user)))

            booking.delete()
            messages.success(request, 'Заявка удалена.')
            return redirect('dashboard')

        if is_photographer:
            if 'update_profile' in request.POST:
                p_form = PhotographerProfileForm(request.POST, request.FILES, instance=profile)
                if p_form.is_valid():
                    p_form.save()
                    messages.success(request, 'Профиль обновлен.')
                    return redirect('dashboard')

            elif 'upload_photo' in request.POST:
                photo_form = PhotoUploadForm(request.POST, request.FILES)
                if photo_form.is_valid():
                    images = request.FILES.getlist('image')
                    for img in images:
                        Photo.objects.create(photographer=profile, image=img)
                    
                    count = len(images)
                    if count > 0:
                        messages.success(request, f'Добавлено фото: {count} шт.')
                    else:
                        messages.warning(request, 'Не выбрано ни одного фото.')
                        
                    return redirect('dashboard')
        else:
            if 'update_client_profile' in request.POST:
                client_form = ClientProfileForm(request.POST, request.FILES, instance=client_profile)
                if client_form.is_valid():
                    client_form.save()
                    messages.success(request, 'Профиль обновлен.')
                    return redirect('dashboard')
    
    return render(request, 'users/dashboard.html', {
        'is_photographer': is_photographer,
        'p_form': p_form,
        'photo_form': photo_form,
        'photos': photos,
        'password_form': password_form,
        'received_bookings': received_active_bookings,
        'received_active_bookings': received_active_bookings,
        'received_completed_bookings': received_completed_bookings,
        'sent_bookings': sent_active_bookings,
        'sent_active_bookings': sent_active_bookings,
        'sent_completed_bookings': sent_completed_bookings,
        'favorites': favorites,
        'client_form': client_form,
        'client_profile': client_profile,
    })


def specialists(request):
    photographers = PhotographerProfile.objects.all()

    specialization = request.GET.get('specialization')
    price_min = request.GET.get('price_min')
    price_max = request.GET.get('price_max')
    city = request.GET.get('city')
    language = request.GET.get('language')

    if specialization and specialization != 'any':
        photographers = photographers.filter(specialization=specialization)

    if language and language != 'any':
        photographers = photographers.filter(language=language)

    if city:
        photographers = photographers.filter(city__icontains=city)

    if price_min:
        try:
            photographers = photographers.filter(price__gte=int(price_min))
        except ValueError:
            pass
            
    if price_max:
        try:
            photographers = photographers.filter(price__lte=int(price_max))
        except ValueError:
            pass

    if request.user.is_authenticated:
        favorite_ids = Favorite.objects.filter(user=request.user).values_list('photographer_id', flat=True)
        for p in photographers:
            p.is_favorite = p.id in favorite_ids

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('users/specialists_list.html', {'photographers': photographers, 'user': request.user})
        return JsonResponse({'html': html})

    return render(request, 'users/specialists.html', {'photographers': photographers})


def photographer_detail(request, pk):
    photographer = get_object_or_404(PhotographerProfile, pk=pk)

    photographer.views_count += 1
    photographer.save(update_fields=['views_count'])
    
    is_favorite = False
    if request.user.is_authenticated:
        is_favorite = Favorite.objects.filter(user=request.user, photographer=photographer).exists()

    initial_data = {}
    if request.user.is_authenticated:
        try:
            if hasattr(request.user, 'clientprofile'):
                 initial_data['contact_phone'] = request.user.clientprofile.phone_number
        except Exception:
            pass

    form = BookingRequestForm(initial=initial_data)

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
            
        if 'submit_booking' in request.POST:
            form = BookingRequestForm(request.POST)
            if form.is_valid():
                booking = form.save(commit=False)
                booking.client = request.user
                booking.photographer = photographer
                booking.save()
                messages.success(request, 'Ваша заявка успешно отправлена!')
                return redirect('photographer_detail', pk=pk)

    return render(request, 'users/photographer_detail.html', {
        'photographer': photographer,
        'booking_form': form,
        'is_favorite': is_favorite
    })


@login_required
def toggle_favorite(request, pk):
    if request.method == 'POST':
        photographer = get_object_or_404(PhotographerProfile, pk=pk)
        favorite, created = Favorite.objects.get_or_create(user=request.user, photographer=photographer)
        
        if not created:
            favorite.delete()
            is_favorite = False
        else:
            is_favorite = True
            
        return JsonResponse({'status': 'ok', 'is_favorite': is_favorite})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def delete_profile_image(request):
    if request.method == 'POST':
        try:
            try:
                profile = request.user.photographerprofile
            except PhotographerProfile.DoesNotExist:
                try:
                    profile = request.user.clientprofile
                except ClientProfile.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Profile not found'}, status=404)

            if profile.profile_image:
                profile.profile_image.delete(save=False)
                profile.profile_image = None
                profile.save()
            return JsonResponse({'status': 'ok'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    return JsonResponse({'status': 'error', 'message': 'Invalid method'}, status=405)


def gallery(request):
    photos = Photo.objects.all().order_by('-uploaded_at')
    
    if request.user.is_authenticated:
        favorite_ids = Favorite.objects.filter(user=request.user).values_list('photographer_id', flat=True)
        for photo in photos:
            photo.is_favorite = photo.photographer.id in favorite_ids
            
    return render(request, 'users/gallery.html', {'photos': photos})


def news(request):
    news_items = News.objects.all().order_by('-created_at')
    return render(request, 'users/news.html', {'news_items': news_items})


def news_detail(request, pk):
    news_item = get_object_or_404(News, pk=pk)
    return render(request, 'users/news_detail.html', {'news': news_item})

