#!/bin/bash

export BLENDER="blender"
echo $BLENDER

echo "Using $BLENDER."
key_file=$1
output_file=$2
echo $key_file
echo $output_file
#"$BLENDER" --background --python render_keys.py -- "example/example$1.txt" --output_folder "example/output$1/" --bg white --width 512 --height 448
"$BLENDER" --background --python render_keys.py -- "$key_file" 1>/dev/null --output_folder "$output_file" --bg white --width 512 --height 512
