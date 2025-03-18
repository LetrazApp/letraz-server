import pytest
from CORE.serializers import WaitlistSerializer, SkillSerializer
from CORE.models import Waitlist, Skill

@pytest.mark.serializer
class TestWaitlistSerializer:
    def test_valid_data(self):
        data = {
            "email": "test@example.com",
            "referrer": "website"
        }
        serializer = WaitlistSerializer(data=data)
        assert serializer.is_valid()
        
    def test_invalid_email(self):
        data = {
            "email": "invalid-email",
            "referrer": "website"
        }
        serializer = WaitlistSerializer(data=data)
        assert not serializer.is_valid()
        assert "email" in serializer.errors
    
    @pytest.mark.django_db
    def test_create_waitlist(self):
        data = {
            "email": "test@example.com",
            "referrer": "website"
        }
        serializer = WaitlistSerializer(data=data)
        assert serializer.is_valid()
        waitlist = serializer.save()
        assert isinstance(waitlist, Waitlist)
        assert waitlist.email == "test@example.com"
        assert waitlist.referrer == "website"
        assert waitlist.waiting_number == 1

@pytest.mark.serializer
class TestSkillSerializer:
    def test_valid_data(self):
        data = {
            "name": "Python",
            "category": "Programming",
            "preferred": True
        }
        serializer = SkillSerializer(data=data)
        assert serializer.is_valid()
    
    def test_minimal_valid_data(self):
        data = {
            "name": "Python"
        }
        serializer = SkillSerializer(data=data)
        assert serializer.is_valid()
    
    @pytest.mark.django_db
    def test_create_skill(self):
        data = {
            "name": "Python",
            "category": "Programming",
            "preferred": True
        }
        serializer = SkillSerializer(data=data)
        assert serializer.is_valid()
        skill = serializer.save()
        assert isinstance(skill, Skill)
        assert skill.name == "Python"
        assert skill.category == "Programming"
        assert skill.preferred is True 