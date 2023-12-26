import bpy

bpy.ops.mesh.primitive_cube_add()

cube = bpy.context.object

cube.location = (0, 0, 2)
cube.scale = (2, 2, 2)