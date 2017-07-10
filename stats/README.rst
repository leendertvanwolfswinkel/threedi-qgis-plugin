Stats Changes
==============

The stats module supports generating the following variables:

Using ``flow_aggregate.nc``:

================  ================ =========================== ==============================
Variable          Layer type       Required parameter/field    Information
================  ================ =========================== ==============================
q_cum             structures                                   Net Volume across flowline structures
q_cum_positive    structures/pipes                             Total volume across flowline in positive drawing direction (ie. overstortvolume)
q_cum_positive    structures/pipes                             Total volume across flowline in negative drawing direction (ie. overstortvolume)
q_max             structures/pipes                             Maximum discharge across flowline (max discharge at strucutre)
q_min             structures                                   Minimum discharge across flowline (min discharge at strucutre)
s1_max            manholes         surface_level               WOS height -> s1_max - surface_level
s1_max            manholes                                     Maximum waterlevel at manhole
s1_max            manholes                                     Maximum waterdepth -> s1_max - bath (Check whether we write this to flow_aggregate.nc)
q_pump_cum        pumps                                        Total volume pumped by pump
================  ================ =========================== ==============================


Using ``subgrid_map.nc``:

=======================  ============== =============================================================
Variable                 Layer type     Information
=======================  ============== =============================================================
q(tend)                  structures     Discharge across structure at end of calculation
s1(tend)                 manholes       Waterlevel at manholes at end of calculation
=======================  ============== =============================================================

Important note: When ther is no aggregation netcdf we do not calculate statistics. Only exception can be flow variables at end of simulation (q_end and s1_end.)


***Duration statistics***

At the moment, it's not possible to accurately determine duration statistics, such as WOS duration and pumping duration and discharge duration at structures. With the information available now we can only determine the durations of variables with an error of maximally aggregate timestep or output timestep. If we want to accurately determine duration statistics this is a new feature to develop! 