from brc_importers.NpyImporter import NpyImporter


class NpyProbImporter(NpyImporter):

    def name(self):
        return "npy_prob"

    @staticmethod
    def preprocess_grid(grid):
        return 0.5 - grid[1,:,:,:]

NpyProbImporter()
