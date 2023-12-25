from brc_importers.OctreeImporter import OctreeImporter, Octree


class OctreeTDFImporter(OctreeImporter):

    def name(self):
        return "octree_tdf"

    @staticmethod
    def preprocess_grid(tree):
        tree.data = tree.data - 0.5
        return tree

OctreeTDFImporter()
