import flask
import sqlite3
import logging
import glob

class CompyDB:
    def __init__(self, app):
        self.app_ = app
        self.db_ = None
        self.app_.teardown_appcontext(self.close_db)
        self.last_index_ = -1

    @property
    def db(self):
        if not self.is_open():
            if "db" not in flask.g:
                logging.debug("Connecting to database:" + flask.current_app.config["DATABASE"])
                flask.g.db = sqlite3.connect(
                    flask.current_app.config["DATABASE"],
                    detect_types=sqlite3.PARSE_DECLTYPES,
                )
                flask.g.db.row_factory = sqlite3.Row
            self.db_ = flask.g.db
        return self.db_

    @property
    def cursor(self):
        return self.db.cursor()

    @property
    def last_index(self):
        return self.last_index_

    def execute(self, cmd, args = ()):
        if type(args) is not tuple:
            args = (args, )
        logging.debug("Execute: '" + cmd + "' args: " + str(args))
        cursor = self.cursor
        data = cursor.execute(cmd, args).fetchall()
        self.last_index_ = cursor.lastrowid
        self.db.commit()
        if len(data) == 0:
            return None
        else:
            return data

    def is_open(self):
        try:
            self.db_.cursor()
            return True
        except Exception as ex:
            return False

    def init_db(self):
        schemas = glob.glob("schemas/*.sql")
        with self.app_.app_context():
            for schema in schemas:
                logging.debug("Initializing database entry from: " + schema)
                with flask.current_app.open_resource(schema) as f:
                    self.db.executescript(f.read().decode("utf-8"))
            logging.info("Database initialized")

    def close_db(self, e=None):
        if self.db_ is not None:
            logging.debug("Closing database")
            self.db_.close()
            self.db_ = None
