import argparse
import pathlib
from pydicom import dcmread

parser = argparse.ArgumentParser(description="DCM image path")
parser.add_argument("src", metavar="src", type=pathlib.Path, help="DCM image path")
args = parser.parse_args()

dcm_path = args.src

print(dcmread(dcm_path))
