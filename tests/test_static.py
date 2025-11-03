"""
Tests for static file serving and frontend functionality
"""
import pytest
from fastapi import status


class TestStaticFiles:
    """Test class for static file serving"""

    def test_static_index_html_accessible(self, client):
        """Test that static/index.html is accessible"""
        response = client.get("/static/index.html")
        assert response.status_code == status.HTTP_200_OK
        assert "text/html" in response.headers.get("content-type", "")
        
        # Check for expected HTML content
        content = response.text
        assert "<title>Mergington High School Activities</title>" in content
        assert "Extracurricular Activities" in content
        assert "Sign Up for an Activity" in content

    def test_static_css_accessible(self, client):
        """Test that static/styles.css is accessible"""
        response = client.get("/static/styles.css")
        assert response.status_code == status.HTTP_200_OK
        assert "text/css" in response.headers.get("content-type", "")
        
        # Check for expected CSS content
        content = response.text
        assert "body" in content
        assert "activity-card" in content

    def test_static_js_accessible(self, client):
        """Test that static/app.js is accessible"""
        response = client.get("/static/app.js")
        assert response.status_code == status.HTTP_200_OK
        
        # Check for expected JavaScript content
        content = response.text
        assert "DOMContentLoaded" in content
        assert "fetchActivities" in content
        assert "unregisterParticipant" in content

    def test_nonexistent_static_file_returns_404(self, client):
        """Test that requesting non-existent static file returns 404"""
        response = client.get("/static/nonexistent.html")
        assert response.status_code == status.HTTP_404_NOT_FOUND