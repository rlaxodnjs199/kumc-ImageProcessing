import os
import copy
from typing import List
import numpy as np
import scipy.ndimage
from pydicom import dcmread, FileDataset, Dataset, uid


def _get_dcm_paths_from_dir(dcm_dir: str):
    for base, _, files in os.walk(dcm_dir):
        for file in files:
            yield os.path.join(base, file)


def _mimic_src_dir_to_build_dst_dir(dcm_dir: str):
    pass


def _check_dataset(dicom_dir: str):
    for dcm_path in _get_dcm_paths_from_dir(dicom_dir):
        dcm = dcmread(dcm_path)
        print(
            dcm.InstanceNumber,
            # dcm.SOPInstanceUID,
            dcm.Rows,
            dcm.Columns,
            dcm.LargestImagePixelValue,
            dcm.BitsStored,
            dcm.BitsAllocated,
            dcm.HighBit,
            dcm.PixelRepresentation,
            dcm.ImagePositionPatient,
            dcm.SliceLocation,
            dcm.PixelSpacing,
        )


def _get_dcm_spacing(dcm: Dataset) -> List:
    return list(map(lambda x: np.float16(x), [*dcm.PixelSpacing, dcm.SliceThickness]))


def _get_dcm_pixel_array(dcm_dir: str) -> np.ndarray:
    dcm_pixel_array = np.transpose(
        np.array(
            [
                dcmread(dcm_path).pixel_array
                for dcm_path in _get_dcm_paths_from_dir(dcm_dir)
            ]
        ),
        (1, 2, 0),
    )

    return dcm_pixel_array


def _get_dcm_template(dcm_dir: str) -> Dataset:
    return dcmread(next(_get_dcm_paths_from_dir(dcm_dir)))


def _resample_dcm_pixel_array(
    dcm_pixel_array: np.ndarray,
    spacing: List[np.float16],
    new_spacing: List[np.float16],
) -> np.ndarray:
    spacing = np.array(spacing, dtype=np.float16)
    resize_factor = spacing / new_spacing
    new_real_shape = dcm_pixel_array.shape * resize_factor
    new_shape = np.round(new_real_shape)
    real_resize_factor = new_shape / dcm_pixel_array.shape
    new_spacing = spacing / real_resize_factor
    # Cubic spline, nearest neighbor for the boundary
    resampled_dcm_pixel_array = scipy.ndimage.interpolation.zoom(
        dcm_pixel_array, real_resize_factor, mode="nearest"
    )
    resampled_dcm_pixel_array = np.transpose(resampled_dcm_pixel_array, (2, 0, 1))

    # This part needs to be revised
    # 
    resampled_dcm_pixel_array = (
        resampled_dcm_pixel_array / np.amax(resampled_dcm_pixel_array) * 4092
    )
    resampled_dcm_pixel_array = resampled_dcm_pixel_array.astype(np.uint16)

    return resampled_dcm_pixel_array


def _construct_new_dcm_slice(
    dcm_template: Dataset,
    new_spacing: np.float16,
    instance_number: int,
    resampled_dcm_pixel_2D: np.ndarray,
) -> Dataset:
    new_dcm_slice = copy.deepcopy(dcm_template)
    new_dcm_slice.file_meta.MediaStorageSOPInstanceUID = uid.generate_uid()
    new_dcm_slice.file_meta.TransferSyntaxUID = uid.ExplicitVRLittleEndian
    new_dcm_slice.is_implicit_VR = False
    new_dcm_slice.is_little_endian = True
    new_dcm_slice.SOPInstanceUID = uid.generate_uid()
    new_dcm_slice.LargestImagePixelValue = np.unique(resampled_dcm_pixel_2D)[-1]
    # new_dcm_slice.BitsAllocated = 16
    # new_dcm_slice.BitsStored = 12
    # new_dcm_slice.HighBit = 11
    # new_dcm_slice.PixelRepresentation = 0
    new_dcm_slice.InstanceNumber = instance_number
    new_dcm_slice.SliceThickness = new_spacing
    new_dcm_slice.SliceLocation = (
        new_dcm_slice.SliceLocation
        - new_dcm_slice.SliceThickness * (instance_number - 1)
    )
    new_dcm_slice.ImagePositionPatient[2] = new_dcm_slice.SliceLocation
    new_dcm_slice.PixelData = resampled_dcm_pixel_2D.tobytes()

    return new_dcm_slice


def _construct_and_save_new_dcm_dataset(
    dcm_template: Dataset,
    new_spacing: np.float16,
    resampled_dcm_pixel_array: np.ndarray,
    output_path: str,
) -> FileDataset:
    for instance_number, resampled_dcm_slice_pixel_array in enumerate(
        resampled_dcm_pixel_array, 1
    ):
        resampled_dcm_slice = _construct_new_dcm_slice(
            dcm_template, new_spacing, instance_number, resampled_dcm_slice_pixel_array
        )
        resampled_dcm_slice.save_as(f"{output_path}/{instance_number}.dcm")


def resample_dcm(dcm_dir: str, output_path: str, new_spacing=1.0):
    dcm_template = _get_dcm_template(dcm_dir)
    dcm_pixel_array = _get_dcm_pixel_array(dcm_dir)
    dcm_spacing = _get_dcm_spacing(dcm_template)
    new_dcm_spacing = [*dcm_spacing[:-1], new_spacing]
    print(dcm_spacing, '->', new_dcm_spacing)
    resampled_dcm_pixel_array = _resample_dcm_pixel_array(
        dcm_pixel_array, dcm_spacing, new_dcm_spacing
    )
    _construct_and_save_new_dcm_dataset(
        dcm_template, new_spacing, resampled_dcm_pixel_array, output_path
    )


if __name__ == "__main__":
    src_dcm_path = r'C:\Users\tkim3\Documents\Codes\ImageProcessing\Data\SampleDicom\1379\dicom'
    output_dcm_path = r'C:\Users\tkim3\Documents\Codes\ImageProcessing\Output\dicom\1379'
    resample_dcm(src_dcm_path, output_dcm_path)
    # _check_dataset(src_dcm_path)
