
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
#  for AIDA International
#  competitions.
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

class CompyConfig:

    def __init__(self):
        self.upload_folder_ = self.initFolder(path.join(path.dirname(path.abspath(__file__)), 'uploads'))
        self.storage_folder_ = self.initFolder(path.join(path.dirname(path.abspath(__file__)), 'storage'))

    def initFolder(self, path):
        if not path.isdir(path):
            mkdir(path)
            logging.debug("Created folder: " + path)
        return path

    @property
    def upload_folder(self):
        return self.upload_folder_

    @property
    def storage_folder(self):
        return self.storage_folder_
