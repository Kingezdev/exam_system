from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg
from django.http import JsonResponse
from django.utils import timezone
from .models import Venue, VenueImage, VenueBlock, VenueRating, VenueLayout
from .forms import VenueForm, VenueImageForm, VenueBlockForm, VenueLayoutForm


@login_required
def venue_list(request):
    """List all venues"""
    venues = Venue.objects.filter(is_active=True).select_related().prefetch_related('ratings')
    
    # Filter by venue type if provided
    venue_type = request.GET.get('type')
    if venue_type:
        venues = venues.filter(venue_type=venue_type)
    
    # Filter by campus location if provided
    campus = request.GET.get('campus')
    if campus:
        venues = venues.filter(campus_location__icontains=campus)
    
    # Filter by capacity range if provided
    min_capacity = request.GET.get('min_capacity')
    max_capacity = request.GET.get('max_capacity')
    if min_capacity:
        venues = venues.filter(exam_capacity__gte=min_capacity)
    if max_capacity:
        venues = venues.filter(exam_capacity__lte=max_capacity)
    
    # Add average rating to each venue
    for venue in venues:
        avg_rating = venue.ratings.aggregate(avg=Avg('rating'))['avg']
        venue.avg_rating = round(avg_rating, 1) if avg_rating else None
    
    return render(request, 'venues/venue_list.html', {
        'venues': venues,
        'venue_types': Venue.VENUE_TYPES,
        'selected_type': venue_type,
        'selected_campus': campus,
        'min_capacity': min_capacity,
        'max_capacity': max_capacity
    })


@login_required
def venue_detail(request, venue_id):
    """View venue details"""
    venue = get_object_or_404(Venue, id=venue_id)
    images = venue.images.all()
    layouts = venue.layouts.filter(is_active=True)
    ratings = venue.ratings.select_related('user').order_by('-created_at')
    upcoming_blocks = venue.blocks.filter(
        start_datetime__gte=timezone.now()
    ).order_by('start_datetime')
    
    # Calculate average rating
    avg_rating = venue.ratings.aggregate(avg=Avg('rating'))['avg']
    
    # Calculate occupied seats (using exam_capacity as the basis)
    occupied_seats = venue.capacity - venue.exam_capacity
    
    context = {
        'venue': venue,
        'images': images,
        'layouts': layouts,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1) if avg_rating else None,
        'occupied_seats': occupied_seats,
        'upcoming_blocks': upcoming_blocks,
    }
    return render(request, 'venues/venue_detail.html', context)


@login_required
def venue_create(request):
    """Create a new venue"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        form = VenueForm(request.POST)
        if form.is_valid():
            venue = form.save()
            messages.success(request, f'Venue "{venue.name}" created successfully!')
            return redirect('venues:venue_detail', venue_id=venue.id)
    else:
        form = VenueForm()
    
    return render(request, 'venues/venue_form.html', {'form': form, 'title': 'Create Venue'})


@login_required
def venue_update(request, venue_id):
    """Update venue details"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    venue = get_object_or_404(Venue, id=venue_id)
    
    if request.method == 'POST':
        form = VenueForm(request.POST, instance=venue)
        if form.is_valid():
            form.save()
            messages.success(request, f'Venue "{venue.name}" updated successfully!')
            return redirect('venues:venue_detail', venue_id=venue.id)
    else:
        form = VenueForm(instance=venue)
    
    return render(request, 'venues/venue_form.html', {
        'form': form,
        'venue': venue,
        'title': 'Update Venue'
    })


