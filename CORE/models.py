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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    referrer = models.CharField(max_length=50, default='website')
    waiting_number = AutoIncrementWaitingNumberField(editable=False)
    created_at = models.DateTimeField(auto_now_add=True)


class Country(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=250)