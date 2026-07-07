
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

"""PDF report generation for Compy (start lists, lane lists, results).

This module contains the PdfReportMixin which is mixed into CompyData.
All methods here only read competition state and produce weasyprint PDFs.
"""

import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd

from compy_constants import DEPTH_DISCIPLINES

_wp = None
_wp_failed = False


def weasyprint():
    """Lazily import weasyprint so the app can run without it (no PDF export).

    On macOS weasyprint needs its native libraries: brew install pango
    (and possibly: export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib).
    """
    global _wp, _wp_failed
    if _wp is None and not _wp_failed:
        try:
            import weasyprint
            _wp = weasyprint
        except (ImportError, OSError) as e:
            _wp_failed = True
            logging.error("PDF export disabled, weasyprint could not be loaded: %s", e)
            logging.error("Install it with 'pip3 install weasyprint'. On macOS also run "
                          "'brew install pango' (and if the libraries are still not found: "
                          "'export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib').")
    return _wp


class PdfReportMixin:

    def getStartListPDF(self, day="all", block="all", in_memory=False):
        wp = weasyprint()
        if wp is None:
            return None
        if day == "all" and block == "all":
            day_block = self.getBlocks()
            files = []
            for d in day_block:
                for block in day_block[d].keys():
                    files.append(self.getStartListPDF(d, block, True))
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_start_lists.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        start_df = pd.DataFrame(self.getStartList(day, block))
        start_df.drop("Id", axis=1, inplace=True)
        blocks = self.getBlocks()
        block_disciplines = blocks[day][int(block)]['dis_s']
        if self.comp_type == "aida":
            start_df.drop("PB", axis=1, inplace=True)
        elif block_disciplines == "STA":
            start_df["AP"] = start_df.apply(lambda row: row["AP"] if row['Discipline'] == "STA" else "", axis=1)
        self.dropUnusedColumns(block_disciplines, start_df)
        html_string = start_df.to_html(index=False, justify="left", classes="df_table")
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        human_day = day_obj.strftime("%d. %m. %Y")
        dis = self.db_.execute('SELECT disciplines FROM block WHERE competition_id==? AND id==?', (self.id_, block))
        if dis is None:
            return None
        disciplines = self.disciplineIntToStr(dis[0][0])
        html_string = """
            <html>
            <head>
            <style>
            table {{
                margin-left: 2cm;
            }}
            tr th:first-child {{
                padding-left:0px;
                text-align: left;
            }}
            tr td:first-child {{
                padding-left:0;
                text-align: left;
            }}
            th, td {{
                padding:5px 0px 2px 20px;
                text-align: center;
                border-bottom: 1px solid #ddd;
                font-size: 12px;
            }}
            @page {{
                margin: 4cm 1cm 6cm 1cm;
                size: A4;
                @top-right {{
                    content: counter(page) "/" counter(pages);
                }}
            }}
            header, footer {{
                position: fixed;
                left: 0;
                right: 0;
            }}
            header {{
                /* subtract @page margin */
                top: -4cm;
                height: 4cm;
                text-align: center;
                vertical-align: center;
            }}
            footer {{
                /* subtract @page margin */
                bottom: -6cm;
                height: 6cm;
                text-align: center;
                vertical-align: center;
            }}
            </style>
            </head>
            <body>
            <header>
                <h1>{}</h1>
                <h2>Start list {} - {}</h2>
            </header>
            {}
            <footer><img src="{}" style="width:{}cm; height:{}cm;"></footer>
            </body>
            </html>
            """.format(self.name, disciplines, human_day, html_string, self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
        html = wp.HTML(string=html_string, base_url="/")
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_start_list_" + day + "_" + disciplines.replace(', ', '_') + ".pdf")
            html.write_pdf(fname)
            return fname

    # Drops columns which are not used under certain conditions, e.g. dive time for pool disciplines.
    def dropUnusedColumns(self, block_disciplines, df):
        block_comma_idx = block_disciplines.find(",")
        if block_comma_idx == -1:
            # drop discipline if only one
            if "Discipline" in df.columns.tolist():
                df.drop("Discipline", axis=1, inplace=True)
            elif "Dis" in df.columns.tolist():
                df.drop("Dis", axis=1, inplace=True)

            # drop AP for CMAS, except for STA
            if self.comp_type == "cmas" and block_disciplines != "STA":
                df.drop("AP", axis=1, inplace=True)

            # drop dive time for pool disciplines
            if not block_disciplines in DEPTH_DISCIPLINES:
                df.drop("Dive Time", axis=1, inplace=True)

        elif not block_disciplines[:block_comma_idx] in DEPTH_DISCIPLINES:
                df.drop("Dive Time", axis=1, inplace=True)

    def getLaneListPDF(self, safety=False, day="all", block="all", lane="all", in_memory=False):
        wp = weasyprint()
        if wp is None:
            return None
        if day == "all" and block == "all":
            blocks = self.getBlocks()
            files = []
            for day in blocks:
                for block in blocks[day].keys():
                    for lane in blocks[day][block]['lanes']:
                        files.append(self.getLaneListPDF(safety, day, block, lane, True))
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_lane_lists.pdf")
            merged_pdf.write_pdf(fname)
            return fname
        ret, content = self.getLaneList(day, block, lane)
        lane_df = pd.DataFrame(content['lane_list'])
        lane_df.drop("id", axis=1, inplace=True)
        lane_df.drop("s_id", axis=1, inplace=True)
        lane_df.drop("RP", axis=1, inplace=True)
        lane_df.drop("Card", axis=1, inplace=True)
        lane_df.drop("Remarks", axis=1, inplace=True)
        if safety:
            lane_df.drop("Nat", axis=1, inplace=True)
            lane_df.drop("NR", axis=1, inplace=True)

        blocks = self.getBlocks()
        block_str = blocks[day][int(block)]['dis_s']
        block_str_underscore = block_str.replace(', ', '_')
        has_multiple_dis = ',' in block_str
        self.dropUnusedColumns(block_str, lane_df)
        if not safety:
            lane_df["RP"] = ""
            lane_df["Card"] = ""
            lane_df["Remarks"] = ""
        col_weight = {
                "OT": 4,
                "Name": 25,
                "Nat": 4,
                "AP": 4,
                "Dive Time": 4,
                "Dis": 4,
                "RP": 10,
                "Card": 10,
                "Remarks": 40,
                "PB": 4,
                "NR": 4}
        cols = lane_df.columns.tolist()
        if not safety:
            dive_time_col = ["Dive Time"] if "Dive Time" in cols else []
            dis_col = ["Dis"] if has_multiple_dis else []
            if self.comp_type == "aida":
                cols = ['OT', 'Name', 'Nat', 'AP'] + dive_time_col + dis_col + ['RP', 'Card', 'Remarks', 'PB', 'NR']
            else:
                ap_col = ['AP'] if block_str == "STA" else []
                cols = ['OT', 'Name', 'Nat'] + ap_col + ['PB'] + dive_time_col + dis_col + ['RP', 'Card', 'Remarks', 'NR']
        sum_col_weight = sum([col_weight[c] for c in cols])
        lane_df = lane_df[cols]
        df_html = lane_df.to_html(index=False, justify="left", classes="df_table")
        day_obj = datetime.strptime(day, "%Y-%m-%d")
        human_day = day_obj.strftime("%d. %m. %Y")
        html_string = """
            <html>
            <head>
            <style>
            table {
                width: 100%;
            }
            tr th:first-child {
                padding-left:0px;
            }
            tr td:first-child {
                padding-left:0px;
            }"""
        if safety:
            html_string += """
                h2 {
                    font-size: 4mm;
                }
                th, td {
                    padding:1mm 0mm 1mm 1mm;
                    text-align: center;
                    font-size: 4mm;
                    border-bottom: 1px solid #ddd;
                }"""
        else:
            html_string += """
                th, td {
                    padding:10px 0px 10px 20px;
                    text-align: center;
                    border-bottom: 1px solid #ddd;
                }"""
        i = 1
        for c in cols:
            alignment = "left" if c == "Name" else "center"
            html_string += """
                table th:nth-child({}), table td:nth-child({}) {{
                    width: {}%;
                    text-align: {};
                }}""".format(str(i), str(i), str(round(100*col_weight[c]/sum_col_weight, 1)), alignment)
            i += 1
        html_string += """
            header, footer {
                position: fixed;
                left: 0;
                right: 0;
            }"""
        if safety:
            html_string += """
                @page {{
                    margin: 1.5cm 0.5cm 0.5cm 0.5cm;
                    size: A5 portrait;
                    @top-right {{
                        content: counter(page) "/" counter(pages);
                    }}
                }}
                header {{
                    /* subtract @page margin */
                    top: -1.5cm;
                    height: 1.5cm;
                    text-align: center;
                    vertical-align: center;
                }}
                footer {{
                    /* subtract @page margin */
                    bottom: -0.5cm;
                    height: 0.5cm;
                    text-align: left;
                    vertical-align: center;
                }}
                </style>
                </head>
                <body>
                <header>
                    <h2>Safety lane list {} - lane {} - {}</h2>
                </header>
                {}
                <footer></footer>
                </body>
                </html>
                """.format(block_str, lane, human_day, df_html)
        else:
            html_string += """
                @page {{
                    margin: 4cm 1cm 1.5cm 2.5cm;
                    size: A4 landscape;
                    @top-right {{
                        content: counter(page) "/" counter(pages);
                    }}
                }}
                header {{
                    /* subtract @page margin */
                    top: -4cm;
                    height: 4cm;
                    text-align: center;
                    vertical-align: center;
                }}
                footer {{
                    /* subtract @page margin */
                    bottom: -1.5cm;
                    height: 1.5cm;
                    text-align: left;
                    vertical-align: center;
                }}
                </style>
                </head>
                <body>
                <header>
                    <h1>{}</h1>
                    <h2>Lane list {} - lane {} - {}</h2>
                </header>
                {}
                <footer><span style="margin-left:3mm">Judge Name:</span><span style="margin-left:8cm">Signature:</span></footer>
                </body>
                </html>
                """.format(self.name, block_str, lane, human_day, df_html)
        html = wp.HTML(string=html_string, base_url="/")
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_lane_list_" + day + "_" + block_str_underscore + "_" + lane + ".pdf")
            html.write_pdf(fname)
            return fname

    def getResultPDF(self, discipline="all", gender="all", country="all", in_memory=False, top3=False):
        wp = weasyprint()
        if wp is None:
            return None
        if discipline == "all" and gender == "all":
            files = []
            gender_list = ["F", "M"]
            if top3:
                gender_list = [gender_list] # if gender is a list, one pdf will contain both genders, for top 3
            for d in self.getDisciplines():
                for g in gender_list:
                    for c in self.getCountries(True):
                        pdf = self.getResultPDF(d, g, c, True, top3)
                        if pdf is not None:
                            files.append(pdf)
            pages = []
            for doc in files:
                for page in doc.pages:
                    pages.append(page)
            merged_pdf = files[0].copy(pages)
            fname = os.path.join(self.config.download_folder, self.name + "_results")
            if top3:
                fname += "_top3"
            fname += ".pdf"
            merged_pdf.write_pdf(fname)
            return fname

        html_string = """
            {}
            <header>
                <h1>{}</h1>
                <h2>Result {} - {}""".format(self.getHtmlHeader(), self.name, discipline, country)
        if top3:
            gender_list = gender # for top 3, this is ["F", "M"]
        else:
            gender_str = "Female" if gender == "F" else "Male"
            html_string += " - " + gender_str
            gender_list = [gender] # for all others a string
        html_string += """</h2>
            </header>
            """
        for g in gender_list:
            ret, content = self.getResult(discipline, g, country, False)
            if content is None:
                return None
            result = content['results']
            result_df = pd.DataFrame(result)
            if len(result_df.index) == 0:
                return None
            if self.comp_type == "cmas":
                result_df.drop("Points", axis=1, inplace=True)
            if "Id" in result_df.columns.tolist():
                result_df.drop("Id", axis=1, inplace=True)
            if "AP_float" in result_df.columns.tolist():
                result_df.drop("AP_float", axis=1, inplace=True)
            if "OT" in result_df.columns.tolist():
                result_df.drop("OT", axis=1, inplace=True)
            if "JudgeRemarks" in result_df.columns.tolist():
                result_df.drop("JudgeRemarks", axis=1, inplace=True)
            if top3:
                gender_str = "Female" if g == "F" else "Male"
                html_string += "<h3>" + gender_str + "</h3>\n"
                # drop all entries where rank is > 3
                # first find one where this is true
                result_df['Rank'] = pd.to_numeric(result_df['Rank'], errors='coerce')
                remainder = result_df[(result_df['Rank'] > 3)]
                if len(remainder.index) != 0:
                    index_to_drop_after = remainder.idxmin(numeric_only=True)[0]
                    # keep only ones before
                    result_df = result_df.loc[:index_to_drop_after-1]
                # convert back to strings
                result_df['Rank'] = result_df['Rank'].replace(np.nan, 0).astype(int).astype(str).replace('0', '')
                # remove all Red cards
                result_df = result_df[(result_df['Card'] != "RED")]
            html_string += result_df.to_html(index=False, justify="left", classes="df_table") + "\n"
            html_string = html_string.replace("&lt;b&gt;", "<b>")
            html_string = html_string.replace("&lt;/b&gt;", "</b>")
        html_string += self.getHtmlFooter()

        html = wp.HTML(string=html_string, base_url="/")
        if in_memory:
            return html.render()
        else:
            fname = os.path.join(self.config.download_folder, self.name + "_result_" + discipline + "_" + gender + "_" + country + ".pdf")
            html.write_pdf(fname)
            return fname

    def getHtmlHeader(self):
        html_header = """
            <html>
            <head>
            <style>
            table {
                width: 100%;
            }
            tr th:first-child {
                padding-left:0px;
                text-align: left;
            }
            tr td:first-child {
                padding-left:0px;
                text-align: left;
            }
            th, td {
                padding:20px 0px 5px 5px;
                text-align: center;
                font-size: 12px;
                border-bottom: 1px solid #ddd;
            }
            @page {
                margin: 4cm 1cm 6cm 1cm;
                size: A4;
                @top-right {
                    content: counter(page) "/" counter(pages);
                }
            }
            header, footer {
                position: fixed;
                left: 0;
                right: 0;
            }
            header {
                /* subtract @page margin */
                top: -4cm;
                height: 4cm;
                text-align: center;
                vertical-align: center;
            }
            footer {
                /* subtract @page margin */
                bottom: -6cm;
                height: 6cm;
                text-align: center;
                vertical-align: center;
            }
            h3 {
                padding-top: 1cm;
            }
            </style>
            </head>
            <body>"""
        return html_header

    def getHtmlFooter(self):
        html_footer = """
            <footer><img src="{}" style="width:{}cm; height:{}cm;"></footer>
            </body>
            </html>
            """.format(self.sponsor_img_data, self.sponsor_img_width, self.sponsor_img_height)
        return html_footer
