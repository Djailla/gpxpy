from copy import deepcopy

from gpxpy import geo as mod_geo
from gpxpy import utils as mod_utils
from gpxpy import gpxfield as mod_gpxfield

from gpxpy.gpx.bounds import GPXBounds
from gpxpy.gpx.track_segment import GPXTrackSegment

from gpxpy.gpx.common import MinimumMaximum, MovingData, TimeBounds, UphillDownhill


class GPXTrack:
    gpx_10_fields = [
        mod_gpxfield.GPXField('name'),
        mod_gpxfield.GPXField('comment', 'cmt'),
        mod_gpxfield.GPXField('description', 'desc'),
        mod_gpxfield.GPXField('source', 'src'),
        mod_gpxfield.GPXField('link', 'url'),
        mod_gpxfield.GPXField('link_text', 'urlname'),
        mod_gpxfield.GPXField('number', type=mod_gpxfield.INT_TYPE),
        mod_gpxfield.GPXComplexField('segments', tag='trkseg', classs=GPXTrackSegment, is_list=True),
    ]
    gpx_11_fields = [
        # See GPX for text field description
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
        mod_gpxfield.GPXComplexField('segments', tag='trkseg', classs=GPXTrackSegment, is_list=True),
    ]

    __slots__ = ('name', 'comment', 'description', 'source', 'link',
                 'link_text', 'number', 'segments', 'link_type', 'type',
                 'extensions')

    def __init__(self, name=None, description=None, number=None):
        self.name = name
        self.comment = None
        self.description = description
        self.source = None
        self.link = None
        self.link_text = None
        self.number = number
        self.segments = []
        self.link_type = None
        self.type = None
        self.extensions = []

    def simplify(self, max_distance=None):
        """
        Simplify using the Ramer-Douglas-Peucker algorithm: http://en.wikipedia.org/wiki/Ramer-Douglas-Peucker_algorithm
        """
        for segment in self.segments:
            segment.simplify(max_distance=max_distance)

    def reduce_points(self, min_distance):
        """
        Reduces the number of points in the track. Segment points will be
        updated in place.

        Parameters
        ----------
        min_distance : float
            The minimum separation in meters between points
        """
        for segment in self.segments:
            segment.reduce_points(min_distance)

    def adjust_time(self, delta):
        """
        Adjusts the time of all segments in the track by the specified delta

        Parameters
        ----------
        delta : datetime.timedelta
            Positive time delta will adjust time into the future
            Negative time delta will adjust time into the past
        """
        for segment in self.segments:
            segment.adjust_time(delta)

    def remove_time(self):
        """ Removes time data for all points in all segments of track. """
        for segment in self.segments:
            segment.remove_time()

    def remove_elevation(self):
        """ Removes elevation data for all points in all segments of track. """
        for segment in self.segments:
            segment.remove_elevation()

    def remove_empty(self):
        """ Removes empty segments in track """
        result = []

        for segment in self.segments:
            if segment.points:
                result.append(segment)

        self.segments = result

    def length_2d(self):
        """
        Computes 2-dimensional length (meters) of track (only latitude and
        longitude, no elevation). This is the sum of the 2D length of all
        segments.

        Returns
        ----------
        length : float
            Length returned in meters
        """
        length = 0
        for track_segment in self.segments:
            d = track_segment.length_2d()
            if d:
                length += d
        return length

    def get_time_bounds(self):
        """
        Gets the time bound (start and end) of the track.

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

        for track_segment in self.segments:
            point_start_time, point_end_time = track_segment.get_time_bounds()
            if not start_time and point_start_time:
                start_time = point_start_time
            if point_end_time:
                end_time = point_end_time

        return TimeBounds(start_time, end_time)

    def get_bounds(self):
        """
        Gets the latitude and longitude bounds of the track.

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
        for track_segment in self.segments:
            bounds = track_segment.get_bounds()

            if not mod_utils.is_numeric(min_lat) or (bounds.min_latitude and bounds.min_latitude < min_lat):
                min_lat = bounds.min_latitude
            if not mod_utils.is_numeric(max_lat) or (bounds.max_latitude and bounds.max_latitude > max_lat):
                max_lat = bounds.max_latitude
            if not mod_utils.is_numeric(min_lon) or (bounds.min_longitude and bounds.min_longitude < min_lon):
                min_lon = bounds.min_longitude
            if not mod_utils.is_numeric(max_lon) or (bounds.max_longitude and bounds.max_longitude > max_lon):
                max_lon = bounds.max_longitude

        return GPXBounds(min_lat, max_lat, min_lon, max_lon)

    def walk(self, only_points=False):
        """
        Generator used to iterates through track

        Parameters
        ----------
        only_point s: boolean
            Only yield points while walking

        Yields
        ----------
        point : GPXTrackPoint
            Point in the track
        segment_no : integer
            Index of segment containint point. This is suppressed if only_points
            is True.
        point_no : integer
            Index of point. This is suppressed if only_points is True.
        """
        for segment_no, segment in enumerate(self.segments):
            for point_no, point in enumerate(segment.points):
                if only_points:
                    yield point
                else:
                    yield point, segment_no, point_no

    def get_points_no(self):
        """
        Get the number of points in all segments in the track.

        Returns
        ----------
        num_points : integer
            Number of points in track
        """
        result = 0

        for track_segment in self.segments:
            result += track_segment.get_points_no()

        return result

    def length_3d(self):
        """
        Computes 3-dimensional length of track (latitude, longitude, and
        elevation). This is the sum of the 3D length of all segments.

        Returns
        ----------
        length : float
            Length returned in meters
        """
        length = 0
        for track_segment in self.segments:
            d = track_segment.length_3d()
            if d:
                length += d
        return length

    def split(self, track_segment_no, track_point_no):
        """
        Splits one of the segments in the track in two parts. If one of the
        split segments is empty it will not be added in the result. The
        segments will be split in place.

        Parameters
        ----------
        track_segment_no : integer
            The index of the segment to split
        track_point_no : integer
            The index of the track point in the segment to split
        """
        new_segments = []
        for i in range(len(self.segments)):
            segment = self.segments[i]
            if i == track_segment_no:
                segment_1, segment_2 = segment.split(track_point_no)
                if segment_1:
                    new_segments.append(segment_1)
                if segment_2:
                    new_segments.append(segment_2)
            else:
                new_segments.append(segment)
        self.segments = new_segments

    def join(self, track_segment_no, track_segment_no_2=None):
        """
        Joins two segments of this track. The segments will be split in place.

        Parameters
        ----------
        track_segment_no : integer
            The index of the first segment to join
        track_segment_no_2 : integer
            The index of second segment to join. If track_segment_no_2 is not
            provided,the join will be with the next segment after
            track_segment_no.
        """
        if not track_segment_no_2:
            track_segment_no_2 = track_segment_no + 1

        if track_segment_no_2 >= len(self.segments):
            return

        new_segments = []
        for i in range(len(self.segments)):
            segment = self.segments[i]
            if i == track_segment_no:
                second_segment = self.segments[track_segment_no_2]
                segment.join(second_segment)

                new_segments.append(segment)
            elif i == track_segment_no_2:
                # Nothing, it is already joined
                pass
            else:
                new_segments.append(segment)
        self.segments = new_segments

    def get_moving_data(self, stopped_speed_threshold=None):
        """
        Return a tuple of (moving_time, stopped_time, moving_distance,
        stopped_distance, max_speed) that may be used for detecting the time
        stopped, and max speed. Not that those values are not absolutely true,
        because the "stopped" or "moving" information aren't saved in the track.

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
                time (seconds) of track in which movement was occurring
            stopped_time : float
                time (seconds) of track in which no movement was occurring
            stopped_distance : float
                distance (meters) travelled during stopped times
            moving_distance : float
                distance (meters) travelled during moving times
            max_speed : float
                Maximum speed (m/s) during the track.
        """
        moving_time = 0.
        stopped_time = 0.

        moving_distance = 0.
        stopped_distance = 0.

        max_speed = 0.

        for segment in self.segments:
            track_moving_time, track_stopped_time, track_moving_distance, track_stopped_distance, track_max_speed = segment.get_moving_data(stopped_speed_threshold)
            moving_time += track_moving_time
            stopped_time += track_stopped_time
            moving_distance += track_moving_distance
            stopped_distance += track_stopped_distance

            if track_max_speed is not None and track_max_speed > max_speed:
                max_speed = track_max_speed

        return MovingData(moving_time, stopped_time, moving_distance, stopped_distance, max_speed)

    def add_elevation(self, delta):
        """
        Adjusts elevation data for track.

        Parameters
        ----------
        delta : float
            Elevation delta in meters to apply to track
        """
        for track_segment in self.segments:
            track_segment.add_elevation(delta)

    def add_missing_data(self, get_data_function, add_missing_function):
        for track_segment in self.segments:
            track_segment.add_missing_data(get_data_function, add_missing_function)

    def move(self, location_delta):
        """
        Moves each point in the track.

        Parameters
        ----------
        location_delta: LocationDelta object
            Delta (distance/angle or lat/lon offset to apply each point in each
            segment of the track
        """
        for track_segment in self.segments:
            track_segment.move(location_delta)

    def get_duration(self):
        """
        Calculates duration or track

        Returns
        -------
        duration: float
            Duration in seconds or None if any time data is missing
        """
        if not self.segments:
            return 0

        result = 0
        for track_segment in self.segments:
            duration = track_segment.get_duration()
            if duration or duration == 0:
                result += duration
            elif duration is None:
                return None

        return result

    def get_uphill_downhill(self):
        """
        Calculates the uphill and downhill elevation climbs for the track.
        If elevation for some points is not found those are simply ignored.

        Returns
        -------
        uphill_downhill: UphillDownhill named tuple
            uphill: float
                Uphill elevation climbs in meters
            downhill: float
                Downhill elevation descent in meters
        """
        if not self.segments:
            return UphillDownhill(0, 0)

        uphill = 0
        downhill = 0

        for track_segment in self.segments:
            current_uphill, current_downhill = track_segment.get_uphill_downhill()

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
        for track_segment in self.segments:
            location = track_segment.get_location_at(time)
            if location:
                result.append(location)

        return result

    def get_elevation_extremes(self):
        """
        Calculate elevation extremes of track

        Returns
        -------
        min_max_elevation: MinimumMaximum named tuple
            minimum: float
                Minimum elevation in meters
            maximum: float
                Maximum elevation in meters
        """
        if not self.segments:
            return MinimumMaximum(None, None)

        elevations = []

        for track_segment in self.segments:
            (_min, _max) = track_segment.get_elevation_extremes()
            if _min is not None:
                elevations.append(_min)
            if _max is not None:
                elevations.append(_max)

        if len(elevations) == 0:
            return MinimumMaximum(None, None)

        return MinimumMaximum(min(elevations), max(elevations))

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
        if not self.segments:
            return None
        sum_lat = 0
        sum_lon = 0
        n = 0
        for track_segment in self.segments:
            for point in track_segment.points:
                n += 1.
                sum_lat += point.latitude
                sum_lon += point.longitude

        if not n:
            return mod_geo.Location(float(0), float(0))

        return mod_geo.Location(latitude=sum_lat / n, longitude=sum_lon / n)

    def smooth(self, vertical=True, horizontal=False, remove_extremes=False):
        """ See: GPXTrackSegment.smooth() """
        for track_segment in self.segments:
            track_segment.smooth(vertical, horizontal, remove_extremes)

    def has_times(self):
        """ See GPXTrackSegment.has_times() """
        if not self.segments:
            return None

        result = True
        for track_segment in self.segments:
            result = result and track_segment.has_times()

        return result

    def has_elevations(self):
        """ Returns true if track data has elevation for all segments """
        if not self.segments:
            return None

        result = True
        for track_segment in self.segments:
            result = result and track_segment.has_elevations()

        return result

    def get_nearest_location(self, location):
        """ Returns (location, track_segment_no, track_point_no) for nearest location on track """
        if not self.segments:
            return None

        result = None
        distance = None
        result_track_segment_no = None
        result_track_point_no = None

        for i in range(len(self.segments)):
            track_segment = self.segments[i]
            nearest_location, track_point_no = track_segment.get_nearest_location(location)
            nearest_location_distance = None
            if nearest_location:
                nearest_location_distance = nearest_location.distance_2d(location)

            if not distance or nearest_location_distance < distance:
                if nearest_location:
                    distance = nearest_location_distance
                    result = nearest_location
                    result_track_segment_no = i
                    result_track_point_no = track_point_no

        return result, result_track_segment_no, result_track_point_no

    def clone(self):
        return deepcopy(self)

    def __repr__(self):
        representation = ''
        for attribute in 'name', 'description', 'number':
            value = getattr(self, attribute)
            if value is not None:
                representation += '%s%s=%s' % (', ' if representation else '', attribute, repr(value))
        representation += '%ssegments=%s' % (', ' if representation else '', repr(self.segments))
        return 'GPXTrack(%s)' % representation
