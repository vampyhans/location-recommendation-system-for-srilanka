from flask import url_for

def test_register(client):
    # Simulate a GET request to the register page
    response = client.get('/register')

    # Check that the response contains the registration form
    assert b'Sign Up' in response.data

    # Simulate a POST request to the register page with valid data
    response = client.post('/register', data={
        'username': 'testuser',
        'email': 'testuser@example.com',
        'password': 'testpassword',
        'confirm_password': 'testpassword'
    })

    # Check that the response redirects to the index page
    assert response.status_code == 302
    assert response.location == url_for('login', _external=True)

    # # Simulate a POST request to the login page with the credentials of the newly registered user
    # response = client.post('/login', data={
    #     'username': 'testuser',
    #     'password': 'testpassword'
    # })

    # # Check that the response redirects to the index page, indicating successful authentication
    # assert response.status_code == 302
    # assert response.location == url_for('index', _external=True)
