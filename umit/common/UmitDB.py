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


try:
    from hashlib import md5
except ImportError:
    # Python 2.4 - Workaround to keep compatible with >= Python2.5
    from md5 import md5

from umit.core.I18N import _

sqlite = None
OperationalError = None
try:
    from pysqlite2 import dbapi2 as sqlite
    from pysqlite2.dbapi2 import OperationalError
except ImportError:
    try:
        # In case this script is being running under python2.5 with sqlite3
        import sqlite3 as sqlite
    except ImportError:
        raise ImportError(_("""No module named pysqlite2 or sqlite3.
            Please install pysqlite2 or sqlite3."""))
    from sqlite3 import OperationalError

from time import time

from umit.core.Paths import Path
from umit.core.UmitLogging import log


umitdb = ""

try:
    umitdb = Path.umitdb
except:
    import os.path
    from BasePaths import base_paths
    
    umitdb = os.path.join(Path.config_dir, base_paths["umitdb"])
    Path.umitdb = umitdb


from os.path import exists, dirname
from os import access, R_OK, W_OK


using_memory = False
connection = None
try:
    connection = sqlite.connect(umitdb)
except OperationalError:
    using_memory = True
    connection = sqlite.connect(":memory:")

# Always return bytestring from the TEXT data type, we will manually handle it.
try:
    connection.text_factory = str
except AttributeError:
    # XXX text_factory didn't exist prior to pysqlite 2.1.0 and TEXT will
    # always return a unicode object. Given how Umit handles the situation,
    # we can't assume this won't cause troubles.
    pass


class Table(object):
    def __init__(self, table_name):
        self.table_name = table_name
        self.table_id = "%s_id" % table_name
        
        self.cursor = connection.cursor()
    
    def get_item(self, item_name):
        if self.__getattribute__("_%s" % item_name):
            return self.__getattribute__("_%s" % item_name)

        sql = "SELECT %s FROM %s WHERE %s_id = %s" % (item_name,
                                                      self.table_name,
                                                      self.table_name,
                                           self.__getattribute__(self.table_id))

        self.cursor.execute(sql)
        
        self.__setattr__("_%s" % item_name, self.cursor.fetchall()[0][0])
        return self.__getattribute__("_%s" % item_name)

    def set_item(self, item_name, item_value):
        if item_value == self.__getattribute__("_%s" % item_name):
            return None
        
        sql = "UPDATE %s SET %s = ? WHERE %s_id = %s" % (self.table_name,
                                                         item_name,
                                                         self.table_name,
                                           self.__getattribute__(self.table_id))
        self.cursor.execute(sql, (item_value,))
        connection.commit()
        self.__setattr__("_%s" % item_name, item_value)

    def insert(self, **kargs):
        sql = "INSERT INTO %s ("
        for k in kargs:
            sql += k
            sql += ", "
        else:
            sql = sql[:][:-2]
            sql += ") VALUES ("
            
        for v in xrange(len(kargs.values())):
            sql += "?, "
        else:
            sql = sql[:][:-2]
            sql += ")"

        sql %= self.table_name
        
        self.cursor.execute(sql, tuple(kargs.values()))
        connection.commit()

        sql = "SELECT MAX(%s_id) FROM %s;" % (self.table_name, self.table_name)
        self.cursor.execute(sql)
        return self.cursor.fetchall()[0][0]

class UmitDB(object):
    def __init__(self):
        self.cursor = connection.cursor()

    def create_db(self):
        drop_string = ("DROP TABLE scans;",)
        
        try:
            for d in drop_string:
                self.cursor.execute(d)
        except:
            connection.rollback()
        else:
            connection.commit()

        
        creation_string = ("""CREATE TABLE IF NOT EXISTS scans (scans_id INTEGER \
                                                  PRIMARY KEY AUTOINCREMENT,
                                                  scan_name TEXT,
                                                  nmap_xml_output TEXT,
                                                  digest TEXT,
                                                  date INTEGER)""",)

        for c in creation_string:
            self.cursor.execute(c)
            connection.commit()

    def add_scan(self, **kargs):
        return Scans(**kargs)

    def get_scans_ids(self):
        sql = "SELECT scans_id FROM scans;"
        self.cursor.execute(sql)
        return [sid[0] for sid in self.cursor.fetchall()]

    def get_scans(self):
        scans_ids = self.get_scans_ids()
        for sid in scans_ids:
            yield Scans(scans_id=sid)

    def cleanup(self, save_time):
        log.debug(">>> Cleanning up data base.")
        log.debug(">>> Removing results olders than %s seconds" % save_time)
        self.cursor.execute("SELECT scans_id FROM scans WHERE date < ?",
                            (time() - save_time,))
        
        for sid in [sid[0] for sid in self.cursor.fetchall()]:
            log.debug(">>> Removing results with scans_id %s" % sid)
            self.cursor.execute("DELETE FROM scans WHERE scans_id = ?", (sid, ))
        else:
            connection.commit()
            log.debug(">>> Data base sucessfully cleanned up!")
        

