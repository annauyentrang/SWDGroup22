from django.test import TestCase
from volunteers_r_us import views

class ViewsHelperTests(TestCase):
    def test_parse_date_formats_and_invalid(self):
        self.assertEqual(views._parse_date("2025-11-02").isoformat(), "2025-11-02")
        self.assertEqual(views._parse_date("11/02/2025").isoformat(), "2025-11-02")
        self.assertIsNone(views._parse_date("not-a-date"))
        self.assertIsNone(views._parse_date(""))

    def test_csv_from_list_skips_empty(self):
        self.assertEqual(views._csv_from_list(["A", "", None, "B"]), "A, B")
