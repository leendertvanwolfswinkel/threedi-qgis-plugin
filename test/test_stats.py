import unittest
import os.path
import numpy as np

from ThreeDiToolbox.stats.ncstats import NcStats
from models.datasources import TimeseriesDatasourceModel

from utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class TestNcStats(unittest.TestCase):
    """Test the NcStats class"""

    def test_smoke(self):
        ncstats = NcStats(datasource='mock')
        self.assertEqual(ncstats.datasource, 'mock')

    def test_available_parameters1(self):
        """Test that we can get all the methods defined in
        AVAILABLE_STRUCTURE_PARAMETERS"""
        ncstats = NcStats(datasource='mock')
        for parameter_name in ncstats.AVAILABLE_STRUCTURE_PARAMETERS:
            # if this crashes a method isn't implemented
            getattr(ncstats, parameter_name)

    def test_available_parameters2(self):
        """Test that we can get all the methods defined in
        AVAILABLE_MANHOLE_PARAMETERS"""
        ncstats = NcStats(datasource='mock')
        for parameter_name in ncstats.AVAILABLE_MANHOLE_PARAMETERS:
            # if this crashes a method isn't implemented
            getattr(ncstats, parameter_name)


class DatasourceStats(unittest.TestCase):
    """Tests using the datasource stat functionalities of the datasource model

    """

    def setUp(self):
        self.tds = TimeseriesDatasourceModel()
        self.tds.model_spatialite_filepath = 'c:\\tmp\\v2_bergermeer.sqlite'
        self.tds.insertRows([{
                'type': 'netcdf',
                'name': 'test',
                'file_path': 'c:\\tmp\\subgrid_map.nc'
            }], signal=False)

    def test_s1_max_stats(self):
        self.tds.rows[0].get_node_statistics()
        self.assertEqual(0, 0)


    def test_manhole(self):
        self.tds.rows[0].get_manhole_statistics()
        self.assertEqual(0, 0)




