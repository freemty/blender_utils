"""
A script to render a sequence of voxel clouds with an animated camera
Using blender to render everything
This is simply for visualization purposes, so we don't generate depth maps or anything else fancy
Also produces depth map at the same time.

blender --background --python render_keys.py -- example/key_list.txt 1>/dev/null
"""

import argparse, sys, os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('/Users/sum_young/miniconda3/envs/blenderviz/lib/python3.8/site-packages')
# sys.path.append('/Users/sum_young/anaconda3/envs/pytorch1.8/lib/python3.8/site-packages')
print(sys.path)
import blender_utils
from render_logging import log, LogLevel
from brc_importers.ImportDelegator import initialize_importers,handle_import

npy_meshtype = "cube_cloud"
sphere_list_quality="high"


def main():
    """
    Main method.
    """

    parser = argparse.ArgumentParser(description='Renders a set of voxel clouds described by a list of keys.')
    parser.add_argument('keys', type=str,
                        help='Path to the key file to be rendered. Mandatory')
    parser.add_argument('--output_folder', type=str, default='output_frames/',
                        help='The path the output will be dumped to.')
    parser.add_argument('--width', type=float, default=1024,
                        help='Width of the output images.')
    parser.add_argument('--height', type=float, default=1024,
                        help='Height of the output images.')
    parser.add_argument('--bg', type=str, default='white',
                        help="Background of the images: either 'transparent' or 'white'. Defaults to white (easier for videos).")

    try:
        argv = sys.argv[sys.argv.index("--") + 1:]
    except ValueError:
        argv = ""
    args = parser.parse_args(argv)

    blender_utils.initialize_blender(args.width, args.height, args.bg, args.output_folder)

    os.makedirs(os.path.dirname(args.output_folder), exist_ok=True)

    # load the key descriptors
    key_file = open(args.keys,'r')
    key_lines = key_file.readlines()
    key_file.close()

    initialize_importers()

    no_render=False

    # now render all frames!
    for line in key_lines:
        line = line.strip()
        if len(line) == 0 or line[0] == '#':
            continue

        commands = line.split()
        if commands[0] == "render":
            if not no_render:
                blender_utils.render(commands[1:])
            else:
                log("Render command in norender mode interpreted as 'exit'")
                return
        elif commands[0] == "norender":
            no_render = True
        elif commands[0] == "dorender":
            no_render = False
        elif commands[0] == "load":
            handle_import(commands[1:])
        elif commands[0] == "clear":
            blender_utils.clear_imported_objects()
        elif commands[0] == "set_color":
            blender_utils.set_default_color(commands[1:])
        elif commands[0] == "set_fps":
            blender_utils.set_fps(commands[1:])
        elif commands[0] == "set_incremental":
            blender_utils.set_incremental(commands[1:])
        elif commands[0] == "quick_render":
            blender_utils.set_quick_rendering()
        elif commands[0] == "high_quality_render":
            blender_utils.set_high_quality_rendering()
        elif commands[0] == "bounding_box":
            blender_utils.bounding_box(commands[1:])
        elif commands[0] == "ground_plane":
            blender_utils.ground_plane(commands[1:])
        elif commands[0] == "shadow_plane":
            blender_utils.shadow_plane(commands[1:])
        elif commands[0] == "exit":
            return
        else:
            log("Command line '%s' not understood. Ignoring." % line, LogLevel.WARNING)


if __name__ == '__main__':
    main()
