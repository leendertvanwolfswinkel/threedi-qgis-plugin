# -*- coding: utf-8 -*-
# (c) Nelen & Schuurmans, see LICENSE.rst.

import logging

from sqlalchemy import (
    Boolean, Column, Integer, String, Float, ForeignKey)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from spatialalchemy.types import Geometry

from .constants import Constants

logger = logging.getLogger(__name__)
Base = declarative_base()


def prettify(value, postfix, value_format='%0.2f'):
    """
    return prettified string of given value
    value may be None
    postfix can be used for unit for example
    """
    if value is None:
        value_str = '--'
    else:
        value_str = value_format % value
    return '%s %s' % (value_str, postfix)


class GlobalSetting(Base):
    __tablename__ = 'v2_global_settings'
    # Here we define columns for the table person
    # Notice that each column is also a normal Python instance attribute.
    id = Column(Integer, primary_key=True)
    dem_file = Column(String(255), nullable=True)
    frict_coef_file = Column(String(255), nullable=True)
    grid_space = Column(Float)
    kmax = Column(Integer)
    nr_timesteps = Column(Integer)
    sim_time_step = Column(Float)

    def __str__(self):
        return u'Global setting [dem_file=%s, frict_coef_file=%s]' % (
            self.dem_file, self.frict_coef_file)


class CrossSectionDefinition(Base):
    __tablename__ = 'v2_cross_section_definition'

    PROFILE_SHAPES = Constants.PROFILE_SHAPES

    id = Column(Integer, primary_key=True)
    width = Column(Float)
    height = Column(Float)
    shape = Column(Integer)  # PROFILE_SHAPES
    _code = Column(String(100))  # nullable=False


class ConnectionNode(Base):
    __tablename__ = 'v2_connection_nodes'

    # why does connection node not has a code and zoom_category???

    id = Column(Integer, primary_key=True)
    storage_area = Column(Float)
    initial_waterlevel = Column(Float)
    the_geom = Column(Geometry(geometry_type='POINT',
                               srid=4326,
                               spatial_index=True),
                      nullable=False)

    the_geom_linestring = Column(Geometry(geometry_type='POINT',
                                          srid=4326,
                                          spatial_index=False),
                                 nullable=True)

    # extra fields:
    _code = Column(String(100), nullable=True)
    _basin_code = Column(String(4), nullable=True)

    manhole = relationship("Manhole",
                           uselist=False,
                           back_populates="connection_node")
    boundary_condition = relationship("BoundaryCondition1D",
                                      uselist=False,
                                      back_populates="connection_node")
    impervious_surface_map = relationship("ImperviousSurfaceMap",
                                          back_populates="connection_node")
#    onedee_lateral = relationship("OnedeeLateral")


class Manhole(Base):
    __tablename__ = 'v2_manhole'

    MANHOLE_INDICATORS = Constants.MANHOLE_INDICATORS
    CALCULATION_TYPES = Constants.CALCULATION_TYPES
    MANHOLE_SHAPES = Constants.MANHOLE_SHAPES

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')
    zoom_category = Column(Integer)

    width = Column(Float)
    shape = Column(String(4))  # MANHOLE_SHAPES
    length = Column(Float)
    surface_level = Column(Float)
    bottom_level = Column(Float)
    drain_level = Column(Float)
    sediment_level = Column(Float)
    manhole_indicator = Column(Integer)  # MANHOLE_INDICATORS
    calculation_type = Column(Integer)  # CALCULATION_TYPES

    connection_node_id = Column(
            Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=False,
            unique=True)  # extra compared to original
    connection_node = relationship(ConnectionNode,
                                   back_populates="manhole")


class BoundaryCondition1D(Base):
    """
    TODO: more fields
    """
    __tablename__ = 'v2_1d_boundary_conditions'

    BOUNDARY_TYPES = Constants.BOUNDARY_TYPES

    id = Column(Integer, primary_key=True)
    boundary_type = Column(Integer)
    timeseries = Column(String)

    connection_node_id = Column(
            Integer, ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=False,
            unique=True)
    connection_node = relationship(ConnectionNode,
                                   foreign_keys=connection_node_id,
                                   back_populates="boundary_condition")


class Channel(Base):

    __tablename__ = 'v2_channel'

    CALCULATION_TYPES = Constants.CALCULATION_TYPES

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')
    zoom_category = Column(Integer, nullable=True)  # default=2

    calculation_type = Column(Integer, nullable=True)
    dist_calc_points = Column(Float, nullable=True)
    the_geom = Column(Geometry(geometry_type='LINESTRING',
                               srid=4326,
                               spatial_index=True),
                      nullable=False)

    # node relations
    connection_node_start_id = Column(
        ForeignKey(ConnectionNode.__tablename__ + ".id"),
        nullable=True)
    connection_node_start = relationship(
        ConnectionNode, foreign_keys=connection_node_start_id)

    connection_node_end_id = Column(
        ForeignKey(ConnectionNode.__tablename__ + ".id"),
        nullable=True)
    connection_node_end = relationship(
        ConnectionNode, foreign_keys=connection_node_end_id)

    cross_section_locations = relationship("CrossSectionLocation",
                                           back_populates="channel")


