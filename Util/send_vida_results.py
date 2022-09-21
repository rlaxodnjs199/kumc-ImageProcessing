import os
from pathlib import Path
import sys
import tarfile
from datetime import datetime
import time
from typing import List
from loguru import logger
import gspread
from dotenv import dotenv_values
from paramiko import SSHClient
from scp import SCPClient
from tqdm import tqdm
import pandas as pd

CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
GOOGLE_SA = gspread.service_account(filename=CONFIG["GOOGLE_TOKEN_PATH"])
VIDASHEET = GOOGLE_SA.open_by_key(CONFIG["VIDASHEET_GOOGLE_API_KEY"])
QCTWORKSHEET = GOOGLE_SA.open_by_key(CONFIG["QCTWORKSHEET_GOOGLE_API_KEY"])

VIDA_RESULT_PATH_PREFIX = CONFIG["VIDA_RESULT_PATH_PREFIX"]
TAR_OUTPUT_PATH = CONFIG["TAR_OUTPUT_PATH"]

B2_PATH = CONFIG["B2_PATH"]
L1_PATH = "/data2/common/ImageData/"
PROJECT = "ILD"


class VidaCase:
    def __init__(self, vida_case_id: str) -> None:
        vidasheet = VIDASHEET.worksheet("Sheet1")
        case_row = vidasheet.find(vida_case_id).row
        self.proj = vidasheet.cell(case_row, 1).value
        self.subj = vidasheet.cell(case_row, 2).value
        self.ctdate = vidasheet.cell(case_row, 8).value
        self.in_ex = vidasheet.cell(case_row, 9).value
        self.case_id = vida_case_id
        self.path = os.path.join(VIDA_RESULT_PATH_PREFIX, vida_case_id)

    def update_qctworksheet(self) -> None:
        case_row = QCTWORKSHEET.worksheet(self.proj).find(self.subj)
        if (
            str(self.ctdate)
            == QCTWORKSHEET.worksheet(self.proj).row_values(case_row.row)[2]
        ):
            if self.in_ex == "IN":
                QCTWORKSHEET.worksheet(self.proj).update_cell(case_row.row, 7, "Done")
                QCTWORKSHEET.worksheet(self.proj).update_cell(
                    case_row.row, 9, self.path
                )
                QCTWORKSHEET.worksheet(self.proj).update_cell(case_row.row, 11, "L1")
            else:
                QCTWORKSHEET.worksheet(self.proj).update_cell(case_row.row, 8, "Done")
                QCTWORKSHEET.worksheet(self.proj).update_cell(
                    case_row.row, 10, self.path
                )
                QCTWORKSHEET.worksheet(self.proj).update_cell(case_row.row, 12, "L1")
            logger.info(
                f"QCTWorksheet row updated: {self.proj}:{self.subj}:{self.ctdate} - {QCTWORKSHEET.worksheet(self.proj).row_values(case_row.row)}"
            )


def tar_vida_cases(vida_cases: List[VidaCase]) -> Path:
    project = vida_cases[0].proj
    date = datetime.today().strftime("%Y%m%d")
    tar_path = os.path.join(TAR_OUTPUT_PATH, f"VIDA_{date}_{project}.tar.bz2")

    with tarfile.open(tar_path, "w:bz2") as tar:
        for vida_case in tqdm(vida_cases):
            tar.add(Path(f"{vida_case.path}"), f"{vida_case.case_id}")

    return tar_path


def transfer_tar(tar_path: Path, path: Path) -> None:
    def progress4(filename, filesize, filesent, peername):
        sys.stdout.write(
            "(%s:%s) %ss progress: %.2f%%   \r"
            % (
                peername[0],
                peername[1],
                filename,
                float(filesent) / float(filesize) * 100,
            )
        )

    with SSHClient() as ssh:
        ssh.load_system_host_keys()
        ssh.connect("l1", username="twkim")
        with SCPClient(ssh.get_transport(), progress4=progress4) as scp:
            logger.info(f"Transfering VIDA Tarfile...")
            time_begin = time.time()
            scp.put(tar_path, remote_path=path)
            time_end = time.time()
            time_interval = time_end - time_begin
            logger.info(f"Finished - execution time: {time_interval}s")


def transfer_all_done_cases():
    XLSX_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\VidaSheet.xlsx"
    df = pd.read_excel(XLSX_PATH)
    done_df = df[df.Progress == "Done"]
    proj_list = done_df.Proj.unique()
    case_dict = {}

    for proj in proj_list:
        proj_done_df = done_df[done_df.Proj == proj]
        proj_done_case_list = proj_done_df.VidaCaseID.to_list()
        case_dict[proj] = proj_done_case_list

    for proj, case_list in case_dict.items():
        date = datetime.today().strftime("%Y%m%d")
        tar_path = os.path.join(TAR_OUTPUT_PATH, f"VIDA_{proj}_{date}.tar.bz2")
        with tarfile.open(tar_path, "w:bz2") as tar:
            for case in tqdm(case_list):
                vidamachine_case_path = os.path.join(VIDA_RESULT_PATH_PREFIX, str(case))
                if isdir(vidamachine_case_path):
                    tar.add(Path(vidamachine_case_path), str(case))

        transfer_tar(tar_path, f"{L1_PATH}")


if __name__ == "__main__":
    cases = sys.argv[1:]
    vida_cases = [VidaCase(case) for case in cases]
    project = vida_cases[0].proj
    # for vida_case in vida_cases:
    #     vida_case.update_qctworksheet()
    tar_path = tar_vida_cases(vida_cases)
    transfer_tar(tar_path, f"{L1_PATH}/{project}")
    # transfer_all_done_cases()
