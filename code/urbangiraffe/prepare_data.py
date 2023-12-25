import numpy as np
import pickle
from labels import labels, id2label
import trimesh

#############################################
### instance 
with open('0000320_ins.pkl','rb') as f:
    data = pickle.load(f)

verts = np.zeros((8, 3), dtype=float)                                         
size = np.ones(3,)
verts[0, :] = (- size[0] / 2, - size[1] / 2, - size[2] / 2) # left lower front   
verts[1, :] = (+ size[0] / 2, - size[1] / 2, - size[2] / 2) # right lower front  
verts[2, :] = (- size[0] / 2, + size[1] / 2, - size[2] / 2) # left upper front   
verts[3, :] = (+ size[0] / 2, - size[1] / 2, + size[2] / 2) # right lower back   
verts[4, :] = (+ size[0] / 2, + size[1] / 2, - size[2] / 2) # right upper front  
verts[5, :] = (+ size[0] / 2, + size[1] / 2, + size[2] / 2) # right upper back   
verts[6, :] = (- size[0] / 2, + size[1] / 2, + size[2] / 2) # left upper back    
verts[7, :] = (- size[0] / 2, - size[1] / 2, + size[2] / 2) # left lower back    

faces = np.array([
    (0, 1, 2),
    (1, 2, 4),
    (3, 5, 6),
    (3, 6, 7),
    (0, 1, 7),
    (1, 3, 7),
    (2, 4, 6),
    (4, 5, 6),
    (0, 2, 7),
    (2, 6, 7),
    (1, 3, 4),
    (3, 4, 5),
])


classes = [11,26]
for cls in classes:
    cnt = 0
    verts_all = []
    faces_all = []
    for bbox in data:
        if bbox[2]!=cls:
            continue
        verts_i = (bbox[3][:3,:3] @ verts.T).T + bbox[3][:3,3]
        verts_i[:,1] = -verts_i[:,1]
        faces_i = faces + cnt*8
        verts_all.append(verts_i)
        faces_all.append(faces_i)
        cnt += 1
    mesh = trimesh.Trimesh(vertices=np.concatenate(verts_all), faces=np.concatenate(faces_all))
    
    mesh.export('instance_%02d.off' % cls)

with open('render_ins.txt', 'w') as f:
    f.write('set_fps 30\n')
    f.write('render    0   0   0   0   1\n')
    for cls in classes:
        color = np.array(id2label[cls].color)/255.
        f.write(f'set_color {color[0]} {color[1]} {color[2]} 1.0 \n')
        f.write(f'load off urbangiraffe/instance_{cls:02d}.off 0.0 0.0 -0.5 0.035 xzy\n')
    f.write('render    1   0   0   360   1\n')
    f.write('clear\n')


exit()

#############################################
### stuff
with open('0000000320.pkl','rb') as f:
    data = pickle.load(f)

dim = 64
data = data.reshape(dim,dim,dim)
data = np.concatenate((data[0:48:4], data[48:]))
x,y,z = np.where(data>0)
ids = data[x,y,z]

x = dim - x

x = x/float(dim) - 0.5
y = y/float(dim) - 0.5
z = z/float(dim) - 0.5
size = np.ones_like(x)*(1/float(dim)*0.9)

xyz = np.vstack((x,y,z,size))
xyz = xyz.T
quick = False
with open('render_color.txt', 'w') as f:
    f.write('set_fps 30 \n')
    if not quick:
        f.write('high_quality_render\n')
    f.write('render    0   0   0   0   1 \n')

    for idx in np.unique(ids):
        mask = ids==idx
        color = np.array(id2label[idx].color)/255.
        np.savetxt('0000000320_%02d.txt' % idx, xyz[mask])

        f.write(f'set_color {color[0]} {color[1]} {color[2]} 1.0 \n')
        idx = int(idx)
        f.write(f'load efficient_txt_voxel_list urbangiraffe/0000000320_{idx:02d}.txt cubes 0.0 0.0 -1.0 2.0 zxy\n')

    f.write('render    1   0   0   360   1\n')

#xyz *= 5

#np.savetxt('0000000320.txt', xyz.T)