class Scans(Table, object):
    def __init__(self, **kargs):
        Table.__init__(self, "scans")
        if "scans_id" in kargs:
            self.scans_id = kargs["scans_id"]
        else:
            log.debug(">>>Ceating new scan result entry at data base")
            fields = ["scan_name", "nmap_xml_output", "date"]
            
            for k in kargs:
                if k not in fields:
                    raise Exception("Wrong table field passed to creation \
method. '%s'" % k)

            if "nmap_xml_output" not in kargs or \
               not kargs["nmap_xml_output"]:
                raise Exception("Can't save result without xml output")
            h = md5(kargs["nmap_xml_output"])
            if not self.verify_digest(h.hexdigest()):
                raise Exception("XML output registered already!")
            
            self.scans_id = self.insert(**kargs)

    def verify_digest(self, digest):
        self.cursor.execute("SELECT scans_id FROM scans WHERE digest = ?",
                            (digest, ))
        result = self.cursor.fetchall()
        if result:
            return False
        return True

    def add_host(self, **kargs):
        kargs.update({self.table_id:self.scans_id})
        return Hosts(**kargs)

    def get_hosts(self):
        sql = "SELECT hosts_id FROM hosts WHERE scans_id= %s" % self.scans_id
        
        self.cursor.execute(sql)
        result = self.cursor.fetchall()
        
        for h in result:
            yield Hosts(hosts_id=h[0])

    def get_scans_id(self):
        return self._scans_id

    def set_scans_id(self, scans_id):
        if scans_id != self._scans_id:
            self._scans_id = scans_id

    def get_scan_name(self):
        return self.get_item("scan_name")

    def set_scan_name(self, scan_name):
        self.set_item("scan_name", scan_name)

    def get_nmap_xml_output(self):
        return self.get_item("nmap_xml_output")

    def set_nmap_xml_output(self, nmap_xml_output):
        self.set_item("nmap_xml_output", nmap_xml_output)
        h = md5(nmap_xml_output)
        self.set_item("digest", h.hexdigest())

    def get_date(self):
        return self.get_item("date")

    def set_date(self, date):
        self.set_item("date", date)
    
    scans_id = property(get_scans_id, set_scans_id)
    scan_name = property(get_scan_name, set_scan_name)
    nmap_xml_output = property(get_nmap_xml_output, set_nmap_xml_output)
    date = property(get_date, set_date)
    
    _scans_id = None
    _scan_name = None
    _nmap_xml_output = None
    _date = None


######################################################################
# Verify if data base exists and if it does have the required tables.
# If something is wrong, re-create table
def verify_db():
    cursor = connection.cursor()
    try:
        cursor.execute("SELECT scans_id FROM scans WHERE date = 0")
    except sqlite.OperationalError:
        u = UmitDB()
        u.create_db()
verify_db()

######################################################################

if __name__ == "__main__":
    from pprint import pprint
    import psyco
    psyco.profile()
    
    u = UmitDB()

    #print "Creating Data Base"
    #u.create_db()

    #print "Creating new scan"
    #s = u.add_scan(scan_name="Fake scan", nmap_xml_output="", date="007")

    #s = Scans(scans_id=2)
    #print s.scans_id
    #print s.scan_name
    #print s.nmap_xml_output
    #print s.date
    
    sql = "SELECT * FROM scans;"
    u.cursor.execute(sql)
    print "Scans:",
    pprint(u.cursor.fetchall())
