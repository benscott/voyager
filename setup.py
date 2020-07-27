from setuptools import setup

setup(
    name='voyager',
    version='0.1',
    py_modules=['voyager'],
    install_requires=[
        'Click',
    ],
    entry_points='''
        [console_scripts]
        voyager=voyager.cli:cli
    ''',
)
