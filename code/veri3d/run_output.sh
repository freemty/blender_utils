#!/bin/bash

if [ -z "$BLENDER" ]; then
    #export BLENDER="/home/yliao/Downloads/blender-2.79b-linux-glibc219-x86_64/blender"
    export BLENDER="blender"
    echo $BLENDER
fi

echo "Using $BLENDER."
#"$BLENDER" --background --python render_keys.py -- "example/example$1.txt" --output_folder "example/output$1/" --bg white --width 512 --height 448
"$BLENDER" --background --python render_keys.py -- "veri3d/render_color.txt" 1>/dev/null  --output_folder "veri3d/output/" --bg white --width 1024 --height 1024
echo $done
#cd "veri3d/output/"
#ffmpeg -y -r 10 -i %05d.png -c:v libx264 -vf fps=30 -pix_fmt yuv420p output.mp4
