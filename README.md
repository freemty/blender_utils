# blendviz

## Requirements
### Necessary
- Blender (suggested version 2.76.0, or 2.79.0 which the code was tested on).
This is present in Ubuntu's official repositories: `sudo apt-get install blender`.

### Suggested
- scikit_image (`pip(3) install scikit_image`) for its marching cubes implementation.
Without it, the `marching_cubes` will not render anything.

### Optional
- torchfile (`pip(3) install torchfile`) for its loading of lua torch data files.
Without it, T7 importers will simply not be available to the script.

## Documentation

The script works with a keyframe-based approach.
It goes sequentially through the key file, and executes the commands found there.
As demonstrated in `code/example.sh`, entry point is `render_key.py` which is - together with blender called as follows:

    "$BLENDER" --background --python render_keys.py -- "key_file.txt" 1>/dev/null --output_folder output/ --bg white --width 512 --height 448

The `--background` argument causes Blender to run in the background.
Removing this argument can be used to interactively debug a scene.
Arguments of `render_keys.py` include:
- `--output_folder`: folder for rendered images;
- `--bg`: background color - currently either `transparent` or `white` (default);
- `--width`: width of rendered image(s);
- `--height`: height of rendered image(s).

The key file has the following form:

    # this is a comment
    # only full-line comments are supported!
    set_fps 10
    # reset
    render 0 0 0 0 0
    # load objects, models etc.
    # ...
    # render up to second 1 with the given view, see below
    render 1 0 0 0 1
    clear

The commands are discussed in detail in the following.

### `set_fps`

Sets the fps rate used for rendering as follows:

    set_fps fps_rate

### `render`

The render command has the form

    render time rot_x rot_y rot_z cam_dist

and causes Blender to render up to the specified time in seconds, using the specified fps rate.
The camera position is specified by the rotation around the x axis, the rotation around the y axis and the rotation around the z axis.
Additionally, the distance of the camera from the origin is specified.
The camera is always looking towards the origin.
Note that in blender, x = right, y = forward and z = up.
If the render command is used multiple times, the view interpolates between the different camera positions.

### `set_incremental`

Toggle incremental mode (without arguments, turn on, or append "on" and "off" as required). In incremental mode, any render command is assumed to contain deltas to the current state.
Incremental mode is ignored for the very first render command of the file (whether or not that occured before the `set_incremental` call), so that the default settings (mainly camera distance) do not interfere with your script.

### `clear`

Used to clear the scene; allows to render another scene by loading new models/objects.

### `exit`

Exit the script at the given line.

### `set_color`

To determine the color, transparency and shadow properties of loaded models and objects (as long as the corresponding loaded supports color):

    set_color r g b a shadow

