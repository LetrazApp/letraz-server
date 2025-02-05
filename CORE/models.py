import uuid
from django.db import models


class AutoIncrementWaitingNumberField(models.IntegerField):
    def pre_save(self, model_instance, add):
        if add:
            last_instance = model_instance.__class__.objects.order_by('waiting_number').last()
            if last_instance:
                value = last_instance.waiting_number + 1
            else:
                value = 1
            setattr(model_instance, self.attname, value)
        return super().pre_save(model_instance, add)


class Waitlist(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text='The unique identifier for the waitlist entry.'
    )
    email = models.EmailField(unique=True, help_text='The email of the user who joined the waitlist.')
    referrer = models.CharField(max_length=50, default='website',
                                help_text='The referrer of the user who joined the waitlist. Usually the source they have come from.')
    waiting_number = AutoIncrementWaitingNumberField(editable=False,
                                                     help_text='The waiting number of the user who joined the waitlist.')
    created_at = models.DateTimeField(auto_now_add=True,
                                      help_text='The timestamp at which the user joined the waitlist.')

    class Meta:
        db_table = "waitlist"


class Country(models.Model):
    code = models.CharField(max_length=3, primary_key=True, help_text='The ISO 3166-1 alpha-3 code of the country.')
    name = models.CharField(max_length=250, help_text='The name of the country.')

    def __str__(self):
        return f'{self.name} [{self.code}]'


class Skill(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False,
                          help_text='The unique identifier for the experience entry.')
    category = models.CharField(max_length=50, blank=True, null=True,
                                help_text='The category of the skill. (optional)')
    name = models.CharField(max_length=250, help_text='The name of the skill.')
    preferred = models.BooleanField(default=False)
    alias = models.ManyToManyField('Skill', blank=True, related_name='alias_skills')
    created_at = models.DateTimeField(auto_now_add=True, help_text='The date and time the skill entry was created.')
    updated_at = models.DateTimeField(auto_now=True,
                                      help_text='The date and time the skill entry was last updated.')

    class Meta:
        unique_together = ('category', 'name')

    def __str__(self):
        return f'{self.name} [{self.category}]'
