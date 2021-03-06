#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Authors: Adriano Monteiro Marques <adriano@umitproject.org>
#          Zhongjie Wang <wzj401@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

__all__ = ['log', 'file_log']

from logging import Logger, StreamHandler, FileHandler, Formatter

#LOGLEVEL = option_parser.get_verbose()
LOGLEVEL = 0

class Log(Logger, object):
    def __init__(self, name, level=0, file_output=None, console=True):
        Logger.__init__(self, name, level)
        self.formatter = self.format

        if console:
            handler = StreamHandler()
            handler.setFormatter(self.formatter)
            self.addHandler(handler)

        if file_output:
            handler = FileHandler(file_output)
            handler.setFormatter(self.formatter)
            self.addHandler(handler)

    def get_formatter(self):
        return self.__formatter

    def set_formatter(self, fmt):
        self.__formatter = Formatter(fmt)


    format = "[%(levelname)s] - %(asctime)s - %(message)s"

    formatter = property(get_formatter, set_formatter, doc="")
    __formatter = Formatter(format)


def file_log(file_output):
    """
    Returns an Log instance that writes to file_output.
    Sets LOGLEVEL to 50, so every message is written.
    """
    try:
        open(file_output, 'a')
        return Log("Umit", 0, file_output, False)
    except IOError, err:
        raise Exception("Bad file output '%s' especified for saving log. \
Error: %s" % (file_output, err))


if __name__ == '__main__':
    log = Log("Umit", LOGLEVEL)
    log.debug("Debug Message")
    log.info("Info Message")
    log.warning("Warning Message")
    log.error("Error Message")
    log.critical("Critical Message")

    log = file_log("myoutput.log")
    log.debug("Debug Message")
    log.info("Info Message")
    log.warning("Warning Message")
    log.error("Error Message")
    log.critical("Critical Message")