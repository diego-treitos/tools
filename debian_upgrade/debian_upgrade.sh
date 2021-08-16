#!/bin/bash
# vim: set ts=2 sw=2 sts=2 et:

#  debian_upgrade.sh. Script to upgrade Debian GNU/Linux systems.
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

#( include
source /etc/os-release

#( globals
pre_hook=""
post_hook=""
dontask=false
deb_releases=(
0
1
2
3
4
5
squeeze
wheezy
jessie
stretch
buster
bullseye
)
deb_release_current=""
deb_release_limit=999
deb_release_next=""
tmux_session_name="debian_upgrade"
#)

#( Colors
#
# fg
red='\e[31m'
lred='\e[91m'
green='\e[32m'
lgreen='\e[92m'
yellow='\e[33m'
lyellow='\e[93m'
blue='\e[34m'
lblue='\e[94m'
magenta='\e[35m'
lmagenta='\e[95m'
cyan='\e[36m'
lcyan='\e[96m'
grey='\e[90m'
lgrey='\e[37m'
white='\e[97m'
black='\e[30m'
#
# bg
b_red='\e[41m'
b_lred='\e[101m'
b_green='\e[42m'
b_lgreen='\e[102m'
b_yellow='\e[43m'
b_lyellow='\e[103m'
b_blue='\e[44m'
b_lblue='\e[104m'
b_magenta='\e[45m'
b_lmagenta='\e[105m'
b_cyan='\e[46m'
b_lcyan='\e[106m'
b_grey='\e[100m'
b_lgrey='\e[47m'
b_white='\e[107m'
b_black='\e[40m'
#
# special
reset='\e[0;0m'
bold='\e[01m'
italic='\e[03m'
underline='\e[04m'
inverse='\e[07m'
conceil='\e[08m'
crossedout='\e[09m'
bold_off='\e[22m'
italic_off='\e[23m'
underline_off='\e[24m'
inverse_off='\e[27m'
conceil_off='\e[28m'
crossedout_off='\e[29m'
#)

#( lib
do_help() {
  echo "Use: $0 [options]" 
  echo
  echo " OPTIONS"
  echo "  -l <version> Limit version number to upgrade to"
  echo "  -p <command> Command to execute as a pre-hook"
  echo "  -P <command> Command to execute as a post-hook"
  echo "  -y           Non interactive"
  echo "  -h           This help"
}
msg_info() {
  printf "\n${white}[${blue}+${white}]${reset} $*\n\n"
  sleep 2
}
msg_error() {
  printf "\n${white}[${red}!${white}]${reset} $*\n\n"
  sleep 2
}
msg_ask() {
  printf "\n${white}[${green}?${white}]${reset} $*"
  sleep 2
}
do_requirements() {
  [ $deb_release_limit -le $(($VERSION_ID)) ] && msg_info "Cannot update. Reached version limit of ${red}$deb_release_limit${reset}" && exit 0
  for i in "${!deb_releases[@]}"; do
    if [ "$VERSION_ID" == "$i" ]; then
      export deb_release_current="${deb_releases[$i]}"
      export deb_release_next="${deb_releases[$((i+1))]}"
    fi
  done
  [ -z "$deb_release_current" ] && msg_error "Current release unknown." && exit 1
  [ -z "$deb_release_next" ] && msg_error "Next release unknown." && exit 1
  if ! which tmux >/dev/null 2>&1; then
    apt-get update && \
      env DEBIAN_FRONTEND=noninteractive APT_LISTCHANGES_FRONTEND=mail apt-get install tmux -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'
  fi
}
do_upgrade() {
  local upgcmd
  upgcmd="upgrade"
  [ "$1" == "dist-upgrade" ] && upgcmd="dist-upgrade"

  env DEBIAN_FRONTEND=noninteractive APT_LISTCHANGES_FRONTEND=mail apt-get "$upgcmd" -y -o Dpkg::Options::='--force-confdef' -o Dpkg::Options::='--force-confold'
}
do_switch() {
  # Disable non-official repos
  for l in /etc/apt/sources.list.d/*.list; do
    sed -i 's/^deb /#deb /g' "$l"
  done
  # Change release-name
  sed -i "s/$deb_release_current/$deb_release_next/g" /etc/apt/sources.list

  # Change security repo structure from buster to bullseye
  sed -i "s#debian-security buster/updates#debian-security bullseye-security#g"
}
do_pre_hook() { eval "$pre_hook"; }
do_post_hook() { eval "$post_hook"; }
#)

#( main
while getopts "hl:p:P:y" option; do
  case "${option}" in
    l) deb_release_limit="$((${OPTARG}))";;
    p) pre_hook="${OPTARG}";;
    P) post_hook="${OPTARG}";;
    y) dontask=true;;
    h) do_help; exit 0;;
    *) do_help; exit 1;;
  esac
done

msg_info "Checking requirements..."
if ! do_requirements; then
  msg_error "Error while fixing requirements"
  exit 1
fi

if ! $dontask; then
  msg_ask "Last chance to ABORT!\n    You are going to upgrade to '${yellow}$deb_release_next${reset}'.\n    The upgrade could damage your installation so be sure to have backups.\n    ${grey}Non official repositories will be commented out before upgrade.\n\n    ${grey}Reply exactly ${green}yEs${grey} if you want to continue.\n    ${white}Do you want to continue? [${red}N${white}/${green}yEs${white}]${reset}: "
  read -r shallpass 
  [ "$shallpass" == "yEs" ] || exit 0
fi

if [ -z "$TMUX" ]; then
  msg_info "Starting tmux session with name '${cyan}$tmux_session_name${reset}' and running script inside. Use '${white}tmux a -t $tmux_session_name${reset}' to check the upgrade status."
  tmux new-session -d -s "$tmux_session_name" && \
    tmux send-keys -t "$tmux_session_name:0" "$0 -p \"$pre_hook\" -P \"$post_hook\" -y" C-m
  exit 0
fi

# RUN_INSIDE_TMUX

if [ "$pre_hook" ]; then
  msg_info "Executing pre-hook..."
  if ! do_pre_hook; then
    msg_error "Error while runnign pre-hook"
    exit 1
  fi
fi

msg_info "Updating current release..."
if ! (apt-get update && do_upgrade && do_upgrade dist-upgrade && apt-get autoremove -y); then
  msg_error "Error while initial update"
  exit 1
fi

if ! do_switch; then
  msg_error "Error while switching"
  exit 1
fi

msg_info "Upgrading to '${yellow}$deb_release_next${reset}' release..."
if ! (apt-get update && do_upgrade && do_upgrade dist-upgrade && apt-get autoremove -y); then
  msg_error "Error while initial update"
  msg_error "IMPORTANT NOTE: A failure in this stage requires manual examination. Keep an eye on the version if you run again this script."
  exit 1
fi

if [ "$post_hook" ]; then
  msg_info "Executing post-hook..."
  if ! do_post_hook; then
    msg_error "Error while runnign post-hook"
    exit 1
  fi
fi

msg_info "SYSTEM UPGRADED to '${yellow}$deb_release_next${reset}'. Please reboot."

#)
