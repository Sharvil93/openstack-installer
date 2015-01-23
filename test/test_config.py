#!/usr/bin/env python
#
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

import logging
import unittest
from unittest.mock import patch
import yaml
import os.path as path
from tempfile import NamedTemporaryFile

from cloudinstall.config import Config
import cloudinstall.utils as utils

log = logging.getLogger('cloudinstall.test_config')

USER_DIR = path.expanduser('~')
DATA_DIR = path.join(path.dirname(__file__), 'files')
GOOD_CONFIG = yaml.load(utils.slurp(path.join(DATA_DIR, 'good_config.yaml')))
BAD_CONFIG = yaml.load(utils.slurp(path.join(DATA_DIR, 'bad_config.yaml')))


class TestGoodConfig(unittest.TestCase):

    def setUp(self):
        self._temp_conf = Config(GOOD_CONFIG)
        with NamedTemporaryFile(mode='w+', encoding='utf-8') as tempf:
            # Override config file to save to
            self.conf = Config(self._temp_conf._config, tempf.name)

    def test_save_openstack_password(self):
        """ Save openstack password to config """
        self.conf.setopt('openstack_password', 'pass')
        self.conf.save()
        self.assertTrue('pass' in self.conf.getopt('openstack_password'))

    def test_save_maas_creds(self):
        """ Save maas credentials """
        self.conf.setopt('maascreds', dict(api_host='127.0.0.1',
                                           api_key='1234567'))
        self.conf.save()
        self.assertTrue(
            '127.0.0.1' in self.conf.getopt('maascreds')['api_host'])

    def test_save_landscape_creds(self):
        """ Save landscape credentials """
        self.conf.setopt('landscapecreds',
                         dict(admin_name='foo',
                              admin_email='foo@bar.com',
                              system_email='foo@bar.com',
                              maas_server='127.0.0.1',
                              maas_apikey='123457'))
        self.conf.save()
        self.assertTrue(
            'foo@bar.com' in self.conf.getopt('landscapecreds')['admin_email'])

    def test_save_installer_type(self):
        """ Save installer type """
        self.conf.setopt("install_type", 'multi')
        self.conf.save()
        self.assertTrue('multi' in self.conf.getopt('install_type'))

    def test_cfg_path(self):
        """ Validate current user's config path """
        self.assertEqual(self.conf.cfg_path,
                         path.join(USER_DIR, '.cloud-install', 'openstack'))

    def test_bin_path(self):
        """ Validate additional tools bin path """
        self.assertEqual(self.conf.bin_path, '/usr/share/openstack/bin')

    def test_juju_environments_path(self):
        """ Validate juju environments path in user dir """
        self.assertEqual(self.conf.juju_environments_path,
                         path.join(USER_DIR, '.cloud-install', 'openstack',
                                   'juju', 'environments.yaml'))


@unittest.skip
class TestBadConfig(unittest.TestCase):

    def setUp(self):
        self._temp_conf = Config(BAD_CONFIG)
        with NamedTemporaryFile(mode='w+', encoding='utf-8') as tempf:
            # Override config file to save to
            self.conf = Config(self._temp_conf._config, tempf.name)

    def test_no_openstack_password(self):
        """ No openstack password defined """
        self.assertFalse(self.conf.getopt('openstack_password'))

    def test_no_landscape_creds(self):
        """ No landscape creds defined """
        self.assertFalse(self.conf.getopt('landscapecreds'))

    def test_no_installer_type(self):
        """ No installer type defined """
        self.assertFalse(self.conf.is_single)


class TestConfigFuncs(unittest.TestCase):

    def test_juju_home(self):
        # mocking install_home instead of Config.cfg_path because it's easier
        with patch('cloudinstall.utils.install_home') as mock_ih:
            with patch('cloudinstall.config.os.path.expanduser') as mock_eu:
                mock_eu.return_value = '/home/user'
                mock_ih.return_value = '/home/user/'

                c = Config(install_name='test')
                # sanity check of cfg_path:
                self.assertEqual(c.cfg_path, '/home/user/.cloud-install/test')

                self.assertEqual(c.juju_home(),
                                 'JUJU_HOME=/home/user/' +
                                 '.cloud-install/test/juju')

                self.assertEqual(c.juju_home(use_expansion=True),
                                 'JUJU_HOME=~/.cloud-install/test/juju')
