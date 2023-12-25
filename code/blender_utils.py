"""
Blender utilities.
"""

import bpy
import bmesh
from mathutils import Vector,Matrix
from math import radians
from render_logging import log, LogLevel
import numpy as np

# This is the OFF Blender addon from https://github.com/alextsui05/blender-off-addon/blob/master/import_off.py
import import_off
import_off.register()

# Globals ...
camera_target = None
""" (bpy.types.Object) The camera target, by default the origin as Blender object. """
color_global = None
""" (tuple) the global color os tuple (r, g, b), all floats in [0,1]. """
material = None
""" (bpy.types.Material) Global material. """
material_idx = 0
""" (int) Current material index. """
voxel_idx = 0
shadow_plane_idx = 0
""" (int) Shapde plane index. """
ground_plane_idx = 0
""" (int) Ground plane index. """
bounding_box_idx = 0
""" (int) Bounding box index. """
""" (int) Current voxel index; used by add_primitive_object and add_primitive_objects. """
wire_material = None
""" (bpy.types.Material) Material defining the wireframe only. """
custom_mesh_idx = 0
""" (int) Mesh index. """
cube_base_mesh = None
""" (bpy.types.ID) Base mesh for cubes. """
sphere_base_mesh = None
""" (bpy.types.ID) Base mesh for spheres. """
detailed_sphere_base_mesh = None
""" (bpy.types.ID) Base mesh for detailed spheres. """
output_folder = ""
""" (str) Output folder. """
state = None
""" (State) Holds the current state, essentially as struct (second, rot_x, rot_y, rot_z, cam_dist). """
fps = 30
""" (int) Frames per second. """
incremental_mode = False
""" (bool) whether or not to interpret the render commands as incremental. """
have_rendered_before = False
""" (bool) internal value, to show whether we have run a render command before. If we haven't, we ignore incremental_mode. """
output_image_idx = 0
""" (int) Index for output images. """


class State:
    """
    Represents the current state of rendering.
    """

    def __init__(self, Time, rotX, rotY, rotZ, camDist):
        """
        Constructor.

        :param Time: time in seconds
        :type Time: int
        :param rotX: rotation around x
        :type rotX: float
        :param rotY: rotation around y
        :type rotY: float
        :param rotZ: rotation around z
        :type rotZ: float
        :param camDist: distance of camera to origin
        :type camDist: float
        """
        self.Time = Time
        self.rotX = rotX
        self.rotY = rotY
        self.rotZ = rotZ
        self.camDist = camDist

def clear_imported_objects():
    """
    Removes all objects where the name starts with 'BRC'.
    """

    for obj in bpy.data.objects:
        if "BRC" in str(obj.name):
            obj.select = True
            bpy.ops.object.delete()


def initialize_blender(width, height, background, output_path):
    """
    Initialize blender.

    :param width: width of rendered images
    :type width: int
    :param height: height of renderd images
    :type height: int
    :param background: background color, 'transparent', white otherwise
    :type background: str
    :param output_path: output folder
    :type output_path: str
    """

    bpy.ops.mesh.primitive_cube_add()
    global cube_base_mesh
    cube_base_mesh = bpy.context.scene.objects.active.data.copy()
    cube_base_mesh.use_auto_smooth = True

    bpy.ops.mesh.primitive_ico_sphere_add()
    global sphere_base_mesh
    sphere_base_mesh = bpy.context.scene.objects.active.data.copy()
    sphere_base_mesh.use_auto_smooth = True

    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4)
    global detailed_sphere_base_mesh
    detailed_sphere_base_mesh = bpy.context.scene.objects.active.data.copy()
    detailed_sphere_base_mesh.use_auto_smooth = True

    bpy.ops.mesh.primitive_circle_add(vertices=1024, radius=1, fill_type='NGON')
    global circle_base_mesh
    circle_base_mesh = bpy.context.scene.objects.active.data.copy()

    for face in sphere_base_mesh.polygons:
        face.use_smooth = True
    for face in detailed_sphere_base_mesh.polygons:
        face.use_smooth = True

    # Delete the scene, except for the camera and the lamp
    for obj in bpy.data.objects:
        if str(obj.name) in ['Camera']:
            continue
        obj.select = True
        bpy.ops.object.delete()

    scene = bpy.context.scene

    def parent_obj_to_camera(b_camera):
        origin = (0, 0, 0)
        b_empty = bpy.data.objects.new("Empty", None)
        b_empty.location = origin
        b_camera.parent = b_empty  # setup parenting

        scn = bpy.context.scene
        scn.objects.link(b_empty)
        scn.objects.active = b_empty
        return b_empty

    # set the camera and its constraint
    cam = scene.objects['Camera']
    cam.location = Vector((0, 3.0, 1.5))
    cam.data.lens = 35
    cam.data.sensor_width = 32
    cam.data.sensor_height = 32
    cam_constraint = cam.constraints.new(type='TRACK_TO')
    cam_constraint.track_axis = 'TRACK_NEGATIVE_Z'
    cam_constraint.up_axis = 'UP_Y'

    global camera_target
    camera_target = parent_obj_to_camera(cam)
    cam_constraint.target = camera_target

    # Make light just directional from the top
    
