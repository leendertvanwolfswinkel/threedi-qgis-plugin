import os
import unittest
import tempfile
import shutil

from utilities import get_qgis_app
QGIS_APP = get_qgis_app()

from qgis.core import QgsVectorLayer, QgsFeature, QgsPoint, QgsField, QgsGeometry
from PyQt4.QtCore import QVariant

from ThreeDiToolbox.datasource.netcdf import NetcdfDataSource, get_variables

from ThreeDiToolbox.datasource.spatialite import Spatialite


spatialite_datasource_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data', 'test_spatialite.sqlite')

netcdf_datasource_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    'data', 'testmodel', 'results', 'subgrid_map.nc')


class TestParameters(unittest.TestCase):
    """Test functions that convert parameters to variable names in the
    datasource."""

    def test_get_variables(self):
        vars = get_variables(object_type='pipe', parameters=['q'])
        self.assertEqual(vars, ['q'])

    def test_get_variables2(self):
        """Get both u variable names for backwards compatability."""
        vars = get_variables('pipe', ['u1'])
        self.assertEqual(vars, ['u1'])

    def test_get_variables3(self):
        vars = get_variables('pumpstation', ['q'])
        self.assertEqual(vars, ['q_pump'])


@unittest.skipIf(not os.path.exists(netcdf_datasource_path),
                 "Path to test netcdf doesn't exist.")
class TestNetcdfDatasource(unittest.TestCase):

    def setUp(self):
        self.ncds = NetcdfDataSource(netcdf_datasource_path,
                                     load_properties=False)

    def test_netcdf_loaded(self):
        """We can open the Netcdf file"""
        self.assertTrue(self.ncds.ds is not None)

    def test_id_mapping_loaded(self):
        """The datasource correctly finds the id_mapping.json."""
        self.assertTrue(self.ncds.id_mapping is not None)

    def test_timestamps(self):
        """We'll asume there are always some time steps"""
        ts = self.ncds.get_timestamps(object_type="doesn't matter")
        self.assertTrue(len(ts) > 0)
        self.assertEqual(ts[0], 0.0)
        self.assertNotEqual(ts[1], 0.0)


class TestSpatialiteDataSource(unittest.TestCase):

    def setUp(self):
        self.tmp_directory = tempfile.mkdtemp()
        self.spatialite_path = os.path.join(self.tmp_directory, 'test.sqlite')

    def tearDown(self):
        shutil.rmtree(self.tmp_directory)

    def test_create_empty_table(self):
        spl = Spatialite(self.spatialite_path + '1')

        layer = spl.create_empty_layer('table_one',
                                       fields=['id INTEGER', 'name TEXT NULLABLE'])
        # test table is created
        self.assertIsNotNone(layer)
        self.assertTrue('table_one' in [c[1] for c in spl.getTables()])
        self.assertFalse('table_two' in spl.getTables())

        # test adding data
        self.assertEqual(layer.featureCount(), 0)
        pr = layer.dataProvider()

        feat = QgsFeature()
        feat.setAttributes([1, 'test'])
        feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(1.0, 2.0)))

        pr.addFeatures([feat])
        self.assertEqual(layer.featureCount(), 1)

    def test_import_layer(self):
        spl = Spatialite(self.spatialite_path + '3')

        # create memory layer
        uri = "Point?crs=epsg:4326&index=yes"
        layer = QgsVectorLayer(uri, "test_layer", "memory")
        pr = layer.dataProvider()

        # add fields
        pr.addAttributes([
            QgsField("id", QVariant.Int),
            QgsField("col2", QVariant.Double),
            QgsField("col3", QVariant.String, None, 20),
            QgsField("col4", QVariant.TextFormat),
        ])
        # tell the vector layer to fetch changes from the provider
        layer.updateFields()
        pr = layer.dataProvider()
        feat = QgsFeature()
        feat.setAttributes([1, 'test'])
        feat.setGeometry(QgsGeometry.fromPoint(QgsPoint(1.0, 2.0)))
        pr.addFeatures([feat])

        spl_layer = spl.import_layer(layer, 'table_one', 'id')

        self.assertIsNotNone(spl_layer)
        self.assertTrue('table_one' in [c[1] for c in spl.getTables()])
        self.assertEqual(layer.featureCount(), 1)


