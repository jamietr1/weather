#!/usr/bin/env python

import os
import re
import forecastio
import whereami
import myconfig
import mytime
import time
from decimal import Decimal

def get_clouds(cloudcover):
    if (cloudcover >= 0.125 and cloudcover < 0.375):
        clouds = "few clouds"
    elif (cloudcover >= 0.375 and cloudcover < 0.625):
        clouds = "scattered clouds"
    elif (cloudcover >= 0.625 and cloudcover < 1.0):
        clouds = "mostly cloudly"
    elif (cloudcover == 1):
        clouds = "overcast"
    else:
        clouds = ""
    return clouds

def get_windspeed(windSpeed):
    wind = ""
    if (windSpeed < 1):
        wind = "calm"
    elif (windSpeed >= 1 and windSpeed < 4):
        wind = "light air"
    elif (windSpeed >= 4 and windSpeed < 8):
        wind = "light breeze"
    elif (windSpeed >= 9 and windSpeed < 13):
        wind = "gentle breeze"
    elif (windSpeed >= 13 and windSpeed < 19):
        wind = "moderate breeze"
    elif (windSpeed >= 19 and windSpeed < 25):
        wind = "fresh breeze"
    elif (windSpeed >= 25 and windSpeed < 32):
        wind = "strong breeze"
    elif (windSpeed >= 32 and windSpeed < 39):
        wind = "high wind"

    return wind

def get_windbearing(bearing):
    if (bearing >= 343 or bearing < 23):
        return "north"
    if (bearing >=23 and bearing < 68):
        return "northeast"
    if (bearing >=68 and bearing < 113):
        return "east"
    if (bearing >= 113 and bearing < 158):
        return "southeast"
    if (bearing >= 158 and bearing < 203):
        return "south"
    if (bearing >= 203 and bearing < 248):
        return "southwest"
    if (bearing >= 248 and bearing < 293):
        return "west"
    if (bearing >= 293 and bearing < 343):
        return "northwest"

def digest(conditions):
    if (str(type(conditions)) == "<class 'forecastio.models.ForecastioDataPoint'>"):
        digest = conditions.summary

        clouds = get_clouds(conditions.cloudCover)
        if clouds != "":
            digest += ', ' + clouds

        digest += ', ' + get_windspeed(conditions.windSpeed)
        if (conditions.windSpeed >=9):
            digest += ' from the ' + get_windbearing(conditions.windBearing)

        digest += ', ' + str(int(conditions.temperature)) + ' F'
        return digest
    elif (str(type(conditions)) == "<class 'forecastio.models.ForecastioDataBlock'>"):
        # Data block
        digest = conditions.summary
        for db in conditions.data:
            # we want to show the weather at 8 am, noon, 4 pm, and 8 pm
            if mytime.dt_format(mytime.datetime_from_string(str(db.time),1), 'time') == "08:00 AM":
                digest += '\n' + '  *  8 AM: ' + db.summary + ', ' + str(int(db.temperature)) + ' F'
            elif mytime.dt_format(mytime.datetime_from_string(str(db.time),1), 'time') == "10:00 AM":
                digest += '\n' + '  * 10 AM: ' + db.summary + ', ' + str(int(db.temperature)) + ' F'
            elif mytime.dt_format(mytime.datetime_from_string(str(db.time),1), 'time') == "12:00 PM":
                digest += '\n' + '  * 12 PM: ' + db.summary + ', ' + str(int(db.temperature)) + ' F'
            elif mytime.dt_format(mytime.datetime_from_string(str(db.time),1), 'time') == "04:00 PM":
                digest += '\n' + '  *  4 PM: ' + db.summary + ', ' + str(int(db.temperature)) + ' F'
            elif mytime.dt_format(mytime.datetime_from_string(str(db.time),1), 'time') == "08:00 PM":
                digest += '\n' + '  *  8 PM: ' + db.summary + ', ' + str(int(db.temperature)) + ' F'

            #print db.time
            #print db.summary
            #print db.icon
            #print get_weather_attribute(db, 'sunriseTime')
            #print get_weather_attribute(db, 'sunsetTime')
            #print get_weather_attribute(db, 'moonPhase')
            #print get_weather_attribute(db, 'precipType')
            #print get_weather_attribute(db, 'precipAccumulation')
            #print get_weather_attribute(db, 'temperatureMin')
            #print get_weather_attribute(db, 'temperatureMax')
        return digest

