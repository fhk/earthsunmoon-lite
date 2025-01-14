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
from qgis.PyQt import uic
from qgis.PyQt.QtCore import Qt
from qgis.core import Qgis, QgsCoordinateReferenceSystem, QgsSettings, QgsApplication
from qgis.PyQt.QtWidgets import QDialog
from datetime import date
from shutil import copyfile
try:
    from jplephem.spk import SPK
    from skyfield.api import load, load_file, wgs84
    from skyfield import almanac
except Exception:
    pass

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

def parse_timeseries(increment, duration):
    """
        Parse the time strings of duration and increment formatted as DD:HH:MM:SS when
        DD are days, HH house, MM minutes, and SS seconds. The numbers are not constrained
        two digits. The returned results are the number of observation instances and the
        incremeantal time in seconds.
    """
    inc = increment.split(':')
    inc_len = len(inc)
    dur = duration.split(':')
    dur_len = len(dur)

    try:
        inc_seconds = float(inc[0]) * 86400.0  # Days: 60 * 60 * 24
        if inc_len >= 2:
            inc_seconds += float(inc[1]) * 3600.0  # Hours
        if inc_len >= 3:
            inc_seconds += float(inc[2]) * 60.0  # Minutes
        if inc_len >= 4:
            inc_seconds += float(inc[3])  # Seconds

        dur_seconds = float(dur[0]) * 86400.0
        if dur_len >= 2:
            dur_seconds += float(dur[1]) * 3600.0
        if dur_len >= 3:
            dur_seconds += float(dur[2]) * 60.0
        if dur_len >= 4:
            dur_seconds += float(dur[2])

        total_instances = math.floor(dur_seconds / inc_seconds)
        return( total_instances, inc_seconds )
    except Exception:
        return(-1, -1)

epsg4326 = QgsCoordinateReferenceSystem('EPSG:4326')

DEFAULT_EPHEM = 'de440s_1990_2040.bsp'

EPHEM_INFO = {
    'de405.bsp': '1600 to 2200',
    'de406.bsp': '−3000 to 3000',
    'de421.bsp': '1900 to 2050',
    'de422.bsp': '−3000 to 3000',
    'de430_1850-2150.bsp': '1850 to 2150',
    'de430t.bsp': '1550 to 2650',
    'de431t.bsp': '–13200 to 17191',
    'de440s.bsp': '1849 to 2150',
    'de440.bsp': '1550 to 2650',
    'de441.bsp': '−13200 to 17191',
    'de440s_1990_2040.bsp': '1990 to 2040'
}

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/settings.ui'))


class Settings():

    def __init__(self):
        self.ephem_dir_path = os.path.abspath(os.path.join(QgsApplication.qgisSettingsDirPath(), "EarthSunMoon"))
        # Initialize the ephemeris file to the default, but it will be overwritten in readSettings()
        self.ephem_file = DEFAULT_EPHEM
        self.readSettings()
        self.eph = None  # Skyfield ephemeris
        self.ts = None  # Skyfield timescale

    def ephemDir(self):
        """Return the directory where the ephemeris files are stored"""
        return(self.ephem_dir_path)

    def defaultEphemPath(self):
        """Return the path of the default ephemeris file"""
        path = os.path.abspath(os.path.join(self.ephem_dir_path, DEFAULT_EPHEM))
        return(path)

    def defaultEphemFile(self):
        """Return the file name of the default ephemeris file"""
        return(DEFAULT_EPHEM)
    
    def ephemFile(self):
        """Return the file name of the user selected ephemeris file"""
        return(self.ephem_file)

    def ephemPath(self):
        """Return the path of the user selected ephemeris file"""
        path = os.path.abspath(os.path.join(self.ephem_dir_path, self.ephem_file))
        return(path)

    def ephem(self):
        if not self.eph:
            self.eph = load_file(self.ephemPath())
        return(self.eph)

    def timescale(self):
        if not self.ts:
            self.ts = load.timescale()
        return(self.ts)

    def allEphemFiles(self):
        files = []
        for file in os.listdir(self.ephemDir()):
            if file.endswith('.bsp'):
                files.append(file)
        return(files)

    def ephemInfo(self):
        """Return an information string about the user selected ephemeris"""
        try:
            file = self.ephemFile()
            spk = SPK.open(self.ephemPath())
            if file in EPHEM_INFO:
                msg = '{}\n{}\n{}'.format(self.ephemPath(), EPHEM_INFO[file], str(spk))
            else:
                msg = '{}\n{}'.format(self.ephemPath(), str(spk))
            spk.close()
        except Exception:
            msg = ''
        return(msg)

    def setEphemFile(self, file):
        self.eph = None
        self.ephem_file = file
        path = self.ephemPath()
        if not os.path.isfile(path):
            self.ephem_file = self.defaultEphemFile()
            return(False)
        qset = QgsSettings()
        qset.setValue('/EarthSunMoon/EphemFile', self.ephem_file)
        return(True)

    def readSettings(self):
        qset = QgsSettings()
        self.ephem_file = qset.value('/EarthSunMoon/EphemFile', self.defaultEphemFile())
        path = self.ephemPath()
        if not os.path.isfile(path):
            self.ephem_file = self.defaultEphemFile()
            qset.setValue('/EarthSunMoon/EphemFile', self.ephem_file)
    

settings = Settings()

class SettingsWidget(QDialog, FORM_CLASS):
    '''Settings Dialog box.'''
    def __init__(self, iface, parent):
        super(SettingsWidget, self).__init__(parent)
        self.setupUi(self)
        self.iface = iface
        self.fileWidget.setFilter('*.bsp')

    def showEvent(self, e):
        self.updateEphemComboBox()

    def updateEphemComboBox(self):
        self.ephemComboBox.clear()
        self.ephemComboBox.addItems(settings.allEphemFiles())
        index = self.ephemComboBox.findText(settings.ephemFile(), Qt.MatchExactly)
        if index != -1:
            self.ephemComboBox.setCurrentIndex(index)
        
    def accept(self):
        text = self.ephemComboBox.currentText()
        settings.setEphemFile(text)
        self.close()
    
    def on_installButton_pressed(self):
        ephem_file = self.fileWidget.filePath()
        if not ephem_file:
            return
        if not os.path.isfile(ephem_file):
            self.iface.messageBar().pushMessage("", "Not a valid file", level=Qgis.Warning, duration=4)
            return
        basename = os.path.basename(ephem_file)
        newpath = os.path.join(settings.ephemDir(), basename)
        if os.path.isfile(newpath):
            self.iface.messageBar().pushMessage("", "This ephemeris file already exists", level=Qgis.Warning, duration=4)
            return
        copyfile(ephem_file, newpath)
        self.updateEphemComboBox()
        index = self.ephemComboBox.findText(basename, Qt.MatchExactly)
        if index != -1:
            self.ephemComboBox.setCurrentIndex(index)
        
        
