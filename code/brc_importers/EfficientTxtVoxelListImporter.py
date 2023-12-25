from brc_importers.ImportDelegator import Importer
import blender_utils
from render_logging import log, LogLevel
import numpy


class EfficientTxtVoxelListImporter(Importer):

    def name(self):
        return "efficient_txt_voxel_list"

    def load(self, arguments):
        filename = arguments[0]
        print("Loading voxel list from '%s'" % filename)

        meshtype = arguments[1] if len(arguments) > 1 else "spheres"
        offset_x = float(arguments[2]) if len(arguments) > 2 else 0
        offset_y = float(arguments[3]) if len(arguments) > 3 else 0
        offset_z = float(arguments[4]) if len(arguments) > 4 else 0
        scale = float(arguments[5]) if len(arguments) > 5 else 0
        axes = str(arguments[6]) if len(arguments) > 6 else "xyz"

        x_index = axes.find("x")
        y_index = axes.find("y")
        z_index = axes.find("z")

        assert x_index >= 0 and x_index < 3
        assert y_index >= 0 and y_index < 3
        assert z_index >= 0 and z_index < 3
        assert x_index != y_index and x_index != z_index and y_index != z_index

        radius = False
        if len(arguments) > 7:
            radius = float(arguments[7])
            assert radius > 0

        voxel_file = open(filename, 'r')
        voxel_lines = voxel_file.readlines()
        voxel_file.close()

        locations = numpy.zeros((0, 3))
        radii = numpy.ones((0, 3))

        for line in voxel_lines:
            if not line.startswith("#") and line.strip() != '':
                vals = line.split(' ')

                # allows for additional formats, i.e. my files include the number of points in the first line
                if len(vals) >= 3:
                    if not radius:
                        radii = numpy.vstack((radii, [float(vals[3]), float(vals[3]), float(vals[3])]))
                    else:
                        radii = numpy.vstack((radii, [radius, radius, radius]))

                    locations = numpy.vstack((locations, [
                        float(vals[x_index])*scale + offset_x,
                        float(vals[y_index])*scale + offset_y,
                        float(vals[z_index])*scale + offset_z
                    ]))

        base_mesh = blender_utils.get_cube_mesh() if meshtype == "cubes" else blender_utils.get_sphere_mesh() if meshtype == "spheres" else blender_utils.get_detailed_sphere_mesh()
        blender_utils.add_primitive_objects(base_mesh, locations, radii)

EfficientTxtVoxelListImporter()
