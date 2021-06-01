#!/bin/bash
# vim: set ts=2 sw=2 sts=2 et:

#  clamav_cron.sh. Script to scan for viruses.
#  Copyright (C) 2020  Diego Blanco
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, version 2 of the License.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


#( options
last_n_minutes=60
notification_mail=''
log_days_keep=7
ionice=3
cpunice=15
#)

#( globals
log_dir="/var/log/clamav/"
log_file="$log_dir/clamav_cron_`date +%Y%m%d_%H%M`.log"
tmp_file=`mktemp -t clamav_cron.XXXXXX` || exit 1
#)

#( lib
do_help() {
  echo "Use: $0 [options]" 
  echo
  echo " OPTIONS"
  echo "  -h           This help"
  echo "  -m MINUTES   Scan only files modified during the last MINUTES number of minutes. Default 60."
  echo "  -n MAIL      In case of infected files were found, notify to MAIL."
}
do_clean()  {
	rm -f "$tmp_file"
  gzip "$log_file"
  find $log_dir -name "*${clamav_cron}_*" -mtime +${log_days_keep} -exec ionice -c3 rm -f {} +
}
do_error() {
  echo -e "ERROR: $*"
	do_clean
  exit 1
}
do_check() {
  which mail > /dev/null || do_error "The 'mail' program was not found."
  which clamscan > /dev/null || do_error "The 'clamscan' program was not found."
  which nice > /dev/null || do_error "The 'nice' program was not found."
  which ionice > /dev/null || do_error "The 'ionice' program was not found."
  [ -d "$log_dir" ] || do_error "The directory for logs '$log_dir' does not exist."
  [ -z "$notification_mail" ] || do_error "No notification email provided. Use '-m' option."
}
#)

#( main
while getopts "hm:n:" option; do
  case "${option}" in
    m) shift; last_n_minutes=$OPTARG;;
    n) shift; notification_mail=$OPTARG;;
    h) do_help; exit 0;;
    *) do_help; exit 1;;
  esac
done

do_check

ionice -c 3 nice -n 20 \
	find / -path /proc -prune -o -path /sys -prune -o -path /dev -prune -o \
	 -type f -mtime "-${last_n_minutes}" -fprint "$tmp_file"

[ -s "$tmp_file" ] && ionice -c$ionice nice -n $cpunice clamscan -io -l "$log_file" -f "$tmp_file" ||\
	echo -e "ClamAV ERROR\n------------\n\n`cat $log_file`" | mail -s "ClamAV Cron ERROR" "$notification_mail"

do_clean
#)
