from brc_importers.ImportDelegator import Importer
import blender_utils
import numpy


class BinImporter(Importer):

    def name(self):
        return "bin"

    def load(self, arguments):
        filename = arguments[0]
        print("Loading voxel list from '%s'" % filename)

        meshtype = arguments[1] if len(arguments) > 1 else "spheres"
        radius = float(arguments[2]) if len(arguments) > 2 else 0.01
        offset_x = float(arguments[3]) if len(arguments) > 3 else 0
        offset_y = float(arguments[4]) if len(arguments) > 4 else 0
        offset_z = float(arguments[5]) if len(arguments) > 5 else 0
        scale_x = float(arguments[6]) if len(arguments) > 6 else 1
        scale_y = float(arguments[7]) if len(arguments) > 7 else 1
        scale_z = float(arguments[8]) if len(arguments) > 8 else 1
        axes = str(arguments[9]) if len(arguments) > 9 else "xyz"
        skip = int(arguments[10]) if len(arguments) > 10 else 10

        x_index = axes.find("x")
        y_index = axes.find("y")
        z_index = axes.find("z")

        assert x_index >= 0 and x_index < 3
        assert y_index >= 0 and y_index < 3
        assert z_index >= 0 and z_index < 3
        assert x_index != y_index and x_index != z_index and y_index != z_index

        # meant to read KITTI bin files, i.e. just a bin file containing
        # x, y and z coordinates for all points with one float, the number of points, as header
        points = numpy.fromfile(filename, dtype=numpy.float32)
        points = points.reshape((points.shape[0]//4, 4))
        points = points[::skip]

        for i in range(points.shape[0]):
            add_voxel = blender_utils.add_cube if meshtype == "cubes" else blender_utils.add_detailed_sphere if meshtype == "detailed_spheres" else blender_utils.add_sphere
            add_voxel(location=(points[i, x_index]*scale_x + offset_x, points[i, y_index]*scale_y + offset_y, points[i, z_index]*scale_z + offset_z), radius=[radius, radius, radius])

BinImporter()