import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPBasicCredentials

from src import app as activities_app


class FacultyAdvisorTests(unittest.TestCase):
    def setUp(self):
        self.original_advisor = activities_app.activities["Chess Club"]["advisor"]
        self.registry_directory = tempfile.TemporaryDirectory()
        self.registry_path = Path(self.registry_directory.name) / "teachers.json"
        self.registry_path.write_text(
            json.dumps({"teachers": {"teacher": {"password": "correct-password"}}}),
            encoding="utf-8",
        )
        self.registry_patch = patch.object(
            activities_app, "teachers_file", self.registry_path
        )
        self.registry_patch.start()

    def tearDown(self):
        activities_app.activities["Chess Club"]["advisor"] = self.original_advisor
        self.registry_patch.stop()
        self.registry_directory.cleanup()

    def test_staff_can_assign_and_clear_advisor(self):
        teacher = activities_app.authenticate_teacher(
            HTTPBasicCredentials.model_validate(
                {"username": "teacher", "password": "correct-password"}
            )
        )

        activities_app.update_activity_advisor(
            "Chess Club",
            activities_app.FacultyAdvisorUpdate(
                advisor=activities_app.FacultyAdvisor(
                    name="  Alex Teacher ", email="alex@mergington.edu"
                )
            ),
            teacher,
        )
        self.assertEqual(
            activities_app.get_activities()["Chess Club"]["advisor"],
            {"name": "Alex Teacher", "email": "alex@mergington.edu"},
        )

        activities_app.update_activity_advisor(
            "Chess Club",
            activities_app.FacultyAdvisorUpdate(advisor=None),
            teacher,
        )
        self.assertIsNone(
            activities_app.get_activities()["Chess Club"]["advisor"]
        )

    def test_missing_or_invalid_teacher_credentials_are_rejected(self):
        for credentials in (
            None,
            HTTPBasicCredentials.model_validate(
                {"username": "teacher", "password": "wrong-password"}
            ),
        ):
            with self.subTest(credentials=credentials):
                with self.assertRaises(HTTPException) as error:
                    activities_app.authenticate_teacher(credentials)
                self.assertEqual(error.exception.status_code, 401)

    def test_student_activity_view_includes_unassigned_advisor(self):
        self.assertIsNone(
            activities_app.get_activities()["Chess Club"]["advisor"]
        )


if __name__ == "__main__":
    unittest.main()
