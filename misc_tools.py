# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.
"""
Miscellaneous tools.
"""

import os
from itertools import chain

from qgis.core import QgsMapLayerRegistry

from .stats.utils import get_csv_layer_cache_files
from .utils.user_messages import pop_up_info, pop_up_question


class About(object):
    """Add 3Di logo and about info."""

    def __init__(self, iface):
        self.iface = iface
        self.icon_path = ':/plugins/ThreeDiToolbox/icon.png'
        self.menu_text = "3Di about"

    def run(self):
        """Shows dialog with version information."""
        # todo: add version number and link to sites
        with open(os.path.join(os.path.dirname(__file__),
                  'version.rst'), 'r') as f:
            version = f.readline().rstrip()

        pop_up_info("3Di Tools versie %s" % version,
                    "About", self.iface.mainWindow())

    def on_unload(self):
        pass


class CacheClearer(object):
    """Tool to delete cache files."""

    def __init__(self, iface, ts_datasource):
        """Constructor.

        Args:
            iface: QGIS interface
            ts_datasource: TimeseriesDatasourceModel instance
        """
        self.iface = iface
        self.icon_path = ':/plugins/ThreeDiToolbox/icon_broom.png'
        self.menu_text = "Clear cache"
        self.ts_datasource = ts_datasource

    def run(self):
        """Find cached spatialite and csv layer files for all items in the
        TimeseriesDatasourceModel object and delete them.
        """
        spatialite_filepaths = [
            item.spatialite_cache_filepath() for
            item in self.ts_datasource.rows if
            os.path.exists(item.spatialite_cache_filepath())
        ]
        result_dirs = [
            os.path.dirname(item.file_path.value) for
            item in self.ts_datasource.rows
        ]
        csv_filepaths = get_csv_layer_cache_files(*result_dirs)
        # Note: convert to set because duplicates are possible if the same
        # datasource is loaded multiple times
        cached = set(spatialite_filepaths + csv_filepaths)
        if not cached:
            pop_up_info("No cached files found.")
            return

        # Files linked to the layers in the map registry are held open by
        # Windows. You need to delete them manually from the registry to be
        # able to remove the underlying data. Note that deleting the layer
        # from the legend doesn't necessarily delete the layer from the map
        # registry, even though it may appear that no more layers are loaded
        # visually.
        result_layers = chain(
            # I've given up on using nested list comprehensions...
            *[item.get_result_layers() for item in self.ts_datasource.rows])

        yes = pop_up_question(
            "The following files will be deleted:\n" +
            ',\n'.join(cached) +
            "\n\nContinue?")

        if yes:
            try:
                QgsMapLayerRegistry.instance().removeMapLayers(
                    [l.id() for l in result_layers])
            except RuntimeError:
                pass

            for f in cached:
                try:
                    os.remove(f)
                except OSError:
                    pop_up_info("Failed to delete %s." % f)
            pop_up_info("Cache cleared. You may need to restart QGIS and "
                        "reload your data.")

    def on_unload(self):
        pass
