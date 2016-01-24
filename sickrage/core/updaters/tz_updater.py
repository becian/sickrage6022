# Author: echel0n <sickrage.tv@gmail.com>
# URL: https://sickrage.tv
# Git: https://github.com/SiCKRAGETV/SickRage.git
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import datetime
import re

import requests
from dateutil import tz

import sickrage
from sickrage.core.databases import cache_db
from sickrage.core.helpers import getURL, tryInt


time_regex = re.compile(r'(\d{1,2})(([:.](\d{2,2}))? ?([PA][. ]? ?M)|[:.](\d{2,2}))\b', flags=re.IGNORECASE)
am_regex = re.compile(r'(A[. ]? ?M)', flags=re.IGNORECASE)
pm_regex = re.compile(r'(P[. ]? ?M)', flags=re.IGNORECASE)

network_dict = None
sr_timezone = tz.tzwinlocal().display() if tz.tzwinlocal else tz.tzlocal()

# update the network timezone table
def update_network_dict():
    """Update timezone information from SR repositories"""

    url = 'http://sickragetv.github.io/sb_network_timezones/network_timezones.txt'
    url_data = getURL(url, session=requests.Session())
    if not url_data:
        sickrage.LOGGER.warning('Updating network timezones failed, this can happen from time to time. URL: %s' % url)
        load_network_dict()
        return

    d = {}
    try:
        for line in url_data.splitlines():
            (key, val) = line.strip().rsplit(':', 1)
            if key is None or val is None:
                continue
            d[key] = val
    except (IOError, OSError):
        pass

    network_list = dict(cache_db.CacheDB().select('SELECT * FROM network_timezones;'))

    queries = []
    for network, timezone in d.iteritems():
        existing = network_list.has_key(network)
        if not existing:
            queries.append(['INSERT OR IGNORE INTO network_timezones VALUES (?,?);', [network, timezone]])
        elif network_list[network] is not timezone:
            queries.append(['UPDATE OR IGNORE network_timezones SET timezone = ? WHERE network_name = ?;',
                            [timezone, network]])

        if existing:
            del network_list[network]

    if network_list:
        purged = [x for x in network_list]
        queries.append(
                ['DELETE FROM network_timezones WHERE network_name IN (%s);' % ','.join(['?'] * len(purged)), purged])

    if queries:
        cache_db.CacheDB().mass_action(queries)
        load_network_dict()


# load network timezones from db into dict
def load_network_dict():
    """
    Load network timezones from db into dict network_dict (global dict)
    """
    try:
        cur_network_list = cache_db.CacheDB().select('SELECT * FROM network_timezones;')
        if not cur_network_list:
            update_network_dict()
            cur_network_list = cache_db.CacheDB().select('SELECT * FROM network_timezones;')
        d = dict(cur_network_list)
    except Exception:
        d = {}

    return d


# get timezone of a network or return default timezone
def get_network_timezone(network, _network_dict):
    """
    Get a timezone of a network from a given network dict

    :param network: network to look up (needle)
    :param _network_dict: dict to look up in (haystack)
    :return:
    """
    if network is None:
        return sr_timezone

    try:
        n_t = tz.gettz(_network_dict[network])
    except Exception:
        return sr_timezone

    return n_t if n_t is not None else sr_timezone


# parse date and time string into local time
def parse_date_time(d, t, network):
    """
    Parse date and time string into local time

    :param d: date string
    :param t: time string
    :param network: network to use as base
    :return: datetime object containing local time
    """

    if not network_dict:
        load_network_dict()

    mo = time_regex.search(t)
    if mo is not None and len(mo.groups()) >= 5:
        if mo.group(5) is not None:
            try:
                hr = tryInt(mo.group(1))
                m = tryInt(mo.group(4))
                ap = mo.group(5)
                # convert am/pm to 24 hour clock
                if ap is not None:
                    if pm_regex.search(ap) is not None and hr != 12:
                        hr += 12
                    elif am_regex.search(ap) is not None and hr == 12:
                        hr -= 12
            except Exception:
                hr = 0
                m = 0
        else:
            try:
                hr = tryInt(mo.group(1))
                m = tryInt(mo.group(6))
            except Exception:
                hr = 0
                m = 0
    else:
        hr = 0
        m = 0
    if hr < 0 or hr > 23 or m < 0 or m > 59:
        hr = 0
        m = 0

    te = datetime.datetime.fromordinal(tryInt(d) or 1)
    try:
        foreign_timezone = get_network_timezone(network, load_network_dict())
        return datetime.datetime(te.year, te.month, te.day, hr, m, tzinfo=foreign_timezone)
    except Exception:
        return datetime.datetime(te.year, te.month, te.day, hr, m, tzinfo=sr_timezone)


def test_timeformat(t):
    mo = time_regex.search(t)
    if mo is None or len(mo.groups()) < 2:
        return False
    else:
        return True
