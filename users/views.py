from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm, PhotographerProfileForm, PhotoUploadForm, BookingRequestForm, ClientProfileForm, SupportRequestForm
from .models import PhotographerProfile, Photo, News, BookingRequest, Favorite, ClientProfile, PhotoLike, SupportRequest, ProfileView, SPECIALIZATION_CHOICES
import random
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q, Count, Exists, OuterRef
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.forms import PasswordChangeForm
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages


def home(request):
    one_week_ago = timezone.now() - timedelta(days=7)
    
    best_photos = Photo.objects.annotate(
        recent_likes_count=Count('likes', filter=Q(likes__created_at__gte=one_week_ago))
    ).filter(recent_likes_count__gt=0).order_by('-recent_likes_count')[:6]
    
    if not best_photos:
        all_photos = list(Photo.objects.all())
        best_photos = random.sample(all_photos, min(len(all_photos), 6))
    
    specializations = SPECIALIZATION_CHOICES
    
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
            
            # Check if photographer
            if form.cleaned_data['is_photographer']:
                PhotographerProfile.objects.create(
                    user=user, 
                    short_intro="Начинающий фотограф", 
                    bio="Расскажите о себе..."
                )
            else:
                # Create ClientProfile
                ClientProfile.objects.create(user=user)
            
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'users/register.html', {'form': form})


