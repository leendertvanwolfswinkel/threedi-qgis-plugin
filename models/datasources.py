# -*- coding: utf-8 -*-
import logging
import os

logger = logging.getLogger(__file__)

from PyQt4.QtCore import Qt, pyqtSignal, QVariant
from PyQt4 import QtCore
from ThreeDiToolbox.datasource.netcdf import NetcdfDataSource
from base import BaseModel
from base_fields import CheckboxField, ValueField
from ThreeDiToolbox.utils.layer_from_netCDF import (
    make_flowline_layer, make_node_layer, make_pumpline_layer)
from ThreeDiToolbox.utils.user_messages import log
from ThreeDiToolbox.datasource.spatialite import Spatialite
from ThreeDiToolbox.stats.stats import (
    StatFunctions, StatMaxWithT, StatMinWithT,
    StatLastValue, StatDuration)

from qgis.core import (
    QgsDataSourceURI, QgsVectorLayer, QGis, QgsGeometry,
    QgsFeature)
import numpy as np


def get_line_pattern(item_field):
    """
    get (default) line pattern for plots from this datasource
    :param item_field:
    :return:
    """
    available_styles = [
        Qt.SolidLine,
        Qt.DashLine,
        Qt.DotLine,
        Qt.DashDotLine,
        Qt.DashDotDotLine
    ]

    used_patterns = [item.pattern.value for item in item_field.item.model.rows]

    for style in available_styles:
        if style not in used_patterns:
            return style

    return Qt.SolidLine

class ValueWithChangeSignal(object):

    def __init__(self, signal_name, signal_setting_name, init_value = None):
        self.signal_name = signal_name
        self.signal_setting_name = signal_setting_name
        self.value = init_value

    def __get__(self, instance, type):
        return self.value

    def __set__(self, instance, value):
        self.value = value
        getattr(instance, self.signal_name).emit(self.signal_setting_name, value)



def some_function_pointer():
    pass


