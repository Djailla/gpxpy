from gpxpy import geo as mod_geo
from gpxpy import gpxfield as mod_gpxfield
from gpxpy import utils as mod_utils
from gpxpy.gpx.common import GPX_10_POINT_FIELDS, GPX_11_POINT_FIELDS


# GPX1.0 track points have two more fields after time
# Note that this is not true for GPX1.1
GPX_TRACK_POINT_FIELDS = (
    GPX_10_POINT_FIELDS[:4] + [
        mod_gpxfield.GPXField('course', type=mod_gpxfield.FLOAT_TYPE),
        mod_gpxfield.GPXField('speed', type=mod_gpxfield.FLOAT_TYPE)
    ] + GPX_10_POINT_FIELDS[4:]
)


class GPXTrackPoint(mod_geo.Location):
    gpx_10_fields = GPX_TRACK_POINT_FIELDS
    gpx_11_fields = GPX_11_POINT_FIELDS

    __slots__ = ('latitude', 'longitude', 'elevation', 'time', 'course',
                 'speed', 'magnetic_variation', 'geoid_height', 'name',
                 'comment', 'description', 'source', 'link', 'link_text',
                 'symbol', 'type', 'type_of_gpx_fix', 'satellites',
                 'horizontal_dilution', 'vertical_dilution',
                 'position_dilution', 'age_of_dgps_data', 'dgps_id',
                 'link_type', 'extensions')

    def __init__(self, latitude=None, longitude=None, elevation=None, time=None, symbol=None, comment=None,
                 horizontal_dilution=None, vertical_dilution=None, position_dilution=None, speed=None,
                 name=None):
        mod_geo.Location.__init__(self, latitude, longitude, elevation)
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        self.time = time
        self.course = None
        self.speed = speed
        self.magnetic_variation = None
        self.geoid_height = None
        self.name = name
        self.comment = comment
        self.description = None
        self.source = None
        self.link = None
        self.link_text = None
        self.link_type = None
        self.symbol = symbol
        self.type = None
        self.type_of_gpx_fix = None
        self.satellites = None
        self.horizontal_dilution = horizontal_dilution
        self.vertical_dilution = vertical_dilution
        self.position_dilution = position_dilution
        self.age_of_dgps_data = None
        self.dgps_id = None
        self.extensions = []

    def __repr__(self):
        representation = '%s, %s' % (self.latitude, self.longitude)
        attributes = [
            'elevation', 'time', 'symbol', 'comment', 'horizontal_dilution',
            'vertical_dilution', 'position_dilution', 'speed', 'name',
        ]
        for attribute in attributes:
            value = getattr(self, attribute)
            if value is not None:
                representation += ', %s=%s' % (attribute, repr(value))
        return 'GPXTrackPoint(%s)' % representation

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

    def time_difference(self, track_point):
        """
        Get time difference between specified point and this point.

        Parameters
        ----------
        track_point : GPXTrackPoint

        Returns
        ----------
        time_difference : float
            Time difference returned in seconds
        """
        if not self.time or not track_point or not track_point.time:
            return None

        time_1 = self.time
        time_2 = track_point.time

        if time_1 == time_2:
            return 0

        if time_1 > time_2:
            delta = time_1 - time_2
        else:
            delta = time_2 - time_1

        return mod_utils.total_seconds(delta)

    def speed_between(self, track_point):
        """
        Compute the speed between specified point and this point.

        NOTE: This is a computed speed, not the GPXTrackPoint speed that comes
              the GPX file.

        Parameters
        ----------
        track_point : GPXTrackPoint

        Returns
        ----------
        speed : float
            Speed returned in meters/second
        """
        if not track_point:
            return None

        seconds = self.time_difference(track_point)
        length = self.distance_3d(track_point)
        if not length:
            length = self.distance_2d(track_point)

        if not seconds or length is None:
            return None

        return length / float(seconds)

    def __str__(self):
        return '[trkpt:%s,%s@%s@%s]' % (self.latitude, self.longitude, self.elevation, self.time)
