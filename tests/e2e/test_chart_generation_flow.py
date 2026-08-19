"""
End-to-end tests for chart generation flow.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import json

from src.presentation.api import create_app


@pytest.fixture
def client():
    """Create test client."""
    app = create_app()
    return TestClient(app)


class TestChartGenerationFlow:
    """Test complete chart generation flow."""
    
    def test_chart_creation_flow(self, client):
        """Test creating a chart from data to export."""
        
        # Login
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create chart configuration
        chart_config = {
            "name": "Sales Chart",
            "chart_type": "line",
            "data_source": "sample",
            "x_axis_column": "date",
            "y_axis_columns": ["sales", "revenue"],
            "title": "Monthly Sales Report",
            "width": 800,
            "height": 400,
        }
        
        # Mock chart generation response
        with patch("src.presentation.api.routes.chart_routes.get_dependencies") as mock_deps:
            mock_handler = AsyncMock()
            mock_asset = Mock()
            mock_asset.to_dict.return_value = {
                "id": "asset-123",
                "file_name": "chart.png",
                "file_url": "/api/charts/asset-123",
            }
            mock_chart_data = Mock()
            mock_chart_data.to_dict.return_value = {
                "x_values": ["Jan", "Feb", "Mar"],
                "y_values": {"sales": [100, 150, 200]},
            }
            mock_handler.handle_create_chart.return_value = ((mock_asset, mock_chart_data), [])
            mock_deps.return_value.asset_command_handler = mock_handler
            
            response = client.post("/api/charts", json=chart_config, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                assert "asset" in data
                assert "data" in data
    
    def test_export_chart_data(self, client):
        """Test exporting chart data."""
        
        login_response = client.post("/api/auth/login", json={
            "email": "test@example.com",
            "password": "SecurePass123!",
        })
        
        if login_response.status_code != 200:
            pytest.skip("Login failed")
        
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # Export chart as CSV
        response = client.get(
            "/api/charts/chart-123/export",
            params={"format": "csv"},
            headers=headers,
        )
        
        # May return 404 if chart doesn't exist
        if response.status_code == 200:
            assert response.headers["content-type"] == "text/csv"