
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
