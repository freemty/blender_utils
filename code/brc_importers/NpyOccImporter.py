from brc_importers.NpyImporter import NpyImporter
import numpy as np

class NpyOccImporter(NpyImporter):

    def name(self):
        return "npy_occ"

    @staticmethod
    def preprocess_grid(grid):
        grid = 0.5 - np.abs(np.squeeze(grid))
        print("Loaded occupancy grid has %d cubes" % np.sum(grid))
        return grid
        
NpyOccImporter()
