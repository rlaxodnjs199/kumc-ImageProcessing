from typing import List
import asyncio
import time
import os, glob
from loguru import logger
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from pydicom import dcmread, FileDataset
import gspread
from dotenv import dotenv_values

CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
GOOGLE_SA = gspread.service_account(filename=CONFIG["GOOGLE_TOKEN_PATH"])
QCTWORKSHEET = GOOGLE_SA.open_by_key(CONFIG["QCTWORKSHEET_GOOGLE_API_KEY"])
IMAGEDATA_PATHS = [
    r"P:\IRB_STUDY00146849_LHC\Data\ImageData",
    r"P:\IRB_STUDY00146630_RheSolve\Data\ImageData",
    r"P:\IRB_STUDY00146203_ SARP 4\Data\ImageData",
    r"P:\IRB_STUDY00144916_PrecISE\Data\ImageData",
    r"P:\IRB_STUDY00146616_COVID_Xe_MRI\Data\ImageData"
]
DEID_FOLDER_MARKER = "deid"
PHANTOM_FOLDER_MARKER = "PHANTOM"


class QctWorksheetWatcher:
    def __init__(self, paths, handler) -> None:
        self.observer = Observer()
        self.handler = handler()
        self.paths = paths

    async def _run(self):
        logger.add(f"logs/watch_VidaVision.log", level="DEBUG")
        for path in self.paths:
            self.observer.schedule(self.handler, path, recursive=True)
            logger.info(f"Watchdog observer starts watching - {path}")
        self.observer.start()

        try:
            while True:
                await asyncio.sleep(1)
        except:
            self.observer.stop()
            logger.info(f"Observer stopped")
        self.observer.join()

    def run(self):
        asyncio.get_event_loop().run_until_complete(self._run())


class DicomHandler(FileSystemEventHandler):
    def __init__(self):
        FileSystemEventHandler.__init__(self)
        self.path = ""

    def on_created(self, event):
        if self.path == event.src_path:
            logger.info("Duplicate event generated -> Skip this event")
        else:
            self.path = event.src_path
            logger.info(f"New folder created: {os.path.basename(event.src_path)}")

            # logger.info("DICOM folder created - % s." % event.src_path)

            # # Wait until first DICOM slice get created
            # while not len(os.listdir(event.src_path)):
            #     time.sleep(1)

            # dicom_slice_path = os.path.join(
            #     event.src_path, os.listdir(event.src_path)[0]
            # )

            # dicom_slice = dcmread(dicom_slice_path)
            # logger.info("Try to update VidaSheet...")
            # try:
            #     append_row_to_VidaSheet_on_vida_import(dicom_slice)
            #     logger.info("Update VidaSheet complete")
            #     self.path = event.src_path
            # except:
            #     logger.error("Update VidaSheet failed")

    def on_modified(self, event):
        #     if self.path == event.src_path:
        #         logger.info("Duplicate event generated -> Skip this event")
        # else:
        self.path = event.src_path
        if DEID_FOLDER_MARKER in os.path.basename(event.src_path):
            pass
        elif PHANTOM_FOLDER_MARKER in os.path.basename(event.src_path):
            pass
        else:
            logger.info(f"Dowloading new DICOM: {event.src_path}")
            time.sleep(0.1)
            try:
                latest_folder_downloaded = max(
                    glob.glob(os.path.join(event.src_path, "*/")), key=os.path.getmtime
                )[:-1]
            except:
                logger.error("Unexpected Delete event")
                return
            proj = os.path.basename(event.src_path).split("_")[-2]
            subj = os.path.basename(latest_folder_downloaded).split("_")[0]
            ctdate = os.path.basename(latest_folder_downloaded).split("_")[1]
            add_row_qctworksheet(proj, subj, ctdate)


def add_row_qctworksheet(proj, subj, ctdate):
    QCTWORKSHEET.worksheet(proj).append_row(values=[proj, subj, ctdate])
    logger.info(f"QCTWorksheet row added: {proj}-{subj}-{ctdate}")


if __name__ == "__main__":
    watcher = QctWorksheetWatcher(IMAGEDATA_PATHS, DicomHandler)
    watcher.run()
