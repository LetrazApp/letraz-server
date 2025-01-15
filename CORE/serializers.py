from rest_framework import serializers
from .models import Country, Waitlist


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'


class WaitlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = Waitlist
        fields = '__all__'
        read_only_fields = ['id', 'waiting_number', 'created_at']
