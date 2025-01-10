from django.db import models
from CORE.models import Country


# Create your models here.
class UserInfo(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    title = models.CharField(max_length=10, null=True, blank=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50, null=True, blank=True)
    email = models.EmailField()
    phone = models.CharField(max_length=25, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    nationality = models.CharField(max_length=50, null=True, blank=True)
    address = models.TextField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=50, null=True, blank=True)
    postal = models.CharField(max_length=50, null=True, blank=True)
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE)
    website = models.CharField(max_length=50, null=True, blank=True)
    profile_text = models.TextField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_full_name(self):
        return f"{self.title}. {self.first_name} {self.last_name}"

    def __str__(self):
        return f'{self.id} [{self.title}. {self.first_name}]'
