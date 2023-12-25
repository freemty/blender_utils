from brc_importers.ImportDelegator import Importer
import bpy
import numpy
import blender_utils
from render_logging import log, LogLevel


class TxtBoundingBoxesBbImporter(Importer):

    def name(self):
        return "txt_bounding_boxes"

    def load(self, arguments):
        filename = arguments[0]
        print("Loading voxel list from '%s'" % filename)

        offset_x = float(arguments[1]) if len(arguments) > 1 else 0
        offset_y = float(arguments[2]) if len(arguments) > 2 else 0
        offset_z = float(arguments[3]) if len(arguments) > 3 else 0
        scale = float(arguments[4]) if len(arguments) > 4 else 0
        axes = str(arguments[5]) if len(arguments) > 5 else "xyz"
        padding = float(arguments[6]) if len(arguments) > 6 else 0

        x_index = axes.find("x")
        y_index = axes.find("y")
        z_index = axes.find("z")

        assert x_index >= 0 and x_index < 3
        assert y_index >= 0 and y_index < 3
        assert z_index >= 0 and z_index < 3
        assert x_index != y_index and x_index != z_index and y_index != z_index

        bb_file = open(filename, 'r')
        lines = bb_file.readlines()
        lines = [line.strip() for line in lines if line.strip() != '']
        bb_file.close()

        num_bounding_boxes = int(lines[0])
        assert num_bounding_boxes == len(lines) - 1

        for i in range(1, len(lines)):
            parts = lines[i].split(' ')
            assert len(parts) >= 9

            size = (float(parts[0]), float(parts[1]), float(parts[2]))
            size = (size[0]/(1 + 2*padding), size[1]/(1 + 2*padding), size[2]/(1 + 2*padding))
            translation = (float(parts[3]), float(parts[4]), float(parts[5]))
            rotation_y = -float(parts[7])

            rotation_matrix = numpy.eye(3)
            rotation_matrix[0, 0] = numpy.cos(rotation_y)
            rotation_matrix[0, 2] = numpy.sin(rotation_y)
            rotation_matrix[2, 0] = -numpy.sin(rotation_y)
            rotation_matrix[2, 2] = numpy.cos(rotation_y)

            verts = numpy.zeros((8, 3), dtype=float)
            verts[0, :] = (- size[0] / 2, - size[1] / 2, - size[2] / 2) # left lower front
            verts[1, :] = (+ size[0] / 2, - size[1] / 2, - size[2] / 2) # right lower front
            verts[2, :] = (- size[0] / 2, + size[1] / 2, - size[2] / 2) # left upper front
            verts[3, :] = (+ size[0] / 2, - size[1] / 2, + size[2] / 2) # right lower back
            verts[4, :] = (+ size[0] / 2, + size[1] / 2, - size[2] / 2) # right upper front
            verts[5, :] = (+ size[0] / 2, + size[1] / 2, + size[2] / 2) # right upper back
            verts[6, :] = (- size[0] / 2, + size[1] / 2, + size[2] / 2) # left upper back
            verts[7, :] = (- size[0] / 2, - size[1] / 2, + size[2] / 2) # left lower back

            faces = [
                (0, 1, 2),
                (1, 2, 4),
                (3, 5, 6),
                (3, 6, 7),
                (0, 1, 7),
                (1, 3, 7),
                (2, 4, 6),
                (4, 5, 6),
                (0, 2, 7),
                (2, 6, 7),
                (1, 3, 4),
                (3, 4, 5),
            ]

            faces = [
                (0, 1, 4, 2),
                (3, 5, 6, 7),
                (2, 4, 5, 6),
                (1, 4, 5, 3),
                (0, 2, 6, 7),
                (0, 1, 3, 7),
            ]

            for j in range(verts.shape[0]):
                vertex = numpy.dot(rotation_matrix, verts[j]) + numpy.array(translation)
                verts[j, :] = (vertex[x_index]*scale + offset_x, vertex[y_index]*scale + offset_y, vertex[z_index]*scale + offset_z)
                verts[j, 0] *= -1

            # https://blender.stackexchange.com/questions/2407/how-to-create-a-mesh-programmatically-without-bmesh
            mesh_data = bpy.data.meshes.new("BRC_BB_Mesh_" + str(i))
            mesh_data.from_pydata(verts, [], faces)
            mesh_data.update()

            obj = bpy.data.objects.new("BRC_BB_Object_" + str(i), mesh_data)

            material = blender_utils.get_default_material()
            if not material:
                log("Global 'material' not defined, use set_color before loading.", LogLevel.WARNING)
                return

            # change color
            # this is based on https://stackoverflow.com/questions/4644650/blender-how-do-i-add-a-color-to-an-object
            # but needed changing a lot of attributes according to documentation
            obj.data.materials.append(material)

            # https://blender.stackexchange.com/questions/16688/how-to-add-an-object-to-the-scene-through-python
            bpy.context.scene.objects.link(obj)

TxtBoundingBoxesBbImporter()