The last argument, `shadow`, determines if the loaded models/objects cast shadow.
Color and transparency, `r g b a`, have to be in `[0, 1]` and shadow is either `1` (casting shadows) or `0``(not casting shadows).

### `ground_plane`

Places a circular ground plane at the given location with the given size:

    ground_plane location_x location_y location_z radius

The color is set using `set_color`.
By default, the ground plane casts and receives shadows, see the `ground_plane` method in `blender_utils.py`.

### `shadow_plane`

Similar to `ground_plane` a circular plane is placed at the specified location.
However, `shadow_plane` only receives shadows using the color specified by `set_color` and is not rendered solid itself:

    shadow_plane location_x location_y location_z radius

See the `shadow_plane` method in `blender_utils.py` for details.

### `load`

The `load` commands loads a model/object using a specified loader.
All supported loaders are defined in `code/brc_importers` and have to provide the `name` method and the `load` method.
As example, a simple loader looks as follows:

from brc_importers.ImportDelegator import Importer
import bpy
import blender_utils
from render_logging import log, LogLevel


    class MyImporter(Importer):
    
        def name(self):
            return "my_importer"
    
        def load(self, arguments):
            pass
    
    MyImporter()

The name of the importer specifies the key used for calling the loader in the key file.
The above loaded is therefore called using

    load my_importer [argument list ...]

Currently, the following importers are provided:

#### `npy`

Loads an `.npy` file corresponding to a signed distance function saved in `1 x X x Y x Z`:

    load npy filepath cubes|spheres|marching_cubes scale_x scale_y scale_z

The loaded signed distance function is displayed using cubes, spheres or as mesh derived from marchign cubes.
The cubes/spheres' size is determined by `scale_x`, `scale_y` and `scale_z`.
If only `scale_x` is given, all axes are scaled using this value.

#### `t7`

Loads an `.t7` file as described using the `npy` loader, see above.

#### `npy_prob`

Similar to the `npy` loader, the `npy_prob` loader takes a `C x X x Y x Z` volume where `C >= 1` and the first channels corresponds to the probability of a voxel belonging to the interior of an object:

    npy_prob filepath cubes|spheres|marching_cubes scale_x scale_y scale_z

The options are the same as for the `npy` loader.

#### `t7_prob`

See the `npy_prob` and `npy` loaders, except that a `.t7` file is expected.

#### `wavefront_obj`

This loader is used to load `.obj` files (including the corresponding `.mtl` material definitions); see [here](http://paulbourke.net/dataformats/obj/) and [here](http://paulbourke.net/dataformats/mtl/) for format specifications.

    load wavefront_obj filepath location_x location_y location_z scale axes

The arguments specify the location of the object as well as its scale (the same for all axes).
The final argument allow sto swap axes, default is `xyz`; every combination of `x`, `y` and `z` can be used.
For example, `xzy` will cause the `y` and `z` axes of the input `.obj` file to be swapped _before_ scaling and translating to the right location (i.e. `location_x`, `location_y` and `location_z` are always in Blender coordinates).
In detail, the string `xzy` specifies, for each axes, the index of the corresponding axes in the input coordinates;
i.e. the `x` axes can be found using index `0` (= first character in `xzy`), the `y` axis can be found using index `2` (= third entry in `xzy`) and so forth.

Note that there is a discrepancy in either the `.off` loader (see `code/import_iff.py`) or Blenders built-in `.obj` loader as the same model will appear slightly shifted.
We assume the `.obj` loader to be the problem.

#### `txt_voxel_list` and `efficient_txt_voxel_list`

Loads a set of points/voxels from a `.txt` file in the following format:

    number_of_points
    p1x p1y p1z optional_radius1
    p2x p2y p2z optional_radius2
    p3x p3y p3z optional_radius3

The points can then be displayed using:

    load txt_voxel_list filepath cubes|spheres|detailed_spheres offset_x offset_y offset_z scale_x scale_y scale_z axes radius

The last argument, `radius` specifies the radius of each cube/sphere if no radius is given in the `.txt` file.
The offset and the scale is applied on each point after determining the correct axes.
This is done as described for the `wavefront_obj` loader, i.e. default is `xyz`, while `xzy` will swap `y` and `z` axes _before_ scaling and offseting.

_Note that in contrast to the `.npy` and `.t7` loaders, scale does not define the size of cubes/spheres._

**Using the `efficient_txt_voxel_list` loader is faster.**

#### `off`

Loads an `.off` file (see [here](http://segeval.cs.princeton.edu/public/off_format.html) for specifications):

    load off filepath location_x location_y location_z scale axes

Parameters are the same as for the `wavefront_obj` loader.
Note that there is a discrepancy in either the `.off` loader (see `code/import_iff.py`) or Blenders built-in `.obj` loader as the same model will appear slightly shifted.
We assume the `.obj` loader to be the problem.

#### `bin` and `efficient_bin`

Loads point clouds from [KITTI](http://www.cvlibs.net/datasets/kitti/)'s `.bin` format:

    load bin filepath cubes|spheres|detailed_spheres radius offset_x offset_y offset_z scale_x scale_y scale_z axes skip
    
Where the radius determines the size of the cubes/spheres, and offset and scale is applied after determining the correct axes as described for the `wavefront_obj` and `off` loaders.
By default, `xyz`, i.e. Blender's, axes are used; `xzy`, for example, flips the `y` and `z` axes.
Finally, `skip` determines how many points to skip, i.e. only every `skip`th point is rendered - useful for large points clouds as rendering and loading can be slow!

**Using the `efficient_bin` loader is faster.**

#### `binvox`

Loads `.binvox` files; see [here](http://www.patrickmin.com/binvox/binvox.html) for specifications:

    load binvox filepath cubes|spheres|detailed_spheres radius offset_x offset_y offset_z scale_x scale_y scale_z axes

Here, the radius determines the size of the spehres/cubes, the offset and scale is applied after determining the axes as
described above or for the `wavefront_obj` loader.

_Note that in contrast to the `.npy` and `.t7` loaders, scale does not define the size of cubes/spheres._

#### `txt_bounding_boxes`

Loads bounding boxes from the following `.txt` format:

    number_of_bounding_boxes
    size1x size1y size1z center1x center1y center1z rotation1x rotation1y rotation1z
    size2x size2y size2z center2x center2y center2z rotation2x rotation2y rotation2z
    size3x size3y size3z center3x center3y center3z rotation3x rotation3y rotation3z
    ...

Arguments are as follows:

    load txt_bounding_boxes offset_x offset_y offset_z scale axes padding
  
Where the offset is defined for all bounding boxes, as is the scale and are applied after determining the axes, see the `wavefront_obj` loader for details.
The padding is applied on each bounding box and is specified as the fraction (in `[0,1]`) of the side length, e.g. the height is multiplied by `1 + 2*padding`.

## Tips, Tricks and Known Issues

**Debugging.**

Remove the `--background` option to load a scene interactively in Blender and manipulate it.
Make sure to remove `render`, `clear` and `exit` statements.

**Lighting and Material.**

Lighting and material (especially with regard to shadows) are best determined interactively by removing the `--background` option and manually adding/manipulating light sources in Blender.
The light sources can then be "exported", i.e. the light properties can be implemented in Python in the `initialize_blender` method in `blender_utils.py`.
For example:

    locations = [
        (-0.98382, 0.445997, 0.526505),
        (-0.421806, -0.870784, 0.524944),
        (0.075576, -0.960128, 0.816464),
        (0.493553, -0.57716, 0.928208),
        (0.787275, -0.256822, 0.635172),
        (1.01032, 0.148764, 0.335078)
    ]

    for i in range(len(locations)):
        lamp_data = bpy.data.lamps.new(name="Point Lamp " + str(i), type="POINT")
        lamp_data.shadow_method = 'RAY_SHADOW'
        lamp_data.shadow_ray_sample_method = 'CONSTANT_QMC'
        lamp_data.use_shadow = True
        lamp_data.shadow_soft_size = 1e6
        lamp_data.distance = 2
        lamp_data.energy = 0.1
        lamp_data.use_diffuse = True
        lamp_data.use_specular = True
        lamp_data.falloff_type = 'CONSTANT'

        lamp_object = bpy.data.objects.new(name="Spot Lamp " + str(i), object_data=lamp_data)
        scene.objects.link(lamp_object)
        lamp_object.location[0] = locations[i][0]
        lamp_object.location[1] = locations[i][1]
        lamp_object.location[2] = locations[i][2]
        lamp_object.rotation_euler[0] = 0
        lamp_object.rotation_euler[1] = 0
        lamp_object.rotation_euler[2] = 0
        lamp_object.parent = camera_target

This will add six lamps in the given locations.

**No admin rights, can't install `scikit-image` globally and Blender isn't able to import it.**

Try to follow these steps:
- Install blender locally by downloading it and extracting it. You might need to use the included binary directly instead of just `blender` to avoid using the globally installed one.
- Install `scikit-image` directly into the python directory included in Blender, e.g. using `pip3 install --target=/path/to/blender-2.79-linux-glibc219-x86_64/2.79/python/lib/python3.5/site-packages scikit-image`. Check that the packages are really installed in this location.
- Use the python binary included in Blender to check whether it is possible to import `skimage`.

## Missing features

A list of the features that still need implementing:
- An importer for lines and arrows as required by Aseem (see respective branch)
- AR mode: setting blender's camera based on a passed camera matrix (see respective branch)
- An importer for textured meshes (e.g. FBX import, see sample code from Simon)
- Unification of the command-line arguments to the key list file.
