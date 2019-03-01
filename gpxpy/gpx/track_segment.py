from copy import deepcopy

from gpxpy import geo as mod_geo
from gpxpy import gpxfield as mod_gpxfield
from gpxpy import utils as mod_utils

from gpxpy.gpx.common import MinimumMaximum, MovingData, TimeBounds, UphillDownhill
from gpxpy.gpx.exceptions import GPXException
from gpxpy.gpx.bounds import GPXBounds
from gpxpy.gpx.track_point import GPXTrackPoint

# Used in smoothing, sum must be 1:
SMOOTHING_RATIO = (0.4, 0.2, 0.4)

# When computing stopped time -- this is the minimum speed between two points,
# if speed is less than this value -- we'll assume it is zero
DEFAULT_STOPPED_SPEED_THRESHOLD = 1


class GPXTrackSegment:
    gpx_10_fields = [
        mod_gpxfield.GPXComplexField('points', tag='trkpt', classs=GPXTrackPoint, is_list=True),
    ]
    gpx_11_fields = [
        mod_gpxfield.GPXComplexField('points', tag='trkpt', classs=GPXTrackPoint, is_list=True),
        mod_gpxfield.GPXExtensionsField('extensions', is_list=True),
    ]

    __slots__ = ('points', 'extensions', )

    def __init__(self, points=None):
        self.points = points if points else []
        self.extensions = []

    def simplify(self, max_distance=None):
        """
        Simplify using the Ramer-Douglas-Peucker algorithm:
        http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm
        """
        if not max_distance:
            max_distance = 10

        self.points = mod_geo.simplify_polyline(self.points, max_distance)

    def reduce_points(self, min_distance):
        """
        Reduces the number of points in the track segment. Segment points will
        be updated in place.

        Parameters
        ----------
        min_distance : float
            The minimum separation in meters between points
        """
        reduced_points = []
        for point in self.points:
            if reduced_points:
                distance = reduced_points[-1].distance_3d(point)
                if distance >= min_distance:
                    reduced_points.append(point)
            else:
                # Leave first point:
                reduced_points.append(point)

        self.points = reduced_points

    def _find_next_simplified_point(self, pos, max_distance):
        for candidate in range(pos + 1, len(self.points) - 1):
            for i in range(pos + 1, candidate):
                d = mod_geo.distance_from_line(self.points[i],
                                               self.points[pos],
                                               self.points[candidate])
                if d > max_distance:
                    return candidate - 1
        return None

    def adjust_time(self, delta):
        """
        Adjusts the time of all points in the segment by the specified delta

        Parameters
        ----------
        delta : datetime.timedelta
            Positive time delta will adjust point times into the future
            Negative time delta will adjust point times into the past
        """
        for track_point in self.points:
            track_point.adjust_time(delta)

    def remove_time(self):
        """ Removes time data for all points in the segment. """
        for track_point in self.points:
            track_point.remove_time()

    def remove_elevation(self):
        """ Removes elevation data for all points in the segment. """
        for track_point in self.points:
            track_point.remove_elevation()

    def length_2d(self):
        """
        Computes 2-dimensional length (meters) of segment (only latitude and
        longitude, no elevation).

        Returns
        ----------
        length : float
            Length returned in meters
        """
        return mod_geo.length_2d(self.points)

    def length_3d(self):
        """
        Computes 3-dimensional length of segment (latitude, longitude, and
        elevation).

        Returns
        ----------
        length : float
            Length returned in meters
        """
        return mod_geo.length_3d(self.points)

    def move(self, location_delta):
        """
        Moves each point in the segment.

        Parameters
        ----------
        location_delta: LocationDelta object
            Delta (distance/angle or lat/lon offset to apply each point in the
            segment
        """
        for track_point in self.points:
            track_point.move(location_delta)

    def walk(self, only_points=False):
        """
        Generator for iterating over segment points

        Parameters
        ----------
        only_points: boolean
            Only yield points (no index yielded)

        Yields
        ------
        point: GPXTrackPoint
            A point in the sement
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
        Gets the number of points in segment.

        Returns
        ----------
        num_points : integer
            Number of points in segment
        """
        if not self.points:
            return 0
        return len(self.points)

    def split(self, point_no):
        """
        Splits the segment into two parts. If one of the split segments is
        empty it will not be added in the result. The segments will be split
        in place.

        Parameters
        ----------
        point_no : integer
            The index of the track point in the segment to split
        """
        part_1 = self.points[:point_no + 1]
        part_2 = self.points[point_no + 1:]
        return GPXTrackSegment(part_1), GPXTrackSegment(part_2)

    def join(self, track_segment):
        """ Joins with another segment """
        self.points += track_segment.points

    def remove_point(self, point_no):
        """ Removes a point specificed by index from the segment """
        if point_no < 0 or point_no >= len(self.points):
            return

        part_1 = self.points[:point_no]
        part_2 = self.points[point_no + 1:]

        self.points = part_1 + part_2

    def get_moving_data(self, stopped_speed_threshold=None):
        """
        Return a tuple of (moving_time, stopped_time, moving_distance,
        stopped_distance, max_speed) that may be used for detecting the time
        stopped, and max speed. Not that those values are not absolutely true,
        because the "stopped" or "moving" information aren't saved in the segment.

        Because of errors in the GPS recording, it may be good to calculate
        them on a reduced and smoothed version of the track.

        Parameters
        ----------
        stopped_speed_threshold : float
            speeds (km/h) below this threshold are treated as if having no
            movement. Default is 1 km/h.

        Returns
        ----------
        moving_data : MovingData : named tuple
            moving_time : float
                time (seconds) of segment in which movement was occurring
            stopped_time : float
                time (seconds) of segment in which no movement was occurring
            stopped_distance : float
                distance (meters) travelled during stopped times
            moving_distance : float
                distance (meters) travelled during moving times
            max_speed : float
                Maximum speed (m/s) during the segment.
        """
        if not stopped_speed_threshold:
            stopped_speed_threshold = DEFAULT_STOPPED_SPEED_THRESHOLD

        moving_time = 0.
        stopped_time = 0.

        moving_distance = 0.
        stopped_distance = 0.

        speeds_and_distances = []

        for i in range(1, len(self.points)):

            previous = self.points[i - 1]
            point = self.points[i]

            # Won't compute max_speed for first and last because of common GPS
            # recording errors, and because smoothing don't work well for those
            # points:
            if point.time and previous.time:
                timedelta = point.time - previous.time

                if point.elevation and previous.elevation:
                    distance = point.distance_3d(previous)
                else:
                    distance = point.distance_2d(previous)

                seconds = mod_utils.total_seconds(timedelta)
                speed_kmh = 0
                if seconds > 0:
                    # TODO: compute threshold in m/s instead this to kmh every time:
                    speed_kmh = (distance / 1000.) / (mod_utils.total_seconds(timedelta) / 60. ** 2)

                if speed_kmh <= stopped_speed_threshold:
                    stopped_time += mod_utils.total_seconds(timedelta)
                    stopped_distance += distance
                else:
                    moving_time += mod_utils.total_seconds(timedelta)
                    moving_distance += distance

                    if distance and moving_time:
                        speeds_and_distances.append((distance / mod_utils.total_seconds(timedelta), distance, ))

        max_speed = None
        if speeds_and_distances:
            max_speed = mod_geo.calculate_max_speed(speeds_and_distances)

        return MovingData(moving_time, stopped_time, moving_distance, stopped_distance, max_speed)

    def get_time_bounds(self):
        """
        Gets the time bound (start and end) of the segment.

        returns
        ----------
        time_bounds : TimeBounds named tuple
            start_time : datetime
                Start time of the first segment in track
            end time : datetime
                End time of the last segment in track
        """
        start_time = None
        end_time = None

        for point in self.points:
            if point.time:
                if not start_time:
                    start_time = point.time
                if point.time:
                    end_time = point.time

        return TimeBounds(start_time, end_time)

    def get_bounds(self):
        """
        Gets the latitude and longitude bounds of the segment.

        Returns
        ----------
        bounds : Bounds named tuple
            min_latitude : float
                Minimum latitude of segment in decimal degrees [-90, 90]
            max_latitude : float
                Maximum latitude of segment in decimal degrees [-90, 90]
            min_longitude : float
                Minimum longitude of segment in decimal degrees [-180, 180]
            max_longitude : float
                Maximum longitude of segment in decimal degrees [-180, 180]
        """
        min_lat = None
        max_lat = None
        min_lon = None
        max_lon = None

        for point in self.points:
            if min_lat is None or point.latitude < min_lat:
                min_lat = point.latitude
            if max_lat is None or point.latitude > max_lat:
                max_lat = point.latitude
            if min_lon is None or point.longitude < min_lon:
                min_lon = point.longitude
            if max_lon is None or point.longitude > max_lon:
                max_lon = point.longitude

        return GPXBounds(min_lat, max_lat, min_lon, max_lon)

    def get_speed(self, point_no):
        """
        Computes the speed at the specified point index.

        Parameters
        ----------
        point_no : integer
            index of the point used to compute speed

        Returns
        ----------
        speed : float
            Speed returned in m/s
        """
        point = self.points[point_no]

        previous_point = None
        next_point = None

        if 0 < point_no < len(self.points):
            previous_point = self.points[point_no - 1]
        if 0 <= point_no < len(self.points) - 1:
            next_point = self.points[point_no + 1]

        speed_1 = point.speed_between(previous_point)
        speed_2 = point.speed_between(next_point)

        if speed_1:
            speed_1 = abs(speed_1)
        if speed_2:
            speed_2 = abs(speed_2)

        if speed_1 and speed_2:
            return (speed_1 + speed_2) / 2.

        if speed_1:
            return speed_1

        return speed_2

    def add_elevation(self, delta):
        """
        Adjusts elevation data for segment.

        Parameters
        ----------
        delta : float
            Elevation delta in meters to apply to track
        """
        if not delta:
            return

        for track_point in self.points:
            if track_point.elevation is not None:
                track_point.elevation += delta

    def add_missing_data(self, get_data_function, add_missing_function):
        """
        Calculate missing data.

        Parameters
        ----------
        get_data_function : object
            Returns the data from point
        add_missing_function : void
            Function with the following arguments: array with points with missing data, the point before them (with data),
            the point after them (with data), and distance ratios between points in the interval (the sum of distances ratios
            will be 1)
        """
        if not get_data_function:
            raise GPXException('Invalid get_data_function: %s' % get_data_function)
        if not add_missing_function:
            raise GPXException('Invalid add_missing_function: %s' % add_missing_function)

        # Points (*without* data) between two points (*with* data):
        interval = []
        # Point (*with* data) before and after the interval:
        start_point = None

        previous_point = None
        for track_point in self.points:
            data = get_data_function(track_point)
            if data is None and previous_point:
                if not start_point:
                    start_point = previous_point
                interval.append(track_point)
            else:
                if interval:
                    distances_ratios = self._get_interval_distances_ratios(interval,
                                                                           start_point, track_point)
                    add_missing_function(interval, start_point, track_point,
                                         distances_ratios)
                    start_point = None
                    interval = []
            previous_point = track_point

    def _get_interval_distances_ratios(self, interval, start, end):
        assert start, start
        assert end, end
        assert interval, interval
        assert len(interval) > 0, interval

        distances = []
        distance_from_start = 0
        previous_point = start
        for point in interval:
            distance_from_start += float(point.distance_3d(previous_point))
            distances.append(distance_from_start)
            previous_point = point

        from_start_to_end = distances[-1] + interval[-1].distance_3d(end)

        assert len(interval) == len(distances)

        return list(map(
            lambda distance: (distance / from_start_to_end) if from_start_to_end else 0,
            distances))

    def get_duration(self):
        """
        Calculates duration or track segment

        Returns
        -------
        duration: float
            Duration in seconds
        """
        if not self.points or len(self.points) < 2:
            return 0

        # Search for start:
        first = self.points[0]
        if not first.time:
            first = self.points[1]

        last = self.points[-1]
        if not last.time:
            last = self.points[-2]

        if not last.time or not first.time:
            return None

        if last.time < first.time:
            return None

        return mod_utils.total_seconds(last.time - first.time)

    def get_uphill_downhill(self):
        """
        Calculates the uphill and downhill elevation climbs for the track
        segment. If elevation for some points is not found those are simply
        ignored.

        Returns
        -------
        uphill_downhill: UphillDownhill named tuple
            uphill: float
                Uphill elevation climbs in meters
            downhill: float
                Downhill elevation descent in meters
        """
        if not self.points:
            return UphillDownhill(0, 0)

        elevations = list(map(lambda point: point.elevation, self.points))
        uphill, downhill = mod_geo.calculate_uphill_downhill(elevations)

        return UphillDownhill(uphill, downhill)

    def get_elevation_extremes(self):
        """
        Calculate elevation extremes of track segment

        Returns
        -------
        min_max_elevation: MinimumMaximum named tuple
            minimum: float
                Minimum elevation in meters
            maximum: float
                Maximum elevation in meters
        """
        if not self.points:
            return MinimumMaximum(None, None)

        elevations = map(lambda location: location.elevation, self.points)
        elevations = filter(lambda elevation: elevation is not None, elevations)
        elevations = list(elevations)

        if not elevations:
            return MinimumMaximum(None, None)

        return MinimumMaximum(min(elevations), max(elevations))

    def get_location_at(self, time):
        """
        Gets approx. location at given time. Note that, at the moment this
        method returns an instance of GPXTrackPoint in the future -- this may
        be a mod_geo.Location instance with approximated latitude, longitude
        and elevation!
        """
        if not self.points:
            return None

        if not time:
            return None

        first_time = self.points[0].time
        last_time = self.points[-1].time

        if not first_time and not last_time:
            return None

        if not first_time <= time <= last_time:
            return None

        for point in self.points:
            if point.time and time <= point.time:
                # TODO: If between two points -- approx position!
                # return mod_geo.Location(point.latitude, point.longitude)
                return point

    def get_nearest_location(self, location):
        """ Return the (location, track_point_no) on this track segment """
        if not self.points:
            return None, None

        result = None
        current_distance = None
        result_track_point_no = None
        for i in range(len(self.points)):
            track_point = self.points[i]
            if not result:
                result = track_point
            else:
                distance = track_point.distance_2d(location)
                if not current_distance or distance < current_distance:
                    current_distance = distance
                    result = track_point
                    result_track_point_no = i

        return result, result_track_point_no

    def smooth(self, vertical=True, horizontal=False, remove_extremes=False):
        """ "Smooths" the elevation graph. Can be called multiple times. """
        if len(self.points) <= 3:
            return

        elevations = []
        latitudes = []
        longitudes = []

        for point in self.points:
            elevations.append(point.elevation)
            latitudes.append(point.latitude)
            longitudes.append(point.longitude)

        avg_distance = 0
        avg_elevation_delta = 1
        if remove_extremes:
            # compute the average distance between two points:
            distances = []
            elevations_delta = []
            for i in range(len(self.points))[1:]:
                distances.append(self.points[i].distance_2d(self.points[i - 1]))
                elevation_1 = self.points[i].elevation
                elevation_2 = self.points[i - 1].elevation
                if elevation_1 is not None and elevation_2 is not None:
                    elevations_delta.append(abs(elevation_1 - elevation_2))
            if distances:
                avg_distance = 1.0 * sum(distances) / len(distances)
            if elevations_delta:
                avg_elevation_delta = 1.0 * sum(elevations_delta) / len(elevations_delta)

        # If The point moved more than this number * the average distance between two
        # points -- then is a candidate for deletion:
        # TODO: Make this a method parameter
        remove_2d_extremes_threshold = 1.75 * avg_distance
        remove_elevation_extremes_threshold = avg_elevation_delta * 5  # TODO: Param

        new_track_points = [self.points[0]]

        for i in range(len(self.points))[1:-1]:
            new_point = None
            point_removed = False
            if vertical and elevations[i - 1] and elevations[i] and elevations[i + 1]:
                old_elevation = self.points[i].elevation
                new_elevation = SMOOTHING_RATIO[0] * elevations[i - 1] + \
                    SMOOTHING_RATIO[1] * elevations[i] + \
                    SMOOTHING_RATIO[2] * elevations[i + 1]

                if not remove_extremes:
                    self.points[i].elevation = new_elevation

                if remove_extremes:
                    # The point must be enough distant to *both* neighbours:
                    d1 = abs(old_elevation - elevations[i - 1])
                    d2 = abs(old_elevation - elevations[i + 1])

                    # TODO: Remove extremes threshold is meant only for 2D, elevation must be
                    # computed in different way!
                    if min(d1, d2) < remove_elevation_extremes_threshold and abs(old_elevation - new_elevation) < remove_2d_extremes_threshold:
                        new_point = self.points[i]
                    else:
                        point_removed = True
                else:
                    new_point = self.points[i]
            else:
                new_point = self.points[i]

            if horizontal:
                old_latitude = self.points[i].latitude
                new_latitude = (
                    SMOOTHING_RATIO[0] * latitudes[i - 1] +
                    SMOOTHING_RATIO[1] * latitudes[i] +
                    SMOOTHING_RATIO[2] * latitudes[i + 1]
                )
                old_longitude = self.points[i].longitude
                new_longitude = (
                    SMOOTHING_RATIO[0] * longitudes[i - 1] +
                    SMOOTHING_RATIO[1] * longitudes[i] +
                    SMOOTHING_RATIO[2] * longitudes[i + 1]
                )

                if not remove_extremes:
                    self.points[i].latitude = new_latitude
                    self.points[i].longitude = new_longitude

                # TODO: This is not ideal.. Because if there are points A, B and C on the same
                # line but B is very close to C... This would remove B (and possibly) A even though
                # it is not an extreme. This is the reason for this algorithm:
                d1 = mod_geo.distance(latitudes[i - 1], longitudes[i - 1], None,
                                      latitudes[i], longitudes[i], None)
                d2 = mod_geo.distance(latitudes[i + 1], longitudes[i + 1], None,
                                      latitudes[i], longitudes[i], None)
                d = mod_geo.distance(latitudes[i - 1], longitudes[i - 1], None,
                                     latitudes[i + 1], longitudes[i + 1], None)

                if d1 + d2 > d * 1.5 and remove_extremes:
                    d = mod_geo.distance(old_latitude, old_longitude, None,
                                         new_latitude, new_longitude, None)
                    if d < remove_2d_extremes_threshold:
                        new_point = self.points[i]
                    else:
                        point_removed = True
                else:
                    new_point = self.points[i]

            if new_point and not point_removed:
                new_track_points.append(new_point)

        new_track_points.append(self.points[- 1])

        self.points = new_track_points

    def has_times(self):
        """
        Returns if points in this segment contains timestamps.

        The first point, the last point, and 75% of the points must have times
        for this method to return true.
        """
        if not self.points:
            return True
            # ... or otherwise one empty track segment would change the entire
            # track's "has_times" status!

        found = 0
        for track_point in self.points:
            if track_point.time:
                found += 1

        return len(self.points) > 2 and float(found) / float(len(self.points)) > .75

    def has_elevations(self):
        """
        Returns if points in this segment contains elevation.

        The first point, the last point, and at least 75% of the points must
        have elevation for this method to return true.
        """
        if not self.points:
            return True
            # ... or otherwise one empty track segment would change the entire
            # track's "has_times" status!

        found = 0
        for track_point in self.points:
            if track_point.elevation:
                found += 1

        return len(self.points) > 2 and float(found) / float(len(self.points)) > .75

    def __repr__(self):
        return 'GPXTrackSegment(points=[%s])' % ('...' if self.points else '')

    def clone(self):
        return deepcopy(self)
