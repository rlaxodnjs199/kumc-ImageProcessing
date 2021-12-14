import pandas as pd
from openpyxl import load_workbook

QCT_WORKSHEET_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\QCT_Worksheet.xlsx"
SNUH_VIDASHEET_PATH = (
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Data\snuh_vida_total.xlsx"
)
SUBJ_PREFIX = "PM"
HP_LOOKUP = {
    "brmh": "BR",
    "kw_knuh": "KW",
    "nmc": "NM",
    "sb_snubh": "SB",
    "snuh": "SN",
    "snuh-IMA": "SI",
}


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
        if row["Organization"] not in HP_LOOKUP:
            print("Organization cannot be identified!")
            continue
        else:
            subj_id = (
                SUBJ_PREFIX
                + HP_LOOKUP[row["Organization"]]
                + row["StudyID"].replace("-", "")
            )
            case = df_SNUH.query("Subj == @subj_id and Date == @row.CTDate")

        if case.empty:
            new_row_dict = {}
            new_row_dict["Proj"] = row["Proj"].upper()
            new_row_dict["Subj"] = subj_id
            new_row_dict["Date"] = row["CTDate"]
            new_row_dict["FU"] = row["Calculated_FU"]

            if row["Status"] == "Done" or row["Status"] == "F>Done":
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
            if row["Status"] == "Done" or row["Status"] == "F>Done":
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


def write_df_to_excel(filename, df, sheet_name="SNUH", **to_excel_kwargs):
    with pd.ExcelWriter(
        filename,
        engine="openpyxl",
        mode="a",
        date_format="m/d/yyyy",
        datetime_format="yyyymmdd",
    ) as writer:
        writer.book = load_workbook(filename)
        writer.sheets = {ws.title: ws for ws in writer.book.worksheets}
        df.to_excel(writer, sheet_name, **to_excel_kwargs)
    return


if __name__ == "__main__":
    df_total = pd.read_excel(SNUH_VIDASHEET_PATH, sheet_name="0-Total")
    df_SNUH = initialize_base_df()
    df_SNUH = append_row_df(df_SNUH, df_total)

    write_df_to_excel(QCT_WORKSHEET_PATH, df_SNUH, index=False)
