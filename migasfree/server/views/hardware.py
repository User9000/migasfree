# -*- coding: utf-8 -*-

import json

from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _

from ..models import (
    HwNode,
    HwConfiguration,
    HwLogicalName,
    HwCapability,
    Notification,
    Computer
)

MAXINT = 9223372036854775807  # sys.maxint = (2**63) - 1


@login_required
def hardware_resume(request, pk):
    computer = get_object_or_404(Computer, id=pk)
    request.user.userprofile.check_scope(pk)

    hardware = HwNode.objects.filter(computer__id=pk).order_by('id', 'parent_id', 'level')
    data = serializers.serialize('python', hardware)

    return render(
        request,
        'computer_hardware_resume.html',
        {
            'title': u'{}: {}'.format(_("Hardware Information"), computer),
            'computer': computer,
            'data': data
        }
    )


@login_required
def hardware_extract(request, pk):
    node = get_object_or_404(HwNode, id=pk)

    capability = HwCapability.objects.filter(node=node.id).values(
        'name', 'description'
    )
    logical_name = HwLogicalName.objects.filter(node=node.id).values('name')
    configuration = HwConfiguration.objects.filter(node=node.id).values(
        'name', 'value'
    )

    name = node.__str__()
    if not name:
        name = node.description
        if node.product:
            name = u'{}: {}'.format(name, node.product)

    return render(
        request,
        'computer_hardware_extract.html',
        {
            'title': u'{}: {}'.format(_("Hardware Information"), smart_unicode(name)),
            'name': name,
            'computer': node.computer,
            'capability': capability,
            'logical_name': logical_name,
            'configuration': configuration,
        }
    )


def load_hw(computer, node, parent, level):
    size = node.get('size')
    if size:
        size = int(size)

    n = HwNode.objects.create({
        'parent': parent,
        'computer': Computer.objects.get(id=computer.id),
        'level': level,
        'name': str(node.get('id')),
        'class_name': node.get('class'),
        'enabled': node.get('enabled', False),
        'claimed': node.get('claimed', False),
        'description': node.get('description'),
        'vendor': node.get('vendor'),
        'product': node.get('product'),
        'version': node.get('version'),
        'serial': node.get('serial'),
        'bus_info': node.get('businfo'),
        'physid': node.get('physid'),
        'slot': node.get('slot'),
        'size': size if (MAXINT >= size >= -MAXINT - 1) else 0,
        'capacity': node.get('capacity'),
        'clock': node.get('clock'),
        'width': node.get('width'),
        'dev': node.get('dev')
    })

    level += 1

    for e in node:
        if e == "children":
            for x in node[e]:
                if isinstance(x, dict):
                    load_hw(computer, x, n, level)
        elif e == "capabilities":
            for x in node[e]:
                HwCapability.objects.create(
                    node=n, name=x, description=node[e][x]
                )
        elif e == "configuration":
            for x in node[e]:
                HwConfiguration.objects.create(node=n, name=x, value=node[e][x])
        elif e == "logicalname":
            if isinstance(node[e], unicode):
                HwLogicalName.objects.create(node=n, name=node[e])
            else:
                for x in node[e]:
                    HwLogicalName.objects.create(node=n, name=x)
        elif e == "resource":
            print(e, node[e])
        else:
            pass


def process_hw(computer, jsonfile):
    with open(jsonfile) as f:
        try:
            data = json.load(f)
        except ValueError:
            Notification.objects.create(
                _("Error: Hardware dictionary is not valid in computer [%s].") % (
                    '<a href="{}">{}</a>'.format(
                        reverse('admin:server_computer_change', args=(computer.id,)),
                        computer
                    )
                )
            )
            return

    HwNode.objects.filter(computer=computer).delete()
    load_hw(computer, data, None, 1)
