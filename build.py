#!/usr/bin/env python3

# standard library imports
import re
import os

# third party imports
import click


@click.command(name='build')
@click.option('--git', is_flag=True, help='Will also commit all changes and commit them to github')
@click.option('--git-username', default='the16thpythonist', help='The username for authentication with Github')
@click.option('--git-password', default='Struppi98!?', help='The password for authentication with Github')
@click.option('--pypi-username', default='the16thplayer', help='The username for the Python Package Index')
@click.option('--pypi-password', default='Struppi98!?', help='The password for the Python Package Index')
@click.argument('version')
@click.argument('name')
def build(git_username, git_password, pypi_username, pypi_password, version, name, git=False):

    # We assume, that the build script gets executed in the folder, where it is located and thus the current working
    # path should be a correct base path for the operations
    folder_path = os.getcwd()
    cd_command = 'cd {} ; '.format(folder_path)

    # Replacing the version within the setup module
    setup_path = os.path.join(folder_path, 'setup.py')
    with open(setup_path, mode='r+') as file:
        content = file.read()
        current_version = re.search(r'([\d.]+)', content).group(1)
        print('FOUND VERSION {}'.format(current_version))

    with open(setup_path, mode='w+') as file:
        content = content.replace(current_version, version)
        print('REPLACING VERSION WITH {}'.format(version))
        file.write(content)

    # Creating the new source dist
    os.system(cd_command + 'python3 setup.py sdist')

    # Uploading the whole thing to twine
    os.system(cd_command + 'twine upload -u {} -p {} dist/*{}.tar.gz'.format(pypi_username, pypi_password, version))

    # If the git flag was set, it will push a new version to git

    # Reinstalling the pip package
    os.system('pip3 uninstall -y {}'.format(name))
    os.system('pip3 install --no-cache-dir {}'.format(name))
    os.system('pip3 uninstall -y {}'.format(name))
    os.system('pip3 install --no-cache-dir {}'.format(name))


if __name__ == '__main__':
    build()
