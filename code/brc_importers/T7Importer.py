from brc_importers.ImportDelegator import Importer
import blender_utils
from itertools import product
import torchfile
from render_logging import log,LogLevel
import numpy as np


class T7Importer(Importer):

    @staticmethod
    def name():
        return "t7"

    @staticmethod
    def preprocess_grid(grid):
        grid = np.squeeze(grid)
        if grid.ndim == 4:
            # first channel is the TSDF, other three are the normal estimate
            grid = grid[0,:,:,:]
        return grid

    def load(self, arguments):
        x_tf = lambda x: x
        y_tf = lambda y: y
        z_tf = lambda z: z
        filename = arguments[0]
        meshtype = arguments[1]
        scale = [0.5, 0.5, 0.5]
        if len(arguments) == 5:
            scale = [float(i) for i in arguments[2:5]]
        elif len(arguments) == 3:
            if arguments[2] == "DTU":
                print("Rendering DTU coordinate system")
                #some DTU-specific settings: invert the Y scale
                x_tf = lambda x: grid.shape[1] - x
                y_tf = lambda y: y
                z_tf = lambda z: grid.shape[2] - z
            else:
                scale_value = float(arguments[2])
                scale = [0.5*scale_val,0.5*scale_val,0.5*scale_val]
                
        print("Loading voxel grid from '%s' as %s" % (filename, meshtype))

        grid = torchfile.load(filename)
        grid = self.preprocess_grid(grid)

        if meshtype in ("cubes", "spheres"):
            base_mesh = blender_utils.get_cube_mesh() if meshtype == "cubes" else blender_utils.get_sphere_mesh()
            cube_count = np.sum(grid <= 0)
            locations = np.zeros((cube_count,3))
            radii = np.zeros((cube_count,3))
            cube_idx = 0
            for ix, iy, iz in product(range(0, grid.shape[0]), range(0, grid.shape[1]),
                                      range(0, grid.shape[2])):
                if grid[ix, iy, iz] <= 0:
                    locations[cube_idx,0] = (x_tf(ix)+0.5) / grid.shape[0] - 0.5
                    locations[cube_idx,1] = (y_tf(iy)+0.5) / grid.shape[1] - 0.5
                    locations[cube_idx,2] = (z_tf(iz)+0.5) / grid.shape[2] - 0.5
                    radii[cube_idx,0] = scale[0] / grid.shape[0]
                    radii[cube_idx,1] = scale[1] / grid.shape[1]
                    radii[cube_idx,2] = scale[2] / grid.shape[2]
                    cube_idx += 1
            blender_utils.add_primitive_objects(base_mesh,locations,radii)
        elif meshtype == "marching_cubes":
            try:
                from skimage import measure
            except ImportError as ex:
                log("Failed to perform marching cubes because 'skimage' is missing.", LogLevel.WARNING)
                return
            if np.max(grid) <= 0.0 or np.min(grid) >= 0.0:
                log("Loaded grid does not contain any surface voxels", LogLevel.WARNING)
                log("Values are in the range %f -> %f" % (np.min(grid),np.max(grid)))
                return
            # we append empty-space everywhere, to close off open surfaces near the border
            DX = grid.shape[0]
            DY = grid.shape[1]
            DZ = grid.shape[2]
            lgrid = np.concatenate((np.ones((1,DY,DZ)), grid,np.ones((1,DY,DZ))),axis=0)
            lgrid = np.concatenate((np.ones((DX+2,1,DZ)),lgrid,np.ones((DX+2,1,DZ))),axis=1)
            lgrid = np.concatenate((np.ones((DX+2,DY+2,1)),lgrid,np.ones((DX+2,DY+2,1))),axis=2)
            verts, faces, _, _ = measure.marching_cubes_lewiner(lgrid, 0.0)
            verts[:,0] = (verts[:,0]-1)
            verts[:,1] = (verts[:,1]-1)
            verts[:,2] = (verts[:,2]-1)
            verts = tuple([tuple([x_tf(float(row[0])), y_tf(float(row[1])), z_tf(float(row[2]))]) for row in verts])
            faces = tuple([tuple([int(row[0]), int(row[1]), int(row[2])]) for row in faces])
            blender_utils.add_object_from_mesh(verts, faces, [1/grid.shape[0],1/grid.shape[1],1/grid.shape[2]], [0.5/grid.shape[0] - 0.5,0.5/grid.shape[1] - 0.5,0.5/grid.shape[2] - 0.5])

T7Importer()
