import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from fastapi.testclient import TestClient

from bilingual_subtitle_studio import api


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        root = Path(self._tmp.name)
        self.upload_dir = root / "uploads"
        self.output_dir = root / "outputs"
        self._patches = [
            mock.patch.object(api, "UPLOAD_DIR", self.upload_dir),
            mock.patch.object(api, "OUTPUT_DIR", self.output_dir),
        ]
        for patch in self._patches:
            patch.start()
        self.client = TestClient(api.create_app())

    def tearDown(self) -> None:
        for patch in self._patches:
            patch.stop()
        self._tmp.cleanup()

    def test_options_list_languages_and_modes(self) -> None:
        data = self.client.get("/api/options").json()

        self.assertIn("en", [language["code"] for language in data["languages"]])
        self.assertIn("Original + Translation", data["output_modes"])

    def test_demo_returns_sample_rows(self) -> None:
        rows = self.client.get("/api/demo").json()["rows"]

        self.assertGreater(len(rows), 0)
        self.assertIn("source_text", rows[0])

    def test_index_page_is_served(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Bilingual Subtitle Studio", response.text)

    def test_upload_saves_audio_and_classifies_it(self) -> None:
        audio = self.client.post("/api/upload", files={"file": ("talk.wav", b"RIFF", "audio/wav")}).json()

        self.assertEqual(audio["kind"], "audio")
        self.assertTrue((self.upload_dir / "talk.wav").exists())

    def test_upload_rejects_other_types_without_saving(self) -> None:
        response = self.client.post("/api/upload", files={"file": ("notes.txt", b"hi", "text/plain")})

        self.assertEqual(response.status_code, 400)
        self.assertFalse((self.upload_dir / "notes.txt").exists())

    def test_extract_refuses_files_outside_upload_folder(self) -> None:
        response = self.client.post("/api/extract", json={"path": "/etc/hosts"})

        self.assertEqual(response.status_code, 400)

    def test_transcribe_refuses_files_outside_upload_folder(self) -> None:
        response = self.client.post("/api/transcribe", json={"path": "/etc/hosts"})

        self.assertEqual(response.status_code, 400)

    def test_translate_rejects_unknown_language(self) -> None:
        rows = self.client.get("/api/demo").json()["rows"]

        response = self.client.post("/api/translate", json={"rows": rows, "target_language": "xx"})

        self.assertEqual(response.status_code, 400)

    def test_progress_starts_at_import(self) -> None:
        rows = self.client.get("/api/demo").json()["rows"]

        data = self.client.post(
            "/api/progress",
            json={"rows": rows, "subtitle_source": "demo", "prepared_audio_path": ""},
        ).json()

        self.assertEqual(data["current_step"], "Import")
        self.assertEqual(data["progress"]["Import"], 0)

    def test_export_preview_does_not_write_files(self) -> None:
        rows = self.client.get("/api/demo").json()["rows"]

        response = self.client.post("/api/export", json={"rows": rows, "target_language": "en"})

        self.assertEqual(response.status_code, 200)
        self.assertIn("-->", response.json()["texts"]["srt"])
        self.assertFalse(self.output_dir.exists())

    def test_export_save_writes_all_three_files(self) -> None:
        rows = self.client.get("/api/demo").json()["rows"]

        self.client.post("/api/export", json={"rows": rows, "target_language": "en", "save": True})

        for name in ("subtitles.srt", "subtitles.txt", "subtitles.fcpxml"):
            self.assertTrue((self.output_dir / name).exists(), name)

    def test_export_rejects_invalid_rows(self) -> None:
        response = self.client.post(
            "/api/export",
            json={"rows": [{"index": 1, "start_seconds": 5, "end_seconds": 1, "source_text": "x"}]},
        )

        self.assertEqual(response.status_code, 400)

    def test_unknown_job_returns_404(self) -> None:
        self.assertEqual(self.client.get("/api/jobs/missing").status_code, 404)

    def test_job_store_runs_work_and_reports_result(self) -> None:
        store = api.JobStore()

        job = store.start("demo", lambda _job: [{"index": 1}])
        for _ in range(100):
            if job.status != "running":
                break
            time.sleep(0.02)

        self.assertEqual(job.status, "done")
        self.assertEqual(job.result, [{"index": 1}])

    def test_job_store_reports_failure(self) -> None:
        store = api.JobStore()

        def boom(_job):
            raise RuntimeError("engine offline")

        job = store.start("demo", boom)
        for _ in range(100):
            if job.status != "running":
                break
            time.sleep(0.02)

        self.assertEqual(job.status, "failed")
        self.assertEqual(job.error, "engine offline")


if __name__ == "__main__":
    unittest.main()