class TimeseriesDatasourceModel(BaseModel):

    model_schematisation_change = pyqtSignal(str, str)
    results_change = pyqtSignal(str, list)

    def __init__(self):
        BaseModel.__init__(self)
        self.dataChanged.connect(self.on_change)
        self.rowsRemoved.connect(self.on_change)
        self.rowsInserted.connect(self.on_change)

    # fields:
    tool_name = 'result_selection'
    model_spatialite_filepath = ValueWithChangeSignal('model_schematisation_change',
                                                      'model_schematisation')

    class Fields:
        active = CheckboxField(show=True, default_value=True, column_width=20,
                               column_name='')
        name = ValueField(show=True, column_width=130, column_name='Name')
        file_path = ValueField(show=True, column_width=260, column_name='File')
        type = ValueField(show=False)
        pattern = ValueField(show=False, default_value=get_line_pattern)

        _line_layer = None
        _node_layer = None
        _pumpline_layer = None

        _node_statistics = None

        def datasource(self):
            if hasattr(self, '_datasource'):
                return self._datasource
            elif self.type.value == 'netcdf':
                self._datasource = NetcdfDataSource(self.file_path.value)
                return self._datasource

        def get_memory_layers(self):
            """Note: lines and nodes are always in the netCDF, pumps are not
            always in the netCDF."""

            file_name = self.datasource().file_path[:-3] + '.sqlite'
            spl = Spatialite(file_name)

            if self._line_layer is None:
                if 'flowlines' in [t[1] for t in spl.getTables()]:
                    # todo check nr of attributes
                    self._line_layer = spl.get_layer('flowlines', None, 'the_geom')
                else:
                    self._line_layer = make_flowline_layer(self.datasource(), spl)

            if self._pumpline_layer is None:

                if 'pumplines' in [t[1] for t in spl.getTables()]:
                    self._pumpline_layer = spl.get_layer('pumplines', None, 'the_geom')
                else:
                    try:
                        self._pumpline_layer = make_pumpline_layer(self.datasource(), spl)
                    except KeyError:
                        log("No pumps in netCDF", level='WARNING')

            return self._line_layer, self.node_layer(), self._pumpline_layer


        def node_layer(self):

            if self._node_layer is None:
                file_name = self.datasource().file_path[:-3] + '.sqlite'
                spl = Spatialite(file_name)

                if 'nodes' in [t[1] for t in spl.getTables()]:
                    self._node_layer = spl.get_layer('nodes', None, 'the_geom')
                else:
                    self._node_layer = make_node_layer(self.datasource(), spl)

            return self._node_layer

        def calc_stats(self, stats, layer, destination_table, mask=None):

            file_name = self.datasource().file_path[:-3] + '.sqlite'
            spl = Spatialite(file_name)

            provider = layer.dataProvider()

            fields = [f[1] for f in spl.getTableFields(destination_table)]

            calc_stats = stats
            # for stat in stats:
            #     if not (stat.column_names[0] in fields or
            #                         stat.column_names[0] + '_estimation' in fields):
            #         calc_stats.append(stat)

            sf = StatFunctions(self.datasource())

            calc_stats = sf.calc_stats(calc_stats, mask)

            for stat in calc_stats:
                for i, (column_name, field_def) in enumerate(
                        zip(stat.column_names, stat.qgs_field_defs)):
                    if column_name not in (f[1] for f in spl.getTableFields(destination_table)):
                        # does not work: spl.addTableColumn('nodes', field_def)
                        provider.addAttributes([field_def])
                        layer.updateFields()

                    field_index = layer.fieldNameIndex(stat.column_names[i])
                    update_dict = dict()

                    if len(stat.cols) == 1:
                        res = stat.results
                    else:
                        res = stat.results[i]

                    for row, value in enumerate(res):
                        if mask:
                            row = mask[row]
                        update_dict[long(row)] = {field_index: float(value)}

                    provider.changeAttributeValues(update_dict)

            return layer

        def get_node_statistics(self):

            if self._node_statistics is not None:
                return self._node_statistics
            else:
                node_layer = self.node_layer()

                stats = [
                    StatMaxWithT('s1_max',
                                 ['s1_max'],
                                 alternative_params=['s1', 's1_mean']),
                    StatMinWithT('s1_min',
                                 ['s1_min'],
                                 alternative_params=['s1', 's1_mean']),
                    StatLastValue('s1_end',
                                  ['s1'])
                ]

                self._node_statistics = self.calc_stats(
                        stats, node_layer, 'nodes')

                return self._node_statistics

            # realtime (relative to s1, s1_max or s1_min):
            # - depth
            # - fill at manholes
            # - depth wos
            # - % between min and max
            # - diff between min en max
            # - diff related to  t0

        def get_manhole_statistics(self):

            uri = QgsDataSourceURI()
            uri.setDatabase(self.model.model_spatialite_filepath)
            uri.setDataSource('', 'v2_manhole', '')
            manhole_layer = QgsVectorLayer(uri.uri(), 'v2_manhole', 'spatialite')

            node_layer = self.node_layer()

            file_name = self.datasource().file_path[:-3] + '.sqlite'
            spl = Spatialite(file_name)

            tables = (t[1] for t in spl.getTables())

            if 'manholes' not in tables:
                fields = [
                    "id INTEGER",
                    "spatialite_id INTEGER",
                    "bottom_level FLOAT",
                    "surface_level FLOAT",
                    "drain_level FLOAT",
                    "fill_end FLOAT",
                    "wos_depth_max FLOAT",
                ]

                layer = spl.create_empty_layer('manholes',
                                               QGis.WKBPoint,
                                               fields,
                                               'id')
                layer.updateFields()
            else:
                layer = spl.get_layer('manholes',
                                      'manhole_statistics',
                                      'the_geom')

            provider = layer.dataProvider()
            levels = []
            geom = {}

            id_mapping = {}
            for feature in node_layer.getFeatures():
                if not hasattr(feature['spatialite_id'], 'isNull'):
                    id_mapping[feature['spatialite_id']] = feature['id']
                    geom[feature['spatialite_id']] = QgsGeometry(feature.geometry())

            new_features = []
            for feature in manhole_layer.getFeatures():

                feat = QgsFeature()

                if feature['connection_node_id'] not in geom:
                    logger.log(logging.WARNING,
                               'manhole connection_node not found in results'
                               'connection_node id: {0}'.format(feature['connection_node_id']))
                else:

                    feat.setGeometry(geom[feature['connection_node_id']])

                    feat.setAttributes([
                        id_mapping[feature['connection_node_id']],
                        feature['connection_node_id'],
                        feature['bottom_level'],
                        feature['surface_level'],
                        feature['drain_level']
                    ])
                    new_features.append(feat)

                    levels.append((id_mapping[feature['connection_node_id']],
                                  feature['surface_level'],
                                  feature['drain_level']))

            provider.addFeatures(new_features)

            layer.updateExtents()

            levels = sorted(levels)
            ids, surface_levels, drain_levels = zip(*levels)
            surface = np.array(surface_levels)
            drain = np.array(drain_levels)

            stats = [
                StatDuration('wos_dur',
                             ['s1'],
                             object_mask=ids,
                             tresholds=surface),
                StatDuration('wos_dur_drain',
                             ['s1'],
                             object_mask=ids,
                             tresholds=drain),
                StatMaxWithT('s1_max',
                             ['s1_max'],
                             alternative_params=['s1', 's1_mean']),
                StatLastValue('s1_end',
                              ['s1'])

            ]

            self._manhole_statistics = self.calc_stats(
                    stats, layer, 'manholes', ids)

            index_wos = layer.fieldNameIndex('wos_depth_max')
            index_fill = layer.fieldNameIndex('fill_end')
            
            update_dict = {}
            for feat in self._manhole_statistics.getFeatures():

                update_dict[feat.id()] = {
                    index_wos: feat['surface_level'] - feat['s1_max']
                    index_fill: ((feat['s1_end'] - feat['bottom_level'])
                                 /(feat['surface_level'] - feat['bottom_level']))
                }

            provider.changeAttributeValues(update_dict)

            return self._manhole_statistics

    def reset(self):

        self.removeRows(0, self.rowCount())

    def on_change(self, start=None, stop=None, etc=None):

        self.results_change.emit('result_directories', self.rows)





