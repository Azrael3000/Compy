 ```
 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

          ━━━━━━━━━━━━━
           ┏┓┏┓┳┳┓┏┓┓┏
           ┃ ┃┃┃┃┃┃┃┗┫
           ┗┛┗┛┛ ┗┣┛┗┛
          ━━━━━━━━━━━━━

 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Competition organization tool
 for freediving competitions.

 Copyright 2023 - Arno Mayrhofer

 Licensed under the GNU AGPL

 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

 Authors:

 - Arno Mayrhofer

 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ```

# Compy

Compy is a competition organization tool for freediving competition. Its current features are:

 - Parse AIDA International Style Excel files
 - Switch between CMAS and AIDA competitions (different countdown, different result view without points for CMAS)
 - Uploading of sponsor image for output on PDFs
 - Output of results, lane lists and start lists via PDF
 - Possibility to select athletes for special ranking (e.g. newcommer)
 - List of breaks for each athlete on each day
 - Automated countdown

Future features can be seen in the TODO file.

## Prerequisites

 - openpyxl
 - pandas
 - country_converter
 - flask

## Want to help?

As is clearly visible, this tool is lacking a nice user interface. If you want to help making one, please write me at hydros@TLD. (`TLD=posteo.net`)
