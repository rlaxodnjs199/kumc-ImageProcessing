import os
import gspread
from dotenv import load_dotenv

load_dotenv()


class Config:
    google_sa = gspread.service_account(filename=os.getenv("GOOGLE_TOKEN_PATH"))
    vidasheet = google_sa.open_by_key(os.getenv("VIDASHEET_GOOGLE_API_KEY"))
    qctworksheet = google_sa.open_by_key(os.getenv("QCTWORKSHEET_GOOGLE_API_KEY"))

    vida_result_path = os.getenv("VIDA_RESULT_PATH_PREFIX")
    tar_output_path = os.getenv("TAR_OUTPUT_PATH")

    b2_path = os.getenv("B2_PATH")
    l1_path = os.getenv("L1_PATH")
