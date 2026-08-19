"""
Integration tests for API endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.presentation.api import create_app
from src.presentation.api.dependencies import get_dependencies


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/api/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_register_success(self, client):
        """Test successful registration."""
        response = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "SecurePass123!",
            "full_name": "New User",
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "newuser@example.com"
        assert data["username"] == "newuser"
    
    def test_register_invalid_email(self, client):
        """Test registration with invalid email."""
        response = client.post("/api/auth/register", json={
            "email": "invalid-email",
            "username": "newuser",
            "password": "SecurePass123!",
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "username": "newuser",
            "password": "weak",
        })
        
        assert response.status_code == 400
    
    def test_login_success(self, client, sample_user):
        """Test successful login."""
        # Mock authentication
        with patch("src.presentation.api.routes.auth_routes.get_dependencies") as mock_deps:
            mock_auth_service = AsyncMock()
            mock_auth_service.authenticate.return_value = (sample_user, None)
            
            mock_deps.return_value.auth_service = mock_auth_service
            mock_deps.return_value.jwt_handler.create_token_pair.return_value = {
                "access_token": "mock_access_token",
                "refresh_token": "mock_refresh_token",
                "token_type": "bearer",
                "expires_in": 3600,
            }
            
            response = client.post("/api/auth/login", json={
                "email": "test@example.com",
                "password": "SecurePass123!",
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        with patch("src.presentation.api.routes.auth_routes.get_dependencies") as mock_deps:
            mock_auth_service = AsyncMock()
            mock_auth_service.authenticate.return_value = (None, "Invalid credentials")
            mock_deps.return_value.auth_service = mock_auth_service
            
            response = client.post("/api/auth/login", json={
                "email": "wrong@example.com",
                "password": "WrongPass123!",
            })
            
            assert response.status_code == 401
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        with patch("src.presentation.api.routes.auth_routes.get_dependencies") as mock_deps:
            mock_user_repo = AsyncMock()
            mock_user = Mock()
            mock_user.id = "test-id"
            mock_user.username = "testuser"
            mock_user.email = "test@example.com"
            mock_user.role = "user"
            mock_user_repo.get_by_id.return_value = mock_user
            mock_deps.return_value.user_repository = mock_user_repo
            
            response = client.get("/api/auth/me", headers=auth_headers)
            
            assert response.status_code == 200


class TestLLMEndpoints:
    """Test LLM endpoints."""
    
    def test_list_models(self, client, auth_headers):
        """Test listing available models."""
        with patch("src.presentation.api.routes.llm_routes.get_dependencies") as mock_deps:
            mock_ollama = AsyncMock()
            mock_ollama.list_models.return_value = ["deepseek-r1:7b", "llama3.2:7b"]
            mock_deps.return_value.ollama_client = mock_ollama
            
            response = client.get("/api/llm/models", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["models"]) == 2
    
    def test_chat_unauthorized(self, client):
        """Test chat endpoint without authentication."""
        response = client.post("/api/llm/chat", json={
            "message": "Hello",
        })
        
        assert response.status_code == 401
    
    def test_chat_success(self, client, auth_headers):
        """Test successful chat request."""
        with patch("src.presentation.api.routes.llm_routes.get_dependencies") as mock_deps:
            mock_handler = AsyncMock()
            mock_response = Mock()
            mock_response.content = "AI response"
            mock_response.model_used = "deepseek-r1:7b"
            mock_response.tokens_used = 50
            mock_response.generation_time_ms = 100.0
            mock_response.finish_reason = "stop"
            mock_handler.handle_send_message.return_value = (mock_response, [])
            mock_deps.return_value.conversation_command_handler = mock_handler
            
            response = client.post("/api/llm/chat", json={
                "message": "Hello, AI!",
                "model": "deepseek-r1:7b",
            }, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["message"] == "AI response"
            assert data["model_used"] == "deepseek-r1:7b"


class TestConversationEndpoints:
    """Test conversation endpoints."""
    
    def test_list_conversations(self, client, auth_headers):
        """Test listing conversations."""
        with patch("src.presentation.api.routes.conversation_routes.get_dependencies") as mock_deps:
            mock_handler = AsyncMock()
            mock_handler.get_user_conversations.return_value = ([], 0, [])
            mock_deps.return_value.conversation_query_handler = mock_handler
            
            response = client.get("/api/conversations", headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert "conversations" in data
            assert "total" in data
    
    def test_create_conversation(self, client, auth_headers):
        """Test creating a conversation."""
        with patch("src.presentation.api.routes.conversation_routes.get_dependencies") as mock_deps:
            mock_handler = AsyncMock()
            mock_conv = Mock()
            mock_conv.to_dict.return_value = {
                "id": "conv-123",
                "title": "New Chat",
                "model_name": "deepseek-r1:7b",
            }
            mock_handler.create_conversation.return_value = (mock_conv, [])
            mock_deps.return_value.conversation_command_handler = mock_handler
            
            response = client.post("/api/conversations", json={
                "title": "New Chat",
                "model_name": "deepseek-r1:7b",
            }, headers=auth_headers)
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "New Chat"
    
    def test_delete_conversation(self, client, auth_headers):
        """Test deleting a conversation."""
        with patch("src.presentation.api.routes.conversation_routes.get_dependencies") as mock_deps:
            mock_handler = AsyncMock()
            mock_handler.handle_delete_conversation.return_value = (True, [])
            mock_deps.return_value.conversation_command_handler = mock_handler
            
            response = client.delete("/api/conversations/conv-123", headers=auth_headers)
            
            assert response.status_code == 200