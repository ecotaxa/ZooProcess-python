def test_ping_endpoint(app_client):
    """
    Test that the /ping endpoint returns 'pong!'.
    """
    response = app_client.get("/ping")
    assert response.status_code == 200
    assert response.text == '"pong!"'  # JSON-encoded string