@login_required
def dashboard(request):
    # Check if user is photographer
    try:
        profile = request.user.photographerprofile
        is_photographer = True
        client_profile = None
    except PhotographerProfile.DoesNotExist:
        profile = None
        is_photographer = False
        # Get or create ClientProfile
        client_profile, created = ClientProfile.objects.get_or_create(user=request.user)

    password_form = PasswordChangeForm(request.user)
    
    # Forms for photographer
    p_form = None
    photo_form = None
    photos = []
    received_active_bookings = []
    received_completed_bookings = []
    
    # Forms for client
    client_form = None
    
    # Support form and data
    support_form = SupportRequestForm()
    my_support_requests = SupportRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Admin data
    admin_support_requests = []
    admin_new_requests_count = 0
    if request.user.is_superuser:
        # Show ONLY new requests as per requirement "Resolved automatically deletes" (from view)
        admin_support_requests = SupportRequest.objects.filter(status='new').order_by('-created_at')
        admin_new_requests_count = admin_support_requests.count()

    if is_photographer:
        p_form = PhotographerProfileForm(instance=profile)
        photo_form = PhotoUploadForm()
        photos = profile.photos.all().order_by('-uploaded_at')
        all_received = BookingRequest.objects.filter(photographer=profile, is_deleted_by_photographer=False).order_by('-created_at')
        received_active_bookings = all_received.exclude(status='completed')
        received_completed_bookings = all_received.filter(status='completed')
    else:
        client_form = ClientProfileForm(instance=client_profile)

    # Common data
    all_sent = BookingRequest.objects.filter(client=request.user, is_deleted_by_client=False).order_by('-created_at')
    sent_active_bookings = all_sent.exclude(status='completed')
    sent_completed_bookings = all_sent.filter(status='completed')
    
    favorites = Favorite.objects.filter(user=request.user)

    if request.method == 'POST':
        # Handle password change
        if 'change_password' in request.POST:
            password_form = PasswordChangeForm(request.user, request.POST)
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Important!
                messages.success(request, 'Ваш пароль был успешно обновлен!')
                return redirect('dashboard')
            else:
                messages.error(request, 'Пожалуйста, исправьте ошибки ниже.')
        
        # Handle settings update (notifications, etc.)
        elif 'update_settings' in request.POST:
             messages.success(request, 'Настройки сохранены!')
             return redirect('dashboard')
             
        # Handle contact form in help section
        elif 'send_question' in request.POST:
            support_form = SupportRequestForm(request.POST)
            if support_form.is_valid():
                support_request = support_form.save(commit=False)
                support_request.user = request.user
                support_request.save()
                messages.success(request, 'Ваш вопрос отправлен в поддержку. Мы ответим в ближайшее время.')
                return redirect('dashboard')
            else:
                messages.error(request, 'Пожалуйста, заполните поле сообщения.')

        # Handle Admin Reply
        elif 'admin_reply' in request.POST and request.user.is_superuser:
            request_id = request.POST.get('request_id')
            admin_response = request.POST.get('admin_response')
            if request_id and admin_response:
                try:
                    support_request = SupportRequest.objects.get(id=request_id)
                    support_request.admin_response = admin_response
                    support_request.status = 'resolved'
                    support_request.save()
                    messages.success(request, f'Ответ пользователю {support_request.user.username} отправлен. Обращение обработано.')
                except SupportRequest.DoesNotExist:
                    messages.error(request, 'Обращение не найдено.')
            else:
                messages.error(request, 'Невозможно отправить пустой ответ.')
            return redirect('dashboard')

        # Handle Admin Delete Request
        elif 'delete_request' in request.POST:
            request_id = request.POST.get('request_id')
            if request_id:
                try:
                    support_request = SupportRequest.objects.get(id=request_id)
                    # Allow deletion if superuser OR (owner of request AND status is resolved)
                    if request.user.is_superuser or (support_request.user == request.user and support_request.status == 'resolved'):
                        support_request.delete()
                        messages.success(request, 'Обращение удалено.')
                    else:
                        messages.error(request, 'У вас нет прав для удаления этого обращения.')
                except SupportRequest.DoesNotExist:
                    messages.error(request, 'Обращение не найдено.')
            return redirect('dashboard')

        # Handle Account Deletion
        elif 'delete_account' in request.POST:
            user = request.user
    
            user.delete()
            logout(request)
            messages.success(request, 'Ваш аккаунт был успешно удален.')
            return redirect('home')

        # Handle Booking Status Update
        elif 'update_booking_status' in request.POST:
            booking_id = request.POST.get('booking_id')
            new_status = request.POST.get('status')
            booking = get_object_or_404(BookingRequest, id=booking_id, photographer=profile)
            booking.status = new_status
            booking.save()
            messages.success(request, 'Статус заявки обновлен.')
            return redirect('dashboard')
        
        # Handle Booking Cancellation
        elif 'cancel_booking' in request.POST:
            booking_id = request.POST.get('booking_id')
            # Check if user is client OR photographer involved in this booking
            try:
                if is_photographer:
                    booking = BookingRequest.objects.get(id=booking_id, photographer=profile)
                    
                    # If status is completed or cancelled -> Soft delete for photographer
                    if booking.status == 'completed' or booking.status == 'cancelled':
                         booking.is_deleted_by_photographer = True
                         booking.save()
                         
                         # Check if both deleted, then actually delete
                         if booking.is_deleted_by_client and booking.is_deleted_by_photographer:
                             booking.delete()
                             
                         messages.success(request, 'Заявка удалена из вашего списка.')
                         return redirect('dashboard')
                         
                    # If active -> Set status to cancelled
                    if booking.status != 'cancelled' and booking.status != 'completed':
                        booking.status = 'cancelled'
                        booking.save()
                        messages.success(request, 'Заявка отменена. Клиент получит уведомление.')
                        return redirect('dashboard')
                        
                else:
                    booking = BookingRequest.objects.get(id=booking_id, client=request.user)
                    
                    # If status is completed or cancelled -> Soft delete for client
                    if booking.status == 'completed' or booking.status == 'cancelled':
                         booking.is_deleted_by_client = True
                         booking.save()
                         
                         # Check if both deleted, then actually delete
                         if booking.is_deleted_by_client and booking.is_deleted_by_photographer:
                             booking.delete()
                             
                         messages.success(request, 'Заявка удалена из вашего списка.')
                         return redirect('dashboard')
                    
                    # For active client bookings, we can default to delete or cancel?
                    # User said previously: "Сейчас после отмены... давай она будет автоматически удаляться"
                    # But now we have soft delete.
                    # If client cancels active booking:
                    # Option 1: Just delete (hard delete) - easiest for "I don't want this anymore"
                    # Option 2: Set status to cancelled?
                    # Let's stick to previous logic: Delete. But now we have flags.
                    # If we hard delete, it disappears for photographer too.
                    # Maybe better to set status=cancelled AND soft delete for client?
                    # But the requirement was "automcatically delete".
                    # Let's keep hard delete for active client cancellation for now as per previous instruction,
                    # UNLESS it's completed/cancelled which we handled above.
                    
                    pass # Go to default delete below

            except BookingRequest.DoesNotExist:
                # Fallback: maybe photographer acting as client? 
                # Or just general check
                booking = get_object_or_404(BookingRequest, Q(id=booking_id) & (Q(client=request.user) | Q(photographer__user=request.user)))
            
            # Default action for fallback (hard delete)
            booking.delete()
            messages.success(request, 'Заявка удалена.')
            return redirect('dashboard')

        if is_photographer:
            # Handle profile update
            if 'update_profile' in request.POST:
                p_form = PhotographerProfileForm(request.POST, request.FILES, instance=profile)
                if p_form.is_valid():
                    p_form.save()
                    messages.success(request, 'Профиль обновлен.')
                    return redirect('dashboard')
            
            # Handle photo upload
            elif 'upload_photo' in request.POST:
                photo_form = PhotoUploadForm(request.POST, request.FILES)
                if photo_form.is_valid():
                    images = request.FILES.getlist('image')
                    category = photo_form.cleaned_data['category']
                    for img in images:
                        Photo.objects.create(photographer=profile, image=img, category=category)
                    
                    count = len(images)
                    if count > 0:
                        messages.success(request, f'Добавлено фото: {count} шт.')
                    else:
                        messages.warning(request, 'Не выбрано ни одного фото.')
                        
                    return redirect('dashboard')
        else:
            # Handle client profile update
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
        'received_bookings': received_active_bookings, # Backward compatibility if needed, but we'll use new names in template
        'received_active_bookings': received_active_bookings,
        'received_completed_bookings': received_completed_bookings,
        'sent_bookings': sent_active_bookings, # Backward compatibility
        'sent_active_bookings': sent_active_bookings,
        'sent_completed_bookings': sent_completed_bookings,
        'favorites': favorites,
        'client_form': client_form,
        'client_profile': client_profile,
        'support_form': support_form,
        'my_support_requests': my_support_requests,
        'admin_support_requests': admin_support_requests,
        'admin_new_requests_count': admin_new_requests_count,
    })


