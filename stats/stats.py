"""
This code was basically copied from python-flow with modifications to make
it work with our own data sources.
"""
import logging

logger = logging.getLogger(__file__)


import numpy as np

from qgis.core import QgsField
from PyQt4.QtCore import QVariant

class BaseStatistic(object):

    is_estimation = None
    used_param = None
    used_ts = None
    results = None

    def init_results(self, length):

        self.results = np.empty((len(self.cols), length))
        for i, col in enumerate(self.cols):
            self.results[i, :] = col['init_value']

    @property
    def column_names(self):
        names = []
        for i, col in enumerate(self.cols):
            if self.is_estimation:
                names.append(col['name'] + '_estimation')
            else:
                names.append(col['name'])
        return names

    @property
    def field_types(self):
        types = []
        for i, col in enumerate(self.cols):
            try:
                types.append(col['field_type'])
            except IndexError:
                types.append('float')
        return types

    @property
    def qgs_field_defs(self):
        map = {'float': QVariant.Double,
               'integer': QVariant.Int}
        defs = []
        for name, type_ in zip(self.column_names, self.field_types):
            defs.append(QgsField(name, map[type_]))

        return defs

    @property
    def field_defs(self):
        defs = []
        for name, type_ in zip(self.column_names, self.field_types):
            defs.append("{0} {1}".format(name, type_))
        return defs

    def get_stat_parameter(self, available_params):
        for param in self.prefered_params:
            if param in available_params:
                self.used_param = param
                return True

        for param in self.alternative_params:
            if param in available_params:
                self.used_param = param
                self.is_estimation = True
                return True

        return False


class StatMaxWithT(BaseStatistic):

    def __init__(self, ident, prefered_params,
                 alternative_params=list()):

        self.ident = ident
        self.prefered_params = prefered_params
        self.alternative_params = alternative_params

        # self.object_mask = object_mask
        # self.tresholds = tresholds

        self.cols = [{
            'name': self.ident,
            'field_type': 'float',
            'init_value': np.NAN
        }, {
            'name': self.ident + '_t',
            'field_type': 'integer',
            'init_value': 0
        }]

    def funct(self, vt, t_idx, t, input_description):
        """Maximum value of a q timeseries; can be negative.
        """
        # creates a new array, probaboly second method is faster?
        # maximum = np.maximum(qmax, np.fabs(qt))

        mask = self.results[0, :] < vt

        self.results[0] = np.ma.masked_where(mask, vt)
        self.results[1, np.ma.where(mask)] = t

        return self.results


class StatMinWithT(StatMaxWithT):

    def funct(self, vt, t_idx, t, input_description):
        """Maximum value of a q timeseries; can be negative.
        """

        mask = self.results[0, :] > vt

        self.results[0] = np.ma.masked_where(mask, vt)
        self.results[1, np.ma.where(mask)] = t

        return self.results


class StatDuration(BaseStatistic):

    def __init__(self, ident, prefered_params, object_mask, tresholds,
                 alternative_params=list()):

        self.ident = ident
        self.prefered_params = prefered_params
        self.alternative_params = alternative_params

        self.object_mask = object_mask
        self.tresholds = tresholds

        self.cols = [{
            'name': self.ident,
            'field_type': 'float',
            'init_value': 0
        }, {
            'name': self.ident + '_tstart',
            'field_type': 'integer',
            'init_value': np.NAN
        }, {
            'name': self.ident + '_tend',
            'field_type': 'integer',
            'init_value': np.NAN
        }]

    def init_results(self, length):

        BaseStatistic.init_results(self, length)

        # tresh = np.full((length), np.NAN)
        # for index, value in zip(self.object_mask, self.tresholds):
        #     if not (hasattr(value, 'isNull') and value.isNull()):
        #         qIsNull(value)
        #         tresh[index] = value
        # self.tresholds = tresh


    def funct(self, vt, t_idx, t, input_description):
        """Cumulative duration of all nonzero occurences of q.
        """
        # todo: do not add last timestep
        mask = vt > self.tresholds
        self.results[0, np.ma.where(mask)] += 1
        self.results[2, np.ma.where(mask)] = t

        start_mask = np.logical_and(mask, np.isnan(self.results[1, :]))
        self.results[1, np.ma.where(start_mask)] = t

        return self.results

    def finalize_funct(self, input_description):
        """
        Returns:

        """
        self.results[0, :] *= input_description['dt']/ 3600
        return self.results


class StatLastValue(BaseStatistic):
    def __init__(self, ident, prefered_params,
                 alternative_params=list()):
        self.ident = ident
        self.prefered_params = prefered_params
        self.alternative_params = alternative_params

        self.cols = [{
            'name': self.ident,
            'field_type': 'float',
            'init_value': np.NAN
        }]

    def funct(self, vt, t_idx, t, input_description):
        """last value of timerange
        """

        if input_description['nr_timestamps'] == t_idx + 1:
            self.results = vt
        return self.results


class DerivedParam(object):

    def __init__(self, ident, name, object_mask, accepted_params, input_params):
        self.ident = ident