@login_required
def upload_venue_image(request, venue_id):
    """Upload venue images"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    venue = get_object_or_404(Venue, id=venue_id)
    
    if request.method == 'POST':
        form = VenueImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.venue = venue
            
            # Set as primary if it's the first image
            if not venue.images.exists():
                image.is_primary = True
            
            image.save()
            messages.success(request, 'Image uploaded successfully!')
            return redirect('venues:venue_detail', venue_id=venue.id)
    else:
        form = VenueImageForm()
    
    # Calculate primary image count
    primary_image_count = venue.images.filter(is_primary=True).count()
    
    return render(request, 'venues/upload_image.html', {
        'form': form,
        'venue': venue,
        'title': 'Upload Venue Image',
        'primary_image_count': primary_image_count
    })


@login_required
def create_venue_block(request, venue_id):
    """Create venue block/unavailability"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    venue = get_object_or_404(Venue, id=venue_id)
    
    if request.method == 'POST':
        form = VenueBlockForm(request.POST)
        if form.is_valid():
            block = form.save(commit=False)
            block.venue = venue
            block.created_by = request.user
            block.save()
            messages.success(request, f'Venue blocked successfully: {block.reason}')
            return redirect('venues:venue_detail', venue_id=venue.id)
    else:
        form = VenueBlockForm()
    
    return render(request, 'venues/block_form.html', {
        'form': form,
        'venue': venue,
        'title': 'Block Venue'
    })


@login_required
def rate_venue(request, venue_id):
    """Rate a venue"""
    venue = get_object_or_404(Venue, id=venue_id)
    
    try:
        rating = VenueRating.objects.get(venue=venue, user=request.user)
    except VenueRating.DoesNotExist:
        rating = None
    
    if request.method == 'POST':
        rating_value = request.POST.get('rating')
        comment = request.POST.get('comment', '')
        
        if rating_value and rating_value.isdigit() and 1 <= int(rating_value) <= 5:
            if rating:
                rating.rating = int(rating_value)
                rating.comment = comment
                rating.save()
                messages.success(request, 'Your rating has been updated!')
            else:
                VenueRating.objects.create(
                    venue=venue,
                    user=request.user,
                    rating=int(rating_value),
                    comment=comment
                )
                messages.success(request, 'Your rating has been submitted!')
        else:
            messages.error(request, 'Please provide a valid rating (1-5).')
        
        return redirect('venues:venue_detail', venue_id=venue.id)
    
    return render(request, 'venues/rate_venue.html', {
        'venue': venue,
        'rating': rating
    })


@login_required
def create_layout(request, venue_id):
    """Create venue layout"""
    if request.user.role not in ['admin', 'exam_officer']:
        messages.error(request, 'Access denied.')
        return redirect('accounts:dashboard')
    
    venue = get_object_or_404(Venue, id=venue_id)
    
    if request.method == 'POST':
        form = VenueLayoutForm(request.POST, request.FILES)
        if form.is_valid():
            layout = form.save(commit=False)
            layout.venue = venue
            layout.save()
            messages.success(request, f'Layout "{layout.name}" created successfully!')
            return redirect('venues:venue_detail', venue_id=venue.id)
    else:
        form = VenueLayoutForm()
    
    # Get active layouts
    active_layouts = venue.layouts.filter(is_active=True)
    
    return render(request, 'venues/layout_form.html', {
        'form': form,
        'venue': venue,
        'title': 'Create Venue Layout',
        'active_layouts': active_layouts
    })


@login_required
def available_venues(request):
    """Find available venues for specific date/time"""
    if request.method == 'GET':
        date = request.GET.get('date')
        start_time = request.GET.get('start_time')
        end_time = request.GET.get('end_time')
        min_capacity = request.GET.get('min_capacity')
        
        venues = Venue.objects.filter(
            is_active=True,
            is_available_for_exams=True
        )
        
        if min_capacity:
            venues = venues.filter(exam_capacity__gte=min_capacity)
        
        # Filter out venues that are blocked during the requested time
        if date and start_time and end_time:
            from django.utils import timezone
            from datetime import datetime
            
            try:
                start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
                end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
                
                # Exclude venues with overlapping blocks
                blocked_venues = VenueBlock.objects.filter(
                    start_datetime__lt=end_datetime,
                    end_datetime__gt=start_datetime
                ).values_list('venue_id', flat=True)
                
                venues = venues.exclude(id__in=blocked_venues)
            except ValueError:
                pass
        
        venue_data = []
        for venue in venues:
            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'code': venue.code,
                'capacity': venue.exam_capacity,
                'building': venue.building,
                'campus_location': venue.campus_location,
            })
        
        return JsonResponse({'venues': venue_data})


