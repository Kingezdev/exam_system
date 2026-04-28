from django.contrib import admin
from .models import Venue, VenueImage, VenueBlock, VenueRating, VenueLayout


class VenueImageInline(admin.TabularInline):
    model = VenueImage
    extra = 1


class VenueLayoutInline(admin.TabularInline):
    model = VenueLayout
    extra = 1


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'code', 'venue_type', 'building', 'capacity', 
        'exam_capacity', 'campus_location', 'is_active', 'is_available_for_exams'
    )
    list_filter = (
        'venue_type', 'campus_location', 'is_active', 
        'is_available_for_exams', 'has_air_conditioning', 'has_projector'
    )
    search_fields = ('name', 'code', 'building', 'campus_location')
    ordering = ('building', 'name')
    inlines = [VenueImageInline, VenueLayoutInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'venue_type', 'building', 'floor')
        }),
        ('Capacity', {
            'fields': ('capacity', 'exam_capacity', 'area_sqm')
        }),
        ('Facilities', {
            'fields': (
                'has_projector', 'has_air_conditioning', 'has_whiteboard',
                'has_computers', 'has_power_outlets', 'is_wheelchair_accessible'
            )
        }),
        ('Location', {
            'fields': ('campus_location', 'gps_coordinates')
        }),
        ('Status', {
            'fields': ('is_active', 'is_available_for_exams')
        }),
        ('Additional', {
            'fields': ('description',)
        }),
    )


@admin.register(VenueImage)
class VenueImageAdmin(admin.ModelAdmin):
    list_display = ('venue', 'caption', 'is_primary', 'uploaded_at')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('venue__name', 'caption')
    ordering = ('-uploaded_at',)


@admin.register(VenueBlock)
class VenueBlockAdmin(admin.ModelAdmin):
    list_display = ('venue', 'reason', 'start_datetime', 'end_datetime', 'is_maintenance', 'created_by')
    list_filter = ('is_maintenance', 'start_datetime', 'created_by')
    search_fields = ('venue__name', 'reason', 'created_by__username')
    ordering = ('-start_datetime',)


@admin.register(VenueRating)
class VenueRatingAdmin(admin.ModelAdmin):
    list_display = ('venue', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('venue__name', 'user__username')
    ordering = ('-created_at',)


@admin.register(VenueLayout)
class VenueLayoutAdmin(admin.ModelAdmin):
    list_display = ('venue', 'name', 'rows', 'columns', 'spacing_type', 'total_seats', 'is_active')
    list_filter = ('spacing_type', 'is_active', 'created_at')
    search_fields = ('venue__name', 'name')
    ordering = ('venue', 'name')
    
    def total_seats(self, obj):
        return obj.total_seats
    total_seats.short_description = 'Total Seats'
