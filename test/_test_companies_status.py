from app import app


def test_companies_status():
    # Create a test client for the Flask app
    with app.test_client() as client:
        # Send a GET request to the /companies_status endpoint
        response = client.get('/companies_status')

        # Assert that the response status code is 200 OK
        assert response.status_code == 200

        # Assert that the response contains the expected HTML content
        assert b'<h1>Company Status</h1>' in response.data
        assert b'<td>company</td>' in response.data or b'<td>notinterested</td>' in response.data or\
               b'<td>inactive</td>' in response.data or b'<td>prospect</td>' in response.data

        # getting a external error 500 which means
