import os
import pandas as pd

input_path = r"P:\IRB_STUDY00145795_COVID-19_CT\Data\Data_Clinical\PFT"

master_df = pd.DataFrame()

for excel in os.listdir(input_path):
    if excel.endswith(".xlsx"):
        mrn = excel.split("_")[0]
        pft_date = excel.split("_")[1].split(".")[0]

        df = pd.read_excel(os.path.join(input_path, excel))
        df = df.T.reset_index(drop=True)
        df = df.rename(columns=df.iloc[0])
        df = df.drop(df.index[0]).reset_index(drop=True)
        df = df.iloc[:1, :]
        df_temp = pd.DataFrame({"MRN": mrn, "PFT_date": pft_date}, index=[0])
        df = pd.concat([df_temp, df], axis=1)
        master_df = pd.concat([master_df, df])

master_df.to_excel("output.xlsx", index=False)
