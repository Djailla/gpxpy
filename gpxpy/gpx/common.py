from collections import namedtuple

from gpxpy import gpxfield as mod_gpxfield


# Fields used for all point elements (route point, track point, waypoint):
GPX_10_POINT_FIELDS = [
    mod_gpxfield.GPXField('latitude', attribute='lat', type=mod_gpxfield.FLOAT_TYPE, mandatory=True),
    mod_gpxfield.GPXField('longitude', attribute='lon', type=mod_gpxfield.FLOAT_TYPE, mandatory=True),
    mod_gpxfield.GPXField('elevation', 'ele', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('time', type=mod_gpxfield.TIME_TYPE),
    mod_gpxfield.GPXField('magnetic_variation', 'magvar', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('geoid_height', 'geoidheight', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('name'),
    mod_gpxfield.GPXField('comment', 'cmt'),
    mod_gpxfield.GPXField('description', 'desc'),
    mod_gpxfield.GPXField('source', 'src'),
    mod_gpxfield.GPXField('link', 'url'),
    mod_gpxfield.GPXField('link_text', 'urlname'),
    mod_gpxfield.GPXField('symbol', 'sym'),
    mod_gpxfield.GPXField('type'),
    mod_gpxfield.GPXField('type_of_gpx_fix', 'fix', possible=('none', '2d', '3d', 'dgps', 'pps',)),
    mod_gpxfield.GPXField('satellites', 'sat', type=mod_gpxfield.INT_TYPE),
    mod_gpxfield.GPXField('horizontal_dilution', 'hdop', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('vertical_dilution', 'vdop', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('position_dilution', 'pdop', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('age_of_dgps_data', 'ageofdgpsdata', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('dgps_id', 'dgpsid'),
]
GPX_11_POINT_FIELDS = [
    # See GPX for description of text fields
    mod_gpxfield.GPXField('latitude', attribute='lat', type=mod_gpxfield.FLOAT_TYPE, mandatory=True),
    mod_gpxfield.GPXField('longitude', attribute='lon', type=mod_gpxfield.FLOAT_TYPE, mandatory=True),
    mod_gpxfield.GPXField('elevation', 'ele', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('time', type=mod_gpxfield.TIME_TYPE),
    mod_gpxfield.GPXField('magnetic_variation', 'magvar', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('geoid_height', 'geoidheight', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('name'),
    mod_gpxfield.GPXField('comment', 'cmt'),
    mod_gpxfield.GPXField('description', 'desc'),
    mod_gpxfield.GPXField('source', 'src'),
    'link:@link',
    mod_gpxfield.GPXField('link', attribute='href'),
    mod_gpxfield.GPXField('link_text', tag='text'),
    mod_gpxfield.GPXField('link_type', tag='type'),
    '/link',
    mod_gpxfield.GPXField('symbol', 'sym'),
    mod_gpxfield.GPXField('type'),
    mod_gpxfield.GPXField('type_of_gpx_fix', 'fix', possible=('none', '2d', '3d', 'dgps', 'pps',)),
    mod_gpxfield.GPXField('satellites', 'sat', type=mod_gpxfield.INT_TYPE),
    mod_gpxfield.GPXField('horizontal_dilution', 'hdop', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('vertical_dilution', 'vdop', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('position_dilution', 'pdop', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('age_of_dgps_data', 'ageofdgpsdata', type=mod_gpxfield.FLOAT_TYPE),
    mod_gpxfield.GPXField('dgps_id', 'dgpsid'),
    mod_gpxfield.GPXExtensionsField('extensions', is_list=True),
]

# When possible, the result of various methods are named tuples defined here:
TimeBounds = namedtuple(
    'TimeBounds',
    ('start_time', 'end_time'))
MovingData = namedtuple(
    'MovingData',
    ('moving_time', 'stopped_time', 'moving_distance', 'stopped_distance', 'max_speed'))
UphillDownhill = namedtuple(
    'UphillDownhill',
    ('uphill', 'downhill'))
MinimumMaximum = namedtuple(
    'MinimumMaximum',
    ('minimum', 'maximum'))
NearestLocationData = namedtuple(
    'NearestLocationData',
    ('location', 'track_no', 'segment_no', 'point_no'))
PointData = namedtuple(
    'PointData',
    ('point', 'distance_from_start', 'track_no', 'segment_no', 'point_no'))
