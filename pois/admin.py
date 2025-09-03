from django.contrib import admin

from pois.models import PointOfInterest

# Register your models here.

@admin.register(PointOfInterest)
class PointOfInterestAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'external_id', 'category', 'average_rating')
    list_filter = ('category',)
    fields = ('id', 'name', 'external_id', 'category', 'longitude', 'latitude', 'ratings', 'average_rating', 'created_at', 'updated_at')
    search_fields = ('id', 'external_id', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('-id',)
