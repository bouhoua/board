from django.db import models

# Create your models here.
class Point(models.Model) :
    title = models.CharField(max_length = 100)
    lat = models.FloatField()
    lng = models.FloatField()