from brc_importers.ImportDelegator import Importer
import numpy as np
import blender_utils
from itertools import product
from render_logging import log, LogLevel


class Octree:
    n = 0
    grid_depth = 0
    grid_height = 0
    grid_width = 0
    feature_size = 0
    n_leafs = 0

    trees = None
    data = None
    prefix_leafs = None

    def n_blocks(self):
        return self.n * self.grid_depth * self.grid_height * self.grid_width

    def isset_bit(self,tree_idx,bit_idx):
        return Octree.isset_bit_s(self.trees[4*tree_idx:4*tree_idx+4],bit_idx)

    @staticmethod
    def isset_bit_s(ints,bit_idx):
        return (ints[bit_idx//32] & (0x1 << (bit_idx % 32)) ) != 0

    @staticmethod
    def child_bit_idx(bit_idx):
        return 8*bit_idx + 1

    @staticmethod
    def parent_bit_idx(bit_idx):
        return (bit_idx - 1) // 8

    def count0(self,tree_idx,start,stop):
        # silly slow implementation because I don't want to implement low-level bit stuff
        count = 0
        for bit in range(start,stop):
            count = count + (1-self.isset_bit(tree_idx,bit))
        return count

    def data_idx(self,tree_idx,bit_idx):
        if bit_idx == 0:
            return self.prefix_leafs[tree_idx]
        data_idx = self.count0(tree_idx,0,min(bit_idx,73))
        if Octree.parent_bit_idx(bit_idx) > 1:
            data_idx = data_idx - 8*self.count0(tree_idx,1,Octree.parent_bit_idx(bit_idx))
        if bit_idx > 72:
            data_idx = data_idx + bit_idx - 73

        return self.prefix_leafs[tree_idx] + data_idx * self.feature_size

    @staticmethod
    def meanpool_dense_grid(dense_grid):
        output_grid = dense_grid[0::2, 0::2, 0::2] + dense_grid[0::2, 0::2, 1::2] + \
                      dense_grid[0::2, 1::2, 0::2] + dense_grid[0::2, 1::2, 1::2] + \
                      dense_grid[1::2, 0::2, 0::2] + dense_grid[1::2, 0::2, 1::2] + \
                      dense_grid[1::2, 1::2, 0::2] + dense_grid[1::2, 1::2, 1::2]
        return output_grid / 8

    @staticmethod
    def set_bit(tree_ints,bit_idx):
        tree_ints[bit_idx // 32] = tree_ints[bit_idx//32] | (0x1 << (bit_idx % 32))

    @staticmethod
    def create_subtree_from_dense(dense_grid_8):
        assert dense_grid_8.shape[1] == 8 and dense_grid_8.shape[2] == 8 and dense_grid_8.shape[3] == 8,\
            "this function should only be used on 1x8x8x8 dense grids"
        subtree_ints = np.zeros(4,dtype=np.int32)
        subtree_data = np.zeros(8*8*8)

        dense_grid_8 = dense_grid_8[0,:,:,:]
        dense_grid_4 = Octree.meanpool_dense_grid(dense_grid_8)
        dense_grid_2 = Octree.meanpool_dense_grid(dense_grid_4)
        dense_grid_1 = Octree.meanpool_dense_grid(dense_grid_2)

        data_index = 0
        data_index_L1 = data_index + np.sum(np.mod(dense_grid_2,1) == 0)
        data_index_L2 = data_index_L1 + np.sum(np.mod(dense_grid_4,1) == 0) - np.sum(np.mod(dense_grid_2,1) == 0)*8

        if dense_grid_1[0,0,0] % 1 == 0:
            subtree_data[data_index] = dense_grid_1[0,0,0]
            # log("root not split (value %f @ %d)" % (subtree_data[data_index],data_index))
            data_index = data_index + 1
        else:
            Octree.set_bit(subtree_ints,0)
            bit_idx_L1 = 1
            for od1,oh1,ow1 in product(range(0,2),range(0,2),range(0,2)):
                if dense_grid_2[od1,oh1,ow1] % 1 == 0:
                    subtree_data[data_index] = dense_grid_2[od1,oh1,ow1]
                    # log("(%d,%d,%d) -> not split (value %f @ %d)" % (od1,oh1,ow1,subtree_data[data_index],data_index))
                    data_index = data_index + 1
                else:
                    Octree.set_bit(subtree_ints,bit_idx_L1)
                    bit_idx_L2 = Octree.child_bit_idx(bit_idx_L1)
                    for od2, oh2, ow2 in product(range(0, 2), range(0, 2), range(0, 2)):
                        if dense_grid_4[2*od1+od2,2*oh1+oh2,2*ow1+ow2] % 1 == 0:
                            subtree_data[data_index_L1] = dense_grid_4[2*od1+od2,2*oh1+oh2,2*ow1+ow2]
                            # log("(%d,%d,%d).(%d,%d,%d) -> not split (value %f @ %d)" % (od1, oh1, ow1, od2, oh2, ow2, subtree_data[data_index_L1],data_index_L1))
                            data_index_L1 = data_index_L1 + 1
                        else:
                            Octree.set_bit(subtree_ints,bit_idx_L2)
                            for od3, oh3, ow3 in product(range(0, 2), range(0, 2), range(0, 2)):
                                subtree_data[data_index_L2] = dense_grid_8[
                                                                        4 * od1 + 2 * od2 + od3,
                                                                        4 * oh1 + 2 * oh2 + oh3,
                                                                        4 * ow1 + 2 * ow2 + ow3
                                                                        ]
                                # log("(%d,%d,%d).(%d,%d,%d).(%d,%d,%d) -> leaf (value %f @ %d)" % (od1, oh1, ow1, od2, oh2, ow2, od3, oh3, ow3, subtree_data[data_index_L2],data_index_L2))
                                data_index_L2 = data_index_L2 + 1
                        bit_idx_L2 = bit_idx_L2 + 1
                bit_idx_L1 = bit_idx_L1 + 1

        return subtree_ints, subtree_data[:data_index_L2]

    @staticmethod
    def create_from_dense(dense_grid):
        assert dense_grid.ndim == 4, "expected a 1xDxHxW dense grid as input"
        assert dense_grid.shape[0] == 1, "create_from_dense only supported for occupancy grids for now!"
        assert (dense_grid.shape[1] % 8 == 0) and (dense_grid.shape[2] % 8 == 0) and (dense_grid.shape[3] % 8 == 0),\
            "the dense grid shape should be a multiple of (8,8,8)"
        tree_grid = Octree()
        tree_grid.n = 1
        tree_grid.grid_depth = dense_grid.shape[1] // 8
        tree_grid.grid_height = dense_grid.shape[2] // 8
        tree_grid.grid_width = dense_grid.shape[3] // 8
        tree_grid.feature_size = dense_grid.shape[0]

        n_blocks = tree_grid.n_blocks()

        tree_grid.trees = np.zeros(4*n_blocks,dtype=np.int32)
        tree_grid.prefix_leafs = np.zeros(n_blocks,dtype=np.int32)
        tree_grid.data = np.zeros(0)

        block_idx = 0
        for n,d,h,w in product(range(0,tree_grid.n),range(0,tree_grid.grid_depth),
                               range(0,tree_grid.grid_height),range(0,tree_grid.grid_width)):
            dense_subgrid = dense_grid[0:1,d*8:d*8+8,h*8:h*8+8,w*8:w*8+8]
            subtree_ints, subtree_data = Octree.create_subtree_from_dense(dense_subgrid)
            subtree_n_leafs = len(subtree_data)

            tree_grid.trees[4*block_idx:4*block_idx + 4] = subtree_ints
            if block_idx < n_blocks - 1:
                tree_grid.prefix_leafs[block_idx + 1] = tree_grid.prefix_leafs[block_idx] + subtree_n_leafs

            # and just append to the data array now
            tree_grid.data = np.concatenate((tree_grid.data,subtree_data))

            block_idx = block_idx + 1
        tree_grid.n_leafs = len(tree_grid.data)
        return tree_grid

    @staticmethod
    def fill_dense_from_subtree(dense_grid, grid_offset,tree_ints,leaf_data):

        def fill_grid(grid,corner,size,value):
            for x,y,z in product(range(0,size),range(0,size),range(0,size)):
                grid[corner[0]+x,corner[1]+y,corner[2]+z] = value

        def d_count0(start, stop):
            count = 0
            for bit in range(start, stop):
                count = count + (1 - Octree.isset_bit_s(tree_ints, bit))
            return count

        def d_data_idx(bit_idx):
            if bit_idx == 0:
                return 0
            data_idx = d_count0(0,min(bit_idx,73))
            if Octree.parent_bit_idx(bit_idx) > 1:
                data_idx = data_idx - 8*d_count0(1,Octree.parent_bit_idx(bit_idx))
            if bit_idx > 72:
                data_idx = data_idx + bit_idx - 73
            return data_idx

        bit_idx_L0 = 0
        L0_size = 8
        L0_corner = np.asarray([0,0,0])

        L1_size = 4
        L2_size = 2
        L3_size = 1

        if Octree.isset_bit_s(tree_ints,bit_idx_L0):
            bit_idx_L1 = 1
            for od1, oh1, ow1 in product(range(0, 2), range(0, 2), range(0, 2)):
                L1_corner = L0_corner + np.asarray([od1, oh1, ow1]) * L1_size
                if Octree.isset_bit_s(tree_ints, bit_idx_L1):
                    bit_idx_L2 = Octree.child_bit_idx(bit_idx_L1)
                    for od2, oh2, ow2 in product(range(0, 2), range(0, 2), range(0, 2)):
                        L2_corner = L1_corner + np.asarray([od2, oh2, ow2]) * L2_size
                        if Octree.isset_bit_s(tree_ints, bit_idx_L2):
                            bit_idx_L3 = Octree.child_bit_idx(bit_idx_L2)
                            for od3, oh3, ow3 in product(range(0, 2), range(0, 2), range(0, 2)):
                                L3_corner = L2_corner + np.asarray([od3, oh3, ow3]) * L3_size
                                fill_grid(dense_grid, grid_offset + L3_corner, L3_size, leaf_data[d_data_idx(bit_idx_L3)])
                                bit_idx_L3 = bit_idx_L3 + 1
                        else:
                            fill_grid(dense_grid, grid_offset + L2_corner, L2_size, leaf_data[d_data_idx(bit_idx_L2)])
                        bit_idx_L2 = bit_idx_L2 + 1
                else:
                    fill_grid(dense_grid, grid_offset + L1_corner, L1_size, leaf_data[d_data_idx(bit_idx_L1)])
                bit_idx_L1 = bit_idx_L1 + 1
        else:
            fill_grid(dense_grid,grid_offset + L0_corner,L0_size,leaf_data[d_data_idx(bit_idx_L0)])

    def create_dense_from_tree(self):
        assert self.n == 1, "Only batch size one supported!"
        assert self.feature_size == 1, "Only single-field trees are supported here!"
        output_size = [self.grid_depth*8,self.grid_height*8,self.grid_width*8]
        dense_grid = np.zeros(output_size)
        block_idx = 0
        for d,h,w in product(range(0,self.grid_depth),range(0,self.grid_height),range(0,self.grid_width)):
            data0 = self.prefix_leafs[block_idx]
            data1 = (self.prefix_leafs[block_idx+1] if block_idx < self.n_blocks()-1 else self.n_leafs)
            Octree.fill_dense_from_subtree(dense_grid,[d*8,h*8,w*8],self.trees[4*block_idx:4*block_idx+4],
                                           self.data[data0:data1])
            block_idx = block_idx + 1

        return dense_grid



class OctreeImporter(Importer):

    @staticmethod
    def name():
        return "octree"

    @staticmethod
    def preprocess_grid(tree):
        return tree

    @staticmethod
    def load_octree(filename):
        with open(filename, "rb") as f:
            # hardcoded for a single octree binary format
            magic_number = np.fromfile(f, dtype=np.int32, count=1)[0]
            assert magic_number == 31193, "We only support one specific octree format, and it isn't this one!"

            tree_grid = Octree()

            tree_grid.n = np.fromfile(f, dtype=np.int32, count=1)[0]
            tree_grid.grid_depth = np.fromfile(f, dtype=np.int32, count=1)[0]
            tree_grid.grid_height = np.fromfile(f, dtype=np.int32, count=1)[0]
            tree_grid.grid_width = np.fromfile(f, dtype=np.int32, count=1)[0]
            tree_grid.feature_size = np.fromfile(f, dtype=np.int32, count=1)[0]
            tree_grid.n_leafs = np.fromfile(f, dtype=np.int32, count=1)[0]

            tree_grid.trees = np.fromfile(f, dtype=np.int32, count=4*tree_grid.n_blocks())
            tree_grid.data = np.fromfile(f, dtype=np.float32, count=tree_grid.n_leafs * tree_grid.feature_size)
            tree_grid.prefix_leafs = np.fromfile(f, dtype=np.int32, count=tree_grid.n_blocks())

            assert len(tree_grid.prefix_leafs) == tree_grid.n_blocks(), "The file did not contain all info!"
            assert not f.read(1), "The file contains too much info!"

            return tree_grid

    @staticmethod
    def crawl_tree_grid(tree_grid):
        centers = list()
        radii = list()
        data_locs = list()
        tree_idx = 0
        L0_radius = np.array([0.5 / tree_grid.grid_depth, 0.5 / tree_grid.grid_height, 0.5 / tree_grid.grid_width ])
        L1_radius = L0_radius / 2
        L2_radius = L1_radius / 2
        L3_radius = L2_radius / 2
        counts = [0,0,0,0]
        valsum = [0,0,0,0]
        for n,d,h,w in product(range(0,tree_grid.n),range(0,tree_grid.grid_depth),
                               range(0,tree_grid.grid_height),range(0,tree_grid.grid_width)):
            L0_center = np.array([(d+0.5)/tree_grid.grid_depth,(h+0.5)/tree_grid.grid_height,(w+0.5)/tree_grid.grid_width])
            if tree_grid.isset_bit(tree_idx,0):
                bit_idx_L1 = 1
                for od1,oh1,ow1 in product(range(0,2),range(0,2),range(0,2)):
                    L1_center = L0_center + np.multiply(np.sign([od1-0.5,oh1-0.5,ow1-0.5]),L1_radius)
                    if tree_grid.isset_bit(tree_idx,bit_idx_L1):
                        bit_idx_L2 = Octree.child_bit_idx(bit_idx_L1)
                        for od2, oh2, ow2 in product(range(0,2),range(0,2),range(0,2)):
                            L2_center = L1_center + np.multiply(np.sign([od2-0.5,oh2-0.5,ow2-0.5]),L2_radius)
                            if tree_grid.isset_bit(tree_idx,bit_idx_L2):
                                bit_idx_L3 = Octree.child_bit_idx(bit_idx_L2)
                                for od3, oh3, ow3 in product(range(0,2),range(0,2),range(0,2)):
                                    L3_center = L2_center + np.multiply(np.sign([od3-0.5,oh3-0.5,ow3-0.5]),L3_radius)
                                    centers.append(L3_center)
                                    radii.append(L3_radius)
                                    data_locs.append(tree_grid.data_idx(tree_idx,bit_idx_L3))
                                    # log("(%d,%d,%d,%d) - (%d,%d,%d) - (%d,%d,%d) - (%d,%d,%d): L3, data_loc %d from bitidx %d: %d" % (n, d, h, w, od1, oh1, ow1, od2, oh2, ow2, od3, oh3, ow3,tree_grid.data_idx(tree_idx, bit_idx_L3), bit_idx_L3,tree_grid.data[tree_grid.data_idx(tree_idx, bit_idx_L3)]))
                                    counts[3] += 1
                                    valsum[3] += tree_grid.data[tree_grid.data_idx(tree_idx, bit_idx_L3)]
                                    bit_idx_L3 = bit_idx_L3 + 1
                            else:
                                centers.append(L2_center)
                                radii.append(L2_radius)
                                data_locs.append(tree_grid.data_idx(tree_idx,bit_idx_L2))
                                # log("(%d,%d,%d,%d) - (%d,%d,%d) - (%d,%d,%d): L2 not split, data_loc %d from bitidx %d: %d" % (n,d,h,w,od1,oh1,ow1,od2,oh2,ow2,tree_grid.data_idx(tree_idx,bit_idx_L2),bit_idx_L2,tree_grid.data[tree_grid.data_idx(tree_idx, bit_idx_L2)]))
                                counts[2] += 1
                                valsum[2] += tree_grid.data[tree_grid.data_idx(tree_idx, bit_idx_L2)]
                            bit_idx_L2 = bit_idx_L2 + 1
                    else:
                        centers.append(L1_center)
                        radii.append(L1_radius)
                        data_locs.append(tree_grid.data_idx(tree_idx,bit_idx_L1))
                        # log("(%d,%d,%d,%d) - (%d,%d,%d): L1 not split, data_loc %d from bitidx %d: %d" % (n,d,h,w,od1,oh1,ow1,tree_grid.data_idx(tree_idx,bit_idx_L1),bit_idx_L1,tree_grid.data[tree_grid.data_idx(tree_idx, bit_idx_L1)]))
                        counts[1] += 1
                        valsum[1] += tree_grid.data[tree_grid.data_idx(tree_idx, bit_idx_L1)]
                    bit_idx_L1 = bit_idx_L1 + 1
            else:
                centers.append(L0_center)
                radii.append(L0_radius)
                data_locs.append(tree_grid.data_idx(tree_idx,0))
                # log("(%d,%d,%d,%d): L0 not split, data_loc %d from bitidx %d: %d" % (n,d,h,w,tree_grid.data_idx(tree_idx,0),0,tree_grid.data[tree_grid.data_idx(tree_idx, 0)]))
                counts[0] += 1
                valsum[0] += tree_grid.data[tree_grid.data_idx(tree_idx, 0)]

            tree_idx = tree_idx + 1
        # log("Node size counts: (%d,%d,%d,%d) of (%d,%d,%d,%d)" % (valsum[0],valsum[1],valsum[2],valsum[3],counts[0],counts[1],counts[2],counts[3]))
        # log("Total occupied voxels in the grid: %d" % (valsum[0]*512 + valsum[1]*64 + valsum[2]*8 + valsum[3]))

        return centers, radii, data_locs

    def load(self, arguments):
        filename = arguments[0]
        meshtype = arguments[1] if len(arguments) > 1 else "marching_cubes"

        x_tf = lambda x: x
        y_tf = lambda y: y
        z_tf = lambda z: z

        tree_grid = self.load_octree(filename)
        tree_grid = self.preprocess_grid(tree_grid)

        if len(arguments) > 2:
            if arguments[2] == "DTU":
                #some DTU-specific settings for nicer visualization
                x_tf = lambda x: x
                y_tf = lambda y: y
                z_tf = lambda z: tree_grid.grid_depth * 8 - z
            else:
                log("Argument '%s' not known, and ignored" % (arguments[2],))

        if meshtype == "cubes":
            add_voxel = blender_utils.add_cube

            centers, radii, data_locs = OctreeImporter.crawl_tree_grid(tree_grid)
            for octant in range(0,len(centers)):
                if tree_grid.data[data_locs[octant]] < 1:
                    continue
                # centers are in the 0->1 range, we want it centered around the origin
                loc = centers[octant] - 0.5
                rad = radii[octant]

                add_voxel(location=(x_tf(loc[0]),y_tf(loc[1]),z_tf(loc[2])),
                          radius=[rad[0],rad[1],rad[2]])
        else:
            if meshtype != "marching_cubes":
                log("Did not understand meshtype '%s', defaulting to marching cubes"%meshtype,LogLevel.WARNING)
            try:
                from skimage import measure
            except ImportError as ex:
                log("Failed to perform marching cubes because 'skimage' is missing.", LogLevel.WARNING)
                return

            dense_grid = tree_grid.create_dense_from_tree()

            if np.max(dense_grid ) <= 0.0 or np.min(dense_grid ) >= 0.0:
                log("The created dense grid does not contain any surface voxels", LogLevel.WARNING)
                log("Values are in the range %f -> %f" % (np.min(dense_grid),np.max(dense_grid)))
                return
            verts, faces, _, _ = measure.marching_cubes_lewiner(dense_grid , 0.0)

            verts = tuple([tuple([x_tf(float(row[0])), y_tf(float(row[1])), z_tf(float(row[2]))]) for row in verts])
            faces = tuple([tuple([int(row[0]), int(row[1]), int(row[2])]) for row in faces])
            blender_utils.add_object_from_mesh(verts, faces, [1/dense_grid.shape[0],1/dense_grid.shape[1],1/dense_grid.shape[2]],
                                               [0.5 / dense_grid.shape[0] - 0.5, 0.5 / dense_grid.shape[1] - 0.5,
                                                0.5 / dense_grid.shape[2] - 0.5])


OctreeImporter()
