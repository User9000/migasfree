# -*- coding: utf-8 -*-

import os
import shutil

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.conf import settings

from migasfree.server.models import Version, VersionManager, MigasLink
from migasfree.server.functions import trans


class Store(models.Model, MigasLink):
    """
    Location where packages will be stored (p.e. /third/vmware)
    """
    name = models.CharField(
        _("name"),
        max_length=50
    )

    version = models.ForeignKey(
        Version,
        verbose_name=_("version")
    )

    objects = VersionManager()  # manager by user version

    def __init__(self, *args, **kwargs):
        super(Store, self).__init__(*args, **kwargs)

        if self.id:
            info_link = reverse(
                'package_info',
                args=('STORES/%s/' % self.name,)
            )

            download_link = '%s%s/STORES/%s/' % (
                settings.MEDIA_URL,
                self.version.name,
                self.name
            )

            self._actions = [
                [trans('Package Information'), info_link],
                [trans('Download'), download_link]
            ]

    def create_dir(self):
        _path = os.path.join(
            settings.MIGASFREE_REPO_DIR,
            self.version.name,
            'STORES',
            self.name
        )
        if not os.path.exists(_path):
            os.makedirs(_path)

    def save(self, *args, **kwargs):
        self.name = self.name.replace(" ", "-")
        self.create_dir()
        super(Store, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # remove the directory of Store
        path = os.path.join(
            settings.MIGASFREE_REPO_DIR,
            self.version.name,
            "STORES",
            self.name
        )
        if os.path.exists(path):
            shutil.rmtree(path)
        super(Store, self).delete(*args, **kwargs)

    def __unicode__(self):
        return self.name

    class Meta():
        app_label = 'server'
        verbose_name = _("Store")
        verbose_name_plural = _("Stores")
        unique_together = (("name", "version"),)
        permissions = (("can_save_store", "Can save Store"),)
