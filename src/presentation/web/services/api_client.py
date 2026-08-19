"""
API client for Streamlit frontend.
"""
import requests
import json
from typing import Optional, Dict, Any, Tuple, Generator
import streamlit as st


class APIClient:
    """HTTP client for the backend API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    @property
    def headers(self) -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {"Content-Type": "application/json"}
        token = st.session_state.get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        timeout: int = 600,
    ) -> Dict[str, Any]:
        """Make an HTTP request."""
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=timeout,
                )
            elif method == "POST":
                response = requests.post(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=timeout,
                )
            elif method == "PUT":
                response = requests.put(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=timeout,
                )
            elif method == "PATCH":
                response = requests.patch(
                    url,
                    headers=self.headers,
                    json=data,
                    timeout=timeout,
                )
            elif method == "DELETE":
                response = requests.delete(
                    url,
                    headers=self.headers,
                    timeout=timeout,
                )
            else:
                return {"success": False, "error": f"Unsupported method: {method}"}
            
            # Handle different status codes
            if response.status_code == 200:
                try:
                    return {"success": True, "data": response.json()}
                except json.JSONDecodeError:
                    return {"success": False, "error": f"Invalid JSON response: {response.text[:200]}"}
            elif response.status_code == 201:
                try:
                    return {"success": True, "data": response.json()}
                except json.JSONDecodeError:
                    return {"success": True, "data": {"message": "Created"}}
            elif response.status_code == 204:
                return {"success": True, "data": {}}
            elif response.status_code == 400:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Bad request")
                except:
                    error_msg = response.text or "Bad request"
                return {"success": False, "error": error_msg}
            elif response.status_code == 401:
                return {"success": False, "error": "Invalid email or password"}
            elif response.status_code == 404:
                return {"success": False, "error": "Endpoint not found"}
            elif response.status_code == 422:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("detail", "Validation error")
                except:
                    error_msg = "Validation error"
                return {"success": False, "error": error_msg}
            elif response.status_code == 500:
                # Internal server error - log for debugging
                print(f"INTERNAL SERVER ERROR at {endpoint}")
                print(f"Response: {response.text[:500]}")
                return {"success": False, "error": "Internal server error. Check backend logs."}
            else:
                try:
                    error_detail = response.json().get("detail", response.text)
                except:
                    error_detail = response.text or f"HTTP {response.status_code}"
                return {"success": False, "error": error_detail}
                
        except requests.exceptions.ConnectionError:
            return {"success": False, "error": "Cannot connect to API server. Is backend running?"}
        except requests.exceptions.Timeout:
            return {
                      "success": False,
                      "error": "Response taking longer than expected. CPU generation is slow."
                    }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health."""
        return self._request("GET", "/api/health", timeout=5)
    
    # Auth endpoints
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login user."""
        print(f"Attempting login for: {email}")  # Debug
        result = self._request("POST", "/api/auth/login", data={
            "email": email,
            "password": password,
        })
        print(f"Login result: {result}")  # Debug
        return result
    
    def register(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register new user."""
        return self._request("POST", "/api/auth/register", data={
            "username": username,
            "email": email,
            "password": password,
            "full_name": full_name,
        })
    
    def logout(self) -> Dict[str, Any]:
        """Logout user."""
        return self._request("POST", "/api/auth/logout")
    
    def get_current_user(self) -> Dict[str, Any]:
        """Get current user info."""
        return self._request("GET", "/api/auth/me")
    
    def change_password(self, current_password: str, new_password: str) -> Dict[str, Any]:
        """Change password."""
        return self._request("POST", "/api/auth/change-password", data={
            "current_password": current_password,
            "new_password": new_password,
        })
    
    # LLM endpoints
    def list_models(self) -> Dict[str, Any]:
        """List available models."""
        return self._request("GET", "/api/llm/models")
    
    def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **parameters,
    ) -> Dict[str, Any]:
        """Send a chat message."""
        data = {
            "message": message,
            "parameters": {
                             **parameters,
                             "stream": True,
                            },
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        if model:
            data["model"] = model
        if system_prompt:
            data["system_prompt"] = system_prompt
        
        return self._request("POST", "/api/llm/chat", data=data, timeout=None)
    
    def stream_chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        **parameters,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream a chat response."""
        try:
            import sseclient
        except ImportError:
            yield {"type": "error", "message": "sseclient not installed. Run: pip install sseclient-py"}
            return
        
        data = {
            "message": message,
            "parameters": parameters,
        }
        if conversation_id:
            data["conversation_id"] = conversation_id
        if model:
            data["model_name"] = model
        if system_prompt:
            data["system_prompt"] = system_prompt
        
        try:
            response = requests.post(
                f"{self.base_url}/api/llm/chat/stream",
                headers=self.headers,
                json=data,
                stream=True,
                timeout=None,
            )
            
            if response.status_code == 200:
                client = sseclient.SSEClient(response)
                for event in client.events():
                    if event.data:
                        try:
                            yield json.loads(event.data)
                        except json.JSONDecodeError:
                            yield {"type": "raw", "data": event.data}
            else:
                yield {"type": "error", "message": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            yield {"type": "error", "message": str(e)}
    
    # Conversation endpoints
    def list_conversations(
        self,
        skip: int = 0,
        limit: int = 50,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List conversations."""
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status
        return self._request("GET", "/api/conversations", params=params)
    
    def get_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation details."""
        return self._request("GET", f"/api/conversations/{conversation_id}")
    
    def create_conversation(self, title: Optional[str] = None, model: str = "phi3-mini-fast") -> Dict[str, Any]:
        """Create new conversation."""
        return self._request("POST", "/api/conversations", data={
            "title": title,
            "model_name": model,
        })
    
    def delete_conversation(self, conversation_id: str) -> Dict[str, Any]:
        """Delete conversation."""
        return self._request("DELETE", f"/api/conversations/{conversation_id}")
    
    # Image endpoints
    def generate_image(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        model: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        seed: Optional[int] = None,
        **parameters,
    ) -> Dict[str, Any]:
        """Generate an image."""
        data = {
            "prompt": prompt,
            "width": width,
            "height": height,
            "num_images": num_images,
            "parameters": parameters,
        }
        if negative_prompt:
            data["negative_prompt"] = negative_prompt
        if model:
            data["model"] = model
        if seed is not None:
            data["seed"] = seed
        
        return self._request("POST", "/api/images/generate", data=data, timeout=600)
    
    def list_assets(
        self,
        asset_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List assets."""
        params = {"skip": skip, "limit": limit}
        if asset_type:
            params["asset_type"] = asset_type
        return self._request("GET", "/api/images", params=params)
    
    def toggle_favorite_asset(self, asset_id: str) -> Dict[str, Any]:
        """Toggle favorite status."""
        return self._request("PATCH", f"/api/images/{asset_id}/favorite")
    
    def delete_asset(self, asset_id: str) -> Dict[str, Any]:
        """Delete an asset."""
        return self._request("DELETE", f"/api/images/{asset_id}")
    
    # Chart endpoints
    def generate_chart_from_prompt(self, prompt: str) -> Dict[str, Any]:
        """Generate chart from prompt."""
        return self._request("POST", "/api/charts/generate-from-prompt", data={
            "prompt": prompt,
        })
    
    def save_chart(
        self,
        name: str,
        chart_type: str,
        image_bytes: bytes,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Save a chart."""
        import base64
        return self._request("POST", "/api/charts", data={
            "name": name,
            "chart_type": chart_type,
            "image_data": base64.b64encode(image_bytes).decode(),
            "config": config,
        })
    
    # Dashboard endpoints
    def get_dashboard_stats(self, period: str = "30d") -> Dict[str, Any]:
        """Get dashboard statistics."""
        return self._request("GET", "/api/admin/dashboard", params={"period": period})
    
    # API Key endpoints
    def list_api_keys(self) -> Dict[str, Any]:
        """List API keys."""
        return self._request("GET", "/api/admin/api-keys")
    
    def create_api_key(self, name: str, scopes: list, expires_in_days: Optional[int] = None) -> Dict[str, Any]:
        """Create API key."""
        data = {"name": name, "scopes": scopes}
        if expires_in_days:
            data["expires_in_days"] = expires_in_days
        return self._request("POST", "/api/admin/api-keys", data=data)
    
    def revoke_api_key(self, key_id: str) -> Dict[str, Any]:
        """Revoke API key."""
        return self._request("DELETE", f"/api/admin/api-keys/{key_id}")
    
    # Profile endpoints
    def update_profile(self, **kwargs) -> Dict[str, Any]:
        """Update user profile."""
        return self._request("PATCH", "/api/users/me", data=kwargs)
    
    def update_preferences(self, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences."""
        return self._request("PUT", "/api/users/me/preferences", data=preferences)
    
    def delete_account(self) -> Dict[str, Any]:
        """Delete user account."""
        return self._request("DELETE", "/api/users/me")

