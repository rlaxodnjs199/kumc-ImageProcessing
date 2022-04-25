import os
import string
import pathlib
from os.path import basename, dirname
import argparse
from typing import List, Tuple, Union
from numpy import full
from tqdm import tqdm
from pydicom import Dataset, dcmread
from loguru import logger
import gspread
from dotenv import dotenv_values

# Create an argument parser ##############################################################
parser = argparse.ArgumentParser(
    description="Recursively de-identify and save DICOM images in the DICOM source folder"
)
parser.add_argument("src", metavar="src", type=pathlib.Path, help="DICOM folder path")

args = parser.parse_args()
src_dcm_dir = args.src


def get_dcm_paths_from_dir(src_dcm_dir: pathlib.Path) -> List[pathlib.Path]:
    dcm_paths = []
    for base, _, files in os.walk(src_dcm_dir):
        for file in files:
            full_file_path = os.path.join(base, file)
            if base != dirname(full_file_path):
                logger.error(
                    "DCM file depth greater than 1. Check the original DCM folder."
                )
                return []
            dcm_paths.append(full_file_path)
    return dcm_paths


if __name__ == "__main__":
    print(
        "-------------------------------------------------------------------------------"
    )
    print(f"De-identify DICOMS on path: {src_dcm_dir}")
    print(
        "-------------------------------------------------------------------------------"
    )
    print(get_dcm_paths_from_dir(src_dcm_dir))
