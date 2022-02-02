import os
from tqdm.auto import tqdm
import numpy as np
import pandas as pd
import scipy.ndimage
from medpy.io import load, save

def _get_img_paths_from_in(in_file_path: str):
    in_file = pd.read_csv(in_file_path,sep='\t')
    img_paths = [os.path.join(subj_path,'zunu_vida-ct.img') for subj_path in in_file.ImgDir]
    return img_paths

def _resample_fix_dim(img,hdr,new_dim=np.array([64,64,64])):
    resize_factor = new_dim/img.shape
    new_spacing = hdr.spacing/resize_factor
    re_img = scipy.ndimage.interpolation.zoom(img,resize_factor, mode='nearest')
    hdr.set_voxel_spacing(new_spacing)
    return re_img, hdr

def main():
    in_file = '/data4/inqlee0704/ENV18PM_ProjSubjList_cleaned_IN.in'
    dst_root = '/data4/inqlee0704/resampled_dim64'
    img_paths = _get_img_paths_from_in(in_file)
    pbar = tqdm(img_paths, total=len(img_paths))
    for img_path in pbar:
        img, hdr = load(img_path)
        re_img, new_hdr = _resample_fix_dim(img,hdr)

        # saving is hard-coded
        dst_img_path = os.path.join(dst_root,img_path[23:])
        dst_dir_path = os.path.join(dst_root,dst_img_path.split('/')[4])
        dst_subdir_path = os.path.join(dst_dir_path,dst_img_path.split('/')[5])
        if not os.path.exists(dst_dir_path):
            os.mkdir(dst_dir_path)
        if not os.path.exists(dst_subdir_path):
            os.mkdir(dst_subdir_path)
        save(re_img,dst_img_path,new_hdr)


if __name__ == "__main__":
    main()
