# Copyright 2014 Canonical, Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import glob
import logging
import os
import platform
import requests
import shutil
import subprocess

from cloudinstall.charms import (CharmBase, DisplayPriorities,
                                 get_charm_config)

CHARM_STABLE_URL = ("https://api.github.com/repos/Ubuntu-Solutions-Engineering"
                    "/glance-simplestreams-sync-charm/tarball/stable")

# Not necessarily required to match because we're local, but easy enough to get
CURRENT_DISTRO = platform.linux_distribution()[-1]

log = logging.getLogger(__name__)


class CharmGlanceSimplestreamsSync(CharmBase):

    """ Charm directives for glance-simplestreams-sync  """

    charm_name = 'glance-simplestreams-sync'
    charm_rev = 1
    menuable = True
    display_name = 'Glance - Simplestreams Image Sync'
    display_priority = DisplayPriorities.Other
    related = ['keystone']

    def download_stable(self):
        self.local_charms_dir = os.path.join(self.config.cfg_path,
                                             "local-charms")

        if not os.path.exists(self.local_charms_dir):
            os.makedirs(self.local_charms_dir)

        r = requests.get(CHARM_STABLE_URL, verify=True)
        tarball_name = os.path.join(self.local_charms_dir, 'stable.tar.gz')
        with open(tarball_name, mode='wb') as tarball:
            tarball.write(r.content)

        try:
            subprocess.check_output(['tar', '-C', self.local_charms_dir,
                                     '-zxf', tarball_name],
                                    stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as e:
            log.warning("error untarring: rc={} out={}".format(e.returncode,
                                                               e.output))
            raise e

        # filename includes commit hash at end:
        srcpat = os.path.join(self.local_charms_dir,
                              'Ubuntu-Solutions-Engineering-'
                              'glance-simplestreams-sync-charm-*')
        srcs = glob.glob(srcpat)
        if len(srcs) != 1:
            log.warning("error finding downloaded stable charm."
                        " got {}".format(srcs))
            raise Exception("Could not find downloaded stable charm.")

        src = srcs[0]
        dest = os.path.join(self.local_charms_dir, CURRENT_DISTRO,
                            'glance-simplestreams-sync')
        if os.path.exists(dest):
            shutil.rmtree(dest)
        os.renames(src, dest)

    def deploy(self, mspec):
        """Temporary override to get local copy of charm."""

        log.debug("downloading stable branch from github")
        try:
            self.download_stable()
            log.debug("done: downloaded to " + self.local_charms_dir)
        except:
            log.exception("problem downloading stable branch."
                          " Falling back to charm store version.")
            return super().deploy(mspec)

        kwds = dict(constraints=self.constraints_arg(),
                    repodir=self.local_charms_dir,
                    distro=CURRENT_DISTRO,
                    mspec=mspec)

        # TODO: See if this is supported by juju api
        cmd = ('{juju_home} juju deploy --repository={repodir}'
               ' local:{distro}/glance-simplestreams-sync'
               ' --constraints {constraints} --to {mspec}').format(
                   juju_home=self.config.juju_home(use_expansion=True),
                   **kwds)

        charm_config, _, charm_config_filename = get_charm_config(self.config)
        if self.charm_name in charm_config:
            cmd += ' --config ' + charm_config_filename

        try:
            log.debug("Deploying {} from local: {}".format(self.charm_name,
                                                           cmd))
            cmd_output = subprocess.check_output(cmd, stderr=subprocess.STDOUT,
                                                 shell=True)

            log.debug("Deploy output: " + cmd_output.decode('utf-8'))

        except subprocess.CalledProcessError as e:
            log.warning("Deploy error. rc={} out={}".format(e.returncode,
                                                            e.output))
            return True
        return False

    def set_relations(self):
        if os.path.exists(os.path.join(self.local_charms_dir,
                                       CURRENT_DISTRO,
                                       'glance-simplestreams-sync')):
            if 'rabbitmq-server' not in self.related:
                self.related.append('rabbitmq-server')
                log.debug("Added rabbitmq to relation list")

        return super(CharmGlanceSimplestreamsSync, self).set_relations()


__charm_class__ = CharmGlanceSimplestreamsSync
