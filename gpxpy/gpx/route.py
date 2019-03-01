from gpxpy import geo as mod_geo
from gpxpy import gpxfield as mod_gpxfield
from gpxpy.gpx.route_point import GPXRoutePoint


class GPXRoute:
    gpx_10_fields = [
        mod_gpxfield.GPXField('name'),
        mod_gpxfield.GPXField('comment', 'cmt'),
        mod_gpxfield.GPXField('description', 'desc'),
        mod_gpxfield.GPXField('source', 'src'),
        mod_gpxfield.GPXField('link', 'url'),
        mod_gpxfield.GPXField('link_text', 'urlname'),
        mod_gpxfield.GPXField('number', type=mod_gpxfield.INT_TYPE),
        mod_gpxfield.GPXComplexField('points', tag='rtept', classs=GPXRoutePoint, is_list=True),
    ]
    gpx_11_fields = [
        # See GPX for description of text fields
        mod_gpxfield.GPXField('name'),
        mod_gpxfield.GPXField('comment', 'cmt'),
        mod_gpxfield.GPXField('description', 'desc'),
        mod_gpxfield.GPXField('source', 'src'),
        'link:@link',
        mod_gpxfield.GPXField('link', attribute='href'),
        mod_gpxfield.GPXField('link_text', tag='text'),
        mod_gpxfield.GPXField('link_type', tag='type'),
        '/link',
        mod_gpxfield.GPXField('number', type=mod_gpxfield.INT_TYPE),
        mod_gpxfield.GPXField('type'),
        mod_gpxfield.GPXExtensionsField('extensions', is_list=True),
        mod_gpxfield.GPXComplexField('points', tag='rtept', classs=GPXRoutePoint, is_list=True),
    ]

    __slots__ = ('name', 'comment', 'description', 'source', 'link',
                 'link_text', 'number', 'points', 'link_type', 'type',
                 'extensions')

    def __init__(self, name=None, description=None, number=None):
        self.name = name
        self.comment = None
        self.description = description
        self.source = None
        self.link = None
        self.link_text = None
        self.number = number
        self.points = []
        self.link_type = None
        self.type = None
        self.extensions = []

    def adjust_time(self, delta):
        """
        Adjusts the time of the all the points in the route by the specified delta.

        Parameters
        ----------
        delta : datetime.timedelta
            Positive time delta will adjust time into the future
            Negative time delta will adjust time into the past
        """
        for point in self.points:
            point.adjust_time(delta)

    def remove_time(self):
        """ Removes time meta data from route. """
        for point in self.points:
            point.remove_time()

    def remove_elevation(self):
        """ Removes elevation data from route """
        for point in self.points:
            point.remove_elevation()

    def length(self):
        """
        Computes length (2-dimensional) of route.

        Returns:
        -----------
        length: float
            Length returned in meters
        """
        return mod_geo.length_2d(self.points)

    def get_center(self):
        """
        Get the center of the route.

        Returns
        -------
        center: Location
            latitude: latitude of center in degrees
            longitude: longitude of center in degrees
            elevation: not calculated here
        """
        if not self.points:
            return None

        if not self.points:
            return None

        sum_lat = 0.
        sum_lon = 0.
        n = 0.

        for point in self.points:
            n += 1.
            sum_lat += point.latitude
            sum_lon += point.longitude

        if not n:
            return mod_geo.Location(float(0), float(0))

        return mod_geo.Location(latitude=sum_lat / n, longitude=sum_lon / n)

    def walk(self, only_points=False):
        """
        Generator for iterating over route points

        Parameters
        ----------
        only_points: boolean
            Only yield points (no index yielded)

        Yields
        ------
        point: GPXRoutePoint
            A point in the GPXRoute
        point_no: int
            Not included in yield if only_points is true
        """
        for point_no, point in enumerate(self.points):
            if only_points:
                yield point
            else:
                yield point, point_no

    def get_points_no(self):
        """
        Get the number of points in route.

        Returns
        ----------
        num_points : integer
            Number of points in route
        """
        return len(self.points)

    def move(self, location_delta):
        """
        Moves each point in the route.

        Parameters
        ----------
        location_delta: LocationDelta
            LocationDelta to move each point
        """
        for route_point in self.points:
            route_point.move(location_delta)

    def __repr__(self):
        representation = ''
        for attribute in 'name', 'description', 'number':
            value = getattr(self, attribute)
            if value is not None:
                representation += '%s%s=%s' % (', ' if representation else '', attribute, repr(value))
        representation += '%spoints=[%s])' % (', ' if representation else '', '...' if self.points else '')
        return 'GPXRoute(%s)' % representation
