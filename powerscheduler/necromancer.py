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

import os
import time
from subprocess import Popen

class NecroException(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		return repr(self.value)


class Necromancer:

	def __init__(self):
		self.rtc_alarm_file='/sys/class/rtc/rtc0/wakealarm'
		self.rtc_check_file='/proc/driver/rtc'
		self.cron_file='/etc/cron.d/necromancer_poweroff'

		# Check what we can do
		self.__check()


	def __check(self):
		# Am I root ?
		if os.geteuid() != 0:
			raise NecroException( 'root permissions needed to complete task' )

		# Do the needed files exist ? (AKA Do I support rtc alarm ?)
		if not os.path.exists( self.rtc_alarm_file ):
			raise NecroException( 'No such file or directory: ' + "'"+self.rtc_alarm_file+"'")
		if not os.path.exists( self.rtc_check_file ):
			raise NecroException( 'No such file or directory: ' + "'"+self.rtc_check_file+"'")

	def __get_rtc_offset(self):
		rtc_time=''
		rtccheck = file( self.rtc_check_file)
		for l in rtccheck.readlines():
			if l.split(':')[0].strip() == 'rtc_time':
				rtc_time=l.split(':')[1:]

		rtc_time = int(rtc_time[0])*3600 + int(rtc_time[1])*60 + int(rtc_time[2])
		ltime = time.localtime()
		ltime = ltime.tm_hour*3600 + ltime.tm_min*60 + ltime.tm_sec

		return ltime - rtc_time

	def _set_hwclock(self):
		Popen('hwclock --set --date $(date -u +%H:%M:%S)', shell=True)

	def poweroff(self, _date):
		""" poweroff(date)

		 Sets the specified date in the format 'struct_time' to power off the computer.
		
		"""
		
		cronline = "%d %d %d %d * root shutdown -h now;rm %s\n" % (_date.tm_min, _date.tm_hour, _date.tm_mday, _date.tm_mon, self.cron_file)

		cronalarm = file(self.cron_file,'w')
		cronalarm.write(cronline)
		cronalarm.close()


	def poweron(self, _date):
		""" poweron(date)

		 Sets the specified date in the format 'struct_time' to power on the computer.
		
		"""

		date = time.mktime(_date)

		rtcalarm = file( self.rtc_alarm_file,'w')
		rtcalarm.write(str(0))
		rtcalarm.close()
		
		rtcalarm = file( self.rtc_alarm_file,'w')
		rtcalarm.write(str(date))
		rtcalarm.close()


	def status(self):
		""" status()

		 Returns a 'dict' like:

		 {
		 	poweron: <None, struct_time>,
		 	poweroff: <None, struct_time>
		 }
		
		"""

		# Get the poweron date
		alrm_time=''
		alrm_date=''
		rtccheck = file( self.rtc_check_file)
		for l in rtccheck.readlines():
			if l.split(':')[0].strip() == 'alrm_time':
				alrm_time=':'.join(l.split(':')[1:]).strip()
			if l.split(':')[0].strip() == 'alrm_date':
				alrm_date=l.split(':')[1].strip()

		pattern = '%Y-%m-%d %H:%M:%S'
		poweron_epoch = time.mktime(time.strptime(alrm_date+" "+alrm_time, pattern)) + self.__get_rtc_offset()
		poweron_date = time.localtime(poweron_epoch)
		
		
	
		# Get the poweroff date
		try:
			cronalarm = file(self.cron_file)
			cronline = cronalarm.readline()
			cronalarm.close()
			
			pattern = "%%Y %%M %%H %%d %%m * root shutdown -h now;rm %s\n" % self.cron_file
			poweroff_date = time.strptime(str(time.localtime().tm_year) + ' ' + cronline, pattern)
		except IOError, e:
			poweroff_date = None

		return {
				'poweron': poweron_date,
				'poweroff': poweroff_date
				}


#a = Necromancer()
#a.poweron(time.strptime('2011-8-26 14:30:15','%Y-%m-%d %H:%M:%S'))
#print a.status()
