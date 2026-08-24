import unittest
import os
import tempfile

from compy_config import CompyConfig, loadEnvironment


class TestEnvironmentPrecedence(unittest.TestCase):
    """.env supplies defaults; the real environment overrides them.

    The other way round (dotenv's override=True) means the app cannot be
    pointed at a different database or port without editing the .env file,
    because the file silently wins over anything exported in the shell.
    """

    VARIABLE = "FLASK_COMPY_PRECEDENCE_PROBE"

    def setUp(self):
        self.previous = os.environ.pop(self.VARIABLE, None)
        self.temp_dir = tempfile.TemporaryDirectory(prefix="compy_env_")
        self.env_file = os.path.join(self.temp_dir.name, ".env")
        with open(self.env_file, "w") as handle:
            handle.write("%s=from_the_file\n" % self.VARIABLE)

    def tearDown(self):
        os.environ.pop(self.VARIABLE, None)
        if self.previous is not None:
            os.environ[self.VARIABLE] = self.previous
        self.temp_dir.cleanup()

    def testEnvironmentWinsOverTheFile(self):
        os.environ[self.VARIABLE] = "from_the_environment"

        self.assertTrue(loadEnvironment(self.env_file))

        self.assertEqual(os.environ[self.VARIABLE], "from_the_environment")

    def testFileSuppliesTheValueWhenTheEnvironmentDoesNot(self):
        self.assertTrue(loadEnvironment(self.env_file))

        self.assertEqual(os.environ[self.VARIABLE], "from_the_file")


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
