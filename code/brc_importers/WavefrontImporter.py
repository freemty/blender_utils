from brc_importers.ImportDelegator import Importer
import bpy
from render_logging import log, LogLevel
import blender_utils
import numpy as np


class WavefrontImporter(Importer):

    def name(self):
        return "wavefront_obj"

    def load(self, arguments):
        filename = arguments[0]
        bpy.ops.import_scene.obj(filepath=filename)

        offset_x = float(arguments[1]) if len(arguments) > 1 else 0
        offset_y = float(arguments[2]) if len(arguments) > 2 else 0
        offset_z = float(arguments[3]) if len(arguments) > 3 else 0
        scale = float(arguments[4]) if len(arguments) > 4 else 1
        axes = str(arguments[5]) if len(arguments) > 5 else "xyz"
        rotate_x = float(arguments[6]) if len(arguments) > 6 else 0
        rotate_y = float(arguments[7]) if len(arguments) > 7 else 0
        rotate_z = float(arguments[8]) if len(arguments) > 8 else 0

        x_index = axes.find("x")
        y_index = axes.find("y")
        z_index = axes.find("z")

        assert x_index >= 0 and x_index < 3
        assert y_index >= 0 and y_index < 3
        assert z_index >= 0 and z_index < 3
        assert x_index != y_index and x_index != z_index and y_index != z_index

        rotation_x = np.array([[1, 0, 0], [0, np.cos(rotate_x), -np.sin(rotate_x)], [0, np.sin(rotate_x), np.cos(rotate_x)]])
        rotation_y = np.array([[np.cos(rotate_y), 0, np.sin(rotate_y)], [0, 1, 0], [-np.sin(rotate_y), 0, np.cos(rotate_y)]])
        rotation_z = np.array([[np.cos(rotate_z), -np.sin(rotate_z), 0], [np.sin(rotate_z), np.cos(rotate_z), 0], [0, 0, 1]])
        rotation = np.dot(rotation_z, np.dot(rotation_y, rotation_x))

        for obj in bpy.context.scene.objects:
            # obj.name contains the group name of a group of faces, see http://paulbourke.net/dataformats/obj/
            # every mesh is of type 'MESH', this works not only for ShapeNet but also for 'simple'
            # obj files
            if obj.type == "MESH" and not "BRC" in obj.name:
                for vertex in obj.data.vertices:
                    # make a copy, otherwise axes switching does not work
                    vertex_copy = (vertex.co[0], vertex.co[1], vertex.co[2])

                    vertex.co[0] = vertex_copy[x_index]*scale + offset_x
                    vertex.co[1] = vertex_copy[y_index]*scale + offset_y
                    vertex.co[2] = vertex_copy[z_index]*scale + offset_z

                    vertex_copy = (vertex.co[0], vertex.co[1], vertex.co[2])
                    vertex.co[0] = rotation[0, 0] * vertex_copy[0] + rotation[0, 1] * vertex_copy[1] + rotation[0, 2] * vertex_copy[2]
                    vertex.co[1] = rotation[1, 0] * vertex_copy[0] + rotation[1, 1] * vertex_copy[1] + rotation[1, 2] * vertex_copy[2]
                    vertex.co[2] = rotation[2, 0] * vertex_copy[0] + rotation[2, 1] * vertex_copy[1] + rotation[2, 2] * vertex_copy[2]
                #mod = obj.modifiers.new("BRC_Wireframe_" + obj.name, 'WIREFRAME')
                #mod.thickness = 0.001
                #mod.use_relative_offset = False
                #mod.material_offset = len(obj.data.materials)
                #mod.use_replace = False
                #mod.use_boundary = False
                #mod.use_apply_on_spline = False
                #obj.data.materials.append(blender_utils.get_wire_material())

                obj.name = "BRC_" + obj.name

WavefrontImporter()
