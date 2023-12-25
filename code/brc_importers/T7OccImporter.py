from brc_importers.T7Importer import T7Importer
import numpy as np
from render_logging import log,LogLevel


class T7OccImporter(T7Importer):

    def name(self):
        return "t7_occ"

    @staticmethod
    def preprocess_grid(grid):
        grid = np.squeeze(grid)
        if len(grid.shape) > 3:
            grid = grid[0,:,:,:]
        grid = 0.5 - np.abs(np.squeeze(grid))
        print("Loaded occupancy grid has %d cubes" % np.sum(grid))
        return grid

T7OccImporter()
