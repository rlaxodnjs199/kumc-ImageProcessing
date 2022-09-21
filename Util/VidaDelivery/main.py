import os
import sys
from typing import List
from paramiko import SSHClient, SFTPClient

from case import VidaCase


class VidaSFTPClient(SFTPClient):
    def mkdir(self, path, mode=755, ignore_existing=False):
        try:
            super(SFTPClient, self).mkdir(path, mode)
        except IOError:
            if ignore_existing:
                print("something exist")
            else:
                raise


def create_combined_vidafolder():
    pass


# with SSHClient() as ssh:
#     ssh.load_system_host_keys()
#     ssh.connect("l1", username="twkim")
#     with ssh.open_sftp() as sftp:
#         try:
#             sftp.mkdir("./testtesttest")
#         except IOError:
#             pass
#         sftp.rmdir("./testtesttest")
#         print(sftp.listdir("."))
#         # sftp.mkdir("~/testtesttest", mode=755)


def compress_vida_cases(vida_cases: List[VidaCase], max_cases_per_tar=10):
    vida_cases_by_project_dict = {}
    for vida_case in vida_cases:
        if hasattr(vida_cases_by_project_dict, vida_case.proj):
            vida_cases_by_project_dict[vida_case.proj]["tar_path"]


if __name__ == "__main__":
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
        vida_case = VidaCase(vida_case_number)
