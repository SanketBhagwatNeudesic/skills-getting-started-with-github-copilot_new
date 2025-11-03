"""
Tests for the FastAPI application endpoints
"""
import pytest
from fastapi import status
from src.app import activities


class TestActivitiesEndpoints:
    """Test class for activities-related endpoints"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
        assert "/static/index.html" in response.headers["location"]

    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all available activities"""
        response = client.get("/activities")
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that each activity has required fields
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that GET /activities contains expected default activities"""
        response = client.get("/activities")
        data = response.json()
        
        # Check for some expected activities
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data

    def test_signup_for_valid_activity_success(self, client):
        """Test successful signup for a valid activity"""
        # First, get current participants count
        response = client.get("/activities")
        initial_data = response.json()
        initial_count = len(initial_data["Chess Club"]["participants"])
        
        # Sign up for Chess Club
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
        
        # Verify the participant was added
        response = client.get("/activities")
        updated_data = response.json()
        assert len(updated_data["Chess Club"]["participants"]) == initial_count + 1
        assert "test@mergington.edu" in updated_data["Chess Club"]["participants"]

    def test_signup_for_nonexistent_activity_fails(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]

    def test_signup_duplicate_email_fails(self, client):
        """Test that signing up with same email twice fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Second signup with same email should fail
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "already signed up" in data["detail"]

    def test_unregister_from_activity_success(self, client):
        """Test successful unregistration from an activity"""
        email = "unregister@mergington.edu"
        
        # First sign up
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
        
        # Then unregister
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "Successfully removed" in data["message"]
        assert email in data["message"]
        
        # Verify the participant was removed
        response = client.get("/activities")
        updated_data = response.json()
        assert email not in updated_data["Chess Club"]["participants"]

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Test unregistration from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "Activity not found" in data["detail"]

    def test_unregister_non_participant_fails(self, client):
        """Test unregistering a non-participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "not signed up" in data["detail"]

    def test_activity_capacity_limit(self, client):
        """Test that activities respect capacity limits"""
        # Create a small test by modifying an activity's capacity temporarily
        original_capacity = activities["Chess Club"]["max_participants"]
        original_participants = activities["Chess Club"]["participants"].copy()
        
        try:
            # Set capacity to current participants + 1
            activities["Chess Club"]["max_participants"] = len(original_participants) + 1
            
            # This signup should succeed (within capacity)
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": "capacity1@mergington.edu"}
            )
            assert response.status_code == status.HTTP_200_OK
            
            # This signup should fail (over capacity)
            response = client.post(
                "/activities/Chess Club/signup",
                params={"email": "capacity2@mergington.edu"}
            )
            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "full" in data["detail"]
            
        finally:
            # Restore original state
            activities["Chess Club"]["max_participants"] = original_capacity
            activities["Chess Club"]["participants"] = original_participants


class TestDataIntegrity:
    """Test class for data integrity and edge cases"""

    def test_activities_have_valid_structure(self, client):
        """Test that all activities have the required structure"""
        response = client.get("/activities")
        data = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in data.items():
            assert isinstance(activity_name, str)
            assert len(activity_name) > 0
            
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in activity '{activity_name}'"
            
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            assert activity_data["max_participants"] > 0

    def test_email_validation_in_signup(self, client):
        """Test email parameter handling in signup"""
        # Test with missing email parameter
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_url_encoding_in_activity_names(self, client):
        """Test that activity names with spaces are properly handled"""
        # Test with URL-encoded activity name
        response = client.post(
            "/activities/Chess%20Club/signup",
            params={"email": "urlencoded@mergington.edu"}
        )
        assert response.status_code == status.HTTP_200_OK