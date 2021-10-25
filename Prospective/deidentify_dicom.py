# Usage
# python deidentify_dicom.py {dicom_src_dir} {dicom_dst_dir}
#   deidentify_dicom.py
#   /e/common/ImageData/DCM_20210929_GALA_127-06-005_TK
#   /e/common/ImageData/DCM_20210929_GALA_127-06-005_DEID_TK
import os
import argparse
from pydicom import Dataset, dcmread


# Create an argument parser
parser = argparse.ArgumentParser(
    description="Recursively de-identify and save DICOM images from src to dst"
)
parser.add_argument("src", metavar="src", type=str, help="DICOM source folder path")
args = parser.parse_args()

src_dcm_dir = args.src
dst_dcm_dir = ('_').join(src_dcm_dir.split('_')[:-1])
dst_dcm_dir = ('_').join([dst_dcm_dir, 'DEID', src_dcm_dir.split('_')[-1]])

def _get_dcm_paths_from_dir(dcm_dir: str):
    for base, _, files in os.walk(dcm_dir):
        for file in files:
            yield os.path.join(base, file)

def _get_patient_id_from_src_dir(dcm_dir: str) -> str:
    if dcm_dir[-1] == "\\" or dcm_dir[-1] == "/":
        dcm_dir = dcm_dir[:-1]
    
    return os.path.basename(dcm_dir).split('_')[-2]

def _get_patient_id_from_dir(dst_dcm_dir: str) -> str:
    if dst_dcm_dir[-1] == "\\" or dst_dcm_dir[-1] == "/":
        dst_dcm_dir = dst_dcm_dir[:-1]

    return os.path.basename(os.path.dirname(dst_dcm_dir))

def _deidentify_dcm_slice(dcm_path: str, patient_ID: str) -> Dataset:
    dicom_to_deidentify = dcmread(dcm_path)

    try:
        dicom_to_deidentify.PatientID = dicom_to_deidentify.PatientName = patient_ID
    except:
        print(f"{dcm_path}: PatientID or PatientName tag does not exist")
    try:
        dicom_to_deidentify.PatientBirthDate = (
            dicom_to_deidentify.PatientBirthDate[:-4] + "0101"
        )
    except:
        print(f"{dcm_path}: PatientBirthDate tag does not exist")

    tags_to_anonymize = [
        # 'PatientBirthDate',
        # 'PatientSex',
        # 'PatientAge',
        "InstitutionName",
        "InstitutionAddress",
        "InstitutionalDepartmentName",
        "ReferringPhysicianName",
        "ReferringPhysicianTelephoneNumbers",
        "ReferringPhysicianAddress",
        "PhysiciansOfRecord",
        "OperatorsName",
        "IssuerOfPatientID",
        "OtherPatientIDs",
        "OtherPatientNames",
        "OtherPatientIDsSequence",
        "PatientBirthName",
        # 'PatientSize',
        # 'PatientWeight',
        "PatientAddress",
        "PatientMotherBirthName",
        "CountryOfResidence",
        "RegionOfResidence",
        "CurrentPatientLocation",
        "PatientTelephoneNumbers",
        "SmokingStatus",
        "PregnancyStatus",
        "PatientReligiousPreference",
        "RequestingPhysician",
        "PerformingPhysicianName",
        "NameOfPhysiciansReadingStudy",
        "MilitaryRank",
        "EthnicGroup",
        "AdditionalPatientHistory",
        "PatientComments",
        "PersonName",
        "ScheduledPatientInstitutionResidence",
    ]
    for tag in tags_to_anonymize:
        if tag in dicom_to_deidentify:
            delattr(dicom_to_deidentify, tag)
    dicom_to_deidentify.remove_private_tags()

    return dicom_to_deidentify


def _save_dcm_slice(deidentified_dcm_slice: Dataset, dcm_path: str, dst_dcm_dir: str):
    if dcm_path[-1] == "\\" or dcm_path[-1] == "/":
        dcm_path = dcm_path[:-1]
    if dst_dcm_dir[-1] == "\\" or dst_dcm_dir[-1] == "/":
        dst_dcm_dir = dst_dcm_dir[:-1]

    output_file_name = os.path.basename(dcm_path)
    output_dir_name = os.path.basename(os.path.dirname(dcm_path))

    if not os.path.exists(f"{dst_dcm_dir}"):
        os.makedirs(f"{dst_dcm_dir}")

    if not os.path.exists(f"{dst_dcm_dir}/{output_dir_name}"):
        os.makedirs(f"{dst_dcm_dir}/{output_dir_name}")

    deidentified_dcm_slice.save_as(
        f"{dst_dcm_dir}/{output_dir_name}/{output_file_name}"
    )


if __name__ == "__main__":
    # patient_id = _get_patient_id_from_dir(dst_dcm_dir)
    patient_id = _get_patient_id_from_src_dir(src_dcm_dir)
    for dcm_path in _get_dcm_paths_from_dir(src_dcm_dir):
        deidentified_dcm_slice = _deidentify_dcm_slice(dcm_path, patient_id)
        _save_dcm_slice(deidentified_dcm_slice, dcm_path, dst_dcm_dir)
