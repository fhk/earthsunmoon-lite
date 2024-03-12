"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
import os
import math
from enum import Enum
from datetime import timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from skyfield.api import load, load_file, wgs84
from skyfield import almanac

class SolarObj(Enum):
    SUN = 0
    EARTH = 1
    MOON = 2
    MERCURY = 3
    VENUS = 4
    MARS = 5
    JUPITER = 6
    SATURN = 7
    URANUS = 8
    NEPTUNE = 9
    PLUTO = 10
    DAY_NIGHT = 11
    CIVIL_TWILIGHT = 12
    NAUTICAL_TWILIGHT = 13
    ASTRONOMICAL_TWILIGHT = 14
    NIGHT = 15

DEFAULT_EPHEM = 'de421.bsp'


class SunPositionAlgorithm():
    """
    Algorithm to to displaye the moon postion directly overhead.
    """
    sun_position = None

    def __init__(self, start_date='2024-04-01 00:00:00', increment_hours=0.1, duration_hours=2) -> None:

        df = pd.DataFrame(columns=[
            'datetime'])
        
        # Calculate the number of periods
        num_periods = int(duration_hours / increment_hours)

        # create the date range
        time_range = pd.date_range(start=start_date, periods=num_periods, freq=f'{increment_hours * 60}min')
        df['datetime'] = time_range_utc = time_range.tz_localize('UTC')

        self.sun_position = df

    def processAlgorithm(self):
        eph = load(DEFAULT_EPHEM)
        earth = eph['earth'] # vector from solar system barycenter to geocenter
        sun = eph['sun'] # vector from solar system barycenter to sun
        geocentric_sun = sun - earth # vector from geocenter to sun
        ts = load.timescale()

        self.sun_position['sun_pos'] = self.sun_position['datetime'].apply(lambda x:
            wgs84.geographic_position_of(geocentric_sun.at(ts.from_datetime(x)))) # geographic_position_of method requires a geocentric position


        self.sun_position['geometry'] = self.sun_position['sun_pos'].apply(lambda x: Point(x.longitude.degrees, x.latitude.degrees))
        del self.sun_position['sun_pos']
        self.sun_position = gpd.GeoDataFrame(self.sun_position, crs='EPSG:4326')

    def name(self):
        return 'sunposition'

    def write(self, driver='FlatGeobuf'):
        self.sun_position.to_file(f'{self.name()}.fgb', driver=driver)


def main():
    # Create the algorithm
    algorithm = SunPositionAlgorithm()
    algorithm.processAlgorithm()
    algorithm.write()


if __name__ == '__main__':
    main()
