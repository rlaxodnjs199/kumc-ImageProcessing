import os
from config import Config


class VidaCase:
    vidasheet = Config.vidasheet.worksheet("Sheet1")

    def __init__(self, case_number) -> None:
        self.case_number = case_number
        case_row = VidaCase.vidasheet.find(self.case_number).row
        self.proj = VidaCase.vidasheet.cell(case_row, 1).value
        self.subj = VidaCase.vidasheet.cell(case_row, 2).value
        self.ctdate = VidaCase.vidasheet.cell(case_row, 8).value
        self.in_ex = VidaCase.vidasheet.cell(case_row, 9).value
        self.local_path = os.path.join(Config.vida_result_path, case_number)
