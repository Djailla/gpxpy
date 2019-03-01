from gpxpy import gpxfield as mod_gpxfield


class GPXBounds:
    gpx_10_fields = gpx_11_fields = [
        mod_gpxfield.GPXField('min_latitude', attribute='minlat', type=mod_gpxfield.FLOAT_TYPE),
        mod_gpxfield.GPXField('max_latitude', attribute='maxlat', type=mod_gpxfield.FLOAT_TYPE),
        mod_gpxfield.GPXField('min_longitude', attribute='minlon', type=mod_gpxfield.FLOAT_TYPE),
        mod_gpxfield.GPXField('max_longitude', attribute='maxlon', type=mod_gpxfield.FLOAT_TYPE),
    ]

    __slots__ = ('min_latitude', 'max_latitude', 'min_longitude', 'max_longitude')

    def __init__(self, min_latitude=None, max_latitude=None, min_longitude=None, max_longitude=None):
        self.min_latitude = min_latitude
        self.max_latitude = max_latitude
        self.min_longitude = min_longitude
        self.max_longitude = max_longitude

    def __iter__(self):
        return (self.min_latitude, self.max_latitude, self.min_longitude, self.max_longitude,).__iter__()
