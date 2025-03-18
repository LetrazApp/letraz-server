import pytest
from django.db import IntegrityError
from CORE.models import Waitlist, Skill, Country

@pytest.mark.model
class TestWaitlistModel:
    @pytest.mark.django_db
    def test_create_waitlist_entry(self):
        waitlist = Waitlist.objects.create(email="test@example.com", referrer="test")
        assert waitlist.email == "test@example.com"
        assert waitlist.referrer == "test"
        assert waitlist.waiting_number == 1  # Should be first entry

    @pytest.mark.django_db
    def test_waiting_number_auto_increments(self):
        waitlist1 = Waitlist.objects.create(email="test1@example.com")
        waitlist2 = Waitlist.objects.create(email="test2@example.com")
        assert waitlist1.waiting_number == 1
        assert waitlist2.waiting_number == 2

    @pytest.mark.django_db
    def test_email_uniqueness(self):
        Waitlist.objects.create(email="duplicate@example.com")
        with pytest.raises(IntegrityError):
            Waitlist.objects.create(email="duplicate@example.com")

@pytest.mark.model
class TestSkillModel:
    @pytest.mark.django_db
    def test_create_skill(self):
        skill = Skill.objects.create(name="Python", category="Programming")
        assert skill.name == "Python"
        assert skill.category == "Programming"
        assert skill.preferred is False  # Default value

    @pytest.mark.django_db
    def test_skill_to_string(self):
        skill = Skill.objects.create(name="Python", category="Programming")
        assert str(skill) == "Python [Programming]"

@pytest.mark.model
class TestCountryModel:
    @pytest.mark.django_db
    def test_create_country(self):
        country = Country.objects.create(code="USA", name="United States of America")
        assert country.code == "USA"
        assert country.name == "United States of America"

    @pytest.mark.django_db
    def test_country_to_string(self):
        country = Country.objects.create(code="USA", name="United States of America")
        assert str(country) == "United States of America [USA]" 