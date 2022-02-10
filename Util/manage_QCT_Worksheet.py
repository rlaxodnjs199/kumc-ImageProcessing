import gspread
import pandas as pd
from loguru import logger
from dotenv import dotenv_values

logger.add(f"logs/qctworksheet.log", level="DEBUG")


class QCTProject:
    def __init__(self, project: str) -> None:
        self.config = dotenv_values(".env")
        self.google_service_account = gspread.service_account(
            filename=self.config["GOOGLE_TOKEN_PATH"]
        )
        self.vidasheet = self.google_service_account.open_by_key(
            self.config["VIDASHEET_GOOGLE_API_KEY"]
        )
        self.qctworksheet = self.google_service_account.open_by_key(
            self.config["QCTWORKSHEET_GOOGLE_API_KEY"]
        )
        self.project = project

    def initialize_project_from_mastersheet(self, mastersheet_path: str):
        pass

    def initialize_project_from_vidasheet(self):
        logger.info(f"Initializing project [{self.project}] in QCT_Worksheet...")
        df_vidasheet = pd.DataFrame(self.vidasheet.sheet1.get_all_records())
        # Initialize new dataframe with column headers
        df_new_project = pd.DataFrame(
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
        # Search row belongs to the project and append to the dataframe
        for _, row in df_vidasheet.iterrows():
            if row["Proj"] == self.project:
                subj = row["Subj"].split("_")[0]
                # Search if an another case in [IN,EX] pair already added to the dataframe
                case = df_new_project.query("Subj == @subj and CTDate == @row.ScanDate")

                if case.empty:
                    new_case = {}
                    new_case["Proj"] = row["Proj"]
                    new_case["Subj"] = subj
                    new_case["CTDate"] = row["ScanDate"]
                    if row["IN/EX"] == "IN":
                        new_case["DCM_IN"] = "O"
                        if row["Progress"] == "Done":
                            new_case["VIDA_IN"] = "Done"
                            new_case["VIDA_IN_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            new_case["VIDA_IN_At"] = self.config["VIDA_RESULT_LOCATION"]
                        # If Progress = blank: add entry
                        elif pd.isna(row["Progress"]):
                            pass
                        # If Progress = Case ID []: Skip without adding entry
                        elif "Case" in row["Progress"]:
                            continue
                        else:
                            new_case["VIDA_IN"] = "Fail"
                            new_case["VIDA_IN_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            new_case["VIDA_IN_At"] = self.config["VIDA_RESULT_LOCATION"]
                    else:
                        new_case["DCM_EX"] = "O"
                        if row["Progress"] == "Done":
                            new_case["VIDA_EX"] = "Done"
                            new_case["VIDA_EX_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            new_case["VIDA_EX_At"] = self.config["VIDA_RESULT_LOCATION"]
                        # If Progress = blank: add entry
                        elif pd.isna(row["Progress"]):
                            pass
                        # If Progress = Case ID []: Skip without adding entry
                        elif "Case" in row["Progress"]:
                            continue
                        else:
                            new_case["VIDA_EX"] = "Fail"
                            new_case["VIDA_EX_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            new_case["VIDA_EX_At"] = self.config["VIDA_RESULT_LOCATION"]
                    df_new_project = df_new_project.append(new_case, ignore_index=True)
                # IN or EX pair already added: Need to integrate into the existing row
                else:
                    if row["IN/EX"] == "IN":
                        df_new_project.loc[case.index, "DCM_IN"] = "O"
                        if row["Progress"] == "Done":
                            df_new_project.loc[case.index, "VIDA_IN"] = "Done"
                            df_new_project.loc[case.index, "VIDA_IN_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            df_new_project.loc[case.index, "VIDA_IN_At"] = self.config[
                                "VIDA_RESULT_LOCATION"
                            ]
                        # If Progress = blank: add entry
                        elif pd.isna(row["Progress"]):
                            pass
                        # If Progress = Case ID []: Skip without adding entry
                        elif "Case" in row["Progress"]:
                            continue
                        else:
                            df_new_project.loc[case.index, "VIDA_IN"] = "Fail"
                            df_new_project.loc[case.index, "VIDA_IN_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            df_new_project.loc[case.index, "VIDA_IN_At"] = self.config[
                                "VIDA_RESULT_LOCATION"
                            ]
                    else:
                        df_new_project.loc[case.index, "DCM_EX"] = "O"
                        if row["Progress"] == "Done":
                            df_new_project.loc[case.index, "VIDA_EX"] = "Done"
                            df_new_project.loc[case.index, "VIDA_EX_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            df_new_project.loc[case.index, "VIDA_EX_At"] = self.config[
                                "VIDA_RESULT_LOCATION"
                            ]
                        # If Progress = blank: add entry
                        elif pd.isna(row["Progress"]):
                            pass
                        # If Progress = Case ID []: Skip without adding entry
                        elif "Case" in row["Progress"]:
                            continue
                        else:
                            df_new_project.loc[case.index, "VIDA_EX"] = "Fail"
                            df_new_project.loc[case.index, "VIDA_EX_Path"] = (
                                self.config["VIDA_RESULT_PATH"]
                                + "\\"
                                + str(row["VidaCaseID"])
                            )
                            df_new_project.loc[case.index, "VIDA_EX_At"] = self.config[
                                "VIDA_RESULT_LOCATION"
                            ]

        df_new_project = df_new_project.fillna("")
        df_new_project["CTDate"].astype(str)
        df_new_project.sort_values(by=["Subj", "CTDate"], inplace=True)
        df_new_project["FU"] = (
            df_new_project.groupby("Subj")["CTDate"].rank(method="first") - 1
        ).astype(int)
        # Create new worksheet by duplicating a template
        try:
            self.qctworksheet.worksheet("Template").duplicate(
                new_sheet_name=self.project
            )
        except:
            # When project already exists, delete the entire
            logger.warning(f"Sheet [{self.project}] already exists.")
            logger.warning(f"Deleting contents in Sheet [{self.project}]...")
            last_row_index = len(
                list(
                    filter(
                        None, self.qctworksheet.worksheet(self.project).col_values(3)
                    )
                )
            )
            self.qctworksheet.worksheet(self.project).delete_rows(2, last_row_index)
        # Append data frame to the new worksheet
        self.qctworksheet.worksheet(self.project).insert_rows(
            df_new_project.values.tolist(), row=2
        )
        logger.info(f"Project [{self.project}] initiated!")

    def update_project_from_vidasheet():
        # update when processed (success or failure)
        # update when new entry created
        pass


if __name__ == "__main__":
    QCTProject("LCP").initialize_project_from_vidasheet()
