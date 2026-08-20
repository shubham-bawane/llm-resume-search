import os
import tempfile
import unittest

from fs_tools import list_files, read_file, search_in_file, write_file
from llm_file_assistant import analyze_resume_folder_for_keyword


class FsToolsTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(prefix="resume_tools_")

    def test_write_and_read_text_file(self):
        filepath = os.path.join(self.temp_dir, "nested", "resume_john.txt")
        result = write_file(filepath, "Experience with Python and SQL\nStrong problem solving skills.")

        self.assertEqual(result["status"], "success")
        read_result = read_file(filepath)
        self.assertEqual(read_result["status"], "success")
        self.assertIn("Python", read_result["content"])

    def test_list_files_filters_extension(self):
        write_file(os.path.join(self.temp_dir, "resume_one.txt"), "text one")
        write_file(os.path.join(self.temp_dir, "resume_two.pdf"), "%PDF-1.4")
        write_file(os.path.join(self.temp_dir, "notes.md"), "markdown")

        files = list_files(self.temp_dir, extension=".txt")
        names = [item["name"] for item in files]

        self.assertIn("resume_one.txt", names)
        self.assertNotIn("resume_two.pdf", names)

    def test_search_in_file_is_case_insensitive(self):
        filepath = os.path.join(self.temp_dir, "resume_search.txt")
        write_file(filepath, "Experienced in python, SQL, and machine learning workflows.")

        result = search_in_file(filepath, "python")
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["match_count"], 1)
        self.assertIn("python", result["matches"][0]["context"].lower())

    def test_analyze_resume_folder_for_keyword(self):
        folder = os.path.join(self.temp_dir, "resumes")
        os.makedirs(folder, exist_ok=True)

        write_file(os.path.join(folder, "candidate_a.txt"), "Event Coordinator experience in large community events.")
        write_file(os.path.join(folder, "candidate_b.txt"), "Worked on product marketing campaigns.")

        matches = analyze_resume_folder_for_keyword("Event Coordinator", folder=folder)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["file"], "candidate_a.txt")


if __name__ == "__main__":
    unittest.main()
