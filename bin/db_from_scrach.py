# -*- coding: utf-8 -*-

import os
import subprocess
import django.core.management
import migasfree
from migasfree import settings
django.core.management.setup_environ(settings)

from django.contrib.auth.models import User as UserSystem
from django.contrib.auth.models import Group
from django.contrib.auth.models import Permission

from migasfree.server.models import UserProfile


def run(cmd_linux):
    (out, err) = subprocess.Popen(cmd_linux,
        stdout=subprocess.PIPE, shell=True).communicate()
    return (out, err)


def create_user(name, groups=[]):
    oUser = UserProfile()
    oUser.username = name
    oUser.is_staff = True
    oUser.is_active = True
    oUser.is_superuser = (name == "admin")
    oUser.save()
    oUser.password = name
    print("Create user [%s] in groups " % name),
    for group in groups:
        oUser.groups.add(group.id)
        print("[%s] " % group.name),
    print('')
    oUser.save()


def add_read_perms(group, tables=[]):
    for table in tables:
        group.permissions.add(
            Permission.objects.get(codename="change_%s" % table,
            content_type__app_label="server").id)


def add_all_perms(group, tables=[]):
    for table in tables:
        group.permissions.add(
            Permission.objects.get(codename="add_%s" % table,
            content_type__app_label="server").id)
        group.permissions.add(
            Permission.objects.get(codename="change_%s" % table,
            content_type__app_label="server").id)
        group.permissions.add(
            Permission.objects.get(codename="delete_%s" % table,
            content_type__app_label="server").id)
        group.permissions.add(
            Permission.objects.get(codename="can_save_%s" % table,
            content_type__app_label="server").id)


def create_users():
    """
    Create default Groups and Users
    """

    # GROUP READER
    oGroupRead = Group()
    oGroupRead.name = "Reader"
    oGroupRead.save()
    tables = ["computer", "device", "user", "login", "attribute", "error",
            "fault", "deviceconnection", "devicemanufacturer", "devicemodel",
            "devicetype", "schedule", "scheduledelay", "autocheckerror",
            "faultdef", "property", "checking", "version", "pms", "query",
            "package", "repository", "store", "message", "update",
            "platform", "messageserver", "migration", "notification"]
    add_read_perms(oGroupRead, tables)
    oGroupRead.save()

    # GROUP LIBERATOR
    oGroupRepo = Group()
    oGroupRepo.name = "Liberator"
    oGroupRepo.save()
    tables = ["repository", "schedule", "scheduledelay"]
    add_all_perms(oGroupRepo, tables)
    oGroupRepo.save()

    # GROUP PACKAGER
    oGroupPackager = Group()
    oGroupPackager.name = "Packager"
    oGroupPackager.save()
    tables = ["package", "store"]
    add_all_perms(oGroupPackager, tables)
    oGroupPackager.save()

    # GROUP COMPUTER CHECKER
    oGroupCheck = Group()
    oGroupCheck.name = "Computer Checker"
    oGroupCheck.save()
    tables = ["autocheckerror", "error", "fault", "message", "update"]
    add_all_perms(oGroupCheck, tables)
    oGroupCheck.save()

    # GROUP DEVICE INSTALLER
    oGroupDev = Group()
    oGroupDev.name = "Device installer"
    oGroupDev.save()
    tables = ["deviceconnection", "devicemanufacturer", "devicemodel",
            "devicetype"]
    add_all_perms(oGroupDev, tables)
    oGroupDev.save()

    # GROUP QUERY
    oGroupQuery = Group()
    oGroupQuery.name = "Query"
    oGroupQuery.save()
    tables = ["query"]
    add_all_perms(oGroupQuery, tables)
    oGroupQuery.save()

    # GROUP CONFIGURATOR
    oGroupSys = Group()
    oGroupSys.name = "Configurator"
    oGroupSys.save()
    tables = ["checking", "faultdef", "property", "pms", "version",
            "message", "update", "platform", "messageserver", "migration",
            "notification"]
    add_all_perms(oGroupSys, tables)
    oGroupSys.save()

    # CREATE DEFAULT USERS
    create_user("admin")
    create_user("packager", [oGroupRead, oGroupPackager])
    create_user("configurator", [oGroupRead, oGroupSys])
    create_user("installer", [oGroupRead, oGroupDev])
    create_user("query", [oGroupRead, oGroupQuery])
    create_user("liberator", [oGroupRead, oGroupRepo])
    create_user("checker", [oGroupRead, oGroupCheck])
    create_user("reader", [oGroupRead])


def create_db():
    DB = settings.DATABASES.get('default')
    if DB.get('ENGINE') == \
        'django.db.backends.postgresql_psycopg2':
        settings.DATABASES.get('default').get('ENGINE')

        _NAME = DB.get('NAME')
        _USER = DB.get('USER')
        _PASSWORD = DB.get('PASSWORD')
        _HOST = ""
        if DB.get('HOST'):
            _HOST = " --host=%s " % DB.get('HOST')

        _PORT = ""
        if DB.get('PORT'):
            _PORT = " --port=%s " % DB.get('PORT')

        # DROP DATABASE
        cmd_linux = "echo 'DROP DATABASE %s;' | su postgres -c psql -" \
            % (_NAME,)
        (out, err) = run(cmd_linux)

        # CREATE DATABASE
        cmd_linux = "su postgres -c 'PGPASSWORD=%s createdb %s %s -w -E utf8 -O %s %s'" % \
            (_PASSWORD, _HOST, _PORT, _USER, _NAME)
        (out, err) = run(cmd_linux)

    else:
        exit(1, "Sorry. No soported this backend: %s" % DB.get("ENGINE"))


def create_tables():
    django.core.management.call_command('syncdb', interactive=False)
    django.core.management.call_command('migrate', 'server')


def create_registers():
    # CREATE GROUPS AND USERS
    create_users()

    # Load Fixtures
    _path_fixtures = os.path.join(migasfree.__path__[0], "server", "fixtures")
    fixtures = ['server.checking.json',
               'server.pms.json',
               'server.query.json',
               'server.property.json',
               'server.faultdef.json',
               ]
    for fixture in fixtures:
        print("    Loading fixture %s: " % fixture),
        django.core.management.call_command('loaddata',
            os.path.join(_path_fixtures, fixture))


def main():
    # Check user is root
    (out, err) = run("whoami")
    if out != "root\n":
        print "You must be root!"
        exit(1)

    create_db()
    create_tables()
    create_registers()


if  __name__ == '__main__':
    main()
