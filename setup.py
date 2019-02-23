from setuptools import setup

setup(
    name='phantom-cli',
    version='0.0.0.8',
    description='command line tools to interact with the phantom camera',
    url='https://github.com/the16thpythonist/phantom-cli',
    author='Jonas Teufel',
    author_email='jonseb1998@gmail.com',
    license='MIT',
    packages=[
        'phantomcli',
        'phantomcli.scripts'
    ],
    package_data={
        'scripts': '*'
    },
    install_requires=[
        'click',
        'demjson',
        'parsimonious',
        'imageio',
        'numpy',
        'matplotlib'
    ],
    entry_points={
        'console_scripts':
            [
                'ph-test=phantomcli.scripts.phtest:command',
                'ph-mock=phantomcli.scripts.phmock:command',
                'ph-get=phantomcli.scripts.phget:command',
                'ph-img=phantomcli.scripts.phimg:command'
            ]
    },
    python_requires='~=3.5',
    zip_safe=False
)
