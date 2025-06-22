def test_favicon_endpoint(app_client):
    """Test that the /favicon.ico endpoint returns a favicon with the correct content type"""
    # Make request to the /favicon.ico endpoint
    response = app_client.get("/favicon.ico")

    # Check that the response is successful
    assert response.status_code == 200

    # Check that the response has the correct content type
    assert response.headers["content-type"] == "image/x-icon"

    # Check that the response contains data (not empty)
    assert len(response.content) > 0
