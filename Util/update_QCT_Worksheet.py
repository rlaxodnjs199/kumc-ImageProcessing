from unicodedata import name
from openpyxl import load_workbook
import pandas as pd
from dotenv import dotenv_values

# Configs --------------------------------------------
PROJ_TO_UPDATE = ["SSCILD", "GALA", "PRECISE"]
CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
QCTWORKSHEET_PATH = CONFIG["QCTWORKSHEET_PATH"]
VIDASHEET_PATH = CONFIG["VIDASHEET_PATH"]
VIDAPROCESSING_MACHINE = CONFIG["VIDAPROCESSING_MACHINE"]
VIDA_RESULT_PATH = CONFIG["VIDA_RESULT_PATH"]
# -----------------------------------------------------


def update_QCTWorksheet_from_VIDAsheet():
    df_vidasheet = pd.read_excel(VIDASHEET_PATH)
    # Initiate empty dataframe
    df_to_update = pd.DataFrame(
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
    # Construct rows to append to QCT_Worksheet from VidaSheet
    for _, row in df_vidasheet.iterrows():
        if row["Proj"] in PROJ_TO_UPDATE:
            subj = row["Subj"].split("_")[0]
            case = df_to_update.query("Subj == @subj and CTDate == @row.ScanDate")

            if case.empty:
                new_row = {}
                new_row["Proj"] = row["Proj"]
                new_row["Subj"] = row["Subj"].split("_")[0]
                new_row["CTDate"] = row["ScanDate"]
                if row["IN/EX"] == "IN":
                    new_row["DCM_IN"] = "O"
                    if row["Progress"] == "Done":
                        new_row["VIDA_IN"] = "Done"
                        new_row["VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_row["VIDA_IN_At"] = VIDAPROCESSING_MACHINE
                    elif pd.isna(row["Progress"]):
                        pass
                    elif "Case" in row["Progress"]:
                        continue
                    else:
                        new_row["VIDA_IN"] = "Fail"
                        new_row["VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_row["VIDA_IN_At"] = VIDAPROCESSING_MACHINE
                else:
                    new_row["DCM_EX"] = "O"
                    if row["Progress"] == "Done":
                        new_row["VIDA_EX"] = "Done"
                        new_row["VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_row["VIDA_EX_At"] = VIDAPROCESSING_MACHINE
                    elif pd.isna(row["Progress"]):
                        pass
                    elif "Case" in row["Progress"]:
                        continue
                    else:
                        new_row["VIDA_EX"] = "Fail"
                        new_row["VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_row["VIDA_EX_At"] = VIDAPROCESSING_MACHINE
                df_to_update = df_to_update.append(new_row, ignore_index=True)
            else:
                if row["IN/EX"] == "IN":
                    df_to_update.loc[case.index, "DCM_IN"] = "O"
                    if row["Progress"] == "Done":
                        df_to_update.loc[case.index, "VIDA_IN"] = "Done"
                        df_to_update.loc[case.index, "VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_IN_At"
                        ] = VIDAPROCESSING_MACHINE
                    elif pd.isna(row["Progress"]):
                        pass
                    else:
                        df_to_update.loc[case.index, "VIDA_IN"] = "Fail"
                        df_to_update.loc[case.index, "VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_IN_At"
                        ] = VIDAPROCESSING_MACHINE
                else:
                    df_to_update.loc[case.index, "DCM_EX"] = "O"
                    if row["Progress"] == "Done":
                        df_to_update.loc[case.index, "VIDA_EX"] = "Done"
                        df_to_update.loc[case.index, "VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_EX_At"
                        ] = VIDAPROCESSING_MACHINE
                    elif pd.isna(row["Progress"]):
                        pass
                    else:
                        df_to_update.loc[case.index, "VIDA_EX"] = "Fail"
                        df_to_update.loc[case.index, "VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_EX_At"
                        ] = VIDAPROCESSING_MACHINE

    df_to_update = df_to_update.fillna("")

    for proj in PROJ_TO_UPDATE:
        # Calculate FU
        df_to_update_portion = df_to_update[df_to_update["Proj"] == proj].sort_values(
            ["Subj", "CTDate"]
        )
        df_to_update_portion["FU"] = (
            df_to_update_portion.groupby("Subj")["CTDate"].rank(method="first") - 1
        ).astype(int)
        # Update the QCT_Worksheet
        with pd.ExcelWriter(QCTWORKSHEET_PATH, engine="openpyxl", mode="a") as writer:
            writer.book = load_workbook(QCTWORKSHEET_PATH)
            writer.sheets = {ws.title: ws for ws in writer.book.worksheets}
            df_to_update_portion.to_excel(writer, sheet_name=proj, index=False)


if __name__ == "__main__":
    update_QCTWorksheet_from_VIDAsheet()
