# Usage
# - python send_dicom_to_remote_host.py /e/common/ImageData/C19/VIDA_20210701-01_C19_TK
# Input
# - VIDA results folder path
# Dependency
# - VidaSheet.xlsx
import os
import sys
import argparse
import subprocess
import tarfile
from pathlib import Path
from datetime import datetime
from typing import List
from tqdm import tqdm
import pandas as pd
from dotenv import dotenv_values

parser = argparse.ArgumentParser(
    description="Prepare ProjSubjList.in, Compressed zip of VIDA results and send it to the B2"
)
parser.add_argument(
    "src", metavar="src", type=str, help="VIDA results source folder path"
)
args = parser.parse_args()


# Global Variable -----------------------------------------------------------
XLSX_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\VidaSheet.xlsx"
OUTPUT_PATH = "Data_to_send"
PATH_IN_REMOTE_HOST = f"/data4/common/ImageData"
VIDA_RESULTS_PATH = args.src
OUTPUT_FOLDER = (
    VIDA_RESULTS_PATH.split("/")[-1]
    if VIDA_RESULTS_PATH.split("/")[-1] != ""
    else VIDA_RESULTS_PATH.split("/")[-2]
)
# ---------------------------------------------------------------------------

# HardCoded Variable --------------------------------------------------------
TIMEPOINT = 0
# ---------------------------------------------------------------------------

def _get_case_ids(vida_result_paths=VIDA_RESULTS_PATH) -> List[int]:
    try:
        case_ids = [int(case) for case in os.listdir(vida_result_paths)]
    except:
        sys.exit("Error: Unexpected data included in source path")
    return case_ids


def _get_ProjSubjList_in_path(xlsx_path=XLSX_PATH, path_in_remote_host=PATH_IN_REMOTE_HOST, output_path=OUTPUT_PATH) -> str:
    vidasheet_df = pd.read_excel(xlsx_path, usecols="A:C,I")
    df = vidasheet_df.query('VidaCaseID in @case_ids')
    df['ImgDir'] = f'{path_in_remote_host}/' +  df['Proj'] + '/' + df['VidaCaseID'].astype(str)
    df.rename(columns={"IN/EX": "Img"}, inplace=True)
    df.drop(columns=["VidaCaseID"], inplace=True)

    proj = df['Proj'].iloc[0]
    today = datetime.today().strftime("%Y%m%d")

    df_to_write = df.to_csv(index=False, line_terminator="\n").replace(
        ",", "    "
    )

    with open(f'{output_path}/ProjSubjList.in.{today}_{proj}_T{TIMEPOINT}', 'w') as f:
        f.write(df_to_write)
    
    return f'{output_path}/ProjSubjList.in.{today}_{proj}_T{TIMEPOINT}'


def _compress_vida_results(case_ids: List[int], vida_results_path=VIDA_RESULTS_PATH, output_path=OUTPUT_PATH, output_folder=OUTPUT_FOLDER):
    with tarfile.open(f"{output_path}/{output_folder}.tar.bz2", "w:bz2") as tar:
        for case in tqdm(case_ids):
            tar.add(Path(f"{vida_results_path}/{case}"), f"{output_folder}/{case}")


def _send_vida_results_to_b2(ProjSubjList_in=False):
    ssh_config = dotenv_values(".env")
    port = ssh_config["SSH_PORT"]
    host = ssh_config["SSH_HOST"]
    user = ssh_config["SSH_USERNAME"]
    if ProjSubjList_in:
        ProjSubjList_in_path = _get_ProjSubjList_in_path()
        subprocess.run(
            [
                "scp",
                "-P",
                port,
                f"{ProjSubjList_in_path}",
                f"{user}@{host}:{PATH_IN_REMOTE_HOST}/",
            ]
        )
    subprocess.run(
        [
            "scp",
            "-P",
            port,
            f"{OUTPUT_PATH}/{OUTPUT_FOLDER}.tar.bz2",
            f"{user}@{host}:{PATH_IN_REMOTE_HOST}/",
        ]
    )


if __name__ == '__main__':
    case_ids = _get_case_ids()
    _compress_vida_results(case_ids)
    _send_vida_results_to_b2(ProjSubjList_in=True)