import pytest
from django.db import IntegrityError
from PROFILE.models import User
from CORE.models import Country

@pytest.mark.model
class TestUserModel:
    @pytest.mark.django_db
    def test_create_user(self):
        user = User.objects.create(
            id="user_test123",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        assert user.id == "user_test123"
        assert user.email == "test@example.com"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.is_active is True  # Default value
        assert user.is_staff is False  # Default value
    
    @pytest.mark.django_db
    def test_email_uniqueness(self):
        User.objects.create(
            id="user_test123",
            email="duplicate@example.com",
            first_name="Test"
        )
        with pytest.raises(IntegrityError):
            User.objects.create(
                id="user_test456",
                email="duplicate@example.com",
                first_name="Another"
            )
    
    @pytest.mark.django_db
    def test_get_full_name(self):
        user = User.objects.create(
            id="user_test123",
            email="test@example.com",
            title="Mr",
            first_name="Test",
            last_name="User"
        )
        assert user.get_full_name() == "Mr. Test User"
    
    @pytest.mark.django_db
    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="password123"
        )
        assert user.is_staff is True
        assert user.is_superuser is True
        assert user.email == "admin@example.com"
        
    @pytest.mark.django_db
    def test_user_with_country(self, country):
        user = User.objects.create(
            id="user_test123",
            email="test@example.com",
            first_name="Test",
            country=country
        )
        assert user.country.code == "USA"
        assert user.country.name == "United States of America" 