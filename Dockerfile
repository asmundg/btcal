FROM python:2.7-onbuild
RUN python setup.py develop
CMD btcal
