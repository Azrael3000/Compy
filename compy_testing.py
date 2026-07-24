"""Shared fixtures for the Compy test suite (the *_test.py files).

The name of this file intentionally does not match the *_test.py discovery
pattern, so unittest imports it as a helper instead of running it.

Two base classes are provided:

- CompyDataTestCase: a fresh sqlite database in a temporary directory per
  test class, plus a flask app context per test, for tests that exercise
  CompyData/CompyDB directly.
- CompyServerTestCase: additionally runs the full flask app on an embedded
  threaded HTTP server, for integration tests that need real concurrent
  requests. No manually started server or pre-existing database is needed.
"""
import logging
import os
import tempfile
import threading
import unittest

import flask
from werkzeug.serving import make_server

import compy_data
import compy_db
import compy_flask

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
TEST_COMPETITION_XLSX = os.path.join(REPO_ROOT, "test_competition.xlsx")


def makeApp(database_path):
    app = flask.Flask("compy", root_path=REPO_ROOT)
    app.config["DATABASE"] = database_path
    app.config["SECRET_KEY"] = "0123456789abcdef0123456789abcdef_compy_test"
    return app


class CompyDataTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory(prefix="compy_test_")
        cls.app = makeApp(os.path.join(cls.temp_dir.name, "compy_test.sqlite"))
        cls.db = compy_db.CompyDB(cls.app)
        cls.db.init_db()
        with cls.app.app_context():
            compy_data.CompyData.ensureDefaultCompetition(cls.db, cls.app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def setUp(self):
        # CompyDB keeps its per-request connection in flask.g, so direct
        # CompyData calls need an app context (one per test)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        self.app_context.pop()

    def newData(self, comp_id = None):
        return compy_data.CompyData(self.db, self.app, comp_id)

    @classmethod
    def createCompetitionWithExcel(cls, comp_name):
        """Create a competition and import the checked-in excel test file.

        Intended for use in setUpClass (creates its own app context).
        Returns the id of the new competition.
        """
        with cls.app.app_context():
            data = compy_data.CompyData(cls.db, cls.app)
            data.changeName(comp_name, False)
            data.compFileChange(TEST_COMPETITION_XLSX)
            return data.id_


class CompyServerTestCase(CompyDataTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # keep the test output readable: no per-request log lines
        logging.getLogger("werkzeug").setLevel(logging.WARNING)
        compy_flask.CompyFlask(cls.app, cls.db, start_flask=False)
        cls.server = make_server("127.0.0.1", 0, cls.app, threaded=True)
        cls.base_url = "http://127.0.0.1:%d" % cls.server.server_port
        cls.server_thread = threading.Thread(target=cls.server.serve_forever,
                                             name="compy-test-server", daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server_thread.join()
        super().tearDownClass()
