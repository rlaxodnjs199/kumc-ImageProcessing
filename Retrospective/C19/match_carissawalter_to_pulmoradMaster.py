import pandas as pd

CARISSA_WALTER_DATA_PATH = (
    "Data/CarissaWalter/COVID_CTs_20210513CarissaWalter_0608jc_20210616.xlsx"
)
PULMONARY_MASTER_DATA_PATH = (
    "Data/PulmonaryMaster/PulmonaryMaster-COVID19Inpatientoutp_DATA_2021-06-22_1040.csv"
)

CW_DATA = pd.read_excel(CARISSA_WALTER_DATA_PATH, header=9, usecols="S,R,I,A")
PM_DATA = pd.read_csv(PULMONARY_MASTER_DATA_PATH)

CW_DATA["first_name"] = CW_DATA["name"].str.split().str[-1]
CW_DATA["last_name"] = CW_DATA["name"].str.split().str[0]

PM_DATA_DICT = {}
for _, row in PM_DATA.iterrows():
    key = row["dob"]
    value = {}
    value["first_name"] = row["first_name"]
    value["last_name"] = row["last_name"]
    value["redcap_id"] = row["redcap_id"]
    value["generated_id"] = row["generated_id"]

    if key not in PM_DATA_DICT:
        PM_DATA_DICT[key] = []

    PM_DATA_DICT[key].append(value)

patient_set = {0}
for _, row in CW_DATA.iterrows():
    key = row["birth"].strftime("%Y-%m-%d")
    if key in PM_DATA_DICT:
        for subj in PM_DATA_DICT[key]:
            if row["first_name"] == subj["first_name"].upper():
                patient_set.add(row["mrn"])
# print(patient_set)

mrn_set = {0}
for _, row in PM_DATA.iterrows():
    mrn_set.add(row["mrn"])
# print(mrn_set)
count = 0
for _, row in CW_DATA.iterrows():
    if row["mrn"] in mrn_set:
        mrn_set.remove(row["mrn"])
        count += 1

print(f"matching patients looking at mrn: {count}")
print(f"matching patients looking at birthdate, name: {len(patient_set)}")
