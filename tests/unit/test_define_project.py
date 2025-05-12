import pytest
import datetime






def test_define_project_unauthorized(client):
    """Test that unauthorized users can't access the define project page"""
    response = client.get('/define_project')
    assert response.status_code == 302  # Redirect to login
    assert b'You must be logged in as an admin or project manager' in response.data or b'Redirecting' in response.data






def test_define_project_get(auth_client, test_db):
    """Test rendering of the define project form for authorized users"""
    response = auth_client.get('/define_project')
    assert response.status_code == 200
    assert b'Define Project' in response.data
    assert b'Project Name' in response.data
    assert b'Start Date' in response.data
    assert b'End Date' in response.data
    assert b'Project Type' in response.data


import pytest
import datetime

def test_define_project_unauthorized(client):
    """Test that unauthorized users can't access the define project page"""
    response = client.get('/define_project')  # Updated path
    assert response.status_code == 302  # Redirect to login
    assert b'You must be logged in as an admin or project manager' in response.data or b'Redirecting' in response.data

def test_define_project_get(auth_client, test_db):
    """Test rendering of the define project form for authorized users"""
    # Verify session is active
    with auth_client.session_transaction() as sess:
        assert sess['loggedin'] is True
        assert sess['user_type'] == 'pm'
    
    response = auth_client.get('/define_project')  # Updated path
    assert response.status_code == 200
    assert b'Define Project' in response.data
    assert b'Project Name' in response.data
    assert b'Start Date' in response.data
    assert b'End Date' in response.data
    assert b'Project Type' in response.data

