import pandas as pd
from loguru import logger
import gspread
from dotenv import dotenv_values

# ----------------------------------------------------------------------
PROJ_TO_INITIALIZE = "LCP"
# ----------------------------------------------------------------------
CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
GOOGLE_SA = gspread.service_account(filename="token.json")
VIDASHEET = GOOGLE_SA.open_by_key(CONFIG["VIDASHEET_GOOGLE_API_KEY"])
QCTWORKSHEET = GOOGLE_SA.open_by_key(CONFIG["QCTWORKSHEET_GOOGLE_API_KEY"])
VIDA_RESULT_PATH = CONFIG["VIDA_RESULT_PATH"]
VIDA_RESULT_LOCATION = CONFIG["VIDA_RESULT_LOCATION"]
# ----------------------------------------------------------------------


def initialize_QCTWorksheet_from_VIDAsheet():
    df_vidasheet = pd.DataFrame(VIDASHEET.sheet1.get_all_records())
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
        if row["Proj"] == PROJ_TO_INITIALIZE:
            subj = row["Subj"].split("_")[0]

            case = df_to_update.query("Subj == @subj and CTDate == @row.ScanDate")

            if case.empty:
                new_case = {}
                new_case["Proj"] = row["Proj"]
                new_case["Subj"] = row["Subj"].split("_")[0]
                new_case["CTDate"] = row["ScanDate"]
                if row["IN/EX"] == "IN":
                    new_case["DCM_IN"] = "O"
                    if row["Progress"] == "Done":
                        new_case["VIDA_IN"] = "Done"
                        new_case["VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_case["VIDA_IN_At"] = VIDA_RESULT_LOCATION
                    # If Progress = blank: add entry
                    elif pd.isna(row["Progress"]):
                        pass
                    # If Progress = Case ID []: Skip without adding entry
                    elif "Case" in row["Progress"]:
                        continue
                    else:
                        new_case["VIDA_IN"] = "Fail"
                        new_case["VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_case["VIDA_IN_At"] = VIDA_RESULT_LOCATION
                else:
                    new_case["DCM_EX"] = "O"
                    if row["Progress"] == "Done":
                        new_case["VIDA_EX"] = "Done"
                        new_case["VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_case["VIDA_EX_At"] = VIDA_RESULT_LOCATION
                    # If Progress = blank: add entry
                    elif pd.isna(row["Progress"]):
                        pass
                    # If Progress = Case ID []: Skip without adding entry
                    elif "Case" in row["Progress"]:
                        continue
                    else:
                        new_case["VIDA_EX"] = "Fail"
                        new_case["VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        new_case["VIDA_EX_At"] = VIDA_RESULT_LOCATION
                df_to_update = df_to_update.append(new_case, ignore_index=True)
            # IN or EX pair already added: Need to integrate to the existing case
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
                        ] = VIDA_RESULT_LOCATION
                    # If Progress = blank: add entry
                    elif pd.isna(row["Progress"]):
                        pass
                    # If Progress = Case ID []: Skip without adding entry
                    elif "Case" in row["Progress"]:
                        continue
                    else:
                        df_to_update.loc[case.index, "VIDA_IN"] = "Fail"
                        df_to_update.loc[case.index, "VIDA_IN_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_IN_At"
                        ] = VIDA_RESULT_LOCATION
                else:
                    df_to_update.loc[case.index, "DCM_EX"] = "O"
                    if row["Progress"] == "Done":
                        df_to_update.loc[case.index, "VIDA_EX"] = "Done"
                        df_to_update.loc[case.index, "VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_EX_At"
                        ] = VIDA_RESULT_LOCATION
                    # If Progress = blank: add entry
                    elif pd.isna(row["Progress"]):
                        pass
                    # If Progress = Case ID []: Skip without adding entry
                    elif "Case" in row["Progress"]:
                        continue
                    else:
                        df_to_update.loc[case.index, "VIDA_EX"] = "Fail"
                        df_to_update.loc[case.index, "VIDA_EX_Path"] = (
                            VIDA_RESULT_PATH + "\\" + str(row["VidaCaseID"])
                        )
                        df_to_update.loc[
                            case.index, "VIDA_EX_At"
                        ] = VIDA_RESULT_LOCATION

    df_to_update = df_to_update.fillna("")
    df_to_update["CTDate"].astype(str)
    df_to_update.sort_values(by=["Subj", "CTDate"], inplace=True)
    df_to_update["FU"] = (
        df_to_update.groupby("Subj")["CTDate"].rank(method="first") - 1
    ).astype(int)
    # Create new worksheet by duplicating a template
    try:
        QCTWORKSHEET.worksheet("Template").duplicate(new_sheet_name=PROJ_TO_INITIALIZE)
    except:
        logger.error(f"Sheet {PROJ_TO_INITIALIZE} already exists.")
        return
    # Append data frame to the new worksheet
    QCTWORKSHEET.worksheet(PROJ_TO_INITIALIZE).insert_rows(
        df_to_update.values.tolist(), row=2
    )


if __name__ == "__main__":
    initialize_QCTWorksheet_from_VIDAsheet()
