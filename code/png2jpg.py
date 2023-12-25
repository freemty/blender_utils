import os
import glob
from PIL import Image
import numpy as np

input_dir='output/*/render_images_512x512'
#input_dir='/is/rg/avg/yliao/shape_as_points/blender_renderings/Shapenet_suppmat/render_images_512x512'
png_files=glob.glob(input_dir+'/*.png')
for png_file in png_files:
    #img = opencv.imread(png_file)
    #opencv.imwrite(png_file.replace('.png', '.jpg'), img)
    im = Image.open(png_file)
    # RGBA -> RGB
    img_np = np.array(im)
    r, g, b, a = np.rollaxis(img_np, axis = -1)
    x = np.dstack([r, g, b])
    im = Image.fromarray(x, 'RGB')
    im.save(png_file.replace('.png', '.jpg'))
