from setuptools import setup

setup(
    name='phantom-cli',
    version='0.0.0.1',
    description='command line tools to interact with the phantom camera',
    ulr='',
    author='Jonas Teufel',
    author_email='jonseb1998@gmail.com',
    license='MIT',
    packages=[
        'phantom-cli'
    ],
    install_requires=[
        'click'
    ],
    python_requires='~=3.5',
    zip_safe=False
)