def specialists(request):
    photographers = PhotographerProfile.objects.all()

    # Filtering
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

    # Annotate favorites
    if request.user.is_authenticated:
        favorite_ids = Favorite.objects.filter(user=request.user).values_list('photographer_id', flat=True)
        for p in photographers:
            p.is_favorite = p.id in favorite_ids

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(photographers, 15)
    
    try:
        photographers_page = paginator.page(page)
    except PageNotAnInteger:
        photographers_page = paginator.page(1)
    except EmptyPage:
        photographers_page = paginator.page(paginator.num_pages)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render_to_string('users/specialists_list.html',
                                {'photographers': photographers_page, 'user': request.user}, request=request)
        return JsonResponse({'html': html})

    return render(request, 'users/specialists.html', {'photographers': photographers_page})


def photographer_detail(request, pk):
    photographer = get_object_or_404(PhotographerProfile, pk=pk)
    
    # Increment views (Unique per user/session)
    if request.user.is_authenticated:
        # Check if user is NOT the photographer themselves
        if request.user != photographer.user:
            # Check if user already viewed
            if not ProfileView.objects.filter(photographer=photographer, user=request.user).exists():
                ProfileView.objects.create(photographer=photographer, user=request.user)
                photographer.views_count += 1
                photographer.save(update_fields=['views_count'])
    else:
        # Check session for anonymous users
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        
        if session_key and not ProfileView.objects.filter(photographer=photographer, session_key=session_key).exists():
             ProfileView.objects.create(
                 photographer=photographer, 
                 session_key=session_key,
                 ip_address=request.META.get('REMOTE_ADDR')
             )
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

    # Get photos with like status
    photos = photographer.photos.all().order_by('-uploaded_at')
    
    # Get distinct categories used by this photographer
    used_categories = set(photos.values_list('category', flat=True))
    
    # Filter specialization choices
    active_specializations = [
        (code, name) for code, name in SPECIALIZATION_CHOICES 
        if code in used_categories
    ]
    
    if request.user.is_authenticated:
        photos = photos.annotate(
            is_liked=Exists(PhotoLike.objects.filter(photo=OuterRef('pk'), user=request.user))
        )

    return render(request, 'users/photographer_detail.html', {
        'photographer': photographer,
        'booking_form': form,
        'is_favorite': is_favorite,
        'photos': photos,
        'specialization_choices': active_specializations
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
def toggle_photo_like(request, pk):
    if request.method == 'POST':
        photo = get_object_or_404(Photo, pk=pk)
        
        # Prevent self-liking
        if photo.photographer.user == request.user:
            return JsonResponse({'status': 'error', 'message': 'Нельзя лайкать свои фотографии'}, status=403)
            
        like, created = PhotoLike.objects.get_or_create(user=request.user, photo=photo)
        
        if not created:
            like.delete()
            is_liked = False
        else:
            is_liked = True
            
        return JsonResponse({
            'status': 'ok', 
            'is_liked': is_liked,
            'likes_count': photo.likes.count()
        })
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def delete_profile_image(request):
    if request.method == 'POST':
        try:
            # Try photographer profile first
            try:
                profile = request.user.photographerprofile
            except PhotographerProfile.DoesNotExist:
                # Try client profile
                try:
                    profile = request.user.clientprofile
                except ClientProfile.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': 'Profile not found'}, status=404)

            if profile.profile_image:
                profile.profile_image.delete(save=False) # Delete file
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

