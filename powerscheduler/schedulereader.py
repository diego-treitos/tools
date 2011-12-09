#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
# Power Scheduler
# Copyright (C) 2011 Diego Blanco
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#			  
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#						
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import ConfigParser
import time, datetime


class schedulereader:
	""" It assumes a configuration file in the format:

	[week]
	Monday = 8.30-20.00
	Tuesday = 8.30-13.15
	Wednesday = 8.30-20.00
	Thursday = 8.30-21.00
	Friday = 8.30-19.00
	Saturday = 
	Sunday = 8.30-20.00

	[exceptions]
	Nov_25 = 8.30-22.00


	Where exceptions format is:
	<month>_<day of month>

	month must be one of: Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec

	Schedules can be:
	
	[poweron_hour]-[poweroff_hour]
	Examples:
	8.30-12.15 -> power on at 8.30 and off at 12.15
	    -22.00 -> power off at 22.00 (check if it is an scheduled power on before the power off)
	9.00-      -> power on at 9.00 and leave it on

	KNOWN BUGS:

	       * Its not contemplated that al week days to be unscheduled and schedule just exceptions

	"""

	def __init__(self, schedule_file='/etc/power_scheduler.cfg'):

		
		self.__config = ConfigParser.ConfigParser()
		self.__prepare( schedule_file )
		self.__localtime = time.localtime()

		self.weekdict = {
				0:'Monday',
				1:'Tuesday',
				2:'Wednesday',
				3:'Thursday',
				4:'Friday',
				5:'Saturday',
				6:'Sunday'
				}

		self.exception_pattern = '%b_%d'

		self.poff_date = self.__get_poff_date()
		self.pon_date = self.__get_pon_date()


	def __prepare(self, schedfile):
		self.__config.read( schedfile )


	def __get_poff_date(self):
		# First of all, lets check exceptions
		# Is today an exception ?
		sched = None
		for exception_day in self.__config.options('exceptions'):
			t = time.strptime( exception_day , self.exception_pattern )
			if (t.tm_mon == self.__localtime.tm_mon) and (t.tm_mday == self.__localtime.tm_mday):
				sched = self.__config.get('exceptions', exception_day).split('-')

		# Which day is today ?
		if not sched:
			wtoday = self.weekdict[ self.__localtime.tm_wday ]
			sched = self.__config.get('week', wtoday).split('-')


		if not (sched.__len__() > 1):
			return None
		elif sched[1] != '':
			hour=sched[1]
			if hour.find(':') != -1:
				hour = hour.split(':')
			else:
				hour = hour.split('.')

			pattern = '%Y-%m-%d %H:%M'
			dateline = '%s-%s-%s %s:%s' % ( self.__localtime.tm_year, self.__localtime.tm_mon, self.__localtime.tm_mday, hour[0], hour[1] )
			return time.strptime(dateline, pattern)
		else:
			return None
		#NOTE: If today schedule is empty, it doesnt matter. We can schedule the poweroff tomorrow.
	

	def __get_pon_date(self):
		nextday = (datetime.date.today() + datetime.timedelta(days=1)).timetuple()
		sched = None

		# Lets find the next scheduled poweron hour
		wnext = self.weekdict[ nextday.tm_wday ]
		i=1
		while self.__config.get('week', wnext).split('-')[0] == '' and i<8:
			i+=1
			nextday = (datetime.date.today()+datetime.timedelta( days = i )).timetuple()
			wnext = self.weekdict[ nextday.tm_wday ]
		if i==8:
			return None
		else:
			sched = self.__config.get('week', wnext).split('-')
		
		
		# Is nextday an exception ?
		for exception_day in self.__config.options('exceptions'):
			t = time.strptime( exception_day , self.exception_pattern )
			if (t.tm_mon == nextday.tm_mon) and (t.tm_mday == nextday.tm_mday):
				sched = self.__config.get('exceptions', exception_day).split('-')

	
		hour=sched[0]
		if hour.find(':') != -1:
			hour = hour.split(':')
		else:
			hour = hour.split('.')

		pattern = '%Y-%m-%d %H:%M'
		dateline = '%s-%s-%s %s:%s' % ( nextday.tm_year, nextday.tm_mon, nextday.tm_mday, hour[0], hour[1] )
		return time.strptime(dateline, pattern)

