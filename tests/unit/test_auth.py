import pytest
from flask import Flask, session
from app import app
from utils.db import get_db_connection
from werkzeug.security import generate_password_hash

# @pytest.fixture
# def client():
#     app.config['TESTING'] = True
#     app.config['WTF_CSRF_ENABLED'] = False
#     with app.test_client() as client:
#         yield client

# @pytest.fixture
# def test_db():
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Create test user
#     hashed_password = generate_password_hash('test123')
#     cursor.execute('''
#         INSERT INTO users (username, password, email, user_type, first_login)
#         VALUES (%s, %s, %s, %s, %s)
#     ''', ('testuser', hashed_password, 'test@example.com', 'team_member', 0))
#     conn.commit()
    
#     yield cursor
    
#     # Clean up
#     cursor.execute('DELETE FROM users WHERE username = %s', ('testuser',))
#     conn.commit()
#     cursor.close()
#     conn.close()

def test_login_success(client, test_db):
    """Test successful login"""
    response = client.post('/login', data={
        'username': 'testpm',
        'password': 'test123',
        'user_type': 'pm'
    }, follow_redirects=True)
    
    # Check response
    assert response.status_code == 200
    
    # Check session
    with client.session_transaction() as sess:
        assert sess.get('loggedin') == True
        assert sess.get('username') == 'testpm'
        assert sess.get('user_type') == 'pm'

def test_login_invalid_credentials(client, test_db):
    """Test login with invalid credentials"""
    # The route should match how your blueprint is registered
    response = client.post('/login', data={
        'username': 'testpm',
        'password': 'wrongpassword',
        'user_type': 'pm'  
    }, follow_redirects=True)
    
    assert response.status_code == 200  # First check that the route exists
    # The test will print the response data on failure to help debugging
    if b'Incorrect username/password!' not in response.data:
        print("Response content:", response.data)
    assert b'Incorrect username/password!' in response.data




def test_login_invalid_user(client, test_db):
    """Test login with non-existent user"""
    response = client.post('/login', data={
        'username': 'nonexistent',
        'password': 'test123',
        'user_type': 'pm'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Incorrect username/password!' in response.data

def test_login_missing_fields(client, test_db):
    """Test login with missing required fields"""
    response = client.post('/login', data={
        'username': 'testpm'
        # Missing password and user_type
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Please fill out all fields' in response.data

def test_logout(client, test_db):
    """Test logout functionality"""
    # First login
    client.post('/login', data={
        'username': 'testpm',
        'password': 'test123',
        'user_type': 'pm'
    })
    
    # Then logout
    response = client.get('/logout', follow_redirects=True)
    
    assert response.status_code == 200
    with client.session_transaction() as sess:
        assert sess.get('loggedin') is None
        assert sess.get('username') is None
        assert sess.get('user_type') is None

def test_login_wrong_user_type(client, test_db):
    """Test login with incorrect user type"""
    response = client.post('/login', data={
        'username': 'testpm',
        'password': 'test123',
        'user_type': 'admin'  # Wrong user type
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Invalid user type for this account' in response.data



def test_first_time_login(client, test_db):
    """Test first time login redirect to change password"""
    cursor = test_db.cursor()  # Create cursor from connection
    cursor.execute('''
        UPDATE users SET first_login = 1 
        WHERE username = %s
    ''', ('testpm',))
    test_db.commit()
    cursor.close()

    response = client.post('/login', data={
        'username': 'testpm',
        'password': 'test123',
        'user_type': 'pm'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b'Change Password' in response.data





def test_password_complexity(client, test_db): 
    """Test password complexity requirements during change"""
    client.post('/login', data={
        'username': 'testpm',
        'password': 'test123',
        'user_type': 'pm'
    })
    
    response = client.post('/change_password', data={
        'current_password': 'test123',
        'new_password': 'weak',
        'confirm_password': 'weak'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b'Password must be at least 8 characters' in response.data


