import os
import vtk
import pyvista

src_filepath = "Util/mesh/airway1.vtk"
dst_dir = "Util/output"


def convert(src_filepath, dst_dir):
    if not os.path.isdir(dst_dir):
        os.makedirs(dst_dir)

    if os.path.isfile(src_filepath):
        basename = os.path.basename(src_filepath)
        print("Converting file: ", basename)
        outputfile = os.path.join(dst_dir, basename + ".gltf")
        reader = vtk.vtkPolyDataReader()
        reader.SetFileName(src_filepath)
        reader.ReadAllScalarsOn()
        reader.ReadAllVectorsOn()
        reader.Update()

        renderer = vtk.vtkRenderer()
        renderWindow = vtk.vtkRenderWindow()
        renderWindow.AddRenderer(renderer)

        writer = vtk.vtkGLTFExporter()
        writer.SetInput(reader.GetOutput().GetPoints().GetData())
        writer.SetFileName(outputfile)
        writer.InlineDataOn()
        writer.SetRenderWindow(renderWindow)
        writer.Write()

        return outputfile


def read_gltf(gltf_filepath):
    importer = vtk.vtkGLTFImporter()
    importer.SetFileName(gltf_filepath)

    return importer


if __name__ == "__main__":
    dst_file = convert(src_filepath, dst_dir)
    # pl = pyvista.Plotter()
    # gltf_importer = read_gltf(dst_file)
    # gltf_importer.SetRenderWindow(pl.ren_win)
    # gltf_importer.Update()
    # pl.show()
