from operator import index
from typing import Dict
import pandas as pd
import numpy as np
from openpyxl import load_workbook

QCT_WORKSHEET_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\QCT_Worksheet.xlsx"
CARISSA_WALTER_DATASHEET_PATH = r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Data\CarissaWalter\COVID_CTs_20210513CarissaWalter_0608jc.xlsx"

qct_df = pd.read_excel(QCT_WORKSHEET_PATH, sheet_name="C19")
carissa_df = pd.read_excel(CARISSA_WALTER_DATASHEET_PATH, header=9, usecols="A,I")
qct_df_filtered = qct_df[qct_df["IR"] == "O"]

final = pd.merge(
    qct_df_filtered, carissa_df, how="inner", left_on="Subj", right_on="Subj"
)
final = final.drop_duplicates(subset=["Subj", "Date"])
final = final[["Proj", "Subj", "Date", "FU", "mrn"]]
final.to_excel(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Output\C19_subjects_20211119.xlsx",
    index=False,
)
