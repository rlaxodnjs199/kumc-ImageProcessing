import pandas as pd
from openpyxl import load_workbook

QCT_WORKSHEET_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\QCT_Worksheet.xlsx"
SNUH_VIDASHEET_PATH = (
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Data\snuh_vida_total.xlsx"
)


def initialize_base_df() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "Proj",
            "Subj",
            "Date",
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
            "IR_Path",
            "QCT",
            "PostIR",
            "CFD1D",
            "CFD3D",
            "Ptcl1D",
            "Ptcl3D",
        ]
    )


def append_row_df(df_SNUH, df_total):
    for _, row in df_total.iterrows():
        subj_id = row["Organization"] + "-" + row["StudyID"]
        case = df_SNUH.query("Subj == @subj_id and Date == @row.CTDate")
        if case.empty:
            new_row_dict = {}
            new_row_dict["Proj"] = row["Proj"]
            new_row_dict["Subj"] = row["Organization"] + "-" + row["StudyID"]
            new_row_dict["Date"] = row["CTDate"]
            new_row_dict["FU"] = row["Calculated_FU"]

            if row["Status"] == "Done":
                if row["InEx"].upper() == "IN":
                    new_row_dict["DCM_IN"] = "O"
                    new_row_dict["VIDA_IN"] = "Done"
                    new_row_dict["VIDA_IN_At"] = "SNUH/B1"
                    new_row_dict["VIDA_IN_Path"] = row["VIDA_result_Full_Path"]
                else:
                    new_row_dict["DCM_EX"] = "O"
                    new_row_dict["VIDA_EX"] = "Done"
                    new_row_dict["VIDA_EX_At"] = "SNUH/B1"
                    new_row_dict["VIDA_EX_Path"] = row["VIDA_result_Full_Path"]
            elif pd.isna(row["Status"]):
                print("Not processed")
            else:
                if row["InEx"].upper() == "IN":
                    new_row_dict["DCM_IN"] = "O"
                    new_row_dict["VIDA_IN"] = "Fail"
                    new_row_dict["VIDA_IN_At"] = "SNUH/B1"
                    new_row_dict["VIDA_IN_Path"] = row["VIDA_result_Full_Path"]
                else:
                    new_row_dict["DCM_EX"] = "O"
                    new_row_dict["VIDA_EX"] = "Fail"
                    new_row_dict["VIDA_EX_At"] = "SNUH/B1"
                    new_row_dict["VIDA_EX_Path"] = row["VIDA_result_Full_Path"]

            df_SNUH = df_SNUH.append(new_row_dict, ignore_index=True)
        else:
            if row["Status"] == "Done":
                if row["InEx"].upper() == "IN":
                    df_SNUH.loc[case.index, "DCM_IN"] = "O"
                    df_SNUH.loc[case.index, "VIDA_IN"] = "Done"
                    df_SNUH.loc[case.index, "VIDA_IN_At"] = "SNUH/B1"
                    df_SNUH.loc[case.index, "VIDA_IN_Path"] = row[
                        "VIDA_result_Full_Path"
                    ]
                else:
                    df_SNUH.loc[case.index, "DCM_EX"] = "O"
                    df_SNUH.loc[case.index, "VIDA_EX"] = "Done"
                    df_SNUH.loc[case.index, "VIDA_EX_At"] = "SNUH/B1"
                    df_SNUH.loc[case.index, "VIDA_EX_Path"] = row[
                        "VIDA_result_Full_Path"
                    ]
            elif pd.isna(row["Status"]):
                print("Not processed")
            else:
                if row["InEx"].upper() == "IN":
                    df_SNUH.loc[case.index, "DCM_IN"] = "O"
                    df_SNUH.loc[case.index, "VIDA_IN"] = "Fail"
                    df_SNUH.loc[case.index, "VIDA_IN_At"] = "SNUH/B1"
                    df_SNUH.loc[case.index, "VIDA_IN_Path"] = row[
                        "VIDA_result_Full_Path"
                    ]
                else:
                    df_SNUH.loc[case.index, "DCM_EX"] = "O"
                    df_SNUH.loc[case.index, "VIDA_EX"] = "Fail"
                    df_SNUH.loc[case.index, "VIDA_EX_At"] = "SNUH/B1"
                    df_SNUH.loc[case.index, "VIDA_EX_Path"] = row[
                        "VIDA_result_Full_Path"
                    ]
    return df_SNUH.fillna("")


def append_df_to_excel(
    filename, df, sheet_name="SNUH", startrow=None, **to_excel_kwargs
):
    with pd.ExcelWriter(
        filename,
        engine="openpyxl",
        mode="a",
        date_format="m/d/yyyy",
        datetime_format="yyyymmdd",
    ) as writer:
        writer.book = load_workbook(filename)
        startrow = writer.book[sheet_name].max_row
        writer.sheets = {ws.title: ws for ws in writer.book.worksheets}
        df.to_excel(writer, sheet_name, startrow=startrow, **to_excel_kwargs)

    return


if __name__ == "__main__":
    df_total = pd.read_excel(SNUH_VIDASHEET_PATH, sheet_name="0-Total")
    df_SNUH = initialize_base_df()
    df_SNUH = append_row_df(df_SNUH, df_total)

    append_df_to_excel(QCT_WORKSHEET_PATH, df_SNUH, index=False)
