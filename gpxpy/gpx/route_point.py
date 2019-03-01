from gpxpy import geo as mod_geo
from gpxpy.gpx.common import GPX_10_POINT_FIELDS, GPX_11_POINT_FIELDS


class GPXRoutePoint(mod_geo.Location):
    gpx_10_fields = GPX_10_POINT_FIELDS
    gpx_11_fields = GPX_11_POINT_FIELDS

    __slots__ = ('latitude', 'longitude', 'elevation', 'time',
                 'magnetic_variation', 'geoid_height', 'name', 'comment',
                 'description', 'source', 'link', 'link_text', 'symbol',
                 'type', 'type_of_gpx_fix', 'satellites',
                 'horizontal_dilution', 'vertical_dilution',
                 'position_dilution', 'age_of_dgps_data', 'dgps_id',
                 'link_type', 'extensions')

    def __init__(self, latitude=None, longitude=None, elevation=None, time=None, name=None,
                 description=None, symbol=None, type=None, comment=None,
                 horizontal_dilution=None, vertical_dilution=None,
                 position_dilution=None):

        mod_geo.Location.__init__(self, latitude, longitude, elevation)
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.time = time
        self.magnetic_variation = None
        self.geoid_height = None
        self.name = name
        self.comment = comment
        self.description = description
        self.source = None
        self.link = None
        self.link_text = None
        self.symbol = symbol
        self.type = type
        self.type_of_gpx_fix = None
        self.satellites = None
        self.horizontal_dilution = horizontal_dilution
        self.vertical_dilution = vertical_dilution
        self.position_dilution = position_dilution
        self.age_of_dgps_data = None
        self.dgps_id = None
        self.link_type = None
        self.extensions = []

    def __str__(self):
        return '[rtept{%s}:%s,%s@%s]' % (self.name, self.latitude, self.longitude, self.elevation)

    def __repr__(self):
        representation = '%s, %s' % (self.latitude, self.longitude)
        attributes = [
            'elevation', 'time', 'name', 'description', 'symbol', 'type',
            'comment', 'horizontal_dilution', 'vertical_dilution',
            'position_dilution',
        ]
        for attribute in attributes:
            value = getattr(self, attribute)
            if value is not None:
                representation += ', %s=%s' % (attribute, repr(value))
        return 'GPXRoutePoint(%s)' % representation

    def adjust_time(self, delta):
        """
        Adjusts the time of the point by the specified delta

        Parameters
        ----------
        delta : datetime.timedelta
            Positive time delta will adjust time into the future
            Negative time delta will adjust time into the past
        """
        if self.time:
            self.time += delta

    def remove_time(self):
        """ Will remove time metadata. """
        self.time = None
