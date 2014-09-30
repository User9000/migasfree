# -*- coding: utf-8 -*-

import json

from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings

from migasfree.server.models import (
    Platform,
    Version,
    Repository,
)

from migasfree.server.api import get_computer
from migasfree.server.functions import uuid_validate
from migasfree.server.security import gpg_export_key_name


def get_versions(request):
    result = []
    _platforms = Platform.objects.all()
    for _platform in _platforms:
        element = {}
        element["platform"] = _platform.name
        element["versions"] = []
        _versions = Version.objects.filter(platform=_platform)
        for _version in _versions:
            element["versions"].append({"name": _version.name})

        result.append(element)

    return HttpResponse(json.dumps(result), mimetype="text/plain")


def get_computer_info(request):
    _uuid = uuid_validate(request.GET.get('uuid', ''))
    _name = request.GET.get('name', '')
    if _uuid == "":
        _uuid == _name

    computer = get_computer(_name, _uuid)

    result = {
        'id': computer.id,
        'uuid': computer.uuid,
        'name': computer.name,
        'helpdesk': settings.MIGASFREE_HELP_DESK,
        'server': request.META.get('HTTP_HOST'),
    }
    result["search"] = result[settings.MIGASFREE_COMPUTER_SEARCH_FIELDS[0]]

    element = []
    for tag in computer.tags.all():
        element.append("%s-%s" % (tag.property_att.prefix, tag.value))
    result["tags"] = element

    result["available_tags"] = {}
    for rps in Repository.objects.all().filter(version=computer.version).filter(active=True):
        for tag in rps.attributes.all().filter(property_att__tag=True).filter(property_att__active=True):
            if not tag.property_att.name in result["available_tags"]:
                result["available_tags"][tag.property_att.name] = []

            value="%s-%s" % (tag.property_att.prefix, tag.value)
            if not value in result["available_tags"][tag.property_att.name]:
                result["available_tags"][tag.property_att.name].append(value)

    return HttpResponse(json.dumps(result), mimetype="text/plain")


def computer_label(request):
    """
    To Print a Computer Label
    """
    return render(
        request,
        'computer_label.html',
        json.loads(get_computer_info(request).content)
    )


def get_key_repositories(request):
    """
    Return the repositories public key
    """
    return HttpResponse(
        gpg_export_key_name("migasfree-repository"),
        mimetype="text/plain"
    )
