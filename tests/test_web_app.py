from web.app import create_app


def test_index_shows_url_entry_form() -> None:
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert b"Carga una necesidad de SERCOP" in response.data
    assert b'name="url"' in response.data


def test_load_rejects_invalid_url() -> None:
    app = create_app()
    app.config["TESTING"] = True

    response = app.test_client().post("/cargar", data={"url": "no-es-url"})

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/")
