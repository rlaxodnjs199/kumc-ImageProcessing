import sched
import time
from datetime import datetime
from loguru import logger
import gspread
import pandas as pd
from pandas import DataFrame
from dotenv import dotenv_values
from paramiko import SSHClient
from scp import SCPClient

CONFIG = dotenv_values(
    r"C:\Users\tkim3\Documents\Codes\ImageProcessing\Scripts\Util\.env"
)
GOOGLE_SA = gspread.service_account(filename=CONFIG["GOOGLE_TOKEN_PATH"])
VIDASHEET = GOOGLE_SA.open_by_key(CONFIG["VIDASHEET_GOOGLE_API_KEY"])
QCTWORKSHEET = GOOGLE_SA.open_by_key(CONFIG["QCTWORKSHEET_GOOGLE_API_KEY"])
VIDA_RESULT_PATH = CONFIG["VIDA_RESULT_PATH"]
VIDASHEET_CSV_PATH = CONFIG["VIDASHEET_CSV_PATH"]

SCHEDULER = sched.scheduler(time.time, time.sleep)


def locally_save_vidasheet():
    DataFrame(VIDASHEET.worksheet("Sheet1").get_all_records()).to_csv(
        VIDASHEET_CSV_PATH,
        index=False,
    )


def find_df_change() -> DataFrame:
    try:
        old_vida_df = pd.read_csv(VIDASHEET_CSV_PATH)[
            ["VidaCaseID", "Progress"]
        ].fillna("")
    except:
        logger.warn("csv file does not exist")
        return
    new_vida_df = DataFrame(VIDASHEET.worksheet("Sheet1").get_all_records())

    vida_diff = old_vida_df.compare(new_vida_df[["VidaCaseID", "Progress"]])
    df_diff = new_vida_df.iloc[vida_diff.index]
    if not df_diff.empty:
        locally_save_vidasheet()
        logger.info("VIDA sheet updated locally")

    df_diff_completed = df_diff[df_diff["Progress"] == "Done"]

    return df_diff_completed


# def prepare_projsubjlist(df: DataFrame):
#     df_projsubjlist = DataFrame(columns=["Proj", "Subj", "Img", "ImgDir"])

#     for _, row in df.iterrows():
#         new_row = {}
#         new_row["Proj"] = row["Proj"]
#         new_row["Subj"] = row["Subj"]
#         new_row["Img"] = row["IN/EX"]
#         new_row["ImgDir"] = row[""]


def update_qctworksheet(proj, subj, ctdate: int, in_ex: str, path: str):
    cell_lookup = QCTWORKSHEET.worksheet(proj).find(subj)

    if str(ctdate) == QCTWORKSHEET.worksheet(proj).row_values(cell_lookup.row)[2]:
        if in_ex == "IN":
            QCTWORKSHEET.worksheet(proj).update_cell(cell_lookup.row, 7, "Done")
            QCTWORKSHEET.worksheet(proj).update_cell(cell_lookup.row, 9, path)
            QCTWORKSHEET.worksheet(proj).update_cell(cell_lookup.row, 11, "L1")
        else:
            QCTWORKSHEET.worksheet(proj).update_cell(cell_lookup.row, 8, "Done")
            QCTWORKSHEET.worksheet(proj).update_cell(cell_lookup.row, 10, path)
            QCTWORKSHEET.worksheet(proj).update_cell(cell_lookup.row, 12, "L1")
        logger.info(
            f"QCTWorksheet row updated: {proj}-{subj}-{ctdate}: {QCTWORKSHEET.worksheet(proj).row_values(cell_lookup.row)}"
        )


def send_dicoms_to_l1(df: DataFrame):
    # Instantiating SSH client
    with SSHClient() as ssh:
        ssh.load_system_host_keys()
        ssh.connect("l1", username="twkim")
        # Transfer directory to the remote_path
        with SCPClient(ssh.get_transport()) as scp:
            total_execution_begin = time.time()
            # df_projsubjlist = DataFrame(columns=["Proj", "Subj", "Img", "ImgDir"])
            for _, row in df.iterrows():
                proj = row["Proj"]
                subj = row["Subj"]
                subj_parsed = row["Subj"].replace("-", "")
                in_ex = row["IN/EX"]
                ctdate = row["ScanDate"]
                src_path = row["VIDA path"]
                case_id = row["VidaCaseID"]
                dst_path = (
                    f"/home/twkim/test/ImageData/{proj}/{subj_parsed}_{ctdate}_{in_ex}"
                )
                # Add entry to ProjSubjList.in
                # new_projsubjlist_row = {}
                # new_projsubjlist_row["Proj"] = proj
                # new_projsubjlist_row["Subj"] = subj
                # new_projsubjlist_row["Img"] = in_ex
                # new_projsubjlist_row["ImgDir"] = dst_path
                # df_projsubjlist = df_projsubjlist.append(
                #     new_projsubjlist_row, ignore_index=True
                # )
                # Transfer VIDA result
                logger.info(f"Transfering VidaCaseID {case_id}...")
                execution_begin = time.time()
                scp.put(
                    src_path,
                    recursive=True,
                    remote_path=dst_path,
                )
                execution_end = time.time()
                execution_interval = execution_end - execution_begin
                logger.info(
                    f"Transfer finished - execution time: {execution_interval}s"
                )
                # Update QCTWorksheet
                update_qctworksheet(proj, subj, ctdate, in_ex, dst_path)
            # Save & Transfer ProjSubjList.in
            # df_projsubjlist = df_projsubjlist.to_csv(
            #     index=False, line_terminator="\n"
            # ).replace(",", "  ")
            # date = datetime.today().strftime("%Y%m%d")
            # src_projsubjlist_path = CONFIG['SRC_PROJSUBJLIST_PATH']
            # with open(f"{src_projsubjlist_path}/ProjSubjList_{date}", "w") as f:
            #     f.write(df_projsubjlist)
            # dst_projsubjlist_path =
            # scp.put(
            # )

            total_execution_end = time.time()
            total_execution_interval = total_execution_end - total_execution_begin
            logger.info(
                f"DICOM Transfer finished - total execution time: {total_execution_interval}s"
            )


def update_qctworksheet_on_finishing_vida_process():
    df_diff = find_df_change()
    if not df_diff.empty:
        send_dicoms_to_l1(df_diff)
    SCHEDULER.enter(60, 1, update_qctworksheet_on_finishing_vida_process)


if __name__ == "__main__":
    SCHEDULER.enter(5, 1, update_qctworksheet_on_finishing_vida_process)
    SCHEDULER.run()
