from typing import Dict
from datetime import datetime
import pandas as pd
import numpy as np
from openpyxl import load_workbook

CARISSA_WALTER_DATASHEET_PATH = r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Data\CarissaWalter\COVID_CTs_20210513CarissaWalter_0608jc.xlsx"
VIDASHEET_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\VidaSheet.xlsx"
QCT_WORKSHEET_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\QCT_Worksheet.xlsx"
OUTPUT_PATH = r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Output\C19_multi.xlsx"

Carissa_df = pd.read_excel(
    CARISSA_WALTER_DATASHEET_PATH, header=9, usecols="A,C,I,J"
).sort_values(by=["mrn", "Time"])
VIDAsheet_df = pd.read_excel(VIDASHEET_PATH)
QCTworksheet_df = pd.read_excel(QCT_WORKSHEET_PATH)

# C19 Multi-timepoints series <all> from CarissaWalterSheet
Carissa_df_multi_timepoints = Carissa_df[
    Carissa_df.duplicated(subset=["Subj"]) == True
].drop_duplicates(subset=["Subj"], keep="first")

# C19 Multi-timepoints series <processed> from VidaSheet
VIDAsheet_df_multi_timepoints = VIDAsheet_df[
    (VIDAsheet_df["VidaCaseID"] >= 81)
    & (VIDAsheet_df["Proj"] == "C19")
    & (VIDAsheet_df["Progress"] == "Done")
]
VIDAsheet_df_multi_timepoints = VIDAsheet_df_multi_timepoints[
    VIDAsheet_df_multi_timepoints.duplicated(subset="Subj", keep=False) == True
].sort_values(by=["Subj", "ScanDate"])
VIDAsheet_df_multi_timepoints = VIDAsheet_df_multi_timepoints.drop_duplicates(
    subset=["Subj"], keep="last"
)
VIDAsheet_df_multi_timepoints.to_excel(OUTPUT_PATH, index=False)

# df_multi_timepoints = pd.merge(
#     Carissa_df_multi_timepoints,
#     VIDAsheet_df_multi_timepoints,
#     how="inner",
#     left_on=["MRN"],
#     right_on=["MRN"],
# )

# print(df_multi_timepoints)
