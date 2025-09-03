from django.contrib.postgres.fields import ArrayField
from django.db import models

# Create your models here.

class PointOfInterest(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255, db_index=True)
    longitude = models.DecimalField(max_digits=19, decimal_places=8)
    latitude = models.DecimalField(max_digits=19, decimal_places=8)
    ratings = ArrayField(base_field=models.PositiveSmallIntegerField(), default=list, blank=True)
    average_rating = models.DecimalField(max_digits=2, decimal_places=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name