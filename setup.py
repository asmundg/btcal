from setuptools import find_packages, setup

setup(
    name='btcal',
    version='0.1',
    description='Barnas Turlag Tromsoe activity iCal generator',
    url='https://github.com/asmundg/btcal',
    author='Aasmund Grammeltvedt',
    author_email='asmundg@big-oil.org',
    entry_points={
        'console_scripts': [
            'btcal = btcal.btcal:main']},
    packages=find_packages())
