# -*- coding: utf-8 -*-

# Copyright 2011 Tomo Krajina
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime as mod_datetime
import re as mod_re
import sys
import xml.sax.saxutils as mod_saxutils

PYTHON_VERSION = sys.version.split(' ')[0]


def to_xml(tag, attributes=None, content=None, default=None, escape=False, prettyprint=True, indent=''):
    if not prettyprint:
        indent = ''
    attributes = attributes or {}
    result = []
    result.append('\n' + indent + '<{0}'.format(tag))

    if content is None and default:
        content = default

    if attributes:
        for attribute in attributes.keys():
            result.append(make_str(' %s="%s"' % (attribute, attributes[attribute])))

    if content is None:
        result.append('/>')
    else:
        if escape:
            result.append(make_str('>%s</%s>' % (mod_saxutils.escape(content), tag)))
        else:
            result.append(make_str('>%s</%s>' % (content, tag)))

    result = make_str(''.join(result))

    return result


def is_numeric(s):
    try:
        float(s)
        return True
    except TypeError:
        return False
    except ValueError:
        return False


def total_seconds(timedelta):
    """ Some versions of python don't have the timedelta.total_seconds() method. """
    if timedelta is None:
        return None
    return (timedelta.days * 86400) + timedelta.seconds


def make_str(s):
    """ Convert a str or unicode or float object into a str type. """
    if isinstance(s, float):
        result = str(s)
        if 'e' not in result:
            return result
        # scientific notation is illegal in GPX 1/1
        return format(s, '.10f').rstrip('0.')
    if PYTHON_VERSION[0] == '2':
        if isinstance(s, unicode):
            return s.encode("utf-8")
    return str(s)


def parse_time(string):
    from . import gpx as mod_gpx
    if not string:
        return None
    if 'T' in string:
        string = string.replace('T', ' ')
    if 'Z' in string:
        string = string.replace('Z', '')
    if '.' in string:
        string = string.split('.')[0]
    if len(string) > 19:
        # remove the timezone part
        d = max(string.rfind('+'), string.rfind('-'))
        string = string[0:d]
    if len(string) < 19:
        # string has some single digits
        p = '^([0-9]{4})-([0-9]{1,2})-([0-9]{1,2}) ([0-9]{1,2}):([0-9]{1,2}):([0-9]{1,2}).*$'
        s = mod_re.findall(p, string)
        if s:
            string = (
                '{0}-{1:02d}-{2:02d} {3:02d}:{4:02d}:{5:02d}'
                .format(*[int(x) for x in s[0]])
            )
    for date_format in mod_gpx.DATE_FORMATS:
        try:
            return mod_datetime.datetime.strptime(string, date_format)
        except ValueError:
            pass
    raise mod_gpx.GPXException('Invalid time: {0}'.format(string))
