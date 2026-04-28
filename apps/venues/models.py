from django.db import models
from django.core.exceptions import ValidationError


class Venue(models.Model):
    """Venue model for examination halls and rooms"""
    VENUE_TYPES = (
        ('lecture_hall', 'Lecture Hall'),
        ('classroom', 'Classroom'),
        ('laboratory', 'Laboratory'),
        ('auditorium', 'Auditorium'),
        ('multipurpose_hall', 'Multipurpose Hall'),
        ('outdoor', 'Outdoor Space'),
    )
    
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)
    venue_type = models.CharField(max_length=20, choices=VENUE_TYPES, default='lecture_hall')
    building = models.CharField(max_length=100, blank=True)
    floor = models.CharField(max_length=10, blank=True)
    capacity = models.PositiveIntegerField(help_text="Maximum number of students")
    exam_capacity = models.PositiveIntegerField(
        help_text="Maximum students for exams (usually less than capacity for spacing)"
    )
    area_sqm = models.DecimalField(
        max_digits=8, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Area in square meters"
    )
    
    # Facilities
    has_projector = models.BooleanField(default=False)
    has_air_conditioning = models.BooleanField(default=False)
    has_whiteboard = models.BooleanField(default=False)
    has_computers = models.BooleanField(default=False)
    has_power_outlets = models.BooleanField(default=True)
    is_wheelchair_accessible = models.BooleanField(default=False)
    
    # Location details
    campus_location = models.CharField(max_length=100, help_text="e.g., Main Campus, City Campus")
    gps_coordinates = models.CharField(max_length=50, blank=True)
    description = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_available_for_exams = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['building', 'floor', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.code}) - Capacity: {self.exam_capacity}"
    
    def clean(self):
        if self.exam_capacity > self.capacity:
            raise ValidationError("Exam capacity cannot exceed total capacity")
        
        if self.capacity <= 0:
            raise ValidationError("Capacity must be greater than 0")
        
        if self.exam_capacity <= 0:
            raise ValidationError("Exam capacity must be greater than 0")


class VenueImage(models.Model):
    """Venue images for better visualization"""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='venue_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_primary', 'uploaded_at']
    
    def __str__(self):
        return f"{self.venue.name} - {self.caption or 'Image'}"


class VenueBlock(models.Model):
    """Venue block for managing unavailability periods"""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='blocks')
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    reason = models.CharField(max_length=200)
    is_maintenance = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['start_datetime']
    
    def __str__(self):
        return f"{self.venue.name} - {self.reason} ({self.start_datetime} to {self.end_datetime})"
    
    def clean(self):
        if self.start_datetime >= self.end_datetime:
            raise ValidationError("Start time must be before end time")


class VenueRating(models.Model):
    """Venue rating and feedback system"""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE
    )
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rating from 1 (Poor) to 5 (Excellent)"
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['venue', 'user']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.venue.name} - {self.user.username}: {self.rating}/5"


class VenueLayout(models.Model):
    """Venue layout for seating arrangements"""
    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, related_name='layouts')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    layout_image = models.ImageField(
        upload_to='venue_layouts/',
        null=True,
        blank=True,
        help_text="Image showing the seating layout"
    )
    rows = models.PositiveIntegerField(help_text="Number of rows")
    columns = models.PositiveIntegerField(help_text="Number of columns per row")
    spacing_type = models.CharField(
        max_length=20,
        choices=[
            ('standard', 'Standard Spacing'),
            ('wide', 'Wide Spacing'),
            ('social_distancing', 'Social Distancing'),
        ],
        default='standard'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['venue', 'name']
        unique_together = ['venue', 'name']
    
    def __str__(self):
        return f"{self.venue.name} - {self.name} ({self.rows}x{self.columns})"
    
    @property
    def total_seats(self):
        return self.rows * self.columns
    
    def get_seat_position(self, seat_number):
        """Convert seat number to row and column position"""
        if seat_number <= 0 or seat_number > self.total_seats:
            return None
        
        row = (seat_number - 1) // self.columns + 1
        column = (seat_number - 1) % self.columns + 1
        
        return {'row': row, 'column': column}
