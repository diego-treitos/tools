#!/usr/bin/env python
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

import schedulereader
import necromancer
import hashlib
import os, sys


# VARIABLES
CONFIG_FILE = '/etc/power_scheduler.cfg'
DATA_FILE= '/var/run/power_scheduler.data' #IMPORTANT This file has to be deleted on poweroff, so its a good idea to keep it in a ram partition



# FUNCTIONS
def get_cfg_md5():
	if os.path.exists( CONFIG_FILE ):
		m = hashlib.md5()
		for l in file( CONFIG_FILE ).readlines():
			m.update(l)
		return m.hexdigest()
	return None

def read_last_cfg_md5():
	if os.path.exists( DATA_FILE ):
		return file( DATA_FILE ).readline().replace('\n','')
	return None

def write_cfg_md5( md5 ):
	f=file( DATA_FILE, 'w')
	f.write( md5 )
	f.close()


# MAIN CODE
last_md5 = read_last_cfg_md5()
if last_md5 == get_cfg_md5():
	sys.exit(0)

write_cfg_md5( get_cfg_md5() )

r = schedulereader.schedulereader( schedule_file=CONFIG_FILE )
n = necromancer.Necromancer()


# Set the RTC clock to UTC based on system time
n._set_hwclock()


if r.pon_date:
	n.poweron( r.pon_date )
#	print 'pon: ',
#	print r.pon_date
else:
	print "Warning, no power on date has been configured !"


if r.poff_date:
	n.poweroff( r.poff_date )
#	print 'poff: ',
#	print r.poff_date


from pprint import pprint
pprint(n.status())
