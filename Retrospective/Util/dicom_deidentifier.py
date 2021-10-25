# Usage
# - python dicom_deidentifier.py {./src_folder} {./dest_folder}
# Dependency
# - COVID_CTs_20210513CarissaWalter_0608jc.xlsx
# Input
# - dicom_source_folder_path
# - deidentified_dicom_destination_folder_path
# Output
# - Deidentified dicom series in the destination path

from pydicom import dcmread
from pydicom.datadict import dictionary_VR
from tqdm import tqdm
import pandas as pd
import argparse
import os
import csv
import re
import logging

# Create an argumnet parser
parser = argparse.ArgumentParser(
    description='Recursively de-identify and copy DICOM images from src to dst')
parser.add_argument('src', metavar='src', type=str,
                    help='DICOM source folder path')
parser.add_argument('dst', metavar='dst', type=str,
                    help='DICOM destination folder path')
args = parser.parse_args()

# Create a logger
logging.basicConfig(filename='Output/deidentifier.log', level=logging.WARNING,
                    filemode='a', format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

src_dicom_path = args.src
dst_dicom_path = args.dst
excel_path = 'Data/CarissaWalter/COVID_CTs_20210513CarissaWalter_0608jc.xlsx'

dicom_series = {}  # {SeriesInstanceUID : {Series Data}}
dicom_series_paths = {}  # {SeriesInstanceUID : [Img Paths]}


def extract_dicom_header(
        dicom_path, mrn, ct_date):
    dicom_img = dcmread(dicom_path)
    try:
        series_uid = dicom_img.SeriesInstanceUID
    except:
        logger.error(f'{dicom_path} - No SeriesInstanceUID')
        return

    if series_uid not in dicom_series:
        dicom_series[series_uid] = {}
        try:
            dicom_series[series_uid]['study_description'] = dicom_img.StudyDescription
        except:
            dicom_series[series_uid]['study_description'] = ''
        try:
            dicom_series[series_uid]['series_description'] = dicom_img.SeriesDescription
        except:
            dicom_series[series_uid]['series_description'] = ''
        if dicom_img.get('SliceThickness'):
            dicom_series[series_uid]['slice_thickness'] = dicom_img.SliceThickness
        else:
            dicom_series[series_uid]['slice_thickness'] = ''
        dicom_series[series_uid]['number_of_slices'] = 1
        dicom_series[series_uid]['mrn'] = mrn
        dicom_series[series_uid]['study_date'] = ct_date
        dicom_series[series_uid]['path'] = os.path.dirname(dicom_path)
        dicom_series_paths[series_uid] = [dicom_path]
    else:
        dicom_series[series_uid]['number_of_slices'] += 1
        dicom_series_paths[series_uid].append(dicom_path)


# precounting files
file_count = 0
for root, dirs, files in os.walk(src_dicom_path):
    for file in files:
        file_count += 1


def walkdir(src):
    for base, dirs, files in os.walk(src):
        for file in files:
            yield os.path.join(base, file)


# recursively read dicom images
print('>>> Generating metadata dictionary')
for dicom_slice_path in tqdm(walkdir(src_dicom_path), total=file_count):
    if not dicom_slice_path.endswith('.dcm'):
        continue
    series_name = os.path.basename(os.path.dirname(dicom_slice_path))
    mrn = series_name.split('_')[0]
    ct_date = series_name.split('_')[1]
    extract_dicom_header(dicom_slice_path, mrn, ct_date)

# write to csv
print('>>> Writing all metadata to dicom_metadata_all.csv', end=' ')
with open(dst_dicom_path + '/dicom_metadata_all.csv', 'w', newline='') as output_csv:
    csv_columns = ['mrn', 'study_date', 'slice_thickness',
                   'number_of_slices', 'study_description', 'series_description', 'path']
    writer = csv.DictWriter(output_csv, fieldnames=csv_columns)
    writer.writeheader()
    for series_uid in dicom_series:
        writer.writerow(dicom_series[series_uid])
print('----- Done')

# pick series of interest
abandoned_keywords = ['SCOUT', 'COR', 'SAG', 'MIP', 'AX', 'EXP']
print('>>> Selecting series of interest', end=' ')
for series_uid in list(dicom_series):
    series_meta = dicom_series[series_uid]
    if series_meta['slice_thickness'] == '' or int(series_meta['slice_thickness']) >= 5:
        del dicom_series[series_uid]
        del dicom_series_paths[series_uid]
        continue
    if int(series_meta['number_of_slices']) < 10:
        del dicom_series[series_uid]
        del dicom_series_paths[series_uid]
        continue
    for keyword in abandoned_keywords:
        if keyword in series_meta['series_description'].upper():
            del dicom_series[series_uid]
            del dicom_series_paths[series_uid]
            break
print('----- Done')

# write to csv
print('>>> Writing selected metadata to dicom_metadata_selected.csv', end=' ')
with open(dst_dicom_path + '/dicom_metadata_selected.csv', 'w', newline='') as output_csv:
    csv_columns = ['mrn', 'study_date', 'patient_name', 'patient_id',
                   'slice_thickness', 'number_of_slices', 'study_description', 'series_description', 'path']
    writer = csv.DictWriter(output_csv, fieldnames=csv_columns)
    writer.writeheader()
    for series_uid in dicom_series:
        writer.writerow(dicom_series[series_uid])
print('----- Done')


def deidentify_and_save(dicom_input_path, dicom_output_path, subj_id):
    try:
        dicom_slice = dcmread(dicom_input_path)
    except:
        logger.error(f'{dicom_input_path} - Error reading DICOM file')
        return
    # Overwrite DICOM headers
    try:
        dicom_slice.PatientName = subj_id
        logger.info(f'{dicom_input_path} - PatientName Header Processed')
    except:
        logger.error(f'{dicom_input_path} - PatientName Header does not exist')
        return
    try:
        dicom_slice.PatientID = subj_id
        logger.info(f'{dicom_input_path} - PatientID Header Processed')
    except:
        logger.error(f'{dicom_input_path} - PatientID Header does not exist')
        return
    if dicom_slice.get('AccessionNumber'):
        dicom_slice.AccessionNumber = subj_id + "_" + img_id
        logger.info(f'{dicom_input_path} - AccessionNumber Header Processed')
    else:
        logger.warning(
            f'{dicom_input_path} - AccessionNumber Header does not exist: Appending Header')
        dicom_slice.add_new([0x0008, 0x0050], dictionary_VR(
            [0x0008, 0x0050]), subj_id + "_" + img_id)
    # if dicom_slice.get('PatientBirthDate'):
    #     dicom_slice.PatientBirthDate = str(
    #         int(dicom_slice.PatientBirthDate) + (randint(1, 500) * 10000))
    #     logger.info(f'{dicom_input_path} - PatientBirthDate Header Processed')
    # else:
    #     logger.warning(
    #         f'{dicom_input_path} - PatientBirthDate Header does not exist')
    # if dicom_slice.get('StudyDate'):
    #     dicom_slice.StudyDate = str(
    #         int(dicom_slice.StudyDate) + (randint(1, 5)))  <FIX -> day % 28>
    #     logger.info(f'{dicom_input_path} - StudyDate Header Processed')
    # else:
    #     logger.warn(f'{dicom_input_path} - StudyDate Header does not exist')
    #     dicom_slice.add_new([0x0008, 0x0050], dictionary_VR(
    #         [0x0008, 0x0020]), '19940912')
    # if dicom_slice.get('SeriesDate'):
    #     dicom_slice.SeriesDate = dicom_slice.StudyDate
    # else:
    #     logger.info(
    #         f'{dicom_input_path} - SeriesDate Header does not exist: Appending Header')
    #     dicom_slice.add_new([0x0008, 0x0021], dictionary_VR(
    #         [0x0008, 0x0021]), dicom_slice.StudyDate)
    # if dicom_slice.get('AcquisitionDate'):
    #     dicom_slice.AcquisitionDate = dicom_slice.StudyDate
    # else:
    #     logger.info(
    #         f'{dicom_input_path} - AcquisitionDate Header does not exist: Appending Header')
    #     dicom_slice.add_new([0x0008, 0x0022], dictionary_VR(
    #         [0x0008, 0x0022]), dicom_slice.StudyDate)
    # if dicom_slice.get('ContentDate'):
    #     dicom_slice.ContentDate = dicom_slice.ContentDate
    # else:
    #     logger.info(
    #         f'{dicom_input_path} - ContentDate Header does not exist: Appending Header')
    #     dicom_slice.add_new([0x0008, 0x0023], dictionary_VR(
    #         [0x0008, 0x0023]), dicom_slice.StudyDate)
    # Sanitize DICOM headers
    if dicom_slice.get('InstitutionName'):
        del dicom_slice[0x0008, 0x0080]
    if dicom_slice.get('InstitutionAddress'):
        del dicom_slice[0x0008, 0x0081]
    if dicom_slice.get('InstitutionalDepartmentName'):
        del dicom_slice[0x0008, 0x1040]
    if dicom_slice.get('ReferringPhysicianName'):
        del dicom_slice[0x0008, 0x0090]
    if dicom_slice.get('ReferringPhysicianTelephoneNumbers'):
        del dicom_slice[0x0008, 0x0094]
    if dicom_slice.get('ReferringPhysicianAddress'):
        del dicom_slice[0x0008, 0x0092]
    if dicom_slice.get('PhysiciansOfRecord'):
        del dicom_slice[0x0008, 0x1048]
    if dicom_slice.get('OperatorsName'):
        del dicom_slice[0x0008, 0x1070]
    if dicom_slice.get('IssuerOfPatientID'):
        del dicom_slice[0x0010, 0x0021]
    if dicom_slice.get('OtherPatientIDs'):
        del dicom_slice[0x0010, 0x1000]
    if dicom_slice.get('OtherPatientNames'):
        del dicom_slice[0x0010, 0x1001]
    if dicom_slice.get('OtherPatientIDsSequence'):
        del dicom_slice[0x0010, 0x1002]
    if dicom_slice.get('PatientBirthName'):
        del dicom_slice[0x0010, 0x1005]
    if dicom_slice.get('PatientSize'):
        del dicom_slice[0x0010, 0x1020]
    if dicom_slice.get('PatientWeight'):
        del dicom_slice[0x0010, 0x1030]
    if dicom_slice.get('PatientAddress'):
        del dicom_slice[0x0010, 0x1040]
    if dicom_slice.get('PatientMotherBirthName'):
        del dicom_slice[0x0010, 0x1060]
    if dicom_slice.get('CountryOfResidence'):
        del dicom_slice[0x0010, 0x2150]
    if dicom_slice.get('RegionOfResidence'):
        del dicom_slice[0x0010, 0x2152]
    if dicom_slice.get('CurrentPatientLocation'):
        del dicom_slice[0x0038, 0x0300]
    if dicom_slice.get('PatientTelephoneNumbers'):
        del dicom_slice[0x0010, 0x2154]
    if dicom_slice.get('SmokingStatus'):
        del dicom_slice[0x0010, 0x21a0]
    if dicom_slice.get('PregnancyStatus'):
        del dicom_slice[0x0010, 0x21c0]
    if dicom_slice.get('PatientReligiousPreference'):
        del dicom_slice[0x0010, 0x21f0]
    if dicom_slice.get('RequestingPhysician'):
        del dicom_slice[0x0032, 0x1032]
    if dicom_slice.get('PerformingPhysicianName'):
        del dicom_slice[0x0008, 0x1050]
    if dicom_slice.get('NameOfPhysiciansReadingStudy'):
        del dicom_slice[0x0008, 0x1060]
    if dicom_slice.get('OtherPatientIDs'):
        del dicom_slice[0x0010, 0x1000]
    if dicom_slice.get('MilitaryRank'):
        del dicom_slice[0x0010, 0x1080]
    if dicom_slice.get('EthnicGroup'):
        del dicom_slice[0x0010, 0x2160]
    if dicom_slice.get('AdditionalPatientHistory'):
        del dicom_slice[0x0010, 0x21b0]
    if dicom_slice.get('PatientComments'):
        del dicom_slice[0x0010, 0x4000]
    if dicom_slice.get('PersonName'):
        del dicom_slice[0x0040, 0xA123]
    if dicom_slice.get('ScheduledPatientInstitutionResidence'):
        del dicom_slice[0x0038, 0x001E]
    # Save modified DICOM
    try:
        dicom_slice.save_as(dicom_output_path)
    except:
        logger.error(
            f'{dicom_input_path} - Error saving DICOM file to {dicom_output_path}')
        return


def parse_series_description(series_description: str) -> str:
    series_description = series_description.lstrip()
    series_description = series_description.rstrip()
    series_description = series_description.replace('.', 'P')
    series_description = re.sub('\W+', '_', series_description)
    return series_description


# Construct {'Series_UID' : ['Subj_ID', 'Img_ID']} from Excel metadata sheet
print('>>> Construct subjID & imgID from excel metadata sheet', end='')
excel_data = pd.read_excel(excel_path, header=9, usecols='A,C,I,J')
series_id_dict = {}
for _, row in excel_data.iterrows():
    subj_id = row['Subj']
    mrn = str(row['mrn']).zfill(7)
    ctdate = row['date'].strftime('%Y%m%d') if type(
        row['date']) == pd.Timestamp else ''
    if ctdate == '':
        logger.warning(f'{subj_id} cannot get ctdate from {excel_path}')
    key = mrn + '_' + ctdate + '_all'
    img_id = str(row['Time'])

    series_id_dict[key] = [subj_id, img_id]
print('----- Done')

# Copy selected DICOM series to destination
print('>>> De-identify and copy selected series to the destination')
for series_uid in tqdm(dicom_series):
    series_meta = dicom_series[series_uid]

    dicom_source_paths = dicom_series_paths[series_uid]
    dicom_source_folder_name = os.path.basename(
        os.path.dirname(dicom_source_paths[0]))

    series_description = parse_series_description(
        series_meta['series_description'])

    try:
        subj_id = series_id_dict[dicom_source_folder_name][0]
        img_id = 'IN' + series_id_dict[dicom_source_folder_name][1] if 'EXP' not in series_description.upper(
        ) else 'EX' + series_id_dict[dicom_source_folder_name][1]
    except:
        logger.error(
            f'{dicom_source_folder_name} - Can\'t match dicom folder name with excel sheet data')
        continue

    dicom_destination_folder_name = subj_id + \
        '_' + img_id + '_' + series_description

    dicom_destination_folder_path = os.path.join(
        dst_dicom_path, dicom_destination_folder_name)
    if not os.path.exists(dicom_destination_folder_path):
        os.makedirs(dicom_destination_folder_path)
    else:
        continue

    for dicom_source_slice_path in dicom_source_paths:
        dicom_source_slice_filename = os.path.basename(dicom_source_slice_path)
        dicom_destination_slice_path = os.path.join(
            dicom_destination_folder_path, dicom_source_slice_filename)
        deidentify_and_save(dicom_source_slice_path,
                            dicom_destination_slice_path, subj_id)