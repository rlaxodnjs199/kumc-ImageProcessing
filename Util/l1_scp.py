import time
from paramiko import SSHClient
from scp import SCPClient
from loguru import logger


# Instantiating SSH client
with SSHClient() as ssh:
    ssh.load_system_host_keys()
    ssh.connect("l1", username="twkim")
    # Transfer directory to the remote_path
    with SCPClient(ssh.get_transport()) as scp:
        logger.info("SCP Transfer starts...")
        execution_begin = time.time()
        scp.put(
            r"P:\IRB_STUDY00146630_RheSolve\Data\ImageData\DCM_20220216-16_GALA_TK\127-06-015_20220216\DEID",
            recursive=True,
            remote_path="/home/twkim/test",
        )
        execution_end = time.time()
        execution_interval = execution_end - execution_begin
        logger.info(f"SCP Transfer finished! Total time: {execution_interval}s")
