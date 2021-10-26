from typing import List, Dict
import pandas as pd
import tarfile
from datetime import datetime
from pathlib import Path
import subprocess
from tqdm import tqdm
import numpy as np
from dotenv import dotenv_values

# ---------------------------------------------------------------------------
QCTCFD_WORKSHEET_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\QCTCFD_Worksheet.xlsx"
VIDA_RESULTS_PATH = r"E:\VIDA\VIDAvision2.2"
OUTPUT_PATH = "Data_to_send"
OUTPUT_FOLDER = "VIDA_20211026-26_SARP3_TK"
PATH_IN_REMOTE_HOST = "/home/twkim/ImageData"
# ---------------------------------------------------------------------------

def pick_baseline_with_both_InEx(df_QCTCFD: pd.DataFrame) -> List[List[int]]:
    VIDA_case_id_list = []
    for _, row in df_QCTCFD.iterrows():
        if row['VIDA_IN'] == 'O' and row['VIDA_EX'] == 'O' and row['FU'] == 0:
            VIDA_case_id_list.append(int(row['VIDA_IN_Path'].split('\\')[-1]))
            VIDA_case_id_list.append(int(row['VIDA_EX_Path'].split('\\')[-1]))
    splitted_VIDA_case_id_list = np.array_split(VIDA_case_id_list, 9)
    
    return splitted_VIDA_case_id_list

def compress_vida_results(case_ids: List[int], index: int, vida_results_path=VIDA_RESULTS_PATH, output_path=OUTPUT_PATH, output_folder=OUTPUT_FOLDER):
    with tarfile.open(f"{output_path}/{output_folder}_{index}.tar.bz2", "w:bz2") as tar:
        for case in tqdm(case_ids):
            tar.add(Path(f"{vida_results_path}/{case}"), f"{output_folder}/{case}")
    
    return f"{output_path}/{output_folder}_{index}.tar.bz2"

def prepare_ProjSubjList(df_QCTCFD: pd.DataFrame, case_ids: List[int], index: int):
    df_row_to_append_list = []
    for case_id in case_ids:
        df_row_to_append = {}
        df_row_to_append['Proj'] = 'SARP'
        if (df_QCTCFD['VIDA_IN_Path'].str.contains(str(case_id))).any():
            df_QCTCFD_row_filtered = df_QCTCFD[df_QCTCFD['VIDA_IN_Path'].str.contains(str(case_id), na=False)]
            # df_row_to_append['Proj'] = df_QCTCFD_row_filtered['Proj'].values[0]
            df_row_to_append['Subj'] = df_QCTCFD_row_filtered['Subj'].values[0]
            df_row_to_append['Img'] = 'IN' + df_QCTCFD_row_filtered['FU'].astype('str').values[0]
            df_row_to_append['ImgDir'] = f'{PATH_IN_REMOTE_HOST}/{OUTPUT_FOLDER}_{index}/{case_id}'
        elif (df_QCTCFD['VIDA_EX_Path'].str.contains(str(case_id))).any():
            df_QCTCFD_row_filtered = df_QCTCFD[df_QCTCFD['VIDA_EX_Path'].str.contains(str(case_id), na=False)]
            # df_row_to_append['Proj'] = df_QCTCFD_row_filtered['Proj'].values[0]            
            df_row_to_append['Subj'] = df_QCTCFD_row_filtered['Subj'].values[0]
            df_row_to_append['Img'] = 'EX' + df_QCTCFD_row_filtered['FU'].astype('str').values[0]
            df_row_to_append['ImgDir'] = f'{PATH_IN_REMOTE_HOST}/{OUTPUT_FOLDER}_{index}/{case_id}'
        else:
            print('error')
        df_row_to_append_list.append(df_row_to_append)
    df_ProjSubjList = pd.DataFrame(df_row_to_append_list)

    today = datetime.today().strftime("%Y%m%d")
    df_to_write = df_ProjSubjList.to_csv(index=False, line_terminator="\n").replace(
        ",", "    "
    )
    with open(f'{OUTPUT_PATH}/ProjSubjList.in.{today}_{index}', 'w') as f:
        f.write(df_to_write)
    
    return f'{OUTPUT_PATH}/ProjSubjList.in.{today}_{index}'


def send_data_to_B2(ProjSubjList_path: str, VIDA_result_path: str):
    ssh_config = dotenv_values(".env")
    port = ssh_config["SSH_PORT"]
    host = ssh_config["SSH_HOST"]
    user = ssh_config["SSH_USERNAME"]


    subprocess.run(
            [
                "scp",
                "-P",
                port,
                f"{ProjSubjList_path}",
                f"{user}@{host}:{PATH_IN_REMOTE_HOST}/",
            ]
        )
    
    subprocess.run(
        [
            "scp",
            "-P",
            port,
            f"{VIDA_result_path}",
            f"{user}@{host}:{PATH_IN_REMOTE_HOST}/",
        ]
    )


if __name__ == '__main__':
    df_QCTCFD = pd.read_excel(QCTCFD_WORKSHEET_PATH)
    splitted_VIDA_case_id_list = pick_baseline_with_both_InEx(df_QCTCFD)
    for i, list in enumerate(splitted_VIDA_case_id_list):
        if i == 2:
            ProjSubjList_path = prepare_ProjSubjList(df_QCTCFD, list, i)
            VIDA_result_path = compress_vida_results(list, i)
            send_data_to_B2(ProjSubjList_path, VIDA_result_path)
