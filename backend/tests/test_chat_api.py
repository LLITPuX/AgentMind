"""
Tests for chat API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import os

# Mock OpenAI before importing the app
os.environ["OPENAI_API_KEY"] = "test-key"

from src.main import app

client = TestClient(app)

class TestChatAPI:
    """Test cases for chat API endpoints."""
    
    def test_chat_endpoint_success(self):
        """Test successful chat request."""
        # Mock OpenAI response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello! I'm AgentMind, your AI assistant."
        mock_response.model = "gpt-4o-mini"
        
        with patch('openai.ChatCompletion.create', return_value=mock_response):
            response = client.post("/api/chat", json={
                "message": "Hello, who are you?",
                "messages": []
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert "timestamp" in data
            assert "model_used" in data
            assert data["response"] == "Hello! I'm AgentMind, your AI assistant."
            assert data["model_used"] == "gpt-4o-mini"
    
    def test_chat_endpoint_with_history(self):
        """Test chat request with conversation history."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "I understand you're working on a project."
        mock_response.model = "gpt-4o-mini"
        
        with patch('openai.ChatCompletion.create', return_value=mock_response):
            response = client.post("/api/chat", json={
                "message": "What do you know about me?",
                "messages": [
                    {"role": "user", "content": "I'm working on a project"},
                    {"role": "assistant", "content": "That's great! What kind of project?"}
                ]
            })
            
            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert data["response"] == "I understand you're working on a project."
    
    def test_chat_endpoint_missing_api_key(self):
        """Test chat request with missing OpenAI API key."""
        with patch.dict(os.environ, {}, clear=True):
            # Re-import to get fresh app without API key
            from src.main import app
            test_client = TestClient(app)
            
            response = test_client.post("/api/chat", json={
                "message": "Hello",
                "messages": []
            })
            
            assert response.status_code == 401
    
    def test_chat_endpoint_rate_limit(self):
        """Test chat request with rate limit error."""
        from openai.error import RateLimitError
        
        with patch('openai.ChatCompletion.create', side_effect=RateLimitError("Rate limit exceeded")):
            response = client.post("/api/chat", json={
                "message": "Hello",
                "messages": []
            })
            
            assert response.status_code == 429
            data = response.json()
            assert "rate limit" in data["detail"].lower()
    
    def test_chat_status_endpoint(self):
        """Test chat status endpoint."""
        response = client.get("/api/chat/status")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "openai_configured" in data
        assert "timestamp" in data
        assert "available_models" in data
        assert data["openai_configured"] == True
        assert "gpt-4o-mini" in data["available_models"]
    
    def test_chat_request_validation(self):
        """Test chat request validation."""
        # Missing message
        response = client.post("/api/chat", json={
            "messages": []
        })
        assert response.status_code == 422
        
        # Empty message
        response = client.post("/api/chat", json={
            "message": "",
            "messages": []
        })
        assert response.status_code == 422
