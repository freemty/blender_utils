from brc_importers.ImportDelegator import Importer
import bpy


class COffImporter(Importer):

    def name(self):
        return "coff"

    def load(self, arguments):
        global material

        filename = arguments[0]
        # support coff files!
        bpy.ops.import_mesh.off(filepath=filename)

        offset_x = float(arguments[1]) if len(arguments) > 1 else 0
        offset_y = float(arguments[2]) if len(arguments) > 2 else 0
        offset_z = float(arguments[3]) if len(arguments) > 3 else 0
        scale = float(arguments[4]) if len(arguments) > 4 else 0
        axes = str(arguments[5]) if len(arguments) > 5 else "xyz"

        x_index = axes.find("x")
        y_index = axes.find("y")
        z_index = axes.find("z")

        assert x_index >= 0 and x_index < 3
        assert y_index >= 0 and y_index < 3
        assert z_index >= 0 and z_index < 3
        assert x_index != y_index and x_index != z_index and y_index != z_index

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

                    obj.name = "BRC_"+obj.name

COffImporter()
