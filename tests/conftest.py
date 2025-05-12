# import pytest
# from app import app
# from utils.db import get_db_connection
# from werkzeug.security import generate_password_hash

# @pytest.fixture
# def client():
#     app.config['TESTING'] = True
#     app.config['WTF_CSRF_ENABLED'] = False
#     return app.test_client()

# @pytest.fixture
# def auth_client(client):
#     """Fixture for authenticated client"""
#     client.post('/auth/login', data={
#         'username': 'testpm',
#         'password': 'test123',
#         'user_type': 'pm'
#     })
#     return client

# @pytest.fixture
# def test_db():
#     """Setup test database connection and test data"""
#     conn = get_db_connection()
#     cursor = conn.cursor()
    
#     # Create test user
#     hashed_password = generate_password_hash('test123')
#     cursor.execute('''
#         INSERT INTO users (username, password, email, user_type, first_login)
#         VALUES (%s, %s, %s, %s, %s)
#     ''', ('testpm', hashed_password, 'testpm@example.com', 'pm', 0))
#     conn.commit()
    
#     yield conn
    
#     # Cleanup
#     cursor.execute('DELETE FROM users WHERE username = %s', ('testpm',))
#     conn.commit()
#     cursor.close()
#     conn.close()

import pytest
from flask import Flask
from app import app as flask_app  # Rename import to avoid conflict
from utils.db import get_db_connection
from werkzeug.security import generate_password_hash

@pytest.fixture
def app():
    """Create and configure test application"""
    flask_app.config.update({
        'TESTING': True,
        'WTF_CSRF_ENABLED': False,
        'SECRET_KEY': 'test-key-123'
    })
    return flask_app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def test_db():
    """Setup test database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create test PM user
    hashed_password = generate_password_hash('test123')
    cursor.execute('''
        INSERT INTO users (username, password, email, user_type, first_login)
        VALUES (%s, %s, %s, %s, %s)
    ''', ('testpm', hashed_password, 'testpm@example.com', 'pm', 0))
    
    cursor.execute('SELECT LAST_INSERT_ID() as id')
    user_id = cursor.fetchone()['id']
    conn.commit()
    
    yield {'conn': conn, 'cursor': cursor, 'user_id': user_id}
    
    # Cleanup
    cursor.execute('DELETE FROM users WHERE username = %s', ('testpm',))
    conn.commit()
    cursor.close()
    conn.close()

@pytest.fixture
def auth_client(client, test_db):
    """Create authenticated client with PM privileges"""
    # Login
    client.post('/auth/login', data={
        'username': 'testpm',
        'password': 'test123',
        'user_type': 'pm'
    })
    
    # Set session data
    with client.session_transaction() as sess:
        sess['loggedin'] = True
        sess['username'] = 'testpm'
        sess['user_type'] = 'pm'
        sess['id'] = test_db['user_id']
    
    return client