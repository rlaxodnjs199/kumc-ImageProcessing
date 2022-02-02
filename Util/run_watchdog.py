from typing import List
import asyncio
import time
import os
from loguru import logger
from watchdog.events import PatternMatchingEventHandler
from watchdog.observers import Observer
from pydicom import dcmread, FileDataset
import gspread
from dotenv import dotenv_values

CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
GOOGLE_SA = gspread.service_account(filename="token.json")
VIDASHEET = GOOGLE_SA.open_by_key(CONFIG["VIDASHEET_GOOGLE_API_KEY"])
QCTWORKSHEET = GOOGLE_SA.open_by_key(CONFIG["QCTWORKSHEET_GOOGLE_API_KEY"])
VIDA_RESULT_PATH = CONFIG["VIDA_RESULT_PATH"]


class VidaVisionWatcher:
    def __init__(self, path, handler) -> None:
        self.observer = Observer()
        self.handler = handler()
        self.path = path

    async def _run(self):
        logger.add(f"logs/watch_VidaVision.log", level="DEBUG")
        self.observer.schedule(self.handler, self.path, recursive=True)
        self.observer.start()
        logger.info(f"Observer started: {self.path}")
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

    def on_created(self, event):
        logger.info("DICOM folder created - % s." % event.src_path)

        # Wait until first DICOM slice get created
        while not len(os.listdir(event.src_path)):
            time.sleep(1)

        dicom_slice_path = os.path.join(event.src_path, os.listdir(event.src_path)[0])

        dicom_slice = dcmread(dicom_slice_path)
        append_row_to_VidaSheet_on_vida_import(dicom_slice)


def construct_new_vida_case(dicom_slice: FileDataset) -> List[str]:
    Proj = dicom_slice.ImageComments if dicom_slice.ImageComments else ""
    Subj = dicom_slice.PatientID
    VidaCaseID = (
        int(list(filter(None, VIDASHEET.worksheet("Sheet1").col_values(3)))[-1]) + 1
    )
    VidaBy = ""
    MRN = ""
    VidaProgress = ""
    Progress = ""
    ScanDate = dicom_slice.AcquisitionDate
    IN_EX = ""
    CT_Protocol = dicom_slice.SeriesDescription
    Disease = ""
    SliceThickness_mm = dicom_slice.SliceThickness
    ScannerVender = dicom_slice.Manufacturer
    ScannerModel = dicom_slice.ManufacturerModelName
    Kernel = dicom_slice.ConvolutionKernel
    Comments = ""
    VIDA_path = VIDA_RESULT_PATH + "\\" + str(VidaCaseID)

    return [
        Proj,
        Subj,
        VidaCaseID,
        VidaBy,
        MRN,
        VidaProgress,
        Progress,
        ScanDate,
        IN_EX,
        CT_Protocol,
        Disease,
        SliceThickness_mm,
        ScannerVender,
        ScannerModel,
        Kernel,
        Comments,
        VIDA_path,
    ]


def append_row_to_VidaSheet_on_vida_import(dicom_slice: FileDataset):
    vida_case = construct_new_vida_case(dicom_slice)
    VIDASHEET.worksheet("Sheet1").append_row(vida_case)


if __name__ == "__main__":
    VidaImportWatcher = VidaVisionWatcher(VIDA_RESULT_PATH, VidaImportHandler)
    VidaImportWatcher.run()
