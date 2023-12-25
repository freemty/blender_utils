from brc_importers.ImportDelegator import Importer
import blender_utils


class TxtVoxelListImporter(Importer):

    def name(self):
        return "txt_voxel_list"

    def load(self, arguments):
        filename = arguments[0]
        print("Loading voxel list from '%s'" % filename)

        meshtype = arguments[1] if len(arguments) > 1 else "spheres"
        offset_x = float(arguments[2]) if len(arguments) > 2 else 0
        offset_y = float(arguments[3]) if len(arguments) > 3 else 0
        offset_z = float(arguments[4]) if len(arguments) > 4 else 0
        scale = float(arguments[5]) if len(arguments) > 5 else 1
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

        voxel_idx = 0
        for line in voxel_lines:
            if not line.startswith("#"):
                vals = line.split()

                # allows for additional formats, i.e. my files include the number of points in the first line
                if len(vals) >= 3:
                    voxel_idx += 1

                    if not radius:
                        r = [float(vals[3]), float(vals[3]), float(vals[3])]
                    else:
                        r = [radius, radius, radius]

                    add_voxel = blender_utils.add_cube if meshtype == "cubes" else blender_utils.add_sphere if meshtype == "spheres" else blender_utils.add_detailed_sphere
                    add_voxel(location=(float(vals[x_index])*scale + offset_x, float(vals[y_index])*scale + offset_y, float(vals[z_index])*scale + offset_z), radius=r)

TxtVoxelListImporter()
