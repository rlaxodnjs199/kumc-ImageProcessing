import os
import sys
import httplib2
import base64
import uuid
from typing import Dict
from pydicom import dcmread

if len(sys.argv) != 4:
    print("Usage: python %s [dicom_directory] [orthanc_username] [orthanc_password]" % (
        sys.argv[0]))
    sys.exit(0)

HOST_URL = '127.0.0.1'
ORTHANC_PORT = 8042
ORTHANC_URL = 'http://%s:%d/instances' % (HOST_URL, ORTHANC_PORT)
SUCCESS_COUNT = 0
TOTAL_COUNT = 0
FAILURE_PATH = []
PULMORAD_ROOT_UID = '1.2.826.0.1.3680043.8.499.'


def parse_string_from_dicom_path(dicom_path) -> str:
    study_name = os.path.basename(os.path.dirname(os.path.dirname(dicom_path)))
    series_name = os.path.basename(os.path.dirname(dicom_path))
    return study_name, series_name


def int_uuid_generator() -> uuid.UUID:
    return int(uuid.uuid4())


def is_dicom(file):
    file_extension = file.split('.')[-1]
    return file_extension == 'dcm'


def upload_dicom_image(dicom_path: str):
    """[Upload single instance of DICOM image(.dcm)]

    Args:
        dicom_path ([str]): [path to the single DICOM image]
    """
    global SUCCESS_COUNT
    global TOTAL_COUNT

    with open(dicom_path, 'rb') as dicom_image:
        content = dicom_image.read()
        TOTAL_COUNT += 1

        try:
            sys.stdout.write("Importing %s" % dicom_path)

            h = httplib2.Http()
            headers = {'content-type': 'application/dicom'}

            username = sys.argv[2]
            password = sys.argv[3]
            creds_str = username + ':' + password
            creds_str_bytes = creds_str.encode("ascii")
            creds_str_bytes_b64 = b'Basic ' + base64.b64encode(creds_str_bytes)
            headers['authorization'] = creds_str_bytes_b64.decode("ascii")

            response, content = h.request(
                ORTHANC_URL, 'POST', body=content, headers=headers)

            if response.status == 200:
                sys.stdout.write(" => success\n")
                SUCCESS_COUNT += 1
            else:
                sys.stdout.write(" => failure\n")
                FAILURE_PATH.append(dicom_path)
        except:
            type, value, traceback = sys.exc_info()
            sys.stderr.write(str(value))
            sys.stdout.write(" => unable to connect\n")


def overwrite_dicom_header(study_instance_uid_dict: Dict, dicom_path: str):
    """[Overwrite dicom headers of interest with processed value]

    Args:
        study_instance_uid_dict (Dict): [store {study_name:uid}]
        dicom_path (str): [dicom instance path]
    """
    study_name, series_name = parse_string_from_dicom_path(dicom_path)
    if study_name not in study_instance_uid_dict:
        uid = PULMORAD_ROOT_UID + str(int_uuid_generator())
        study_instance_uid_dict[study_name] = uid
        #print(study_instance_uid_dict.get(study_name))

    dicom_instance = dcmread(dicom_path)
    dicom_instance.StudyInstanceUID = study_instance_uid_dict[study_name]
    dicom_instance.PatientName = study_name
    # dicom_instance.AccessionNumber = accession_number
    # print(study_name, series_name)
    dicom_instance.SeriesDescription = dicom_instance.SeriesDescription + ' - ' + series_name    
    dicom_instance.save_as(dicom_path)

if __name__ == '__main__':
    dicom_directory = sys.argv[1]
    study_instance_uid_dict: Dict = {}
    # Recursively upload all .dcm files in dicom_directory
    for root, dirs, files in os.walk(dicom_directory):
        for file in files:
            if is_dicom(file):
                dicom_path = os.path.join(root, file)
                try:
                    overwrite_dicom_header(study_instance_uid_dict, dicom_path)
                    upload_dicom_image(dicom_path)
                except OSError as err:
                    sys.stdout.write("OS error: {0}".format(err))
                except:
                    sys.stdout.write("Unexpected error:", sys.exc_info()[0])

    if SUCCESS_COUNT == TOTAL_COUNT:
        print("\nSummary: all %d DICOM file(s) have been imported successfully" %
              SUCCESS_COUNT)
    else:
        print("\nSummary: %d out of %d files have been imported successfully as DICOM instances" % (
            SUCCESS_COUNT, TOTAL_COUNT))
        print("\n", FAILURE_PATH)
