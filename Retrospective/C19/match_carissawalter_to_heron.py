import pandas as pd

CARISSA_WALTER_DATASHEET_PATH = (
    "./Data/CarissaWalter/COVID_CTs_20210513CarissaWalter_0608jc_20210630.xlsx"
)
HERON_DATASHEET_PATH = "./Data/Heron/20210629_HeronData.xlsx"
EXCEL_OUTPUT_PATH = "./Output/C19_Demographics.xlsx"

carissa_df = pd.read_excel(
    CARISSA_WALTER_DATASHEET_PATH, header=9, usecols="A,I,E,J"
).sort_values(by=["mrn", "date"])
heron_df = pd.read_excel(HERON_DATASHEET_PATH, usecols="B,H,K,F,PY,FB,QH,PP")
merged_df = pd.merge(carissa_df, heron_df, how="inner", on=["mrn"])

merged_df.drop_duplicates(subset=["mrn"], keep="first", inplace=True)
merged_df.drop(columns="date", inplace=True)
merged_df.to_excel(EXCEL_OUTPUT_PATH, index=False)
