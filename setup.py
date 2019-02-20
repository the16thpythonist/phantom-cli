from setuptools import setup

setup(
    name='phantom-cli',
    version='0.0.0.3',
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
            ['ph-test=phantomcli.scripts.phtest:command']
    },
    python_requires='~=3.5',
    zip_safe=False
)
