async def test_get_settings(client):
    response = await client.get("/settings")
    assert response.status_code == 200
    data = response.json()
    assert "app" in data
    assert "run" in data
    assert "db" in data
    assert "s3" in data
    assert "broker" in data
    assert "log" in data
    assert "use_mock" in data
    assert data["app"]["title"] is not None
    assert isinstance(data["run"]["port"], int)
    assert isinstance(data["db"]["port"], int)
