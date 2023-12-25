from abc import ABC, abstractmethod
from render_logging import log, LogLevel


loaders = dict()


def handle_import(arguments):
    loaders[arguments[0]].load(arguments[1:])


def register_importer(name,importer):
    loaders[name] = importer


class Importer(ABC,object):

    def __init__(self):
        register_importer(self.name(), self)

    @staticmethod
    @abstractmethod
    def name():
        pass

    @abstractmethod
    def load(self, arguments):
        pass


def initialize_importers():
    import sys

    import importlib, pkgutil
    package = sys.modules["brc_importers"]
    for loader, name, is_pkg in pkgutil.walk_packages(package.__path__):
        try:
            importlib.import_module("brc_importers" + '.' + name)
        except ImportError as ex:
            log("Failed to import '"+name+"': "+str(ex),LogLevel.WARNING)


def get_importer_names():
    return loaders.keys()