#    lamp_data = bpy.data.lamps.new(name="Area Lamp", type="SPOT")
#    lamp_data.shadow_method = 'RAY_SHADOW'
#    lamp_data.spot_blend = 1
#    lamp_data.shadow_soft_size = 1000
#    lamp_data.use_shadow = True
#    lamp_data.energy = 0.5
#  


####

    lamp_energy = 1000.0
    # 1.8 for FFHQ/AFHQ, 4.0 for car, 5.0 for the car in method
    lamp_size = 4.0 
    lamp_radius = 1.1
    lamp_type = "AREA"

    lamp_data = bpy.data.lamps.new(name="Area Lamp", type=lamp_type)
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = 1e6
    lamp_data.size = lamp_size
    lamp_data.energy = lamp_energy
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_object = bpy.data.objects.new(name="Spot Lamp", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = 1.5 * lamp_radius
    lamp_object.location[1] = 0
    lamp_object.location[2] = 1.5 * lamp_radius
    lamp_object.rotation_euler[0] = 0.65
    lamp_object.rotation_euler[1] = 0.0
    lamp_object.rotation_euler[2] = 1.8
    lamp_object.parent = camera_target

    lamp_data = bpy.data.lamps.new(name="Area Lamp", type=lamp_type)
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = 1e6
    lamp_data.size = lamp_size
    lamp_data.energy = lamp_energy
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_object = bpy.data.objects.new(name="Spot Lamp", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = -1.74 * lamp_radius
    lamp_object.location[1] = 1.9 * lamp_radius
    lamp_object.location[2] = 1.5 * lamp_radius
    lamp_object.rotation_euler[0] = -0.2199
    lamp_object.rotation_euler[1] = 1.0158
    lamp_object.rotation_euler[2] = 2.042
    lamp_object.parent = camera_target

    lamp_data = bpy.data.lamps.new(name="Area Lamp", type=lamp_type)
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = 1e6
    lamp_data.size = lamp_size
    lamp_data.energy = lamp_energy
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_object = bpy.data.objects.new(name="Spot Lamp", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = -1.74 * lamp_radius
    lamp_object.location[1] = 1.9 * lamp_radius
    lamp_object.location[2] = 1.5 * lamp_radius
    lamp_object.rotation_euler[0] = -0.2199
    lamp_object.rotation_euler[1] = 1.0158
    lamp_object.rotation_euler[2] = 2.042
    lamp_object.parent = camera_target

    #lamp_data = bpy.data.lamps.new(name="Area Lamp", type=lamp_type)
    #lamp_data.shadow_method = 'RAY_SHADOW'
    #lamp_data.shadow_ray_sample_method = 'CONSTANT_QMC'
    #lamp_data.use_shadow = True
    #lamp_data.shadow_soft_size = 1e6
    #lamp_data.size = lamp_size
    #lamp_data.energy = lamp_energy
    #lamp_data.use_diffuse = True
    #lamp_data.cycles.max_bounces = 16
    #lamp_object = bpy.data.objects.new(name="Spot Lamp", object_data=lamp_data)
    #scene.objects.link(lamp_object)
    #lamp_object.location[0] = 0.11
    #lamp_object.location[1] = -2.0
    #lamp_object.location[2] = 1.5
    #lamp_object.rotation_euler[0] = 0.65
    #lamp_object.rotation_euler[1] = 0.0
    #lamp_object.rotation_euler[2] = -0.24
    #lamp_object.parent = camera_target

    #lamp_data = bpy.data.lamps.new(name="Area Lamp", type=lamp_type)
    #lamp_data.shadow_method = 'RAY_SHADOW'
    #lamp_data.shadow_ray_sample_method = 'CONSTANT_QMC'
    #lamp_data.use_shadow = True
    #lamp_data.shadow_soft_size = 1e6
    #lamp_data.size = lamp_size * 20
    #lamp_data.energy = lamp_energy/20
    #lamp_data.use_diffuse = True
    #lamp_data.cycles.max_bounces = 16
    #lamp_object = bpy.data.objects.new(name="Spot Lamp", object_data=lamp_data)
    #scene.objects.link(lamp_object)
    #lamp_object.location[0] = 1.5
    #lamp_object.location[1] = 1.0 
    #lamp_object.location[2] = -0.43
    #lamp_object.rotation_euler[0] = radians(-461)
    #lamp_object.rotation_euler[1] = radians(-96)
    #lamp_object.rotation_euler[2] = radians(-49.5)
    #lamp_object.parent = camera_target

    lamp_data = bpy.data.lamps.new(name="Area Lamp", type=lamp_type)
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.shadow_ray_sample_method = 'CONSTANT_QMC'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = 1e6
    lamp_data.size = lamp_size
    lamp_data.energy = lamp_energy
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_object = bpy.data.objects.new(name="Spot Lamp", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = -2.21917
    lamp_object.location[1] = -0.889489
    lamp_object.location[2] = 1.68379
    lamp_object.rotation_euler[0] = radians(-48.3)
    lamp_object.rotation_euler[1] = radians(-20.4)
    lamp_object.rotation_euler[2] = radians(105.)
    lamp_object.parent = camera_target

    '''
####


    lamp_energy = 100.0
    lamp_size = 1

    lamp_data = bpy.data.lamps.new(name="Lamp 1 data", type="POINT")
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = lamp_size
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_data.use_nodes = True
    lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = lamp_energy
    
    lamp_object = bpy.data.objects.new(name="Lamp 1 instance", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = 1.5
    lamp_object.location[1] = 0
    lamp_object.location[2] = 1.5
    lamp_object.rotation_euler[0] = 0.65
    lamp_object.rotation_euler[1] = 0.0
    lamp_object.rotation_euler[2] = 1.8
    lamp_object.parent = camera_target

    lamp_data = bpy.data.lamps.new(name="Lamp 2 data", type="POINT")
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = lamp_size
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_data.use_nodes = True
    lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = lamp_energy
    
    lamp_object = bpy.data.objects.new(name="Lamp 2 instance", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = 0.11
    lamp_object.location[1] = -2.0
    lamp_object.location[2] = 1.5
    lamp_object.rotation_euler[0] = 0.65
    lamp_object.rotation_euler[1] = 0.0
    lamp_object.rotation_euler[2] = -0.24
    lamp_object.parent = camera_target

    lamp_data = bpy.data.lamps.new(name="Lamp 3 data", type="POINT")
    lamp_data.shadow_method = 'RAY_SHADOW'
    lamp_data.use_shadow = True
    lamp_data.shadow_soft_size = lamp_size
    lamp_data.use_diffuse = True
    lamp_data.cycles.max_bounces = 16
    lamp_data.use_nodes = True
    lamp_data.node_tree.nodes["Emission"].inputs[1].default_value = lamp_energy
    
    lamp_object = bpy.data.objects.new(name="Lamp 3 instance", object_data=lamp_data)
    scene.objects.link(lamp_object)
    lamp_object.location[0] = -0.35
    lamp_object.location[1] = 0.44
    lamp_object.location[2] = 1.5
    lamp_object.rotation_euler[0] = 0.65
    lamp_object.rotation_euler[1] = 0.0
    lamp_object.rotation_euler[2] = -2.1
    lamp_object.parent = camera_target
    '''

    for scene in bpy.data.scenes:
        scene.render.engine = 'CYCLES'
    try:
        log("Running Blender version %d.%d.%d" % bpy.app.version, LogLevel.INFO)
        if (2, 78, 0) <= bpy.app.version:            
            prefs = bpy.context.user_preferences
            cprefs = prefs.addons['cycles'].preferences
            bpy.context.user_preferences.addons['cycles'].preferences.compute_device_type = 'CUDA'
            bpy.context.user_preferences.addons['cycles'].preferences.devices[0].use = True
            bpy.context.user_preferences.addons['cycles'].preferences.devices[1].use = False
            bpy.context.scene.cycles.device = "GPU"
        else:
            raise TypeError()
    except TypeError:
        log("Could not enable CUDA for Blender. Rendering will be slow.", LogLevel.WARNING)

    scene.render.use_file_extension = False
    scene.render.resolution_x = width
    scene.render.resolution_y = height
    scene.render.resolution_percentage = 100
    scene.render.use_antialiasing = True
    scene.render.use_shadows = True
    world = bpy.context.scene.world
    if background == "transparent":
        scene.render.alpha_mode = 'TRANSPARENT'
        scene.cycles.film_transparent = True
    else:
        world.zenith_color = [1.0, 1.0, 1.0]
        world.horizon_color = [1.0, 1.0, 1.0]
        scene.render.alpha_mode = 'SKY'

    world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs[0].default_value[:3] = (1.,1.,1.)
    bg.inputs[1].default_value = 1.
    world.cycles_visibility.camera = True
    world.cycles_visibility.diffuse = False
    world.cycles_visibility.glossy = False
    world.cycles_visibility.scatter = False
    world.cycles_visibility.shadow = False
    world.cycles_visibility.transmission = False

    
    set_default_color(["0.5","0.5","0.5","1.0"])

    global output_folder
    output_folder = output_path

    global state
    state = State(0, 0, 0, 0, 1)


def set_fps(arguments):
    """
    Set fps.

    :param arguments: list of at least one element, the fps
    :type arguments: list
    """

    global fps
    fps = float(arguments[0])


def set_incremental(arguments):
    """
    Set incremental mode. In incremental mode, every argument in the render command is assumed to be a change compared to where we are currently. This is ignored for the first render command of the file (whether or not that occurred before turning on the incremental mode) so that the default camera position does not interfere.
    
    :param arguments: optionally, "on" or "off". If omitted, turn incremental mode on
    :type arguments: list
    """
    
    global incremental_mode
    if len(arguments) > 0:
        incremental_mode = arguments[0] == "on"
    else:
        incremental_mode = True


def set_quick_rendering():
    """
    Decimates some rendering parameters. Resolution divided by 4, and the number of Cycles samples divided by 16.
    This provides a simple toggle to make sure the animation is what you want it to be before full-quality rendering.
    """
    bpy.context.scene.cycles.samples = bpy.context.scene.cycles.samples/4
    bpy.context.scene.render.resolution_percentage = 25

def set_high_quality_rendering():
    """
    Decimates some rendering parameters. Resolution divided by 4, and the number of Cycles samples divided by 16.
    This provides a simple toggle to make sure the animation is what you want it to be before full-quality rendering.
    """
    bpy.context.scene.cycles.samples = bpy.context.scene.cycles.samples*16


def render(arguments):
    """
    Renders from the last state to the current one by interpolating using the current fps.

    :param arguments: list of arguments
    :return:
    """

    global state, output_folder, fps, output_image_idx, incremental_mode, have_rendered_before

    new_state = State(Time=float(arguments[0]), rotX=float(arguments[1]), rotY=float(arguments[2]),
                      rotZ=float(arguments[3]), camDist=float(arguments[4]))
    
    if incremental_mode and have_rendered_before:
        new_state.Time += state.Time
        new_state.rotX += state.rotX
        new_state.rotY += state.rotY
        new_state.rotZ += state.rotZ
        new_state.camDist += state.camDist
    have_rendered_before = True

    if state.Time > new_state.Time:
        log("Key time lies in the past (%d<%d). Ignoring." % (new_state.Time, state.Time), LogLevel.WARNING)
        return

    log("Rendering from %f to %f with fps %0.2f" % (state.Time, new_state.Time, fps), LogLevel.INFO)
    startframe = int(state.Time*fps)
    stopframe = int(new_state.Time*fps)


    for i in range(startframe, stopframe):
        if fps==1:
            bpy.context.scene.render.filepath = "%s.png" % (output_folder)
        else:
            bpy.context.scene.render.filepath = "%s_%03d.png" % (output_folder,output_image_idx)
        output_image_idx += 1

        alpha = (i - startframe) / (stopframe - startframe)
        this_rot_x = state.rotX + (new_state.rotX - state.rotX) * alpha
        this_rot_y = state.rotY + (new_state.rotY - state.rotY) * alpha
        this_rot_z = state.rotZ + (new_state.rotZ - state.rotZ) * alpha
        print('****************************')
        print(this_rot_x, this_rot_y, this_rot_z)
        # set the camera
        camera_target.rotation_euler[0] = radians(this_rot_x)
        camera_target.rotation_euler[1] = radians(this_rot_y)
        camera_target.rotation_euler[2] = radians(this_rot_z)

        cam = bpy.context.scene.objects['Camera']
        this_dist = state.camDist + (new_state.camDist - state.camDist) * alpha
        cam.location = Vector((0, 3.0, 0.0)) * this_dist

        bpy.ops.render.render(animation=False, write_still=True)

    state = new_state


def make_material(name, diffuse, specular, alpha, shadow=False):
    """
    Make a material of the given name and properties.

    :param name: name of material
    :type name: str
    :param diffuse: use diffuse color
    :type diffuse: bool
    :param specular: use specular color
    :type specular: bool
    :param alpha: transparency
    :type alpha: float
    :param shadow: use shadows
    :type shadow: bool
    :return: material
    :rtype: bpy.types.Material
    """

    mat = bpy.data.materials.new(name)
    mat.diffuse_color = diffuse
    # mat.specular_color = specular
    # mat.specular_shader = 'COOKTORR'
    # mat.specular_intensity = 2
    mat.use_nodes = True

    ng = mat.node_tree
    diffuse_node = ng.nodes.new("ShaderNodeBsdfPrincipled")
    diffuse_node.inputs[0].default_value[0] = diffuse[0]
    diffuse_node.inputs[0].default_value[1] = diffuse[1]
    diffuse_node.inputs[0].default_value[2] = diffuse[2]
    diffuse_node.inputs[0].default_value[3] = 1.0
    diffuse_node.inputs[4].default_value = 0.2 # metallic
    diffuse_node.inputs[5].default_value = 0.2 # specular
    diffuse_node.inputs[7].default_value = 0.5  # roughness
    diffuse_node.inputs[12].default_value = 0.5 # clearcoat
    diffuse_node.distribution = "GGX"
    transparent = ng.nodes.new("ShaderNodeBsdfTransparent")
    mixer = ng.nodes.new("ShaderNodeMixShader")
    mixer.inputs[0].default_value = alpha

    ng.links.new(mixer.inputs[1], transparent.outputs[0])
    ng.links.new(mixer.inputs[2], diffuse_node.outputs[0])
    material_output = ng.nodes.get('Material Output')
    ng.links.new(material_output.inputs[0], mixer.outputs[0])

    mat.use_cast_shadows = shadow
    mat.use_shadows = shadow

    return mat


def set_default_color(arguments):
    """
    Set the default color, sets the globals color_global, material_idx, material and wire_material.

    :param arguments: argument list
    :type arguments: list
    """
    global color_global

    color_global = [float(arguments[0]), float(arguments[1]), float(arguments[2])]
    alpha = float(arguments[3]) if len(arguments) > 3 else 1
    shadow = float(arguments[4]) if len(arguments) > 4 else True
    shadow = True if shadow > 0 else False


    global material_idx
    material_idx += 1
    mat = make_material('BRC_CubeMaterial_%d' % material_idx,
                       color_global, [1., 1., 1.], alpha, shadow)

    global material
    material = mat

    global wire_material
    wire_material = make_material('BRC_wireframe_%d' % material_idx,
                       [color_global[0]/3, color_global[1]/3, color_global[2]/3], [0., 0., 0.], 1.0)


def get_default_color():
    """
    Get the default color.

    :return: color as tuple
    :rtype: tuple
    """

    global color_global
    return color_global


def get_default_material():
    """
    Get default material.

    :return: material
    :rtype: bpy.types.Material
    """

    global material
    return material


def get_wire_material():
    """
    Get wire material.

    :return: wire material
    :rtype: bpy.types.Material
    """

    global wire_material
    return wire_material


def add_cube(location,radius,color=None):
    """
    Add a single cube at given location with given radius

    :param location: tuple as location
    :type location: tuple
    :param radius: radius
    :type radius: float
    :param color: color tuple
    :type color: tuple
    :return:
    """

    add_primitive_object(cube_base_mesh,location,radius,color,wireframe=True)


def get_cube_mesh():
    """
    Get the cube base mesh.

    :return: mesh
    :rtype: bpy.types.ID
    """

    global cube_base_mesh
    return cube_base_mesh


def add_sphere(location,radius,color=None):
    """
    Add a single sphere at given location with given radius

    :param location: tuple as location
    :type location: tuple
    :param radius: radius
    :type radius: float
    :param color: color tuple
    :type color: tuple
    :return:
    """

    add_primitive_object(sphere_base_mesh, location, radius, color, wireframe=False)


def get_sphere_mesh():
    """
    Get the sphere base mesh.

    :return: mesh
    :rtype: bpy.types.ID
    """

    global sphere_base_mesh
    return sphere_base_mesh


def add_detailed_sphere(location,radius,color=None):
    """
    Add a single detailed sphere at given location with given radius

    :param location: tuple as location
    :type location: tuple
    :param radius: radius
    :type radius: float
    :param color: color tuple
    :type color: tuple
    :return:
    """

    add_primitive_object(detailed_sphere_base_mesh,location,radius,color,wireframe=False)


def get_detailed_sphere_mesh():
    """
    Get the detailed sphere base mesh.

    :return: mesh
    :rtype: bpy.types.ID
    """

    global detailed_sphere_base_mesh
    return detailed_sphere_base_mesh


def shadow_plane(arguments):
    """
    Place a shadow plane at the given location with given radius.

    :param arguments: argument list
    :type arguments: list
    """

    offset_x = float(arguments[0]) if len(arguments) > 0 else 0.
    offset_y = float(arguments[1]) if len(arguments) > 1 else 0.
    offset_z = float(arguments[2]) if len(arguments) > 2 else 0.
    scale = float(arguments[3]) if len(arguments) > 3 else 1.

    global circle_base_mesh
    global shadow_plane_idx
    ob = bpy.data.objects.new("BRC_Shadow_Plane", circle_base_mesh)
    shadow_plane_idx += 1

    ob.location = (offset_x, offset_y, offset_z)
    ob.scale = (scale, scale, scale)
    bpy.context.scene.objects.link(ob)

    global material
    mat = material

    mat.use_shadows = True
    mat.use_transparent_shadows = True
    mat.use_only_shadow = True
    mat.use_raytrace = True
    mat.ambient = 0

    ob.data.materials.append(mat)
    ob.active_material_index = 0
    ob.active_material =False


def bounding_box(arguments):
    """
    Place a bounding box at the given position with the given 5ize.

    :param arguments: argument list
    :type arguments: list
    """

    center_x = float(arguments[0]) if len(arguments) > 0 else 0
    center_y = float(arguments[1]) if len(arguments) > 1 else 0
    center_z = float(arguments[2]) if len(arguments) > 2 else 0
    size_x = float(arguments[3]) if len(arguments) > 3 else 1
    size_y = float(arguments[4]) if len(arguments) > 4 else 1
    size_z = float(arguments[5]) if len(arguments) > 5 else 1
    rotation_y = float(arguments[6]) if len(arguments) > 6 else 0

    rotation = np.eye(3)
    rotation[0, 0] = np.cos(rotation_y)
    rotation[0, 1] = -np.sin(rotation_y)
    rotation[1, 0] = np.sin(rotation_y)
    rotation[1, 1] = np.cos(rotation_y)

    verts = np.zeros((8, 3), dtype=float)
    verts[0, :] = (- size_x / 2, - size_y / 2, - size_z / 2)  # left lower front
    verts[1, :] = (+ size_x / 2, - size_y / 2, - size_z / 2)  # right lower front
    verts[2, :] = (- size_x / 2, + size_y / 2, - size_z / 2)  # left upper front
    verts[3, :] = (+ size_x / 2, - size_y / 2, + size_z / 2)  # right lower back
    verts[4, :] = (+ size_x / 2, + size_y / 2, - size_z / 2)  # right upper front
    verts[5, :] = (+ size_x / 2, + size_y / 2, + size_z / 2)  # right upper back
    verts[6, :] = (- size_x / 2, + size_y / 2, + size_z / 2)  # left upper back
    verts[7, :] = (- size_x / 2, - size_y / 2, + size_z / 2)  # left lower back

    faces = [
        (0, 1, 4, 2),
        (3, 5, 6, 7),
        (2, 4, 5, 6),
        (1, 4, 5, 3),
        (0, 2, 6, 7),
        (0, 1, 3, 7),
    ]

    verts = np.dot(rotation, verts.T).T
    verts[:, 0] += center_x
    verts[:, 1] += center_y
    verts[:, 2] += center_z

    # https://blender.stackexchange.com/questions/2407/how-to-create-a-mesh-programmatically-without-bmesh
    global bounding_box_idx
    mesh_data = bpy.data.meshes.new("BRC_BoundingBox_" + str(bounding_box_idx))

    mesh_data.from_pydata(verts, [], faces)
    mesh_data.update()

    obj = bpy.data.objects.new("BRC_BB_Object_" + str(bounding_box_idx), mesh_data)

    material = get_default_material()
    if not material:
        log("Global 'material' not defined, use set_color before loading.", LogLevel.WARNING)
        return

    # change color
    # this is based on https://stackoverflow.com/questions/4644650/blender-how-do-i-add-a-color-to-an-object
    # but needed changing a lot of attributes according to documentation
    obj.data.materials.append(material)

    mod = obj.modifiers.new("BRC_BB_Object_Wireframe_" + str(bounding_box_idx), 'WIREFRAME')
    mod.thickness = 0.01 / 2.5
    mod.use_relative_offset = False
    mod.material_offset = len(obj.data.materials)
    mod.use_replace = False
    obj.data.materials.append(get_wire_material())

    # https://blender.stackexchange.com/questions/16688/how-to-add-an-object-to-the-scene-through-python
    bpy.context.scene.objects.link(obj)
    bounding_box_idx += 1


def ground_plane(arguments):
    """
    Place a ground plane at the given location with given radius.

    :param arguments: argument list
    :type arguments: list
    """

    offset_x = float(arguments[0]) if len(arguments) > 0 else 0.
    offset_y = float(arguments[1]) if len(arguments) > 1 else 0.
    offset_z = float(arguments[2]) if len(arguments) > 2 else 0.
    scale = float(arguments[3]) if len(arguments) > 3 else 1.

    global circle_base_mesh
    global ground_plane_idx
    ob = bpy.data.objects.new("BRC_Ground_Plane_%d" % ground_plane_idx, circle_base_mesh)
    ground_plane_idx += 1

    ob.location = (offset_x, offset_y, offset_z)
    ob.scale = (scale, scale, scale)
    bpy.context.scene.objects.link(ob)

    global material
    mat = material

    ob.data.materials.append(mat)
    ob.active_material_index = 0
    ob.active_material = mat


def add_primitive_object(base_mesh,location,radius,color=None,wireframe=False):
    """
    Adds a single primitive object based on the given mesh.

    :param base_mesh: mesh to place
    :type base_mesh: bpy.types.ID
    :param location: location as tuple
    :type location: tuple
    :param radius:  radius of mesh, i.e. scale
    :type radius: float
    :param color: color as tuple
    :type color: tuple
    :param wireframe: whether to set wireframe material
    :type wireframe: bool
    """

    global voxel_idx
    ob = bpy.data.objects.new("BRC_Voxel_%d" % voxel_idx, base_mesh.copy())
    voxel_idx += 1
    ob.location = location
    ob.scale = radius
    bpy.context.scene.objects.link(ob)

    if not color:
        global material
        mat = material
    else:
        mat = make_material('BRC_Voxel_color_%d' % voxel_idx, color, [1., 1., 1.], 1. )

    ob.data.materials.append(mat)
    ob.active_material_index = 0
    ob.active_material = mat
    ob.show_transparent = True

    if wireframe:
        mod = ob.modifiers.new("Wireframe_%d" % voxel_idx, 'WIREFRAME')
        mod.thickness = 0.01/(radius[0])
        mod.use_relative_offset = False
        mod.material_offset = len(ob.data.materials)
        mod.use_replace = False
        ob.data.materials.append(wire_material)


def add_primitive_objects(base_mesh,locations,radii,color=None,rotation=None):
    """
    Adds a set of primitiev object based on the given mesh.

    :param base_mesh: mesh to place
    :type base_mesh: bpy.types.ID
    :param locations: locations
    :type locations: numpy.ndarray
    :param radius:  radii
    :type radius: numpy.ndarray
    :param color: color as tuple
    :type color: tuple
    :param wireframe: whether to set wireframe material
    :type wireframe: bool
    """

    assert locations.shape[0] == radii.shape[0]

    mesh = bmesh.new()
    for i in range(locations.shape[0]):
        m = base_mesh.copy()

        for vertex in m.vertices:
            vertex_copy = [vertex.co[0], vertex.co[1], vertex.co[2]]

            if not rotation is None:
                vertex_copy[0] = rotation[0, 0] * vertex.co[0] + rotation[0, 1] * vertex.co[1] + rotation[0, 2] * vertex.co[2]
                vertex_copy[1] = rotation[1, 0] * vertex.co[0] + rotation[1, 1] * vertex.co[1] + rotation[1, 2] * vertex.co[2]
                vertex_copy[2] = rotation[2, 0] * vertex.co[0] + rotation[2, 1] * vertex.co[1] + rotation[2, 2] * vertex.co[2]

            vertex.co[0] = vertex_copy[0] * radii[i, 0] + locations[i, 0]
            vertex.co[1] = vertex_copy[1] * radii[i, 1] + locations[i, 1]
            vertex.co[2] = vertex_copy[2] * radii[i, 2] + locations[i, 2]

        mesh.from_mesh(m)

    global custom_mesh_idx
    custom_mesh_idx += 1

    mesh2 = bpy.data.meshes.new("newMesh_%d" % custom_mesh_idx)
    mesh.to_mesh(mesh2)

    if not color:
        global material
        mat = material
    else:
        mat = make_material('BRC_Voxel_color_%d' % voxel_idx, color, [1., 1., 1.], 1. )

    obj = bpy.data.objects.new("BRC_Custom_Object_%d" % custom_mesh_idx, mesh2)
    obj.data.materials.append(mat)
    obj.active_material_index = 0
    obj.active_material = mat

    bpy.context.scene.objects.link(obj)


def add_object_from_mesh(vertices, faces, scale, offset):
    """
    Add an object from mesh.

    :param vertices: list of vertices
    :type vertices: list
    :param faces: list of faces
    :type faces: list
    :param scale: scale as tuple
    :type scale: tuple
    :param offset: offset as tuple
    :type offset: tuple
    """

    global custom_mesh_idx
    custom_mesh_idx += 1
    me = bpy.data.meshes.new("BRC_Custom_Mesh_%d" % custom_mesh_idx)
    me.from_pydata(vertices, [], faces)
    me.update()
    for vertex in me.vertices:
        vertex.co[0] = vertex.co[0] * scale[0] + offset[0]
        vertex.co[1] = vertex.co[1] * scale[1] + offset[1]
        vertex.co[2] = vertex.co[2] * scale[2] + offset[2]
    for face in me.polygons:
        face.use_smooth = True
    ob = bpy.data.objects.new("BRC_Custom_Object_%d" % custom_mesh_idx, me)
    bpy.context.scene.objects.link(ob)
    bpy.context.scene.objects.active = ob

    ob.data.materials.append(material)
