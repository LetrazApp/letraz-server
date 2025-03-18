import pytest
from PROFILE.serializers import UserSerializer
from PROFILE.models import User
from CORE.models import Country

@pytest.mark.serializer
class TestUserSerializer:
    @pytest.mark.django_db
    def test_serialize_user(self, user):
        """Test serializing a user object"""
        serializer = UserSerializer(user)
        data = serializer.data
        
        assert data['id'] == user.id
        assert data['email'] == user.email
        assert data['first_name'] == user.first_name
        assert data['last_name'] == user.last_name
    
    @pytest.mark.django_db
    def test_deserialize_valid_user_data(self, country):
        """Test deserializing valid user data"""
        data = {
            'id': 'user_test123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '+1234567890',
            'country': country.code
        }
        
        serializer = UserSerializer(data=data)
        assert serializer.is_valid()
        
        user = serializer.save()
        assert user.id == 'user_test123'
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.phone == '+1234567890'
        assert user.country.code == country.code
    
    @pytest.mark.django_db
    def test_deserialize_invalid_user_data(self):
        """Test deserializing invalid user data"""
        # Missing required fields
        data = {
            'email': 'invalid-email',  # Invalid email format
            'first_name': ''  # Empty first name
        }
        
        serializer = UserSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors
        assert 'id' in serializer.errors  # Missing required field
    
    @pytest.mark.django_db
    def test_update_user(self, user, country):
        """Test updating a user through the serializer"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'country': country.code
        }
        
        serializer = UserSerializer(user, data=data, partial=True)
        assert serializer.is_valid()
        
        updated_user = serializer.save()
        assert updated_user.first_name == 'Updated'
        assert updated_user.last_name == 'Name'
        assert updated_user.country.code == country.code 