import sys
import asyncio
import time
import os
from typing import List
from loguru import logger
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from pydicom import dcmread
from pydicom.multival import MultiValue
import gspread
from dotenv import dotenv_values

CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
GOOGLE_SA = gspread.service_account(filename=CONFIG["GOOGLE_TOKEN_PATH"])
VIDASHEET = GOOGLE_SA.open_by_key(CONFIG["VIDASHEET_GOOGLE_API_KEY"])
QCTWORKSHEET = GOOGLE_SA.open_by_key(CONFIG["QCTWORKSHEET_GOOGLE_API_KEY"])
VIDAVISION_PATH = CONFIG["VIDA_RESULT_PATH_PREFIX"]
VIDASHEET_CSV_PATH = CONFIG["VIDASHEET_CSV_PATH"]


class VidaVisionWatcher:
    def __init__(self, path, handler) -> None:
        self.observer = Observer()
        self.handler = handler()
        self.path = path

    async def _run(self):
        logger.add(f"logs/watch_VidaVision.log", level="DEBUG")
        self.observer.schedule(self.handler, self.path, recursive=True)
        self.observer.start()
        logger.info(f"Watchdog observer starts watching - {self.path}")
        try:
            while True:
                await asyncio.sleep(1)
        except:
            self.observer.stop()
            logger.info(f"Observer stopped")
        self.observer.join()

    def run(self):
        asyncio.get_event_loop().run_until_complete(self._run())


class VidaImportHandler(PatternMatchingEventHandler):
    def __init__(self):
        PatternMatchingEventHandler.__init__(self, patterns=["dicom"])
        self.path = ""

    def on_created(self, event):
        if self.path == event.src_path:
            logger.info("Duplicate event generated -> Skip")
        else:
            logger.info("DICOM folder created - % s" % event.src_path)

            # Wait until first DICOM slice is created
            while not len(os.listdir(event.src_path)):
                time.sleep(1)

            vida_case_number = os.path.basename(os.path.dirname(event.src_path))
            # try:
            vida_case = VidaCaseRow(vida_case_number).from_case_number()
            update_vidasheet(vida_case)
            logger.info(f"Update VidaSheet succeed - {vida_case_number}")
        # except:
        #     logger.error(f"Update VidaSheet failed - {vida_case_number}")


class VidaCaseRow:
    def __init__(self, vida_case_number: str):
        self.vida_case_number = vida_case_number

    def from_case_number(self) -> List:
        dicom_folder_path = os.path.join(
            VIDAVISION_PATH, self.vida_case_number, "dicom"
        )
        try:
            dicom_slice_path = os.path.join(
                dicom_folder_path, os.listdir(dicom_folder_path)[0]
            )
        except:
            logger.error(f"DICOM slice has not been created - {self.vida_case_number}")
            return None

        dicom = dcmread(dicom_slice_path)
        proj = ""
        if hasattr(dicom, "DeidentificationMethod"):
            proj = dicom.DeidentificationMethod
        # When VIDA append case number at the end of PatientID, then exclude the case number.
        subj = (
            dicom.PatientID
            if len(dicom.PatientID.split("_")) == 1
            else dicom.PatientID.split("_")[0]
        )
        vida_by = ""
        mrn = ""
        vida_progress = ""
        progress = ""
        scan_date = dicom.AcquisitionDate
        scan_type = "IN"
        for ex_validator in ["EX", "RV"]:
            if ex_validator in dicom.SeriesDescription.upper():
                scan_type = "EX"
        protocol = dicom.SeriesDescription
        disease = ""
        slice_thickness = dicom.SliceThickness
        scanner_vendor = dicom.Manufacturer
        scanner_model = dicom.ManufacturerModelName
        kernel = dicom.ConvolutionKernel
        if isinstance(kernel, List) or isinstance(kernel, MultiValue):
            kernel = kernel[0]
        comments = ""
        path = os.path.join(VIDAVISION_PATH, self.vida_case_number)

        return [
            proj,
            subj,
            self.vida_case_number,
            vida_by,
            mrn,
            vida_progress,
            progress,
            scan_date,
            scan_type,
            protocol,
            disease,
            slice_thickness,
            scanner_vendor,
            scanner_model,
            kernel,
            comments,
            path,
        ]


def update_vidasheet(vida_case_row: List[str]):
    if VIDASHEET.worksheet("Sheet1").find(vida_case_row[2]):
        logger.warning(f"Skip duplicate VIDA sheet update on case - {vida_case_row[2]}")
        return
    VIDASHEET.worksheet("Sheet1").append_row(vida_case_row)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "-r":
            if len(sys.argv) == 4:
                vida_case_numbers_start = sys.argv[2]
                vida_case_numbers_end = sys.argv[3]
                vida_case_numbers = [
                    str(vida_case_number)
                    for vida_case_number in range(
                        int(vida_case_numbers_start), int(vida_case_numbers_end) + 1
                    )
                ]
            else:
                print("Please enter two case numbers for the range")
                vida_case_numbers = []
        else:
            vida_case_numbers = sys.argv[1:]
        for vida_case_number in vida_case_numbers:

            vida_case = VidaCaseRow(vida_case_number).from_case_number()
            update_vidasheet(vida_case)

        logger.info("Update VidaSheet succeed")
    else:
        VidaImportWatcher = VidaVisionWatcher(VIDAVISION_PATH, VidaImportHandler)
        VidaImportWatcher.run()
