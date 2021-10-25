import pandas as pd

START_VIDA_CASE_ID = 960
END_VIDA_CASE_ID = 1394
EXCEL_PATH = "Data/Datasheet/DataSheet.xlsx"
df = pd.read_excel(EXCEL_PATH, sheet_name=0)
df = df[(df["VidaCaseID"] >= START_VIDA_CASE_ID) & (df["VidaCaseID"] <= 1394)]

SUCCESS_COUNT = 0
NEED_LABELS_COUNT = 0
FAILURE_COUNT = 0

for _, row in df.iterrows():
    if row["Vida Progress"] == "Success":
        SUCCESS_COUNT += 1
    elif row["Vida Progress"] == "Needs Labels":
        NEED_LABELS_COUNT += 1
    else:
        FAILURE_COUNT += 1

print(
    f"SUCCESS: {SUCCESS_COUNT}, NEED_LABELS: {NEED_LABELS_COUNT}, FAILURE: {FAILURE_COUNT}"
)

print(df["Vida Progress"].value_counts())

need_to_work_df = df[(df["Vida Progress"] == "Success")]
print(need_to_work_df["SliceThickness_mm"].value_counts())

need_label_df = df[(df["Vida Progress"] == "Needs Labels")]
print(need_label_df["SliceThickness_mm"].value_counts())

failure_label_df = df[
    (df["Vida Progress"] != "Success") & (df["Vida Progress"] != "Needs Labels")
]
print(failure_label_df["SliceThickness_mm"].value_counts())