class CrossSectionLocation(Base):
    __tablename__ = 'v2_cross_section_location'

    FRICTION_TYPE = Constants.FRICTION_TYPES

    id = Column(Integer, primary_key=True)
    channel_id = Column(
        Integer, ForeignKey("v2_channel.id"),
        nullable=False)
    channel = relationship(Channel,
                           back_populates="cross_section_locations")

    definition_id = Column(
        Integer, ForeignKey("v2_cross_section_definition.id"),
        nullable=True)
    definition = relationship(CrossSectionDefinition)

    reference_level = Column(Float)
    friction_type = Column(Integer)  # FRICTION_TYPES
    friction_value = Column(Float)


class Pipe(Base):

    __tablename__ = 'v2_pipe'

    CALCULATION_TYPES = Constants.CALCULATION_TYPES
    SEWERAGE_TYPES = Constants.SEWERAGE_TYPES
    MATERIALS = Constants.MATERIALS

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')
    zoom_category = Column(Integer, nullable=True, default=2)

    # node relations
    connection_node_start_id = Column(
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_start = relationship(
            ConnectionNode, foreign_keys=connection_node_start_id)

    connection_node_end_id = Column(
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_end = relationship(
            ConnectionNode, foreign_keys=connection_node_end_id)

    original_length = Column(Float)

    # cross section and level
    cross_section_definition_id = Column(
            Integer, ForeignKey("v2_cross_section_definition.id"),
            nullable=True)
    cross_section_definition = relationship("CrossSectionDefinition")

    invert_level_start_point = Column(Float)
    invert_level_end_point = Column(Float)

    # friction
    friction_value = Column(Float)
    friction_type = Column(Integer)  # FRICTION_TYPE

    profile_num = Column(Integer)  # ??
    sewerage_type = Column(Integer)  # SEWERAGE_TYPES
    calculation_type = Column(Integer)  # CALCULATION_TYPES
    dist_calc_points = Column(Float)

    material = Column(Integer)  # MATERIALS
    pipe_quality = Column(Float)

    _basin = Column(String(4), nullable=True)


class Culvert(Base):
    # todo: check this definition with original
    __tablename__ = 'v2_culvert'

    CALCULATION_TYPES = Constants.CALCULATION_TYPES

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False)
    zoom_category = Column(Integer, nullable=True)  # default=2

    # node relations
    connection_node_start_id = Column(
            'connection_node_start_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=False)
    connection_node_start = relationship(
            ConnectionNode, foreign_keys=connection_node_start_id)

    connection_node_end_id = Column(
            'connection_node_end_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=False)
    connection_node_end = relationship(
            ConnectionNode, foreign_keys=connection_node_end_id)

    # cross section and level
    cross_section_definition_id = Column(
            Integer, ForeignKey("v2_cross_section_definition.id"),
            nullable=True)
    cross_section_definition = relationship(CrossSectionDefinition)
    invert_level_start_point = Column(Float)
    invert_level_end_point = Column(Float)

    # friction and flow direction
    friction_value = Column(Float)
    friction_type = Column(Integer)
    discharge_coefficient_positive = Column(Float)
    discharge_coefficient_negative = Column(Float)

    # other attributes
    calculation_type = Column(Integer)
    dist_calc_points = Column(Float, nullable=True)

    the_geom = Column(Geometry(geometry_type='LINESTRING',
                               srid=4326,
                               spatial_index=True),
                      nullable=True)


class Weir(Base):

    __tablename__ = 'v2_weir'

    CREST_TYPES = Constants.CREST_TYPES
    FRICTION_TYPES = Constants.FRICTION_TYPES

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')
    zoom_category = Column(Integer, nullable=True, default=2)

    # node relations
    connection_node_start_id = Column(
            'connection_node_start_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_start = relationship(
            ConnectionNode, foreign_keys=connection_node_start_id)

    connection_node_end_id = Column(
            'connection_node_end_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_end = relationship(
            ConnectionNode, foreign_keys=connection_node_end_id)

    # crest level and cross section
    crest_type = Column(Integer)  # CREST_TYPE
    crest_level = Column(Float)

    cross_section_definition_id = Column(
            Integer, ForeignKey("v2_cross_section_definition.id"),
            nullable=True)
    cross_section_definition = relationship("CrossSectionDefinition")

    # friction and flow direction
    friction_value = Column(Float)
    friction_type = Column(Integer)  # FRICTION_TYPES
    discharge_coefficient_positive = Column(Float)
    discharge_coefficient_negative = Column(Float)

    sewerage = Column(Boolean)
    external = Column(Boolean)


class Orifice(Base):

    __tablename__ = 'v2_orifice'

    CREST_TYPES = Constants.CREST_TYPES
    FRICTION_TYPES = Constants.FRICTION_TYPES

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')
    zoom_category = Column(Integer, nullable=True)  # default=2

    # node relations
    connection_node_start_id = Column(
            'connection_node_start_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_start = relationship(
            ConnectionNode, foreign_keys=connection_node_start_id)

    connection_node_end_id = Column(
            'connection_node_end_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_end = relationship(
            ConnectionNode, foreign_keys=connection_node_end_id)

    # crest and cross section
    crest_type = Column(Integer)  # CREST_TYPES
    crest_level = Column(Float)

    cross_section_definition_id = Column(
            Integer, ForeignKey("v2_cross_section_definition.id"),
            nullable=True)
    cross_section_definition = relationship("CrossSectionDefinition")

    # friction and flow direction
    friction_value = Column(Float)
    friction_type = Column(Integer)  # FRICTION_TYPES
    discharge_coefficient_positive = Column(Float)
    discharge_coefficient_negative = Column(Float)

    sewerage = Column(Boolean, default=False)
    max_capacity = Column(Float)

    @property
    def max_capacity_str(self):
        if self.max_capacity is None:
            max_capacity_rep = "-- [m3/s]"
        else:
            max_capacity_rep = '%0.1f [m3/s]' % self.max_capacity
        return max_capacity_rep


class Pumpstation(Base):

    __tablename__ = 'v2_pumpstation'

    id = Column(Integer, primary_key=True)
    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')
    zoom_category = Column(Integer, nullable=True)

    sewerage = Column(Boolean, default=False)
    classification = Column(Integer)  # in use?

    # relation ships
    connection_node_start_id = Column(
            'connection_node_start_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_start = relationship(
            ConnectionNode, foreign_keys=connection_node_start_id)

    connection_node_end_id = Column(
            'connection_node_end_id',
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=True)
    connection_node_end = relationship(
            ConnectionNode, foreign_keys=connection_node_end_id)

    # pump details
    start_level_delivery_side = Column(Float)
    stop_level_delivery_side = Column(Float)
    start_level_suction_side = Column(Float)
    stop_level_suction_side = Column(Float)
    capacity = Column(Float)


class Obstacle(Base):
    __tablename__ = 'v2_levee'

    id = Column(Integer, primary_key=True)
    _code = Column(String(100), nullable=True)  # extra

    crest_level = Column(Float)
    the_geom = Column(Geometry(geometry_type='LINESTRING',
                               srid=4326,
                               spatial_index=True),
                      nullable=True)


class Levee(Base):
    __tablename__ = 'v2_obstacle'

    LEVEE_MATERIALS = Constants.LEVEE_MATERIALS

    id = Column(Integer, primary_key=True)
    _code = Column(String(100), nullable=True)  # extra

    crest_level = Column(Float)
    the_geom = Column(Geometry(geometry_type='LINESTRING',
                               srid=4326,
                               spatial_index=True),
                      nullable=True)

    material = Column(Integer)
    max_breach_depth = Column(Float)


class ImperviousSurface(Base):

    __tablename__ = 'v2_impervious_surface'

    id = Column(Integer, primary_key=True)

    code = Column(String(100), nullable=False)
    display_name = Column(String(255), nullable=False, default='')

    surface_inclination = Column(String(64), nullable=False)
    surface_class = Column(String(128), nullable=False)
    surface_sub_class = Column(String(128), nullable=True)
    function_ = Column(String(64), name="function", nullable=True)

    zoom_category = Column(Integer)
    nr_of_inhabitants = Column(Float)
    area = Column(Float)
    dry_weather_flow = Column(Float)

    the_geom = Column(Geometry(geometry_type="POLYGON",
                               srid=4326,
                               spatial_index=True),
                      nullable=True)

    impervious_surface_maps = relationship("ImperviousSurfaceMap",
                                           back_populates="impervious_surface")


class ImperviousSurfaceMap(Base):
    __tablename__ = 'v2_impervious_surface_map'

    id = Column(Integer, primary_key=True)

    impervious_surface_id = Column(
            Integer,
            ForeignKey(ImperviousSurface.__tablename__ + ".id"),
            nullable=True)
    impervious_surface = relationship(ImperviousSurface,
                                      back_populates="impervious_surface_maps")

    connection_node_id = Column(
            Integer,
            ForeignKey(ConnectionNode.__tablename__ + ".id"),
            nullable=False)
    connection_node = relationship(ConnectionNode,
                                   back_populates="impervious_surface_map")

    percentage = Column(Float)


# todo: add windshielding, 2d boundary_conditions, floodfill, grid refinement, initial_waterlevel
# 2dlateral, v2 pumpeddrainagearea