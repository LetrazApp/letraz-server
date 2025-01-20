from django.db import models
from CORE.models import Country
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils.translation import gettext_lazy as _
from nanoid import generate as generate_nanoid


# Create your models here.
class UserManager(BaseUserManager):
    def create_user(self, user_id, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, id=user_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user('superuser__'+generate_nanoid(), email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.CharField(max_length=32, primary_key=True, editable=False,
                          help_text='The unique identifier for the user. Typically provided from the client side while creating the user.')
    title = models.CharField(max_length=10, null=True, blank=True,
                             help_text='The title of the user. This can be Mr., Mrs., Dr., etc. (optional)')
    first_name = models.CharField(max_length=50, help_text='The first name of the user.')
    last_name = models.CharField(max_length=50, null=True, blank=True,
                                 help_text='The last name of the user. (optional)')
    email = models.EmailField(unique=True, help_text='The email of the user. Needs to be unique and a valid email.')
    phone = models.CharField(max_length=25, null=True, blank=True, help_text='The phone number of the user. (optional)')
    dob = models.DateField(null=True, blank=True, help_text='The date of birth of the user. (optional)')
    nationality = models.CharField(max_length=50, null=True, blank=True,
                                   help_text='The nationality of the user. (optional)')
    address = models.TextField(max_length=500, null=True, blank=True,
                               help_text='The address line of the user. Typically includes the apartment or plot number and the locality. (optional)')
    city = models.CharField(max_length=50, null=True, blank=True, help_text='The city the user lives in. (optional)')
    postal = models.CharField(max_length=50, null=True, blank=True, help_text='The postal code of the user. (optional)')
    country = models.ForeignKey(Country, null=True, blank=True, on_delete=models.CASCADE,
                                help_text='The country the user lives in. (optional)')
    website = models.CharField(max_length=50, null=True, blank=True,
                               help_text='The user\'s personal portfolio or blog website. (optional)')
    profile_text = models.TextField(max_length=1000, null=True, blank=True,
                                    help_text='The profile text of the user. This can be a short bio or a summary This would be shows on top of the user\'s resume. (optional)')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, help_text='The timestamp at which the user was created.')
    updated_at = models.DateTimeField(auto_now=True, help_text='The timestamp at which the user was last updated.')

    objects = UserManager()

    USERNAME_FIELD = 'email'

    def get_full_name(self):
        return f"{self.title}. {self.first_name} {self.last_name}"

    def __str__(self):
        return self.email