def get_weather_attribute(data_block, attribute):
    try:
        if attribute == 'sunriseTime':
            value = data_block.sunriseTime
        elif attribute == 'sunsetTime':
            value = data_block.sunsetTime
        elif attribute == 'moonPhase':
            value = data_block.moonPhase
        elif attribute == 'precipType':
            value = data_block.precipType
        elif attribute == 'precipAccumulation':
            value = data_block.precipAccumulation
        elif attribute == 'temperatureMin':
            value = data_block.temperatureMin
        elif attribute == 'temperatureMax':
            value = data_block.temperatureMax
    except AttributeError:
        value = None
    return value

def conditions(lat, lon, dt):
    api_key = myconfig.get_setting('weather_api')

    # Okay, is dt past, present, or currently
    now_local = mytime.now()
    seconds = mytime.epoch_from_datetime(now_local) - mytime.epoch_from_datetime(dt)
    if (seconds >= 0 and seconds < 3600):
        # Within the hour - check the cache first
        try:
            forecast = forecastio.load_forecast(api_key, lat, lon)
            update_weather_obs(dt, lat, lon, forecast.currently())
        except:
            return "NULL"
        else:
            return forecast.currently()
    elif (seconds > 3600):
        # In the past - check the repo first
        try:
            forecast = forecastio.load_forecast(api_key, lat, lon, time=dt)
        except:
            return "NULL"
        #update_weather_obs(dt, lat, lon, forecast.currently())
        else:
            return forecast.currently()
    elif (seconds < 0):
        # In the future - get a forecast, but don't update obs
        try:
            forecast = forecastio.load_forecast(api_key, lat, lon, time=dt)
        except:
            forecast = "NULL"
        if (abs(seconds) < 60*60*24*2):
            # Within the next 2 days
            if forecast == "NULL":
                return forecast
            else:
                return forecast.hourly()
        else:
            # Can only go a week out
            if forecast == "NULL":
                return forecast.daily()
            else:
                return "NULL"

def local_conditions(dt):
    lat, lon = whereami.coords()
    return conditions(lat, lon, dt)

def update_weather_obs(dt, lat, lon, forecast):
    weather_summary = forecast.summary
    weather_icon = forecast.icon
    weather_temp = forecast.temperature
    weather_dewpoint = forecast.dewPoint
    weather_windspeed = forecast.windSpeed
    weather_winddir = forecast.windBearing
    weather_cloudcover = forecast.cloudCover
    weather_humidity = forecast.humidity
    weather_pressure = forecast.pressure
    weather_visibility = forecast.visibility

    # Write observation to file
    REPO_PATH = myconfig.get_setting('repo_path')
    LOCATION_REPO = os.path.join(REPO_PATH, "weather.txt")
    if (os.path.isfile(LOCATION_REPO)):
        file_obj = open(LOCATION_REPO, "a")
    else:
        file_obj = open(LOCATION_REPO ,"w")

    observation = str(dt.isoformat()) + ','
    observation += str(lat) + ','
    observation += str(lon) + ','
    observation += weather_summary + ','
    observation += weather_icon + ','
    observation += str(weather_temp) + ','
    observation += str(weather_dewpoint) + ','
    observation += str(weather_windspeed) + ','
    observation += str(weather_winddir) + ','
    observation += str(weather_cloudcover) + ','
    observation += str(weather_humidity) + ','
    observation += str(weather_pressure) + ','
    observation += str(weather_visibility)
    file_obj.write(observation + '\n')
    file_obj.close()


def cache_time():
    # Gets the last update/time of the cache file
    this_dir, this_file = os.path.split(__file__)
    CACHE_FILE = os.path.join(this_dir, "data/weather.cache")
    if (os.path.isfile(CACHE_FILE)):
        mod_time = os.path.getmtime(CACHE_FILE)
    else:
        mod_time = 0
    return mod_time

def update_cache(dt, lat, lon, forecast):
    this_dir, this_file = os.path.split(__file__)
    CACHE_FILE = os.path.join(this_dir, "data/weather.cache")
    file_obj = open(CACHE_FILE, "w")
    conditions = forecast.currently()
    file_obj.write(dt.isoformat() + ',' + lat + ',' +lon + ',' + conditions.summary + ',' + conditions.icon + ',' + conditions.temperature + '\n')
    file_obj.close()

#def digest(forecast):
