import os
from datetime import datetime
import pandas as pd
from dotenv import dotenv_values

# Configs --------------------------------------------
CONFIG = dotenv_values(".env")
QCTWORKSHEET_PATH = CONFIG["QCTWORKSHEET_PATH"]
VIDASHEET_PATH = CONFIG["VIDASHEET_PATH"]
OUTPUT_PATH = CONFIG["OUTPUT_PATH"]
# -----------------------------------------------------


def update_QCTWorksheet_from_VIDAsheet():
    df_vidasheet = pd.read_excel(VIDASHEET_PATH)

    PROJ_TO_UPDATE = ["SSCILD", "GALA", "PRECISE"]

    df_update = pd.DataFrame(
        columns=[
            "Proj",
            "Subj",
            "CTDate",
            "FU",
            "DCM_IN",
            "DCM_EX",
            "VIDA_IN",
            "VIDA_EX",
            "VIDA_IN_Path",
            "VIDA_EX_Path",
            "VIDA_IN_At",
            "VIDA_EX_At",
            "IR",
            "QCT",
            "PostIR",
            "CFD1D",
            "CFD3D",
            "Ptcl1D",
            "Ptcl3D",
        ]
    )

    for _, row in df_vidasheet.iterrows():
        if row["Proj"] in PROJ_TO_UPDATE:
            pass


def prepare_ProjSubList_from_QCTWorksheet(proj: str):
    df_qctworksheet = pd.read_excel(QCTWORKSHEET_PATH, sheet_name=proj)
    df_projsubjlist = pd.DataFrame(columns=["Proj", "Subj", "Img", "ImgDir"])

    for _, row in df_qctworksheet.iterrows():
        if row["VIDA_IN"] == "Done":
            new_row = {}
            new_row["Proj"] = row["Proj"]
            new_row["Subj"] = row["Subj"]
            new_row["Img"] = "IN" + str(row["FU"])
            new_row["ImgDir"] = row["VIDA_IN_Path"]
            df_projsubjlist = df_projsubjlist.append(new_row, ignore_index=True)
        if row["VIDA_EX"] == "Done":
            new_row = {}
            new_row["Proj"] = row["Proj"]
            new_row["Subj"] = row["Subj"]
            new_row["Img"] = "EX" + str(row["FU"])
            new_row["ImgDir"] = row["VIDA_EX_Path"]
            df_projsubjlist = df_projsubjlist.append(new_row, ignore_index=True)

    df_projsubjlist = df_projsubjlist.to_csv(index=False, line_terminator="\n").replace(
        ",", "  "
    )

    date = datetime.today().strftime("%Y%m%d")
    with open(f"{OUTPUT_PATH}/ProjSubjList.in.{proj}_{date}", "w") as f:
        f.write(df_projsubjlist)


if __name__ == "__main__":
    prepare_ProjSubList_from_QCTWorksheet("SNUH")
