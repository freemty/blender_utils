from brc_importers.T7Importer import T7Importer
import numpy as np


class T7TDFImporter(T7Importer):

    def name(self):
        return "t7_tdf"

    @staticmethod
    def preprocess_grid(grid):
        grid = np.squeeze(grid)
        if grid.ndim == 4:
            # first channel is the TSDF, other three are the normal estimate
            grid = grid[0,:,:,:]
        return np.abs(grid)-0.5

T7TDFImporter()
