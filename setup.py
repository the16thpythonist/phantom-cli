from setuptools import setup

setup(
    name='phantom-cli',
    version='0.0.0.6',
    description='command line tools to interact with the phantom camera',
    url='https://github.com/the16thpythonist/phantom-cli',
    author='Jonas Teufel',
    author_email='jonseb1998@gmail.com',
    license='MIT',
    packages=[
        'phantomcli'
    ],
    install_requires=[
        'click'
    ],
    entry_points={
        'console_scripts':
            [
                'ph-test=phantomcli.scripts.phtest:command',
                'ph-mock=phantomcli.scripts.phmock:command',
                'ph-get=phantomcli.scripts.phget:command'
            ]
    },
    python_requires='~=3.5',
    zip_safe=False
)
