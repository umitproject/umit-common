#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2005-2006 Insecure.Com LLC.
# Copyright (C) 2007-2008 Adriano Monteiro Marques
#
# Author: Adriano Monteiro Marques <adriano@umitproject.org>
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

import locale

from umit.core.BasePaths import LOCALE_DIR

try:
    # If the content of the environment variable LANG contains a string which
    # represents a language or encoding not supported by the system, the 
    # following line will raise an exception.
    LC_ALL = locale.setlocale(locale.LC_ALL, '')
except locale.Error, error_msg:
    # Here we tell user that it's system is set to an unsupported language,
    # and that Umit will proceed using the system's default.
    # Latter, we call setlocale again, but now providing None as the second
    # argument, avoiding the occourrance of the exception.
    # Gtk will raise a warning in this case, but will work just perfectly.
    print "Your locale setting is not supported. Umit will continue using \
using your system's preferred language."
    LC_ALL = locale.setlocale(locale.LC_ALL, None)

LANG, ENC = locale.getdefaultlocale()
ERRORS = "ignore"

# If not correct locale could be retrieved, set en_US.utf8 as default
if ENC is None:
    ENC = "utf8"

if LANG is None:
    LANG = "en_US"

try:
    import gettext
except ImportError:
    # define _() so program will not fail
    import __builtin__
    __builtin__.__dict__["_"] = str
else:
    lang = gettext.translation('umit', LOCALE_DIR, [LANG], fallback=True)
    _ = lang.gettext


def enc(string):
    """Encoding conversion. This function is entended to receive a locale
    created string with locale encoding and return an utf8 string.
    """
    # FIXME: Urgent! Find a way to make the encodings work here, decoding
    # from the correct codec and encoding to utf8, which should be the
    # pattern here. Currently, this only removes the chars that it can't encode,
    # and thus, the text may be very hard to understand, but yet, no error will
    # occour
    string = string.decode("utf8", ERRORS).encode("utf8", ERRORS)

    return string

if __name__ == '__main__':
    print _('Umit - Take the red pill')
