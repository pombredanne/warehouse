def test_index_404(client):
    resp = client.get("/")
    assert resp.status_code == 404