class StatFunctions(object):
    """Get basic stats about subgrid netCDF files"""

    # TODO: there are possible issues when you have arrays with shapes or
    # lengths of 2. I.e. a q slice array has a shape of (2,), and when
    # the last element is truncated you will get an array of shape (1,)
    # which can be broadcasted together with everything. In practise there
    # should probably be no issues since the time and q arrays are of the
    # same length, but you never know. Might need some investigation.

    # Update these lists if you add a new method
    def __init__(self, datasource):
        self.ds = datasource

    def calc_stats(self, stats, mask=None):
        """

        Returns:

        """
        available_params = self.ds.get_available_variables()
        used_parameters = set()

        for stat in stats:
            if not stat.get_stat_parameter(available_params):
                logger.log(logging.WARNING,
                           'No results available to generate statistics of '
                           '{0}.'.format(stat['ident']))
                stats.remove(stat)
            else:
                used_parameters.add(stat.used_param)

        for param in used_parameters:
            pstats = [stat for stat in stats if stat.used_param == param]

            ts = self.ds.get_timestamps(parameter=param)
            result_description = {
                'dt': ts[1] - ts[0],
                'nr_timestamps': len(ts)
            }

            if mask is not None:
                rows = len(mask)
            else:
                rows = len(self.ds.get_values_by_timestamp(param, 0))

            for stat in pstats:
                stat.init_results(rows)

            for ts_idx, t in enumerate(ts):
                valuest = self.ds.get_values_by_timestamp(param, ts_idx, mask)
                for stat in pstats:
                    stat.results = stat.funct(
                        valuest,
                        ts_idx,
                        t,
                        result_description)

            for stat in pstats:
                if hasattr(stat, 'finalize_funct'):
                    stat.finalize_funct(
                        result_description
                    )
        return stats

    @staticmethod
    def calc_tot_vol(stat, qtot, qt, t, result):
        """Total volume through a structure. Structures are: pipes, weirs,
        orifices, pumps (pumps q's are in another netCDF array, but are
        supported in the datasource using the usual 'q' name).

        Note that the last element in q_slice is skipped (skipping the first
        element is another option, but not implemented here). Also note that q
        can be negative, so the absolute values are used.
        """
        # not absolute, not very usefull
        # todo: do not add last timestep
        qtot += qt
        return qtot

    @staticmethod
    def calc_tot_vol_positive(stat, qtot, qt, t, result):
        """Total volume through structure, counting only positive q's."""
        # mask negative values
        # todo: do not add last timestep
        qtot += np.ma.masked_where(qt < 0., qt)
        return qtot

    @staticmethod
    def calc_tot_vol_negative(stat, qtot, qt, t, result):
        """Total volume through structure, counting only negative q's."""
        # todo: do not add last timestep
        qtot += np.ma.masked_where(qtot > 0., qt)
        return qtot

    @staticmethod
    def calc_tot_vol_finalize(stat, qtot, result):
        qtot *= result['dt']  # = vtot
        return qtot

    @staticmethod
    def calc_max_abs_with_t(stat, v_t_max, vt, t, result):
        """Maximum value of a q timeseries; can be negative.
        """
        # creates a new array, probaboly second method is faster?
        # maximum = np.maximum(qmax, np.fabs(qt))

        absolute = np.fabs(vt)
        return StatFunctions.max_with_t(stat, v_t_max, absolute, t)


    @staticmethod
    def calc_cumulative_duration_pos(stat, vdur, vt, t, result):
        """Cumulative duration of all nonzero occurences of q.
        """
        # todo: do not add last timestep
        vdur += np.ma.masked_where(vt > stat.tresholds, 1)
        return vdur

    @staticmethod
    def calc_cumulative_duration_finalize(stat, vdur, result):
        """
        Returns:

        """
        vdur *= result['dt']
        return vdur



"""
link_stats = {
    'q_max': BaseStatistic(
        ident='s1_max',
        funct=StatFunctions.max_with_t,
        prefered_params=['s1_max'],
        alternative_params=['s1', 's1_mean'],
        nr_results=2
    ),
    'v_tot': BaseStatistic(
        ident='s1_max',
        funct=StatFunctions.max_with_t,
        prefered_params=['s1_max'],
        alternative_params=['s1', 's1_mean'],
        nr_results=2
    ),
    'v_tot_pos': BaseStatistic(
        ident='s1_max',
        funct=StatFunctions.max_with_t,
        prefered_params=['s1_max'],
        alternative_params=['s1', 's1_mean'],
        nr_results=2
    ),
    'v_tot_neg': BaseStatistic(),
    'q_end': BaseStatistic(),
    'vel_max': BaseStatistic(),
    'q_start_end': BaseStatistic()
}

pump_stats = {
    'v_tot': BaseStatistic(),
    'v_start_end': BaseStatistic(),
    'perc_full_cap': {},
}

node_calc = {
    'depth'
    'manhole_fill'
    'rel_to_surface'
    'rel_to_drain'
}

link_calc = {
    'depth'
    'pipe_fill'
    'direction'
    'width_'

}

pump_calc = {
    'percentage_full'
}

"""