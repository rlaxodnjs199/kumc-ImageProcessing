import pandas as pd

DATASHEET_PATH = "Data/Datasheet/DataSheet.xlsx"
CARISSA_WALTER_DATASHEET_PATH = (
    "Data/CarissaWalter/COVID_CTs_20210513CarissaWalter_0608jc.xlsx"
)
HERON_DATASHEET_PATH = "Data/Heron/20210629_HeronData.xlsx"
PULMONARY_MASTER_DATA_PATH = (
    "Data/PulmonaryMaster/PulmonaryMaster-COVID19Inpatientoutp_DATA_2021-06-22_1040.csv"
)

# Prepare dataframes of interest from excel files
datasheet_df = pd.read_excel(DATASHEET_PATH)
carissa_df = pd.read_excel(
    CARISSA_WALTER_DATASHEET_PATH, header=9, usecols="A,I,E,J"
).sort_values(by=["mrn", "date"])
heron_df = pd.read_excel(HERON_DATASHEET_PATH, usecols="A,K")
pulmaster_df = pd.read_csv(PULMONARY_MASTER_DATA_PATH)

# Multi-timepoints, Single-timepoint subjects from CarissaWalter
multi_timepoints_subjects_from_carissa_df = carissa_df[
    carissa_df.duplicated(subset=["Subj"]) == True
].drop_duplicates(subset=["Subj"], keep="first")
single_timepoint_subjects_from_carissa_df = carissa_df.drop_duplicates(
    subset=["Subj"], keep=False
)

# Multi-timepoints from DataSheet
MT_START_VIDA_CASE_ID = 88
MT_END_VIDA_CASE_ID = 1394
multi_timepoints_subjects_from_datasheet_df = datasheet_df[
    (datasheet_df["VidaCaseID"] >= MT_START_VIDA_CASE_ID)
    & (datasheet_df["VidaCaseID"] <= MT_END_VIDA_CASE_ID)
]
multi_timepoints_subjects_from_datasheet_success_df = (
    multi_timepoints_subjects_from_datasheet_df[
        (multi_timepoints_subjects_from_datasheet_df["Vida Progress"] == "Success")
        & (multi_timepoints_subjects_from_datasheet_df["SliceThickness_mm"] <= 2)
    ]
)

multi_timepoints_subjects_from_datasheet_success_df = (
    multi_timepoints_subjects_from_datasheet_success_df[
        multi_timepoints_subjects_from_datasheet_success_df.duplicated(subset="Subj")
        == True
    ].drop_duplicates(subset=["Subj"])
)

# DataSheet_Success N Heron
merge_datasheet_heron_df = pd.merge(
    multi_timepoints_subjects_from_datasheet_success_df,
    heron_df,
    how="inner",
    left_on=["MRN"],
    right_on=["mrn"],
)
# print(merge_datasheet_heron_df.shape)

# DataSheet_Success N PulmonaryMaster
merge_datasheet_pulmaster_df = pd.merge(
    multi_timepoints_subjects_from_datasheet_success_df,
    pulmaster_df,
    how="inner",
    left_on=["MRN"],
    right_on=["mrn"],
)
# print(merge_datasheet_pulmaster_df.shape)

# Current VIDA processing status
VIDA_done_df = multi_timepoints_subjects_from_datasheet_df[
    multi_timepoints_subjects_from_datasheet_df["Progress"] == "Done"
]
print(f"VIDA processing Done: {VIDA_done_df.shape[0]} cases")
VIDA_done_subjects_df = VIDA_done_df[
    VIDA_done_df.duplicated(subset="Subj") == True
].drop_duplicates(subset="Subj")
print(f"VIDA processing Done: {VIDA_done_subjects_df.shape[0]} subjects")
