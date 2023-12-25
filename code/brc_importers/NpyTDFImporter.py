from brc_importers.NpyImporter import NpyImporter
import numpy as np


class NpyTDFImporter(NpyImporter):

    def name(self):
        return "npy_tdf"

    @staticmethod
    def preprocess_grid(grid):
        return np.abs(np.squeeze(grid)) - 0.5

NpyTDFImporter()
