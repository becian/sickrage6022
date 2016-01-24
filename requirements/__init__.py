#!/usr/bin/env python2
# Author: echel0n <sickrage.tv@gmail.com>
# URL: http://www.github.com/sickragetv/sickrage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import os
import sys


def install_pip(user=False):
    print("Downloading pip ...")
    import urllib2

    url = "https://bootstrap.pypa.io/get-pip.py"
    file_name = url.split('/')[-1]
    u = urllib2.urlopen(url)
    with open(file_name, 'wb') as f:
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print("Downloading: %s Bytes: %s" % (file_name, file_size))
        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break
            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8) * (len(status) + 1)
            print(status),

    print("Installing pip ...")
    import subprocess
    subprocess.call([sys.executable, ('get-pip.py', 'get-pip.py --user')[user]])

    print("Cleaning up downloaded pip files")
    os.remove('get-pip.py')


def install_pkgs(requirements, user=False):
    import pip

    # list installed packages
    try:installed = [x.project_name.lower() for x in pip.get_installed_distributions(local_only=True, user_only=user)]
    except:installed = []

    try:
        with open(requirements) as f:
            packages = [x.strip() for x in f.readlines()]

        for i, pkg in enumerate(packages, start=1):
            pkg_name = pkg.lower()
            if pkg_name not in installed:
                print(r"[%3.2f%%]::Installing %s package" % (i * 100 / len(packages), pkg_name))
                pip.main(['-q', 'install', (pkg, '--user {}'.format(pkg))[user]])
    except KeyboardInterrupt:raise

def upgrade_pkgs(user=False):
    import pip
    from pip.commands.list import ListCommand

    pip_list = ListCommand()
    pip_options = pip_list.parse_args(['--no-cache-dir', '-o', ('', '--user')[user]])

    while(True):
        # list packages that need upgrading
        try:packages = [p.project_name for p, y, _ in pip_list.find_packages_latest_versions(pip_options[0])
                        if p.version == y.available]
        except:packages = []

        for i, pkg_name in enumerate(packages, start=1):
            try:
                print(r"[%3.2f%%]::Upgrading %s package" % (i * 100 / len(packages), pkg_name.lower()))
                pip.main(['-q', 'install', '-U', (pkg_name, '--user {}'.format(pkg_name))[user]])
            except IndexError:continue
            except KeyboardInterrupt:raise
        else:break

def ssl_contexts(user=False):
    try:
        print("Patching SiCKRAGE SSL Context")
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
        urllib3.contrib.pyopenssl.DEFAULT_SSL_CIPHER_LIST = "MEDIUM"
    except ImportError:
        # ssl contexts
        install_pkgs(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ssl.txt'), user)

        # restart to enable sni contexts
        os.execl(sys.executable, sys.executable, *sys.argv)


def install_reqs(optional=False, user=False):
    # get and load pip
    install_pip(user)
    import pip

    # install ssl sni contexts
    ssl_contexts(user)

    # install configobj seperately
    pip.main(['-q', '--no-cache-dir', 'install', '-U', ('configobj', '--user {}'.format('configobj'))[user]])

    print("Checking for required SiCKRAGE packages, please stand by ...")
    install_pkgs(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'global.txt'), user)

    if optional:
        print("Checking for optional SiCKRAGE packages, please stand by ...")
        try:install_pkgs(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'optional.txt'), user)
        except:pass

    print("Checking for upgradable SiCKRAGE packages, please stand by ...")
    upgrade_pkgs(user)