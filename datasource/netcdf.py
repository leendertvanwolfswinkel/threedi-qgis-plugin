import glob
import json
import os

from netCDF4 import Dataset
import numpy as np

from ..utils.user_messages import log
from .spatialite import get_object_type, get_variables


def get_id_mapping_file(netcdf_file_path):
    """An ad-hoc way to get the id_mapping file.

    We assume the id_mapping file is always in ../input_generated
    relative to the netcdf file and that it always starts with
    'id_mapping'.

    Returns: id_mapping file path
    """
    pattern = 'id_mapping*'
    inpdir = os.path.join(os.path.dirname(netcdf_file_path),
                          '..', 'input_generated')
    return glob.glob(os.path.join(inpdir, pattern))[0]


def get_channel_mapping(ds):
    """Map inp ids to flowline ids.

    Note that you need to subtract 1 from the resulting flowline id because of
    Python's 0-based indexing array (versus Fortran's 1-based indexing). These
    flowline ids are used for  pipes, weirs and orifices.
    """
    cm = np.copy(ds.variables['channel_mapping'])
    cm[:, 1] = cm[:, 1] - 1  # the index transformation
    return dict(cm)


def get_node_mapping(ds):
    """Map inp ids to node ids.

    Note that you need to subtract 1 from the resulting node id because of
    Python's 0-based indexing array (versus Fortran's 1-based indexing). These
    node ids are used for manholes.
    """
    cm = np.copy(ds.variables['node_mapping'])
    cm[:, 1] = cm[:, 1] - 1  # the index transformation
    return dict(cm)


def get_timesteps(ds):
    """Timestep determination using consecutive element difference"""
    return np.ediff1d(ds.variables['time'])




class NetcdfDataSource(object):

    def __init__(self, file_path):
        """
        Args:
            file_path: path to netcdf
        """
        self.file_path = file_path
        # Load netcdf
        self.ds = Dataset(self.file_path, mode='r', format='NETCDF4')
        log("Opened netcdf: %s" % self.file_path)

        self.channel_mapping = get_channel_mapping(self.ds)
        self.node_mapping = get_node_mapping(self.ds)

        self.id_mapping_file = get_id_mapping_file(file_path)
        # Load id mapping
        with open(self.id_mapping_file) as f:
            self.id_mapping = json.load(f)

    @property
    def metadata(self):

        pass

    def get_object_types(self, parameter=None):

        pass

    def get_objects(self, object_type):

        pass

    def get_object_count(self, object_type):

        pass

    def get_timestamps(self, object_type=None, parameter=None):
        return self.ds.variables['time'][:]

    def get_parameters(self, object_type=None):
        pass

    def get_object(self, object_type, object_id):

        pass

    def get_netcdf_id(self, inp_id, object_type):
        """Get the node or flow link id needed to get data from netcdf."""
        if object_type in ['manhole', 'connection_nodes']:
            return self.node_mapping[inp_id]
        else:
            return self.channel_mapping[inp_id]

    def get_timeseries(self, object_type, object_id, parameters, start_ts=None,
                       end_ts=None):
        """Get a list of time series from netcdf.

        Note: if there are multiple parameters, all result values are just
        lumped together and returned

        Args:
            object_type: e.g. 'v2_weir'
            object_id: spatialite id?
            parameters: a list of params, e.g.: ['q', 'q_pump']

        Returns:
            a list of 2-tuples (time, value)
        """
        # Normalize the name
        n_object_type = get_object_type(object_type)

        # Mapping: spatialite id -> inp id -> netcdf id
        obj_id_mapping = self.id_mapping[n_object_type]
        inp_id = obj_id_mapping[str(object_id)]  # strings because: JSON
        netcdf_id = self.get_netcdf_id(inp_id, n_object_type)

        variables = get_variables(n_object_type, parameters)

        # Get data from all variables and just put them in the same list:
        result = []
        for v in variables:
            vals = self.ds.variables[v][:, netcdf_id]
            timestamps = self.get_timestamps(self.ds)
            result += zip(timestamps, vals)

        # from ..qdebug import pyqt_set_trace; pyqt_set_trace()
        return result
