"""
Once VIDA processing is finished for some VIDA cases, transfer those case from
VIDA folder (/e/VIDA/VIDAvision2.2) to transfer folder (/e/VIDA_more/NeedTransfer)
and update VidaSheet (Progress, VidaBy)
"""
import os
import sys
from typing import List, Optional
import gspread
from gspread import Cell
import shutil
from dotenv import load_dotenv

load_dotenv()
google_sa_token_path = os.getenv("GOOGLE_TOKEN_PATH", "token.json")
google_sa = gspread.service_account(filename=google_sa_token_path)
vidasheet = google_sa.open_by_key(os.getenv("VIDASHEET_GOOGLE_API_KEY")).worksheet(
    "Sheet1"
)
qctworksheet = google_sa.open_by_key(os.getenv("QCTWORKSHEET_GOOGLE_API_KEY"))

vida_result_path = os.getenv("VIDA_RESULT_PATH", r"E:\VIDA\VIDAvision2.2")
vida_transfer_path = os.getenv("VIDA_TRANSFER_PATH", r"E:\VIDA_more\NeedTransfer")
tar_output_path = os.getenv("TAR_OUTPUT_PATH")

b2_path = os.getenv("B2_PATH")
l1_path = os.getenv("L1_PATH")

cells_to_update = []

user_dict = {"tkim3": "TK"}


def transfer_vida_case(case_id: str):
    """
    Transfer VIDA result from VIDA_RESULT_PATH to VIDA_TRANSFER_PATH
    """
    src = os.path.join(vida_result_path, case_id)
    dst = os.path.join(vida_transfer_path, case_id)

    try:
        shutil.copytree(src, dst)
    except Exception as e:
        print(e)


def update_vidasheet(case_id: str, cells_to_update: List[Cell], status: str = "Done"):
    """
    Append cells to update to the global list after finishing VIDA processing
    """
    case: Optional[Cell] = vidasheet.find(case_id)
    if case:
        case_row = case.row
        progress_cell = Cell(case_row, 7, status)
        processed_by_cell = Cell(case_row, 4, user_dict[os.getlogin()])
        cells_to_update.append(progress_cell)
        cells_to_update.append(processed_by_cell)
    else:
        print(f"Could not find case ID {case_id} in VidaSheet")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-r":
            if len(sys.argv) == 4:
                case_id_start = sys.argv[2]
                case_id_end = sys.argv[3]
                case_ids = [
                    str(case_id)
                    for case_id in range(int(case_id_start), int(case_id_end) + 1)
                ]
            else:
                print("Please enter two case numbers for the range")
                case_ids = []
            for case_id in case_ids:
                transfer_vida_case(case_id)
        else:
            case_ids = sys.argv[1:]
            for case_id in case_ids:
                transfer_vida_case(case_id)
                update_vidasheet(case_id, cells_to_update)
            vidasheet.update_cells(cells_to_update)
