# Usage
# python deidentify_dicom.py {dicom_src_dir}
# >> python deidentify_dicom.py /e/common/ImageData/DCM_20210929_GALA_127-06-005_TK
import os
import pathlib
from os.path import basename, dirname
import argparse
from typing import List
from tqdm import tqdm
from pydicom import Dataset, dcmread

IN_EX_DIR_SYNTAX = ["TLC", "RV"]

# Create an argument parser
parser = argparse.ArgumentParser(
    description="Recursively de-identify and save DICOM images from src"
)
parser.add_argument("src", metavar="src", type=pathlib.Path, help="DICOM source folder path")
args = parser.parse_args()

src_dcm_dir = args.src


def _get_dcm_paths_from_dir(dcm_dir: str) -> List[str]:
    dcm_dir_list = []
    for base, _, files in os.walk(dcm_dir):
        for file in files:
            dcm_dir_list.append(os.path.join(base, file))
    return dcm_dir_list


def _get_patient_id(dcm_path: str) -> str:
    dcm_dir = (
        basename(dirname(dirname(dcm_path)))
        if basename(dirname(dcm_path)) in IN_EX_DIR_SYNTAX
        else basename(dirname(dcm_path))
    )
    return dcm_dir.split("_")[-2]


def _get_dst_dcm_dir(dcm_path: str) -> str:
    if basename(dirname(dcm_path)) in IN_EX_DIR_SYNTAX:
        base_path = dirname(dirname(dirname(dcm_path)))
        in_or_ex = basename(dirname(dcm_path))
        src_dir_name = basename(dirname(dirname(dcm_path)))
        output_dir_prefix = ("_").join(src_dir_name.split("_")[:-1])
        output_dir_name = ("_").join(
            [output_dir_prefix, "DEID", src_dir_name.split("_")[-1]]
        )
        output_dir = os.path.join(base_path + "\\" + output_dir_name)

        if not os.path.exists(os.path.join(base_path, output_dir_name)):
            os.makedirs(output_dir)
        if not os.path.exists(os.path.join(output_dir, in_or_ex)):
            os.makedirs(os.path.join(output_dir, in_or_ex))

        return os.path.join(output_dir, in_or_ex)

    else:
        base_path = dirname(dirname(dcm_path))
        src_dir_name = basename(dirname(dcm_path))
        output_dir_prefix = ("_").join(src_dir_name[:-1])
        output_dir_name = ("_").join(
            [output_dir_prefix, "DEID", src_dir_name.split("_")[-1]]
        )
        output_dir = os.path.join(base_path, output_dir_name)

        if not os.path.exists(os.path.join(base_path, output_dir_name)):
            os.makedirs(output_dir)

        return os.path.join(output_dir)


def _deidentify_dcm_slice(dcm_path: str) -> Dataset:
    dicom_to_deidentify = dcmread(dcm_path)
    patient_id = _get_patient_id(dcm_path)

    try:
        dicom_to_deidentify.PatientID = dicom_to_deidentify.PatientName = patient_id
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


def _save_dcm_slice(deidentified_dcm_slice: Dataset, dcm_path: str):
    dst_file_path = os.path.join(_get_dst_dcm_dir(dcm_path), basename(dcm_path))
    deidentified_dcm_slice.save_as(dst_file_path)


if __name__ == "__main__":
    print(">> Start De-identification...")
    for dcm_path in tqdm(_get_dcm_paths_from_dir(src_dcm_dir)):
        deidentified_dcm_slice = _deidentify_dcm_slice(dcm_path)
        _save_dcm_slice(deidentified_dcm_slice, dcm_path)
    print(f">> De-identification Done. The results are in {src_dcm_dir}")
