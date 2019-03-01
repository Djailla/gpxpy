from copy import deepcopy
import datetime as mod_datetime
from math import ceil

from gpxpy import utils as mod_utils
from gpxpy import gpxfield as mod_gpxfield

from gpxpy.gpx.exceptions import GPXException
from gpxpy.gpx.route import GPXRoute
from gpxpy.gpx.waypoint import GPXWaypoint
from gpxpy.gpx.track import GPXTrack
from gpxpy.gpx.bounds import GPXBounds
from gpxpy.gpx.common import MinimumMaximum, MovingData, TimeBounds, UphillDownhill, NearestLocationData, PointData


class GPX:
    gpx_10_fields = [
        mod_gpxfield.GPXField('version', attribute=True),
        mod_gpxfield.GPXField('creator', attribute=True),
        mod_gpxfield.GPXField('name'),
        mod_gpxfield.GPXField('description', 'desc'),
        mod_gpxfield.GPXField('author_name', 'author'),
        mod_gpxfield.GPXField('author_email', 'email'),
        mod_gpxfield.GPXField('link', 'url'),
        mod_gpxfield.GPXField('link_text', 'urlname'),
        mod_gpxfield.GPXField('time', type=mod_gpxfield.TIME_TYPE),
        mod_gpxfield.GPXField('keywords'),
        mod_gpxfield.GPXComplexField('bounds', classs=GPXBounds),
        mod_gpxfield.GPXComplexField('waypoints', classs=GPXWaypoint, tag='wpt', is_list=True),
        mod_gpxfield.GPXComplexField('routes', classs=GPXRoute, tag='rte', is_list=True),
        mod_gpxfield.GPXComplexField('tracks', classs=GPXTrack, tag='trk', is_list=True),
    ]
    # Text fields serialize as empty container tags, dependents are
    # are listed after as 'tag:dep1:dep2:dep3'. If no dependents are
    # listed, it will always serialize. The container is closed with
    # '/tag'. Required dependents are preceded by an @. If a required
    # dependent is empty, nothing in the container will serialize. The
    # format is 'tag:@dep2'. No optional dependents need to be listed.
    # Extensions not yet supported
    gpx_11_fields = [
        mod_gpxfield.GPXField('version', attribute=True),
        mod_gpxfield.GPXField('creator', attribute=True),
        'metadata:name:description:author_name:author_email:author_link:copyright_author:copyright_year:copyright_license:link:time:keywords:bounds',
        mod_gpxfield.GPXField('name', 'name'),
        mod_gpxfield.GPXField('description', 'desc'),
        'author:author_name:author_email:author_link',
        mod_gpxfield.GPXField('author_name', 'name'),
        mod_gpxfield.GPXEmailField('author_email', 'email'),
        'link:@author_link',
        mod_gpxfield.GPXField('author_link', attribute='href'),
        mod_gpxfield.GPXField('author_link_text', tag='text'),
        mod_gpxfield.GPXField('author_link_type', tag='type'),
        '/link',
        '/author',
        'copyright:copyright_author:copyright_year:copyright_license',
        mod_gpxfield.GPXField('copyright_author', attribute='author'),
        mod_gpxfield.GPXField('copyright_year', tag='year'),
        mod_gpxfield.GPXField('copyright_license', tag='license'),
        '/copyright',
        'link:@link',
        mod_gpxfield.GPXField('link', attribute='href'),
        mod_gpxfield.GPXField('link_text', tag='text'),
        mod_gpxfield.GPXField('link_type', tag='type'),
        '/link',
        mod_gpxfield.GPXField('time', type=mod_gpxfield.TIME_TYPE),
        mod_gpxfield.GPXField('keywords'),
        mod_gpxfield.GPXComplexField('bounds', classs=GPXBounds),
        mod_gpxfield.GPXExtensionsField('metadata_extensions', tag='extensions'),
        '/metadata',
        mod_gpxfield.GPXComplexField('waypoints', classs=GPXWaypoint, tag='wpt', is_list=True),
        mod_gpxfield.GPXComplexField('routes', classs=GPXRoute, tag='rte', is_list=True),
        mod_gpxfield.GPXComplexField('tracks', classs=GPXTrack, tag='trk', is_list=True),
        mod_gpxfield.GPXExtensionsField('extensions', is_list=True),
    ]

    __slots__ = ('version', 'creator', 'name', 'description', 'author_name',
                 'author_email', 'link', 'link_text', 'time', 'keywords',
                 'bounds', 'waypoints', 'routes', 'tracks', 'author_link',
                 'author_link_text', 'author_link_type', 'copyright_author',
                 'copyright_year', 'copyright_license', 'link_type',
                 'metadata_extensions', 'extensions', 'nsmap',
                 'schema_locations')

    def __init__(self):
        self.version = None
        self.creator = None
        self.name = None
        self.description = None
        self.link = None
        self.link_text = None
        self.link_type = None
        self.time = None
        self.keywords = None
        self.bounds = None
        self.author_name = None
        self.author_email = None
        self.author_link = None
        self.author_link_text = None
        self.author_link_type = None
        self.copyright_author = None
        self.copyright_year = None
        self.copyright_license = None
        self.metadata_extensions = []
        self.extensions = []
        self.waypoints = []
        self.routes = []
        self.tracks = []
        self.nsmap = {}
        self.schema_locations = []

    def simplify(self, max_distance=None):
        """
        Simplify using the Ramer-Douglas-Peucker algorithm:
        http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm
        """
        for track in self.tracks:
            track.simplify(max_distance=max_distance)

    def reduce_points(self, max_points_no=None, min_distance=None):
        """
        Reduces the number of points. Points will be updated in place.

        Parameters
        ----------

        max_points : int
            The maximum number of points to include in the GPX
        min_distance : float
            The minimum separation in meters between points
        """
        if max_points_no is None and min_distance is None:
            raise ValueError("Either max_point_no or min_distance must be supplied")

        if max_points_no is not None and max_points_no < 2:
            raise ValueError("max_points_no must be greater than or equal to 2")

        points_no = len(list(self.walk()))
        if max_points_no is not None and points_no <= max_points_no:
            # No need to reduce points only if no min_distance is specified:
            if not min_distance:
                return

        length = self.length_3d()

        min_distance = min_distance or 0
        max_points_no = max_points_no or 1000000000

        min_distance = max(min_distance, ceil(length / float(max_points_no)))

        for track in self.tracks:
            track.reduce_points(min_distance)

        # TODO
        # log.debug('Track reduced to %s points' % self.get_track_points_no())

    def adjust_time(self, delta, all=False):
        """
        Adjusts the time of all points in all of the segments of all tracks by
        the specified delta.

        If all=True, waypoints and routes will also be adjusted by the specified delta.

        Parameters
        ----------
        delta : datetime.timedelta
            Positive time delta will adjust times into the future
            Negative time delta will adjust times into the past
        all : bool
            When true, also adjusts time for waypoints and routes.
        """
        if self.time:
            self.time += delta
        for track in self.tracks:
            track.adjust_time(delta)

        if all:
            for waypoint in self.waypoints:
                waypoint.adjust_time(delta)
            for route in self.routes:
                route.adjust_time(delta)

    def remove_time(self, all=False):
        """
        Removes time data of all points in all of the segments of all tracks.

        If all=True, time date will also be removed from waypoints and routes.

        Parameters
        ----------
        all : bool
            When true, also removes time data for waypoints and routes.
        """
        for track in self.tracks:
            track.remove_time()

        if all:
            for waypoint in self.waypoints:
                waypoint.remove_time()
            for route in self.routes:
                route.remove_time()

    def remove_elevation(self, tracks=True, routes=False, waypoints=False):
        """ Removes elevation data. """
        if tracks:
            for track in self.tracks:
                track.remove_elevation()
        if routes:
            for route in self.routes:
                route.remove_elevation()
        if waypoints:
            for waypoint in self.waypoints:
                waypoint.remove_elevation()

    def get_time_bounds(self):
        """
        Gets the time bounds (start and end) of the GPX file.

        Returns
        ----------
        time_bounds : TimeBounds named tuple
            start_time : datetime
                Start time of the first segment in track
            end time : datetime
                End time of the last segment in track
        """
        start_time = None
        end_time = None

        for track in self.tracks:
            track_start_time, track_end_time = track.get_time_bounds()
            if not start_time:
                start_time = track_start_time
            if track_end_time:
                end_time = track_end_time

        return TimeBounds(start_time, end_time)

    def get_bounds(self):
        """
        Gets the latitude and longitude bounds of the GPX file.

        Returns
        ----------
        bounds : Bounds named tuple
            min_latitude : float
                Minimum latitude of track in decimal degrees [-90, 90]
            max_latitude : float
                Maximum latitude of track in decimal degrees [-90, 90]
            min_longitude : float
                Minimum longitude of track in decimal degrees [-180, 180]
            max_longitude : float
                Maximum longitude of track in decimal degrees [-180, 180]
        """
        min_lat = None
        max_lat = None
        min_lon = None
        max_lon = None
        for track in self.tracks:
            bounds = track.get_bounds()

            if not mod_utils.is_numeric(min_lat) or bounds.min_latitude < min_lat:
                min_lat = bounds.min_latitude
            if not mod_utils.is_numeric(max_lat) or bounds.max_latitude > max_lat:
                max_lat = bounds.max_latitude
            if not mod_utils.is_numeric(min_lon) or bounds.min_longitude < min_lon:
                min_lon = bounds.min_longitude
            if not mod_utils.is_numeric(max_lon) or bounds.max_longitude > max_lon:
                max_lon = bounds.max_longitude

        return GPXBounds(min_lat, max_lat, min_lon, max_lon)

    def get_points_no(self):
        """
        Get the number of points in all segments of all track.

        Returns
        ----------
        num_points : integer
            Number of points in GPX
        """
        result = 0
        for track in self.tracks:
            result += track.get_points_no()
        return result

    def refresh_bounds(self):
        """
        Compute bounds and reload min_latitude, max_latitude, min_longitude
        and max_longitude properties of this object
        """

        bounds = self.get_bounds()

        self.bounds = bounds

    def smooth(self, vertical=True, horizontal=False, remove_extremes=False):
        """ See GPXTrackSegment.smooth(...) """
        for track in self.tracks:
            track.smooth(vertical=vertical, horizontal=horizontal, remove_extremes=remove_extremes)

    def remove_empty(self):
        """ Removes segments, routes """

        routes = []

        for route in self.routes:
            if len(route.points) > 0:
                routes.append(route)

        self.routes = routes

        for track in self.tracks:
            track.remove_empty()

    def get_moving_data(self, stopped_speed_threshold=None):
        """
        Return a tuple of (moving_time, stopped_time, moving_distance, stopped_distance, max_speed)
        that may be used for detecting the time stopped, and max speed. Not that those values are not
        absolutely true, because the "stopped" or "moving" information aren't saved in the track.

        Because of errors in the GPS recording, it may be good to calculate them on a reduced and
        smoothed version of the track. Something like this:

        cloned_gpx = gpx.clone()
        cloned_gpx.reduce_points(2000, min_distance=10)
        cloned_gpx.smooth(vertical=True, horizontal=True)
        cloned_gpx.smooth(vertical=True, horizontal=False)
        moving_time, stopped_time, moving_distance, stopped_distance, max_speed_ms = cloned_gpx.get_moving_data
        max_speed_kmh = max_speed_ms * 60. ** 2 / 1000.

        Experiment with your own variations to get the values you expect.

        Max speed is in m/s.
        """
        moving_time = 0.
        stopped_time = 0.

        moving_distance = 0.
        stopped_distance = 0.

        max_speed = 0.

        for track in self.tracks:
            track_moving_time, track_stopped_time, track_moving_distance, track_stopped_distance, track_max_speed = track.get_moving_data(stopped_speed_threshold)
            moving_time += track_moving_time
            stopped_time += track_stopped_time
            moving_distance += track_moving_distance
            stopped_distance += track_stopped_distance

            if track_max_speed > max_speed:
                max_speed = track_max_speed

        return MovingData(moving_time, stopped_time, moving_distance, stopped_distance, max_speed)

    def split(self, track_no, track_segment_no, track_point_no):
        """
        Splits one of the segments of a track in two parts. If one of the
        split segments is empty it will not be added in the result. The
        segments will be split in place.

        Parameters
        ----------
        track_no : integer
            The index of the track to split
        track_segment_no : integer
            The index of the segment to split
        track_point_no : integer
            The index of the track point in the segment to split
        """
        track = self.tracks[track_no]

        track.split(track_segment_no=track_segment_no, track_point_no=track_point_no)

    def length_2d(self):
        """
        Computes 2-dimensional length of the GPX file (only latitude and
        longitude, no elevation). This is the sum of 2D length of all segments
        in all tracks.

        Returns
        ----------
        length : float
            Length returned in meters
        """
        result = 0
        for track in self.tracks:
            length = track.length_2d()
            if length:
                result += length
        return result

    def length_3d(self):
        """
        Computes 3-dimensional length of the GPX file (latitude, longitude, and
        elevation). This is the sum of 3D length of all segments in all tracks.

        Returns
        ----------
        length : float
            Length returned in meters
        """
        result = 0
        for track in self.tracks:
            length = track.length_3d()
            if length:
                result += length
        return result

    def walk(self, only_points=False):
        """
        Generator used to iterates through points in GPX file

        Parameters
        ----------
        only_point s: boolean
            Only yield points while walking

        Yields
        ----------
        point : GPXTrackPoint
            Point in the track
        track_no : integer
            Index of track containint point. This is suppressed if only_points
            is True.
        segment_no : integer
            Index of segment containint point. This is suppressed if only_points
            is True.
        point_no : integer
            Index of point. This is suppressed if only_points is True.
        """
        for track_no, track in enumerate(self.tracks):
            for segment_no, segment in enumerate(track.segments):
                for point_no, point in enumerate(segment.points):
                    if only_points:
                        yield point
                    else:
                        yield point, track_no, segment_no, point_no

    def get_track_points_no(self):
        """ Number of track points, *without* route and waypoints """
        result = 0

        for track in self.tracks:
            for segment in track.segments:
                result += len(segment.points)

        return result

    def get_duration(self):
        """
        Calculates duration of GPX file

        Returns
        -------
        duration: float
            Duration in seconds or None if time data is not fully populated.
        """
        if not self.tracks:
            return 0

        result = 0
        for track in self.tracks:
            duration = track.get_duration()
            if duration or duration == 0:
                result += duration
            elif duration is None:
                return None

        return result

    def get_uphill_downhill(self):
        """
        Calculates the uphill and downhill elevation climbs for the gpx file.
        If elevation for some points is not found those are simply ignored.

        Returns
        -------
        uphill_downhill: UphillDownhill named tuple
            uphill: float
                Uphill elevation climbs in meters
            downhill: float
                Downhill elevation descent in meters
        """
        if not self.tracks:
            return UphillDownhill(0, 0)

        uphill = 0
        downhill = 0

        for track in self.tracks:
            current_uphill, current_downhill = track.get_uphill_downhill()

            uphill += current_uphill
            downhill += current_downhill

        return UphillDownhill(uphill, downhill)

    def get_location_at(self, time):
        """
        Gets approx. location at given time. Note that, at the moment this
        method returns an instance of GPXTrackPoint in the future -- this may
        be a mod_geo.Location instance with approximated latitude, longitude
        and elevation!
        """
        result = []
        for track in self.tracks:
            locations = track.get_location_at(time)
            for location in locations:
                result.append(location)

        return result

    def get_elevation_extremes(self):
        """
        Calculate elevation extremes of GPX file

        Returns
        -------
        min_max_elevation: MinimumMaximum named tuple
            minimum: float
                Minimum elevation in meters
            maximum: float
                Maximum elevation in meters
        """
        if not self.tracks:
            return MinimumMaximum(None, None)

        elevations = []

        for track in self.tracks:
            (_min, _max) = track.get_elevation_extremes()
            if _min is not None:
                elevations.append(_min)
            if _max is not None:
                elevations.append(_max)

        if len(elevations) == 0:
            return MinimumMaximum(None, None)

        return MinimumMaximum(min(elevations), max(elevations))

    def get_points_data(self, distance_2d=False):
        """
        Returns a list of tuples containing the actual point, its distance from the start,
        track_no, segment_no, and segment_point_no
        """
        distance_from_start = 0
        previous_point = None

        # (point, distance_from_start) pairs:
        points = []

        for track_no in range(len(self.tracks)):
            track = self.tracks[track_no]
            for segment_no in range(len(track.segments)):
                segment = track.segments[segment_no]
                for point_no in range(len(segment.points)):
                    point = segment.points[point_no]
                    if previous_point and point_no > 0:
                        if distance_2d:
                            distance = point.distance_2d(previous_point)
                        else:
                            distance = point.distance_3d(previous_point)

                        distance_from_start += distance

                    points.append(PointData(point, distance_from_start, track_no, segment_no, point_no))

                    previous_point = point

        return points

    def get_nearest_locations(self, location, threshold_distance=0.01):
        """
        Returns a list of locations of elements like
        consisting of points where the location may be on the track

        threshold_distance is the minimum distance from the track
        so that the point *may* be counted as to be "on the track".
        For example 0.01 means 1% of the track distance.
        """

        assert location
        assert threshold_distance

        result = []

        points = self.get_points_data()

        if not points:
            return ()

        distance = points[- 1][1]

        threshold = distance * threshold_distance

        min_distance_candidate = None
        distance_from_start_candidate = None
        track_no_candidate = None
        segment_no_candidate = None
        point_no_candidate = None

        for point, distance_from_start, track_no, segment_no, point_no in points:
            distance = location.distance_3d(point)
            if distance < threshold:
                if min_distance_candidate is None or distance < min_distance_candidate:
                    min_distance_candidate = distance
                    distance_from_start_candidate = distance_from_start
                    track_no_candidate = track_no
                    segment_no_candidate = segment_no
                    point_no_candidate = point_no
            else:
                if distance_from_start_candidate is not None:
                    result.append((distance_from_start_candidate, track_no_candidate, segment_no_candidate, point_no_candidate))
                min_distance_candidate = None
                distance_from_start_candidate = None
                track_no_candidate = None
                segment_no_candidate = None
                point_no_candidate = None

        if distance_from_start_candidate is not None:
            result.append(NearestLocationData(distance_from_start_candidate, track_no_candidate, segment_no_candidate, point_no_candidate))

        return result

    def get_nearest_location(self, location):
        """ Returns (location, track_no, track_segment_no, track_point_no) for the
        nearest location on map """
        if not self.tracks:
            return None

        result = None
        distance = None
        result_track_no = None
        result_segment_no = None
        result_point_no = None
        for i in range(len(self.tracks)):
            track = self.tracks[i]
            nearest_location, track_segment_no, track_point_no = track.get_nearest_location(location)
            nearest_location_distance = None
            if nearest_location:
                nearest_location_distance = nearest_location.distance_2d(location)
            if not distance or nearest_location_distance < distance:
                result = nearest_location
                distance = nearest_location_distance
                result_track_no = i
                result_segment_no = track_segment_no
                result_point_no = track_point_no

        return NearestLocationData(result, result_track_no, result_segment_no, result_point_no)

    def add_elevation(self, delta):
        """
        Adjusts elevation data of GPX data.

        Parameters
        ----------
        delta : float
            Elevation delta in meters to apply to GPX data
        """
        for track in self.tracks:
            track.add_elevation(delta)

    def add_missing_data(self, get_data_function, add_missing_function):
        for track in self.tracks:
            track.add_missing_data(get_data_function, add_missing_function)

    def add_missing_elevations(self):
        def _add(interval, start, end, distances_ratios):
            if (start.elevation is None) or (end.elevation is None):
                return
            assert start
            assert end
            assert interval
            assert len(interval) == len(distances_ratios)
            for i in range(len(interval)):
                interval[i].elevation = start.elevation + distances_ratios[i] * (end.elevation - start.elevation)

        self.add_missing_data(get_data_function=lambda point: point.elevation,
                              add_missing_function=_add)

    def add_missing_times(self):
        def _add(interval, start, end, distances_ratios):
            if (not start) or (not end) or (not start.time) or (not end.time):
                return
            assert interval
            assert len(interval) == len(distances_ratios)

            seconds_between = float(mod_utils.total_seconds(end.time - start.time))

            for i in range(len(interval)):
                point = interval[i]
                ratio = distances_ratios[i]
                point.time = start.time + mod_datetime.timedelta(
                    seconds=ratio * seconds_between)

        self.add_missing_data(get_data_function=lambda point: point.time,
                              add_missing_function=_add)

    def add_missing_speeds(self):
        """
        The missing speeds are added to a segment.

        The weighted harmonic mean is used to approximate the speed at
        a :obj:'~.GPXTrackPoint'.
        For this to work the speed of the first and last track point in a
        segment needs to be known.
        """
        def _add(interval, start, end, distances_ratios):
            if (not start) or (not end) or (not start.time) or (not end.time):
                return
            assert interval
            assert len(interval) == len(distances_ratios)

            time_dist_before = (interval[0].time_difference(start),
                                interval[0].distance_3d(start))
            time_dist_after = (interval[-1].time_difference(end),
                               interval[-1].distance_3d(end))

            # Assemble list of times and distance to neighbour points
            times_dists = [(interval[i].time_difference(interval[i + 1]),
                            interval[i].distance_3d(interval[i + 1]))
                           for i in range(len(interval) - 1)]
            times_dists.insert(0, time_dist_before)
            times_dists.append(time_dist_after)

            for i, point in enumerate(interval):
                time_left, dist_left = times_dists[i]
                time_right, dist_right = times_dists[i + 1]
                point.speed = float(dist_left + dist_right) / (time_left + time_right)

        self.add_missing_data(get_data_function=lambda point: point.speed,
                              add_missing_function=_add)

    def fill_time_data_with_regular_intervals(self, start_time=None, time_delta=None, end_time=None, force=True):
        """
        Fills the time data for all points in the GPX file. At least two of the parameters start_time, time_delta, and
        end_time have to be provided. If the three are provided, time_delta will be ignored and will be recalculated
        using start_time and end_time.

        The first GPX point will have a time equal to start_time. Then points are assumed to be recorded at regular
        intervals time_delta.

        If the GPX file currently contains time data, it will be overwritten, unless the force flag is set to False, in
        which case the function will return a GPXException error.

        Parameters
        ----------
        start_time: datetime.datetime object
            Start time of the GPX file (corresponds to the time of the first point)
        time_delta: datetime.timedelta object
            Time interval between two points in the GPX file
        end_time: datetime.datetime object
            End time of the GPX file (corresponds to the time of the last point)
        force: bool
            Overwrite current data if the GPX file currently contains time data
        """
        if not (start_time and end_time) and not (start_time and time_delta) and not (time_delta and end_time):
            raise GPXException('You must provide at least two parameters among start_time, time_step, and end_time')

        if self.has_times() and not force:
            raise GPXException('GPX file currently contains time data. Use force=True to overwrite.')

        point_no = self.get_points_no()

        if start_time and end_time:
            if start_time > end_time:
                raise GPXException('Invalid parameters: end_time must occur after start_time')
            time_delta = (end_time - start_time) / (point_no - 1)
        elif not start_time:
            start_time = end_time - (point_no - 1) * time_delta

        self.time = start_time

        i = 0
        for point in self.walk(only_points=True):
            if i == 0:
                point.time = start_time
            else:
                point.time = start_time + i * time_delta
            i += 1

    def move(self, location_delta):
        """
        Moves each point in the gpx file (routes, waypoints, tracks).

        Parameters
        ----------
        location_delta: LocationDelta
            LocationDelta to move each point
        """
        for route in self.routes:
            route.move(location_delta)

        for waypoint in self.waypoints:
            waypoint.move(location_delta)

        for track in self.tracks:
            track.move(location_delta)

    def to_xml(self, version=None, prettyprint=True):
        """
        FIXME: Note, this method will change self.version
        """
        if not version:
            if self.version:
                version = self.version
            else:
                version = '1.1'

        if version != '1.0' and version != '1.1':
            raise GPXException('Invalid version %s' % version)

        self.version = version
        if not self.creator:
            self.creator = 'gpx.py -- https://github.com/tkrajina/gpxpy'

        self.nsmap['xsi'] = 'http://www.w3.org/2001/XMLSchema-instance'

        version_path = version.replace('.', '/')

        self.nsmap['defaultns'] = 'http://www.topografix.com/GPX/{0}'.format(
            version_path
        )

        if not self.schema_locations:
            self.schema_locations = [
                p.format(version_path) for p in (
                    'http://www.topografix.com/GPX/{0}',
                    'http://www.topografix.com/GPX/{0}/gpx.xsd',
                )
            ]

        content = mod_gpxfield.gpx_fields_to_xml(
            self, 'gpx', version,
            custom_attributes={
                'xsi:schemaLocation': ' '.join(self.schema_locations)
            },
            nsmap=self.nsmap,
            prettyprint=prettyprint
        )

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + content.strip()

    def has_times(self):
        """ See GPXTrackSegment.has_times() """
        if not self.tracks:
            return None

        result = True
        for track in self.tracks:
            result = result and track.has_times()

        return result

    def has_elevations(self):
        """ See GPXTrackSegment.has_elevations()) """
        if not self.tracks:
            return None

        result = True
        for track in self.tracks:
            result = result and track.has_elevations()

        return result

    def __repr__(self):
        representation = ''
        for attribute in 'waypoints', 'routes', 'tracks':
            value = getattr(self, attribute)
            if value:
                representation += '%s%s=%s' % (', ' if representation else '', attribute, repr(value))
        return 'GPX(%s)' % representation

    def clone(self):
        return deepcopy(self)
