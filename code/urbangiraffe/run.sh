#!/bin/bash

if [ -z "$BLENDER" ]; then
    #export BLENDER="/home/yliao/Downloads/blender-2.79b-linux-glibc219-x86_64/blender"
    export BLENDER="blender"
    echo $BLENDER
fi

echo "Using $BLENDER."
#"$BLENDER" --background --python render_keys.py -- "urbangiraffe/render_color.txt" 1>/dev/null  --output_folder "urbangiraffe/output/" --bg white --width 1024 --height 1024
"$BLENDER" --background --python render_keys.py -- "urbangiraffe/render_ins.txt" 1>/dev/null  --output_folder "urbangiraffe/output_ins/" --bg white --width 1024 --height 1024
cd "veri3d/output/"
#ffmpeg -y -r 10 -i %05d.png -c:v libx264 -vf fps=30 -pix_fmt yuv420p output.mp4
