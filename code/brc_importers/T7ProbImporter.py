from brc_importers.T7Importer import T7Importer


class T7ProbImporter(T7Importer):

    def name(self):
        return "t7_prob"

    @staticmethod
    def preprocess_grid(grid):
        return 0.5 - grid[1,:,:,:]

T7ProbImporter()
