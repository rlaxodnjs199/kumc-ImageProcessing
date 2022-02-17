# Usage
# python deidentify.py {dicom_src_dir}
# >> python deidentify.py /p/IRB_STUDY00146630_RheSolve/Data/ImageData/DCM_20220216-16_GALA_TK/127-06-15_20220216/
import os
import pathlib
from os.path import basename, dirname
import argparse
from typing import List, Tuple, Union
from tqdm import tqdm
from pydicom import Dataset, dcmread
from loguru import logger

# Create an argument parser ##############################################################
parser = argparse.ArgumentParser(
    description="Recursively de-identify and save DICOM images in the DICOM source folder"
)
parser.add_argument("src", metavar="src", type=pathlib.Path, help="DICOM folder path")
parser.add_argument("-p", "--project", action="store", type=str, help="Project Name")
parser.add_argument("-s", "--subject", action="store", type=str, help="Subject ID")

args = parser.parse_args()
src_dcm_dir = args.src

# Global variables ########################################################################
DEID_DCM_DIRNAME = "DEID"
TAGS_TO_ANONYMIZE = [
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
VALIDATE_SUBSTRINGS = ["IN", "EX", "TLC", "RV"]
########################################################################################


def get_metadata_from_dcm_path(dcm_dir: str) -> Tuple[str]:
    if args.project:
        proj = args.project
    else:
        proj = basename(dirname(dcm_dir)).split("_")[-2]

    if args.subject:
        subj = args.subject
    else:
        subj = basename(dcm_dir).split("_")[0]

    return proj, subj


def get_dcm_paths_from_dcm_dir(src_dcm_dir: str) -> List[pathlib.Path]:
    dcm_paths = []
    for base, _, files in os.walk(src_dcm_dir):
        for file in files:
            full_file_path = os.path.join(base, file)
            if str(dirname(full_file_path)) == str(src_dcm_dir):
                dcm_paths.append(full_file_path)
            else:
                logger.error(
                    "DCM file depth greater than 1. Check the original DCM folder."
                )
                return []
    return dcm_paths


def prepare_deid_dcm_dir(src_dcm_dir) -> pathlib.Path:
    deid_dcm_dir = DEID_DCM_DIRNAME
    deid_dcm_dir_path = os.path.join(src_dcm_dir, deid_dcm_dir)

    if not os.path.exists(deid_dcm_dir_path):
        os.makedirs(deid_dcm_dir_path)
        logger.info(f"DEID folder created at: {deid_dcm_dir_path}")
    else:
        logger.info(f"DEID folder already created at: {deid_dcm_dir_path}")

    return deid_dcm_dir_path


def filter_dcm_img_to_deidentify(dcm_img: Dataset) -> bool:
    for validate_substring in VALIDATE_SUBSTRINGS:
        if validate_substring in dcm_img.SeriesDescription.upper():
            return True
    return False


@logger.catch
def deidentify_dcm_img(
    dcm_img_path: pathlib.Path, proj: str, subj: str
) -> Union[Tuple[Dataset, str], None]:
    dcm_img: Dataset = dcmread(dcm_img_path)

    if filter_dcm_img_to_deidentify(dcm_img):
        # PatientID = subj, PatientName = subj
        try:
            dcm_img.PatientID = dcm_img.PatientName = subj
        except:
            logger.warning(
                f"{dcm_img_path}: [PatientID] or [PatientName] tag does not exist"
            )
        # Anonymize month & day of birthdate to '0101'
        try:
            dcm_img.PatientBirthDate = dcm_img.PatientBirthDate[:-4] + "0101"
        except:
            logger.warning(f"{dcm_img_path}: [PatientBirthDate] tag does not exist")
        # Delete tags to anonymize
        for tag in TAGS_TO_ANONYMIZE:
            if tag in dcm_img:
                delattr(dcm_img, tag)
        dcm_img.remove_private_tags()
        # Record proj at 'DeidentificationMethod' tag
        dcm_img.add_new([0x0012, 0x0063], "LO", proj)
        # Construct deidentified DICOM folder path
        deid_dcm_dirname_components = [
            "DCM",
            proj,
            subj,
            dcm_img.SeriesDescription,
        ]
        deid_dcm_dirname = ("_").join(deid_dcm_dirname_components)

        return dcm_img, deid_dcm_dirname

    else:
        return None, None


def save_dcm_img(
    deidentified_dcm_img: Dataset,
    deid_dcm_dir: pathlib.Path,
    deid_dcm_dirname: str,
    dcm_img_path: pathlib.Path,
):
    deid_dcm_dirpath = os.path.join(deid_dcm_dir, deid_dcm_dirname)

    if not os.path.exists(deid_dcm_dirpath):
        os.makedirs(deid_dcm_dirpath)

    deid_dcm_img_path = os.path.join(deid_dcm_dirpath, basename(dcm_img_path))
    deidentified_dcm_img.save_as(deid_dcm_img_path)


if __name__ == "__main__":
    logger.info(f"De-Identification started on path: {src_dcm_dir}")

    proj, subj = get_metadata_from_dcm_path(src_dcm_dir)
    dcm_img_paths = get_dcm_paths_from_dcm_dir(src_dcm_dir)
    deid_dcm_dir = prepare_deid_dcm_dir(src_dcm_dir)

    for dcm_img_path in tqdm(dcm_img_paths):
        deidentified_dcm_img, deid_dcm_dirname = deidentify_dcm_img(
            dcm_img_path, proj, subj
        )
        if deidentified_dcm_img:
            save_dcm_img(
                deidentified_dcm_img, deid_dcm_dir, deid_dcm_dirname, dcm_img_path
            )

    logger.info(f"De-Identification finished: Results at {deid_dcm_dir}")
