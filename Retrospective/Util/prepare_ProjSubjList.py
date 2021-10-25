# Usage Example
# - python prepare_ProjSubjList.py /e/jchoi4/ImageData/C19/VIDA_20210701-01_C19_TK
# Input
# -------------------------------------------------------------------
# - VIDA results folder path
# -------------------------------------------------------------------
# Dependency
# - VidaDataSheet.xlsx

import os
import sys
import subprocess
import argparse
from datetime import datetime
import tarfile
from pathlib import Path
import pandas as pd
from tqdm import tqdm
from dotenv import dotenv_values

# import paramiko
# from scp import SCPClient

parser = argparse.ArgumentParser(
    description="Prepare ProjSubjList.in, Compressed zip of VIDA results and send it to the B2"
)
parser.add_argument(
    "src", metavar="src", type=str, help="VIDA results source folder path"
)
args = parser.parse_args()

PROJ = "C19"
VIDA_RESULTS_PATH = args.src
try:
    CASE_ID_LIST = [int(case) for case in os.listdir(VIDA_RESULTS_PATH)]
except:
    sys.exit("Error: Unexpected data included in source path")
OUTPUT_FOLDER_NAME = (
    VIDA_RESULTS_PATH.split("/")[-1]
    if VIDA_RESULTS_PATH.split("/")[-1] != ""
    else VIDA_RESULTS_PATH.split("/")[-2]
)
PATH_IN_B2 = f"/data4/common/ImageData/{PROJ}"
OUTPUT_PATH = "Data_to_send"
DATASHEET_PATH = "Data/Datasheet/DataSheet.xlsx"


print(">>> Construct Dataframe for ProjSubjList.in from Datasheet.xlsx", end=" ")
datasheet_df = pd.read_excel(DATASHEET_PATH, usecols="A:C,I")
case_data_list = []
for case in CASE_ID_LIST:
    try:
        row = datasheet_df.loc[datasheet_df["VidaCaseID"] == case]
        temp_dict = {}
        for k1, v1 in row.to_dict().items():
            for k2, v2 in v1.items():
                temp_dict[k1] = v2
        temp_dict["ImgDir"] = f"{PATH_IN_B2}/{OUTPUT_FOLDER_NAME}/{case}"
        case_data_list.append(temp_dict)
    except:
        print(f"Cannot find case id {case}")
case_data_df = pd.DataFrame(case_data_list)
case_data_df.rename(columns={"IN/EX": "Img"}, inplace=True)
case_data_df.drop(columns=["VidaCaseID"], inplace=True)
print("----- Done")


print(">>> Create ProjSubjList.in", end=" ")
today = datetime.today().strftime("%Y%m%d")
projSubjListTitle = f"ProjSubjList.in.{today}_{PROJ}"
case_data_df = case_data_df.to_csv(index=False, line_terminator="\n").replace(
    ",", "    "
)
with open(f"{OUTPUT_PATH}/{projSubjListTitle}", "w") as f:
    f.write(case_data_df)
print("----- Done")


print(">>> Compress VIDA results into one tar file")
with tarfile.open(f"{OUTPUT_PATH}/{OUTPUT_FOLDER_NAME}.tar.bz2", "w:bz2") as tar:
    for case in tqdm(CASE_ID_LIST):
        tar.add(Path(f"{VIDA_RESULTS_PATH}/{case}"), f"{OUTPUT_FOLDER_NAME}/{case}")


print(">>> Send Data to B2")
ssh_config = dotenv_values(".env")
port = ssh_config["SSH_PORT"]
host = ssh_config["SSH_HOST"]
user = ssh_config["SSH_USERNAME"]
scp_process_1 = subprocess.run(
    [
        "scp",
        "-P",
        port,
        f"{OUTPUT_PATH}/{projSubjListTitle}",
        f"{user}@{host}:{PATH_IN_B2}/",
    ]
)
scp_process_2 = subprocess.run(
    [
        "scp",
        "-P",
        port,
        f"{OUTPUT_PATH}/{OUTPUT_FOLDER_NAME}.tar.bz2",
        f"{user}@{host}:{PATH_IN_B2}/",
    ]
)

# SFTP using paramiko
# class FastTransport(paramiko.Transport):
#     def __init__(self, sock):
#         super(FastTransport, self).__init__(sock)
#         self.window_size = 2147483647
#         self.packetizer.REKEY_BYTES = pow(2, 40)
#         self.packetizer.REKEY_PACKETS = pow(2, 40)

# ssh_config = dotenv_values('.env')
# ssh_conn = FastTransport((ssh_config['SSH_HOST'], int(ssh_config['SSH_PORT'])))
# ssh_conn.connect(username=ssh_config['SSH_USERNAME'], password=ssh_config['SSH_PW'])
# sftp = paramiko.SFTPClient.from_transport(ssh_conn)
# sftp.put(Path(f'{OUTPUT_PATH}/{projSubjListTitle}'), f'{PATH_IN_B2}/{projSubjListTitle}')
# sftp.put(f'{OUTPUT_PATH}/{OUTPUT_FOLDER_NAME}.tar.bz2', f'{PATH_IN_B2}/{OUTPUT_FOLDER_NAME}.tar.bz2')
# sftp.close()

# SCP using paramiko
# ssh = SSHClient()
# ssh.load_system_host_keys()
# ssh.connect(ssh_config['SSH_HOST'], port=ssh_config['SSH_PORT'], username=ssh_config['SSH_USERNAME'], password=ssh_config['SSH_PW'], look_for_keys=False)

# def progress(filename, size, sent):
#     sys.stdout.write("%s's progress: %.2f%%   \r" % (filename, float(sent)/float(size)*100) )

# with SCPClient(ssh.get_transport(), progress=progress) as scp:
#     scp.put(f'{OUTPUT_PATH}/{projSubjListTitle}', remote_path=PATH_IN_B2)
#     scp.put(f'{OUTPUT_PATH}/{OUTPUT_FOLDER_NAME}.tar.bz2', remote_path=PATH_IN_B2)
