from brc_importers.ImportDelegator import Importer
import numpy as np
import blender_utils
from itertools import product
from render_logging import log, LogLevel


class NpyImporter(Importer):

    @staticmethod
    def name():
        return "npy"

    @staticmethod
    def preprocess_grid(grid):
        grid = np.squeeze(grid)
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
                x_tf = lambda x: grid.shape[0] - x
                y_tf = lambda y: y
                z_tf = lambda z: grid.shape[2] - z
            if arguments[2] == "YIYI":
                upscale = 1.1
                scale = [upscale*0.5,upscale*0.5,upscale*0.5,]

                x_tf = lambda x: x*upscale + grid.shape[0]*0.6
                y_tf = lambda y: y*upscale
                z_tf = lambda z: z*upscale
            else:
                try:
                    scale_value = float(arguments[2])
                    scale = [0.5*scale_value,0.5*scale_value,0.5*scale_value]
                except ValueError:
                    pass
        print("Loading voxel grid from '%s' as %s" % (filename, meshtype))

        grid = np.load(filename)
        grid = self.preprocess_grid(grid)

        if meshtype in ("cubes", "spheres"):
            nrcubes = np.sum(grid <= 0)
            locations = np.zeros((nrcubes,3))
            radii = np.concatenate((
                        np.ones((nrcubes, 3))*scale[0] / grid.shape[0],
                        np.ones((nrcubes, 3))*scale[1] / grid.shape[1],
                        np.ones((nrcubes, 3))*scale[2] / grid.shape[2],
                    ),axis=1)

            cube_count = 0
            location_list = [((x_tf(ix)+0.5) / grid.shape[0] - 0.5, (y_tf(iy)+0.5) / grid.shape[1] - 0.5, (z_tf(iz)+0.5) / grid.shape[2] - 0.5) for ix,iy,iz in product(range(0, grid.shape[0]), range(0, grid.shape[1]),range(0, grid.shape[2])) if grid[ix, iy, iz] <= 0]
            locations = np.asarray(location_list)
            base_mesh = blender_utils.get_cube_mesh() if meshtype == "cubes" \
                    else blender_utils.get_sphere_mesh() if meshtype == "spheres"\
                    else blender_utils.get_detailed_sphere_mesh()

            if len(arguments) > 2 and arguments[2] == "YIYI":
                log("YIYI-based coordinate system")
                t = locations[:,1].copy()
                locations[:,1] = locations[:,2].copy()
                locations[:,2] = t

            blender_utils.add_primitive_objects(base_mesh, locations, radii)
        elif meshtype == "marching_cubes":
            try:
                from skimage import measure
            except ImportError as ex:
                log("Failed to perform marching cubes because 'skimage' is missing.", LogLevel.WARNING)
                return

            if np.max(grid) <= 0.0 or np.min(grid) >= 0.0:
                log("Loaded grid does not contain any surface voxels", LogLevel.WARNING)
                log("Data is between %f and %f" % (np.min(grid),np.max(grid)), LogLevel.WARNING)
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
            blender_utils.add_object_from_mesh(verts, faces, [scale[0]/grid.shape[0],scale[1]/grid.shape[1],scale[2]/grid.shape[2]],
                                               [scale[0]*(0.5/grid.shape[0] - 0.5),scale[1]*(0.5/grid.shape[1] - 0.5),scale[2]*(0.5/grid.shape[2] - 0.5)])

NpyImporter()
