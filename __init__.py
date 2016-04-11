# -*- coding: utf-8 -*-
"""
/***************************************************************************
 ThreeDiToolbox
                                 A QGIS plugin
 Toolbox for working with 3di hydraulic models
                             -------------------
        begin                : 2016-03-04
        copyright            : (C) 2016 by Nelen&Schuurmans
        email                : bastiaan.roos@nelen-schuurmans.nl
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""
import sys
import os
from utils.user_messages import pop_up_info, log


try:
    import netCDF4
    log('Use local installation of python netCDF4 library')
except ImportError:
    if os.name == 'nt':
        if sys.maxsize > 2**32:
            # Windows 64 bit
            # use netCDF in external map
            sys.path.append(os.path.join(
                os.path.dirname(os.path.realpath(__file__)),
                'external', 'netCDF4-win64'))
            import netCDF4

            msg = 'Used netCDF4 library, provided with plugin. Python-netcdf version %{python-netcdf}s, '\
                'netCDF4 version %{netcdf)s and HDF5 version %{netcdf)s.'% {
                'python-netcdf': netCDF4.__version__,
                'netcdf': netCDF4.__netcdf4libversion__,
                'hdf5': netCDF4.__hdf5libversion__
            }
            log(msg)
            print msg
        else:
            pop_up_info('Error: could not find netCDF4 installation. Change to the 64-bit vresion of QGIS or try to '
                        'install the netCDF4 python libary yourself.')
    else:
        pop_up_info('Error: could not find netCDF4 installation. Please install python-netCDF4 package.')

print os.path.dirname(netCDF4.__file__)

try:
    import pyqtgraph
    log('Use local installation of pyqtgraph ')
except ImportError:
        log('Use provided version of pyatgraph')
        sys.path.append(os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'external', 'pyqtgraph-0.9.10'))
        import pyqtgraph

print os.path.dirname(pyqtgraph.__file__)


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load ThreeDiToolbox class from file ThreeDiToolbox.

    :param iface: QgsInterface. A QGIS interface instance.
    """

    from .threedi_tools import ThreeDiTools
    return ThreeDiTools(iface)
