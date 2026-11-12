import io

PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"0" * 128
PDF_BYTES = b"%PDF-1.4\n" + b"0" * 128


def test_media_upload_and_delete(client, auth):
    response = client.post(
        "/api/v1/admin/media",
        headers=auth,
        data={"file": (io.BytesIO(PNG_BYTES), "photo.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201, response.get_json()
    media = response.get_json()["data"]
    assert media["mime_type"] == "image/png"
    assert media["url"].startswith("/uploads/media/")

    listing = client.get("/api/v1/admin/media", headers=auth).get_json()["data"]
    assert len(listing) == 1

    assert client.delete(f"/api/v1/admin/media/{media['id']}", headers=auth).status_code == 200
    assert client.get("/api/v1/admin/media", headers=auth).get_json()["data"] == []


def test_upload_rejects_disallowed_extension(client, auth):
    response = client.post(
        "/api/v1/admin/media",
        headers=auth,
        data={"file": (io.BytesIO(b"hello"), "script.exe")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_media_type"


def test_upload_rejects_mismatched_content(client, auth):
    response = client.post(
        "/api/v1/admin/media",
        headers=auth,
        data={"file": (io.BytesIO(b"not really a png"), "fake.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415


def test_resume_upload_default_and_download(client, auth):
    first = client.post(
        "/api/v1/admin/resumes",
        headers=auth,
        data={"label": "Data CV", "is_default": "true", "file": (io.BytesIO(PDF_BYTES), "cv.pdf")},
        content_type="multipart/form-data",
    )
    assert first.status_code == 201, first.get_json()
    resume = first.get_json()["data"]
    assert resume["is_default"] is True

    second = client.post(
        "/api/v1/admin/resumes",
        headers=auth,
        data={"label": "ML CV", "is_default": "true", "file": (io.BytesIO(PDF_BYTES), "cv2.pdf")},
        content_type="multipart/form-data",
    )
    assert second.status_code == 201

    resumes = client.get("/api/v1/admin/resumes", headers=auth).get_json()["data"]
    defaults = [item for item in resumes if item["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["label"] == "ML CV"

    download = client.get(f"/api/v1/resumes/{resume['id']}/download")
    assert download.status_code == 200
    url = download.get_json()["data"]["download_url"]
    file_response = client.get(url)
    assert file_response.status_code == 200
    assert file_response.mimetype == "application/pdf"


def test_resume_requires_pdf(client, auth):
    response = client.post(
        "/api/v1/admin/resumes",
        headers=auth,
        data={"label": "Fake CV", "file": (io.BytesIO(PNG_BYTES), "cv.png")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415
