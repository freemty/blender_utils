from brc_importers.ImportDelegator import Importer
import blender_utils
import binvox_rw
import numpy as np


class BinvoxImporter(Importer):

    def name(self):
        return "binvox"

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

        x_index = axes.find("x")
        y_index = axes.find("y")
        z_index = axes.find("z")

        assert x_index >= 0 and x_index < 3
        assert y_index >= 0 and y_index < 3
        assert z_index >= 0 and z_index < 3
        assert x_index != y_index and x_index != z_index and y_index != z_index

        with open(filename, 'rb') as f:
            model = binvox_rw.read_as_3d_array(f)

        points = np.where(model.data)
        locations = np.zeros((points[0].shape[0], 3), dtype=float)
        locations[:, 0] = (points[x_index][:] + 0.5)/model.data.shape[x_index]
        locations[:, 1] = (points[y_index][:] + 0.5)/model.data.shape[y_index]
        locations[:, 2] = (points[z_index][:] + 0.5)/model.data.shape[z_index]
        locations[:, 0] -= 0.5
        locations[:, 1] -= 0.5
        locations[:, 2] -= 0.5

        locations[:, 0] = locations[:, 0] * scale_x + offset_x
        locations[:, 1] = locations[:, 1] * scale_y + offset_y
        locations[:, 2] = locations[:, 2] * scale_z + offset_z

        radii = np.ones((locations.shape[0], 3)) * radius

        base_mesh = blender_utils.get_cube_mesh() if meshtype == "cubes" else blender_utils.get_sphere_mesh() if meshtype == "spheres" else blender_utils.get_detailed_sphere_mesh()
        blender_utils.add_primitive_objects(base_mesh, locations, radii)

BinvoxImporter()