@login_required
def availability(request):
    """Check venue availability"""
    venues = Venue.objects.filter(is_active=True).order_by('building', 'name')
    
    # Get filter parameters
    venue_type = request.GET.get('type')
    building = request.GET.get('building')
    date = request.GET.get('date')
    start_time = request.GET.get('start_time')
    end_time = request.GET.get('end_time')
    
    # Apply filters
    if venue_type:
        venues = venues.filter(venue_type=venue_type)
    if building:
        venues = venues.filter(building=building)
    
    # Filter out venues that are blocked during the requested time
    if date and start_time and end_time:
        from django.utils import timezone
        from datetime import datetime
        
        try:
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            # Exclude venues with overlapping blocks
            blocked_venues = VenueBlock.objects.filter(
                start_datetime__lt=end_datetime,
                end_datetime__gt=start_datetime
            ).values_list('venue_id', flat=True)
            
            venues = venues.exclude(id__in=blocked_venues)
        except ValueError:
            pass
    
    context = {
        'venues': venues,
        'venue_types': Venue.VENUE_TYPES,
        'buildings': Venue.objects.values_list('building', flat=True).distinct().order_by('building'),
        'search_performed': bool(date or start_time or end_time),
        'selected_type': venue_type,
        'selected_building': building,
        'selected_date': date,
        'selected_start_time': start_time,
        'selected_end_time': end_time,
    }
    
    return render(request, 'venues/availability.html', context)


@login_required
def layout_list(request):
    """List all venue layouts"""
    layouts = VenueLayout.objects.select_related('venue').order_by('venue__name', 'name')
    
    # Filter by venue if provided
    venue_id = request.GET.get('venue')
    if venue_id:
        layouts = layouts.filter(venue_id=venue_id)
    
    context = {
        'layouts': layouts,
        'venues': Venue.objects.filter(is_active=True).order_by('name'),
        'selected_venue': venue_id,
    }
    
    return render(request, 'venues/layout_list.html', context)


@login_required
def rating_list(request):
    """List all venue ratings"""
    ratings = VenueRating.objects.select_related('venue', 'user').order_by('-created_at')
    
    # Filter by venue if provided
    venue_id = request.GET.get('venue')
    if venue_id:
        ratings = ratings.filter(venue_id=venue_id)
    
    # Filter by rating if provided
    rating_filter = request.GET.get('rating')
    if rating_filter:
        ratings = ratings.filter(rating=rating_filter)
    
    context = {
        'ratings': ratings,
        'venues': Venue.objects.filter(is_active=True).order_by('name'),
        'selected_venue': venue_id,
        'selected_rating': rating_filter,
    }
    
    return render(request, 'venues/rating_list.html', context)


@login_required
def block_list(request):
    """List all venue blocks"""
    blocks = VenueBlock.objects.select_related('venue', 'created_by').order_by('-created_at')
    
    # Filter by venue if provided
    venue_id = request.GET.get('venue')
    if venue_id:
        blocks = blocks.filter(venue_id=venue_id)
    
    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        blocks = blocks.filter(end_datetime__gt=timezone.now())
    elif status_filter == 'expired':
        blocks = blocks.filter(end_datetime__lte=timezone.now())
    
    context = {
        'blocks': blocks,
        'venues': Venue.objects.filter(is_active=True).order_by('name'),
        'selected_venue': venue_id,
        'selected_status': status_filter,
    }
    
    return render(request, 'venues/block_list.html', context)
