import os
import SimpleITK as sitk
import sys


def DCMtoVidaCT(pathImage, saveImage=None):

    if saveImage == None:
        print(f"Save path is  not given, image will be saved in: ")
        print(pathImage)
        saveImage = pathImage

    path = os.getcwd()
    print("")
    print("---------------------------------------------------")
    print(" PROGRAM BEGINS (Generate zunu_vida-ct.img & .hdr)")
    print("---------------------------------------------------")
    print(" Reading project directory:", path)
    n = 0
    print("===================================================")

    nImage = 1

    i = 0
    for i in range(nImage):
        reader = sitk.ImageSeriesReader()
        filenamesDICOM = reader.GetGDCMSeriesFileNames(pathImage)
        reader.SetFileNames(filenamesDICOM)
        imgOriginal = reader.Execute()
        print("    The origin after creating DICOM:", imgOriginal.GetOrigin())
        # Flip the image.
        # The files from Apollo have differnt z direction.
        # Thus, we need to flip the image to make it consistent with Apollo.
        flipAxes = [False, False, True]
        flipped = sitk.Flip(imgOriginal, flipAxes, flipAboutOrigin=True)
        print("    The origin after flipping DICOM:", flipped.GetOrigin())
        # Move the origin to (0,0,0)
        # After converting dicom to .hdr with itkv4, the origin of images changes.
        # Thus we need to reset it to (0,0,0) to make it consistent with Apollo files.
        origin = [0.0, 0.0, 0.0]
        flipped.SetOrigin(origin)
        print(
            "    The origin after flipping and changing origin to [0.,0.,0.]:",
            flipped.GetOrigin(),
        )
        sitk.WriteImage(flipped, saveImage + "/" + "zunu_vida-ct.hdr")

        print("    " + "/" + "zunu_vida-ct.img & .hdr", "----> written")
        print("===================================================")

    print("zunu_vida-ct.img/.hdr are created for {0} images".format(n))
    print("-------------------------------------------------")
    print(" PROGRAM ENDS (Generate zunu_vida-ct.img & .hdr)")
    print("-------------------------------------------------")


if __name__ == "__main__":
    src = sys.argv[1]
    DCMtoVidaCT(src)
