#!/usr/bin/env python

from time import sleep, localtime, strftime
from subprocess import Popen, PIPE
from threading import Thread
import os


#( Classes
class Pylot(Thread):

    def __init__(self, name, cmd, restart_on=None, flush_output=True):
        """ name: process name to be identified
         cmd: string with command and arguments to execute
         flush_output: send all stderr and stdout output to /dev/null."""
        # Thread init
        Thread.__init__(self)
        
        self.name = name

        self.pid = None
        self.stderr = None
        self.stdout = None
        self.stdin  = None
       
        # Private attrs
        self.__cmd = cmd
        self.__p = None
        self.__psh = None
        self.__stop = False
        self.__flush_output = flush_output


    def __stop_program(self):
        if self.__p and self.__p.poll() == None:
            print '%s  <= Stopping process name "%s" ...' % (strftime("%y-%m-%d %H:%M:%S", localtime()), self.name)
            try:
                self.__p.terminate()
                self.__psh.terminate()
                self.__p.kill()
                self.__psh.kill()
            except OSError:
                pass


    def __start_program(self):
        print '%s  => Starting process name "%s" ...' % (strftime("%y-%m-%d %H:%M:%S", localtime()), self.name)
        if not self.__flush_output:
            so = PIPE
        else:
            so = file(os.devnull,'a')

        self.__p = Popen( self.__cmd.split(), stderr=so , stdout=so, stdin=PIPE )
        self.__psh = Popen('while [ -d /proc/%d ];do sleep 1; [ -d /proc/%d ] || kill -9 %d 2>/dev/null;done' % (self.__p.pid, os.getpid(), self.__p.pid), shell=True)
        
        # Set info
        self.stdin = self.__p.stdin
        self.pid = self.__p.pid
      
        # Set stdout and stderr to Popen ones
        if not self.__flush_output:
            self.stdout = self.__p.stdout
            self.stderr = self.__p.stderr


    def stop(self):
        """ stop() -> None
        Stops process"""
        self.__stop = True
        self.__stop_program()

    def isStopped(self):
        """ isStopped() -> Bool
        Checks if process is stopped."""
        return self.__stop

    def run(self):
        """ start()
        Starts execution."""
        self.__start_program()
        while not self.__stop:
            self.__p.wait()
            if not self.__stop:
                self.__stop_program()
                print '%s  == Process name "%s" died. Restarting... ' % (strftime("%y-%m-%d %H:%M:%S", localtime()), self.name)
                sleep(1)
                self.__start_program()


class PylotManager(Thread):

    def __init__(self):
        # Thread init
        Thread.__init__(self)
        # pylot_name:<Pylot>
        self.__pylots = {}
        self.__stop = True

    def __checkStatus(self):
        return self.__stop

    def stopPylot(self, p_name):
        "Stops given pylot name 'p_name'"
        self.__pylots[ p_name ].stop()
        self.__pylots.pop( p_name )
        while self.checkPylot( p_name ):
            sleep(0.5)
    
    def stop(self):
        "Stops all pylots."
        for c in self.__pylots.keys():
            self.stopPylot( c )
        self.__stop = True

    def addPylot(self, name, cmd, flush_output=True):
        """ name: process name to be identified
         cmd: string with command and arguments to execute
         flush_output: send all stderr and stdout output to /dev/null."""
        if self.__checkStatus(): return
        if not isinstance(cmd,( str,unicode )):
            print "'cmd' is not a string."
            return False
        if self.checkPylot( name ):
            print "Pylot '%s' already exists !" % name
            return False
        self.__pylots[ name ] = Pylot( name, cmd, flush_output )
        self.__pylots[ name ].start()
        sleep(0.1)
    
    def checkPylot(self, p_name):
        if self.__checkStatus(): return
        """Checks if the pylot 'p_name' is still running.
        Returns True if it so or False if not."""
        if self.__pylots.has_key( p_name ):
            if not self.__pylots[ p_name ].isStopped():
                return True
            else:
                self.__pylots.pop( p_name )
        return False

    def getPylots(self):
        """Returns a dictionary of 'pylot_name:<Pylot>'"""
        return self.__pylots

    def run(self):
        self.__stop = False
        while not self.__stop:
            sleep(10)
            # Clean pylots
            for p in self.__pylots.keys():
                self.checkPylot(p)


