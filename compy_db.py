import flask
import sqlite3
import logging
import glob
import os
from contextlib import contextmanager

class CompyDB:
    """Thread-safe database access layer.

    Every flask app/request context gets its own sqlite3 connection, stored in
    flask.g and closed on teardown. No connection, cursor or last-rowid state
    is kept on this object, so a single CompyDB instance can safely be shared
    between concurrent requests (the flask dev server is threaded by default).
    """

    def __init__(self, app):
        self.app_ = app
        self.app_.teardown_appcontext(self.close_db)

    @property
    def db(self):
        if "db" not in flask.g:
            logging.debug("Connecting to database:" + flask.current_app.config["DATABASE"])
            flask.g.db = sqlite3.connect(
                flask.current_app.config["DATABASE"],
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            flask.g.db.row_factory = sqlite3.Row
        return flask.g.db

    @property
    def cursor(self):
        return self.db.cursor()

    def execute(self, cmd, args = ()):
        """Execute a statement and return all rows, or None if there are none."""
        data, _ = self.executeWithRowId(cmd, args)
        return data

    def insert(self, cmd, args = ()):
        """Execute an INSERT statement and return the id of the inserted row.

        Unlike the removed last_index property this value comes from the
        cursor of this very statement, so it cannot be corrupted by other
        requests executing statements in parallel.
        """
        _, rowid = self.executeWithRowId(cmd, args)
        return rowid

    def executeWithRowId(self, cmd, args = ()):
        if type(args) is not tuple:
            args = (args, )
        logging.debug("Execute: '" + cmd + "' args: " + str(args))
        cursor = self.db.cursor()
        data = cursor.execute(cmd, args).fetchall()
        rowid = cursor.lastrowid
        self.commitUnlessInTransaction()
        if len(data) == 0:
            return None, rowid
        else:
            return data, rowid

    @contextmanager
    def transaction(self):
        """Group several statements into one atomic commit.

        Usage:
            with db.transaction():
                db.execute(...)
                db.insert(...)

        Inside the with-block no per-statement commits happen; the outermost
        transaction commits on success and rolls back if an exception is
        raised, so concurrent readers never see half-applied state.
        """
        if flask.g.get("db_in_transaction", False):
            # nested transaction: the outermost one commits
            yield
            return
        flask.g.db_in_transaction = True
        try:
            yield
            self.db.commit()
        except Exception:
            self.db.rollback()
            raise
        finally:
            flask.g.db_in_transaction = False

    def commitUnlessInTransaction(self):
        if not flask.g.get("db_in_transaction", False):
            self.db.commit()

    def init_db(self):
        # resolve the schemas relative to the app root so that init_db also
        # works when the process was not started from the repository root
        schemas = glob.glob(os.path.join(self.app_.root_path, "schemas", "*.sql"))
        with self.app_.app_context():
            for schema in schemas:
                logging.debug("Initializing database entry from: " + schema)
                with open(schema, "r", encoding="utf-8") as f:
                    self.db.executescript(f.read())
            logging.info("Database initialized")

    def close_db(self, e=None):
        db = flask.g.pop("db", None)
        if db is not None:
            logging.debug("Closing database")
            db.close()
