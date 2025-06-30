from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class Spending_Type(models.Model):
    spendings = (
        ('Beach', 'Beaches & Relaxation'),
        ('Sports', 'Adventure & Sports'),
        ('Hiking', 'Hiking & Nature'),
        ('Entertainment', 'Entertainment & Nightlife'),
        ('Culture', 'Culture & History'),
        ('Shopping', 'Shopping & Markets'),
        ('Food', 'Food & Dining'),
        ('Wellness', 'Wellness & Spa'),
    )

    name = models.CharField(max_length=100, choices=spendings, unique=True)

    def __str__(self):
        return self.get_name_display()



class Trip(models.Model):
    trip_types=(
        ('SOLO','Solo'),
        ('FAMILY','Family'),
        ('FRIENDS','Friends'),
        ('PARTNER','Partner'),
    )

    

    
    
    start_date=models.DateField()
    end_date=models.DateField()
    destination=models.TextField(max_length=100)
    trip_type=models.TextField(max_length=20,choices=trip_types)
    spending_types=models.ManyToManyField(Spending_Type)
    plan=models.JSONField(blank=True,null=True)

    def __str__(self):
        return f"{self.destination}"
    
