#!/bin/bash
if [ -z "$1" ]
  then
    echo "No example selected, this script expects a number corresponding to the example to render. See example/ for available examples."
fi

if [ -z "$BLENDER" ]; then
    #export BLENDER="/home/yliao/Downloads/blender-2.79b-linux-glibc219-x86_64/blender"
    export BLENDER="blender"
    echo $BLENDER
fi

echo "Using $BLENDER."
rm -rf "example/output$1/*.png"
rm -f "example/output$1/output.mp4"
#"$BLENDER" --background --python render_keys.py -- "example/example$1.txt" --output_folder "example/output$1/" --bg white --width 512 --height 448
"$BLENDER" --python render_keys.py -- "example/example$1.txt" 1>/dev/null  --output_folder "example/output$1/" --bg white --width 512 --height 512
cd "example/output$1/"
ffmpeg -y -r 10 -i %05d.png -c:v libx264 -vf fps=30 -pix_fmt yuv420p output.mp4
