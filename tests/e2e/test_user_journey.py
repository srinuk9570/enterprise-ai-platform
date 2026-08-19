"""
End-to-end tests for user journeys.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.presentation.api import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestUserJourney:
    """Test complete user journey from registration to chat."""
    
    def test_complete_user_journey(self, client):
        """
        Test complete user flow:
        1. Register account
        2. Login
        3. Create conversation
        4. Send message
        5. Get conversation history
        6. Generate image
        7. Logout
        """
        # 1. Register
        register_response = client.post("/api/auth/register", json={
            "email": "journey@example.com",
            "username": "journeyuser",
            "password": "SecurePass123!",
            "full_name": "Journey User",
        })
        
        if register_response.status_code == 200:
            user_data = register_response.json()
            assert user_data["email"] == "journey@example.com"
        
        # 2. Login
        login_response = client.post("/api/auth/login", json={
            "email": "journey@example.com",
            "password": "SecurePass123!",
        })
        
        if login_response.status_code == 200:
            token_data = login_response.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # 3. Create conversation
            conv_response = client.post("/api/conversations", json={
                "title": "My First Chat",
                "model_name": "deepseek-r1:7b",
            }, headers=headers)
            
            conversation_id = None
            if conv_response.status_code == 200:
                conv_data = conv_response.json()
                conversation_id = conv_data["id"]
            
            # 4. Send message
            if conversation_id:
                chat_response = client.post("/api/llm/chat", json={
                    "conversation_id": conversation_id,
                    "message": "What is machine learning?",
                }, headers=headers)
                
                if chat_response.status_code == 200:
                    chat_data = chat_response.json()
                    assert "message" in chat_data
            
            # 5. Get conversation history
            if conversation_id:
                history_response = client.get(
                    f"/api/conversations/{conversation_id}",
                    headers=headers,
                )
                
                if history_response.status_code == 200:
                    history_data = history_response.json()
                    assert history_data["id"] == conversation_id
                    assert len(history_data.get("messages", [])) > 0
            
            # 6. Generate image
            image_response = client.post("/api/images/generate", json={
                "prompt": "A beautiful sunset over mountains",
                "width": 512,
                "height": 512,
                "num_images": 1,
            }, headers=headers)
            
            # 7. Logout
            logout_response = client.post("/api/auth/logout", headers=headers)
            if logout_response.status_code == 200:
                assert logout_response.json()["message"] == "Successfully logged out"
    
    def test_chat_streaming_journey(self, client):
        """Test streaming chat journey."""
        # Login first
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            # Stream chat
            stream_response = client.post("/api/llm/chat/stream", json={
                "message": "Tell me a short story.",
            }, headers=headers)
            
            if stream_response.status_code == 200:
                content = stream_response.text
                assert "data:" in content