"""Tests for GH#294: Restart Gateway endpoint."""
import json
import pytest
from unittest.mock import patch, MagicMock

# We need to import the Flask app
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import app from dashboard.py
# Note: This is a simple test that checks the endpoint exists


def test_restart_gateway_endpoint_structure():
    """Test that the endpoint code exists in dashboard.py."""
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard.py')
    
    with open(dashboard_path) as f:
        content = f.read()
    
    # Check that the endpoint is defined
    assert '@bp_gateway.route("/api/gateway/restart"' in content, "Endpoint route not found"
    assert 'def api_gateway_restart()' in content, "Endpoint function not found"
    assert 'openclaw gateway restart' in content, "Restart command not found"
    
    # Check JavaScript functions exist
    assert 'openRestartGatewayModal()' in content, "Modal open function not found"
    assert 'executeGatewayRestart()' in content, "Execute restart function not found"
    
    # Check HTML modal exists
    assert 'restart-gateway-modal' in content, "Modal HTML not found"
    
    # Check Quick Actions section exists
    assert 'sh-quick-actions-wrap' in content, "Quick Actions section not found"


def test_restart_gateway_modal_html_structure():
    """Test that the modal HTML has proper structure."""
    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'dashboard.py')
    
    with open(dashboard_path) as f:
        content = f.read()
    
    # Check modal structure
    assert 'id="restart-gateway-modal"' in content, "Modal ID not found"
    assert 'id="restart-gateway-result"' in content, "Result banner not found"
    assert 'Restart OpenClaw Gateway?' in content, "Modal title not found"
    assert 'openclaw gateway restart' in content, "Restart command description not found"
    
    # Check buttons
    assert 'executeGatewayRestart()' in content, "Execute button not found"
    assert "document.getElementById('restart-gateway-modal').style.display='none'" in content, "Cancel button not found"


if __name__ == '__main__':
    test_restart_gateway_endpoint_structure()
    test_restart_gateway_modal_html_structure()
    print("All tests passed!")
