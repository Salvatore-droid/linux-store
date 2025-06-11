from django.db import models
from django.contrib.auth.models import User

class InstalledApp(models.Model):
    STATUS_CHOICES = [
        ('up_to_date', 'Up to date'),
        ('update_available', 'Update available'),
        ('not_installed', 'Not installed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    app_id = models.CharField(max_length=255)  # Removed unique=True
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=100)
    size = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='up_to_date')
    icon = models.CharField(max_length=50, default='cube')
    icon_color = models.CharField(max_length=50, default='indigo')
    install_date = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-install_date']
        unique_together = ('user', 'app_id')  # Added composite unique constraint

    def __str__(self):
        return f"{self.name} ({self.version})"