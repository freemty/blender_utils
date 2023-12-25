import os
import yaml
import glob
#from ply2obj import convert
import trimesh
import numpy as np
import sys

tmp_dir='./tmp'
os.makedirs(tmp_dir, exist_ok=True)

def convert(ply_file, obj_file, cut=-1, cut_axis=0):
    mesh=trimesh.load(ply_file) 
    if cut>0: 
        mask=mesh.vertices[:,cut_axis]>cut
        # all vertices of the face fall into the cut-off region
        face_mask = mask[mesh.faces].sum(1)==3
        mesh.faces = mesh.faces[np.logical_not(face_mask)]

    mesh.export(obj_file)

# create off file for point cloud
def create_pointcloud_off(ply_file, off_file, radius=0.008, max_npoints=20000):

    if ply_file.endswith('.xyz'):
        pointcloud = np.loadtxt(ply_file)
    else:
        pointcloud = trimesh.load(ply_file).vertices
    scale = np.abs(pointcloud-pointcloud.mean(0)).max()
    sphere = trimesh.creation.icosphere(2, radius=radius*scale)
    s_nvertices = sphere.vertices.shape[0]
    print(pointcloud.shape)
    if pointcloud.shape[0]>max_npoints:
        pointcloud=pointcloud[np.random.permutation(pointcloud.shape[0])[:max_npoints]]
    print(pointcloud.shape)

    vertices = (pointcloud.reshape(-1, 1, 3) + sphere.vertices)
    vertices = vertices.reshape(-1, 3)
    print(np.mean(vertices, 0))
    face_offset = (
        s_nvertices * np.arange(pointcloud.shape[0], dtype=np.int32)
    )
    faces = (face_offset.reshape(-1, 1, 1) + sphere.faces)
    faces = faces.reshape(-1, 3)
    mesh = trimesh.Trimesh(vertices, faces, process=False)
    mesh.export(off_file)

def write_render_key(filename, object_name, idx, config, quick=False, pcl=False):
    with open(filename, 'w') as f:
        f.write('set_fps %d\n' % config['render']['number_frame'][idx])
        if quick:
            f.write('quick_render\n')
        else:
            f.write('high_quality_render\n')
        #if pcl:
        #    #f.write('set_color 0.6 0.6 1.0 1\n')
        #    f.write('set_color 0.7 0.7 1.0 1\n')
        #else:
        f.write('set_color 0.5 0.5 0.5 1\n')
        render_format = config['render']['format'] #if not pcl else 'off'
        f.write('load %s %s %f %f %f %f %s %f %f %f\n' % (render_format,
                                                 object_name, 
                                                 config['render']['offset_x'][idx],
                                                 config['render']['offset_y'][idx],
                                                 config['render']['offset_z'][idx],
                                                 config['render']['scale'][idx],
                                                 config['render']['axis'],
                                                 config['render']['rotate_x'][idx],
                                                 config['render']['rotate_y'][idx],
                                                 config['render']['rotate_z'][idx]))
        f.write('render 1 0 0 360 1\n')
        #f.write('clear\n')

# for each method, find the objects and write a render file for each object
def render_single_method(key, path_pattern, dataset_name, config, output_dir, output_image_dir, quick=False, pcl=False, radius=0.008, cut=-1, cut_axis=0):
    object_names = sorted(glob.glob(path_pattern))
    if len(object_names)!=config['number_obj']:
        print('Warning: %d objects found for %s, expecting %d!'% (len(object_names), key, config['number_obj']))
        return
    for i, object_name in enumerate(object_names):
        #if i==0 or i==1:
        #    continue
        #if i!=3:
        #    continue
        if i!=1:
            continue
        suffix=os.path.splitext(object_name)[-1]
        if (suffix=='.ply' or suffix=='.stl' or suffix=='.obj') and not pcl:
            #if not os.path.isfile(object_name.replace('.ply', '.obj')):
            convert(object_name, object_name.replace(suffix, '.off'))
            object_name = object_name.replace(suffix, '.off')
        elif suffix=='.xyz' or pcl:
            create_pointcloud_off(object_name, os.path.join(tmp_dir, os.path.basename(object_name).replace(suffix,'.off')), radius=radius)
            object_name = os.path.join(tmp_dir, os.path.basename(object_name).replace(suffix,'.off'))
            pcl=True
 
        if cut<0:
            render_file = os.path.join(output_dir, '%s_%04d.txt'%(key, i))
            write_render_key(render_file, object_name, i, config, quick=quick, pcl=pcl)
            print('Written %s' % render_file)
 
            cmd = './render_single_frame.sh %s %s/%s_%04d' % (render_file, output_image_dir, key, i)
            print(cmd)
            os.system(cmd)
        else:
            #for cut in range(30,120,10):
            for cut in [65]:
                convert(object_name, object_name.replace(suffix, '_%d.off'%cut), cut, cut_axis)
                object_name = object_name.replace(suffix, '_%d.off'%cut)
                render_file = os.path.join(output_dir, '%s_%03d_%04d.txt'%(key, cut, i))
                write_render_key(render_file, object_name, i, config, quick=quick, pcl=pcl)
                print('Written %s' % render_file)
 
                cmd = './render_single_frame.sh %s %s/%s_%03d_%04d' % (render_file, output_image_dir, key, cut, i)
                print(cmd)
                os.system(cmd)

if __name__=='__main__':

    quick=False
    if len(sys.argv)>1:
        quick=True

    config_path='./results_voxgraf.yaml'
    radius=0.008

    with open(config_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.Loader)

    cut_axis=1
    cut = -1 #if dataset!='teaser_left' else 1
    for dataset, dataset_config in config.items():
        #if dataset!='multires':
        #    continue
        if not 'three' in dataset:
            continue
    
        if quick:
            output_image_dir='output/%s/render_images_64x64' % dataset
        else:
            output_image_dir='output/%s/render_images_512x512' % dataset
        output_dir='output/%s/render_files' % dataset
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(output_image_dir, exist_ok=True)

        if 'input' in dataset_config.keys():
            render_single_method('input', dataset_config['input'], dataset, dataset_config, output_dir, output_image_dir, quick, radius=radius, cut=cut, cut_axis=cut_axis)
