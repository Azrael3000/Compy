
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#           ━━━━━━━━━━━━━
#            ┏┓┏┓┳┳┓┏┓┓┏
#            ┃ ┃┃┃┃┃┃┃┗┫
#            ┗┛┗┛┛ ┗┣┛┗┛
#           ━━━━━━━━━━━━━
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Competition organization tool
#  for freediving competitions.
#
#  Copyright 2023 - Arno Mayrhofer
#
#  Licensed under the GNU AGPL
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#
#  Authors:
#
#  - Arno Mayrhofer
#
#  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from os import path,mkdir
import logging

import dotenv


def loadEnvironment(env_path = None):
    """Load the .env file as defaults, letting the real environment win.

    override is deliberately False: a FLASK_* variable exported in the
    shell has to beat the file, or the app cannot be pointed at another
    database or port without editing .env. The ui test suite needs its own
    server harness (compy_testing.makeApp) precisely because that used to
    be impossible.

    Returns whether a .env file was found and read, like load_dotenv does.
    """
    if env_path is None:
        env_path = dotenv.find_dotenv(usecwd=True)
    return dotenv.load_dotenv(env_path, override=False)


class CompyConfig:

    def __init__(self):
        self.upload_folder_ = self.initFolder(path.join(path.dirname(path.abspath(__file__)), 'uploads'))
        self.storage_folder_ = self.initFolder(path.join(path.dirname(path.abspath(__file__)), 'storage'))
        self.download_folder_ = self.initFolder(path.join(path.dirname(path.abspath(__file__)), 'download'))

    def initFolder(self, folder):
        if not path.isdir(folder):
            mkdir(folder)
            logging.debug("Created folder: " + folder)
        return folder

    @property
    def upload_folder(self):
        return self.upload_folder_

    @property
    def storage_folder(self):
        return self.storage_folder_

    @property
    def download_folder(self):
        return self.download_folder_
