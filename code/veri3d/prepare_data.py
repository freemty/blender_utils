import numpy as np
import os
from matplotlib import cm
cmap = cm.get_cmap('Pastel2')
import glob


if False:
    for vertex_file in os.listdir('./'):
        if vertex_file.endswith('.npy'):
            vertex_name = vertex_file.split('.')[0]
            vertices = np.load(vertex_name + '.npy')
            vertices -= np.mean(vertices, axis=0)
            vertices[:,[0,1,2]] = vertices[:,[0,2,1]]
            if vertex_name=='vertices_obv_space':
                vertices[:,2] = -vertices[:,2]
            vertices = np.concatenate((vertices, np.ones((vertices.shape[0],1))*0.005), 1)
            np.savetxt(vertex_name + '.txt', vertices)

if False:
    npy_files = glob.glob('teaser/vertices*.npy')
    quick = False 
    #for vid in range(10):

    for vid, vertice_file in enumerate(npy_files):
        with open('render_color.txt', 'w') as f:
            f.write('set_fps 1 \n')
            if not quick:
                f.write('high_quality_render\n')
            else:
                f.write('quick_render\n')
            #vertice_file = 'diff_shape86/vertices_%d.npy' % vid 
            vertices = np.load(vertice_file)[0]
            #vertices[:,[0,1,2]] = vertices[:,[0,2,1]]
            vertices[:,2]=-vertices[:,2]
            vertices[:,1]=-vertices[:,1]
            vertices[:,0]=-vertices[:,0]
            vertices = np.concatenate((vertices, np.ones((vertices.shape[0],1))*0.007), 1)
            txt_name = vertice_file.replace('.npy', '.txt')
            np.savetxt(txt_name, vertices)
            
            f.write(f'set_color {248/255.} {184/255.} {168/255.} 1.0 \n')
            f.write(f'load txt_voxel_list veri3d/{txt_name} spheres 0. 0. -0.25 1. xzy\n')
            
            f.write('render    1   0   0   360   1\n')
        os.chdir('/home/yliao/projects/blendviz/code/')
        os.system('./veri3d/run.sh %s' % vertice_file.split('/')[-1].replace('.npy',''))
        os.chdir('/home/yliao/projects/blendviz/code/veri3d')

### Teaser
if False:
    quick = False
    name='232'
    vertices = np.load('%s/vertices.npy' % name)[0]
    parts = np.load('data/vertices_part.npy')
    #vertices[:,[0,1,2]] = vertices[:,[0,2,1]]
    vertices[:,2]=-vertices[:,2]
    vertices[:,1]=-vertices[:,1]
    vertices[:,0]=-vertices[:,0]
    vertices = np.concatenate((vertices, np.ones((vertices.shape[0],1))*0.007), 1)
    
    fine2coarse_part = {0:0,3:0,6:0,9:0,13:0,14:0,12:0,
                        16:1,17:1,18:1,19:1,20:1,21:1,22:1,23:1,
                        15:2,
                        1:3,2:3,4:3,5:3,7:3,8:3,11:3,10:3}
    # colors = {0: (172, 11, 136),
    #           2: (254, 190, 140),
    #           1: (125, 110, 131),
    #           3: (120, 149, 178)}
    
    colors = {2: (245*0.9, 237*0.9, 220*0.9), # head 
              1: (130, 159, 188), # arm
              0: (244, 199, 171), # upper body
              3: (128, 110, 131)} # leg
    parts_new = np.zeros_like(parts)
    for i in np.unique(parts):
        parts_new[parts==i] = fine2coarse_part[i]
        
    
    with open('render_color.txt', 'w') as f:
        f.write('set_fps 30 \n')
        if not quick:
            f.write('high_quality_render\n')
        else:
            f.write('quick_render\n')
        f.write('render    0   0   0   0   1 \n')
    
        for idx in np.unique(parts_new):
            mask = parts_new==idx
            txt_name = '%s/vertices_part%02d.txt' % (name,idx)
            np.savetxt(txt_name, vertices[mask])
    
            #f.write(f'set_color {cmap(idx)[0]} {cmap(idx)[1]} {cmap(idx)[2]} 1.0 \n')
            f.write(f'set_color {colors[idx][0]/255.} {colors[idx][1]/255.} {colors[idx][2]/255.} 1.0 \n')
            idx = int(idx)
            f.write(f'load txt_voxel_list veri3d/{txt_name} spheres 0. 0. -0.25 1. xzy\n')
    
        f.write('render    1   0   0   360   1\n')


if True:
    quick = False
    name='232'
    vertices = np.load('teaser/vertices_teaser.npy')[0]
    parts = np.load('data/vertices_part.npy')
    #vertices[:,[0,1,2]] = vertices[:,[0,2,1]]
    vertices[:,2]=-vertices[:,2]
    vertices[:,1]=-vertices[:,1]
    vertices[:,0]=-vertices[:,0]
    vertices = np.concatenate((vertices, np.ones((vertices.shape[0],1))*0.007), 1)
    fine2coarse_part = {0:0,3:0,6:0,9:0,13:0,14:0,12:0,
                            16:0,17:0,18:0,19:0,20:0,21:0,22:0,23:0,
                            # 16:1,17:1,18:1,19:1,20:1,21:1,22:1,23:1,
                            15:2,
                            1:3,2:3,4:3,5:3,7:3,8:3,11:3,10:3}
    colors = {2: (245*0.9, 237*0.9, 220*0.9), # head 
              1: (130, 159, 188), # arm
              0: (244, 199, 171), # upper body
              3: (128, 110, 131)} # leg
    
    basecolor = (248, 184, 168)
    parts_new = np.zeros_like(parts)
    for i in np.unique(parts):
        parts_new[parts==i] = fine2coarse_part[i]
        
    
    with open('render_color.txt', 'w') as f:
        f.write('set_fps 2 \n')
        if not quick:
            f.write('high_quality_render\n')
        else:
            f.write('quick_render\n')
    
        for idx in np.unique(parts_new):
            mask = parts_new==idx
            txt_name = 'teaser/vertices_part%02d.txt' % (idx)
            np.savetxt(txt_name, vertices[mask])
    
            #f.write(f'set_color {cmap(idx)[0]} {cmap(idx)[1]} {cmap(idx)[2]} 1.0 \n')
            #if idx==3:
            if True:
                #f.write(f'set_color {colors[idx][0]/255.*0.8} {colors[idx][1]/255.*0.8} {colors[idx][2]/255.*0.8} 1.0 \n')
                f.write(f'set_color {cmap(idx+5)[0]} {cmap(idx+5)[1]} {cmap(idx+5)[2]} 1.0 \n')
            else:
                f.write(f'set_color {248/255.} {184/255.} {168/255.} 1.0 \n')
            idx = int(idx)
            f.write(f'load txt_voxel_list veri3d/{txt_name} spheres 0. 0. -0.25 1. xzy\n')
    
        f.write('render    1   0   0   360   1\n')



