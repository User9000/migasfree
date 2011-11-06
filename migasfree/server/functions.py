# -*- coding: UTF-8 -*-

import os
import sys
import errno
from datetime import timedelta

import django
from django.utils.translation import ugettext_lazy as _

from migasfree.settings import DATABASES, MIGASFREE_APP_DIR, MIGASFREE_REPO_DIR

def is_db_sqlite():
    return DATABASES['default']['ENGINE'] == 'django.db.backends.sqlite3'

def config_apache():
    _apache_path = ''
    if os.path.exists('/etc/apache/conf.d'):
        _apache_path = '/etc/apache/conf.d'
    elif os.path.exists('/etc/apache2/conf.d'):
        _apache_path = '/etc/apache2/conf.d'
    elif os.path.exists('/etc/httpd/conf.d'):
        _apache_path = '/etc/httpd/conf.d'

    if not _apache_path:
        print 'Apache path not found.'
        sys.exit(errno.ENOTDIR)

    # FIXME VirtualHost
    _config = \
"""
Alias /media/ %(django_dir)s/contrib/admin/media/

Alias /repo %(migasfree_repo_dir)s
<Directory %(migasfree_repo_dir)s>
    Order allow,deny
    Options Indexes FollowSymlinks
    Allow from all
    IndexOptions FancyIndexing
</Directory>

WSGIScriptAlias / %(migasfree_app_dir)s/django.wsgi
"""

    _filename = os.path.join(_apache_path, 'migasfree.conf')
    _write_web_config(_filename, _config)

def config_cherokee():
    _cherokee_conf = '/etc/cherokee/cherokee.conf'
    if not os.path.exists(_cherokee_conf):
        print 'Cherokee config not found.'
        sys.exit(errno.ENOTDIR)

    _config = \
"""
vserver!20!document_root = %(migasfree_repo_dir)s
vserver!20!match = wildcard
vserver!20!match!domain!1 = *
vserver!20!nick = www.migasfree.com
vserver!20!rule!220!document_root = %(django_dir)s/contrib/admin/media
vserver!20!rule!220!handler = common
vserver!20!rule!220!handler!backup = 0
vserver!20!rule!220!handler!date = 1
vserver!20!rule!220!handler!group = 0
vserver!20!rule!220!handler!hidden = 0
vserver!20!rule!220!handler!redir_symlinks = 0
vserver!20!rule!220!handler!size = 1
vserver!20!rule!220!handler!symlinks = 1
vserver!20!rule!220!handler!user = 0
vserver!20!rule!220!match = directory
vserver!20!rule!220!match!directory = /media
vserver!20!rule!120!document_root = %(migasfree_repo_dir)s
vserver!20!rule!120!handler = common
vserver!20!rule!120!match = directory
vserver!20!rule!120!match!directory = /repo
vserver!20!rule!20!handler = uwsgi
vserver!20!rule!20!handler!balancer = round_robin
vserver!20!rule!20!handler!balancer!source!10 = 1
vserver!20!rule!20!handler!check_file = 0
vserver!20!rule!20!handler!error_handler = 1
vserver!20!rule!20!handler!modifier1 = 0
vserver!20!rule!20!handler!modifier2 = 0
vserver!20!rule!20!handler!pass_req_headers = 1
vserver!20!rule!20!match = directory
vserver!20!rule!20!match!directory = /
vserver!20!rule!10!handler = common
vserver!20!rule!10!handler!iocache = 0
vserver!20!rule!10!match = default
source!1!env_inherited = 1
source!1!host = 127.0.0.1:32942
source!1!interpreter = /usr/sbin/uwsgi -s 127.0.0.1:32942 -M -p 2 -z 15 -L -l 128 %(migasfree_app_dir)s/django.wsgi
source!1!nick = uWSGI 1
source!1!type = interpreter
"""

    _filename = '/etc/cherokee/migasfree.conf'
    _write_web_config(_filename, _config)

    _line = 'include = %s\n' % _filename
    _cherokee_lines = open(_cherokee_conf, 'rb').readlines()
    if _line not in _cherokee_lines:
        _f = open(_cherokee_conf, 'a')
        _f.write(_line)
        _f.close()

def _write_web_config(filename, config):
    _content = config % {
        'django_dir': os.path.dirname(os.path.abspath(django.__file__)),
        'migasfree_repo_dir': MIGASFREE_REPO_DIR,
        'migasfree_app_dir': MIGASFREE_APP_DIR
    }

    if not writefile(filename, _content):
        print 'Problem found creating Apache configuration file.'
        sys.exit(errno.EINPROGRESS)

def trans(string):
    return unicode(_(string)) #pylint: disable-msg=E1102

def writefile(filename, content):
    '''
    bool writefile(string filename, string content)
    '''

    _file = None
    try:
        _file = open(filename, 'wb')
        _file.write(content)
        _file.flush()
        os.fsync(_file.fileno())
        _file.close()

        return True
    except IOError:
        return False
    finally:
        if _file is not None:
            _file.close()

def readfile(filename):
    fp = open(filename, 'rb')
    ret = fp.read()
    fp.close()

    return ret

def s2l(cad):
    """
    string to list
    """
    lst = []
    if str(cad) == "None":
        return lst
    try:
        lst = eval(cad)
        return lst
    except:
        return lst

def vl2s(field):
    """
    value_list("id") to string
    """
    return str(field.values_list("id")).replace("(", "").replace(",)", "")

class Mmcheck():
    field = None #is a ManyToManyField
    field_copy = None #is a Text Field

    def __init__(self, field, field_copy):
        self.field = field
        self.field_copy = field_copy

    def mms(self):
        return vl2s(self.field)

    def changed(self):
        return not self.mms() == str(self.field_copy)

def horizon(mydate, delay):
    """
    No weekends
    """
    iday = int(mydate.strftime("%w"))
    idelta = delay + (((delay + iday - 1) / 5) * 2)

    return mydate + timedelta(days=idelta)

def compare_values(val1, val2):
    if len(val1) != len(val2):
        return False

    for x in val1:
        if not x in val2:
            return False

    return True

def list_difference(list1, list2):
    """uses list1 as the reference, returns list of items not in list2"""
    diff_list = []
    for item in list1:
        if not item in list2:
            diff_list.append(item)

    return diff_list

def run_in_server(code_bash):
    my_file = os.tmpnam()
    writefile(my_file, code_bash)

    os.system("bash %s 1> %s.out 2> %s.err" % (my_file, my_file, my_file))

    out = readfile('%s.out' % my_file)
    err = readfile('%s.err' % my_file)

    os.system("rm %s" % my_file)
    os.system("rm %s.out" % my_file)
    os.system("rm %s.err" % my_file)

    return {"out": out, "err": err}
