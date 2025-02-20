import unittest
import os

from compy_config import CompyConfig

class TestCompyConfig(unittest.TestCase):
    def setUp(self):
        self.cc = CompyConfig()

    def testDefaultValues(self):
        file_path = os.path.dirname(os.path.abspath(__file__))

        self.assertEqual(self.cc.upload_folder, os.path.join(file_path, "uploads"))
        self.assertEqual(self.cc.storage_folder, os.path.join(file_path, "storage"))
        self.assertEqual(self.cc.download_folder, os.path.join(file_path, "download"))

        self.assertTrue(os.path.exists(self.cc.upload_folder))
        self.assertTrue(os.path.exists(self.cc.storage_folder))
        self.assertTrue(os.path.exists(self.cc.download_folder))
