# docker image for QLF deployment
FROM continuumio/miniconda3
LABEL maintainer "itteam@linea.gov.br"

WORKDIR /opt/app/quicklook/qlf
COPY . .

# QLF dependencies

# gcc and make are required to install fitsio
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y gcc make supervisor \
    && mkdir -p /var/log/supervisor

#RUN conda config --add channels conda-forge \
#    && conda create --name quicklook python=3.5 --yes --file requirements.txt

RUN conda config --add channels conda-forge \
    && conda install python=3.5 --yes --file requirements.txt

# Some dependencies must be installed with pip (see README.md)
#RUN /bin/bash -c "source /opt/conda/bin/activate quicklook && pip install -r extras.txt"

RUN pip install -r extras.txt

COPY config/qlf.cfg.production config/qlf.cfg

WORKDIR /opt/app/quicklook/qlf/qlf

# initialize QLF database
#ENV TEST_USER nobody
#ENV TEST_USER_EMAIL nobody@example.com
#ENV TEST_USER_PASSWD nobody

#RUN /bin/bash -c "source /opt/conda/bin/activate quicklook && python manage.py migrate \
#    && python -Wi manage.py createsuperuser --noinput --username $TEST_USER --email $TEST_USER_EMAIL"

# set environment for QL pipeline
ENV PATH /opt/app/quicklook/desispec/bin:$PATH
ENV PYTHONPATH /opt/app/quicklook/desispec/py:$PYTHONPATH

ENV PATH /opt/app/quicklook/desiutil/bin:$PATH
ENV PYTHONPATH /opt/app/quicklook/desiutil/py:$PYTHONPATH

# on the localhost django will run on port 8000 and bokeh on 5006
EXPOSE 8000 5006

# Use bash in exec mode
# start django, bokeh and qlf daemon
CMD ["/usr/bin/supervisord", "-c", "supervisord.conf"]


