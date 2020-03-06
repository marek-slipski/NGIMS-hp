FROM pytorch/pytorch:latest
ADD requirements.txt /app/requirements.txt
# set working directory to /app/
WORKDIR /app/
# install packages
RUN apt-get update &&\
apt-get install -y wget &&\
apt-get install unzip &&\
rm -rf /var/lib/apt/lists/*
# set up pip
RUN pip install --upgrade pip
# install python dependencies
RUN pip install -r requirements.txt
# create unprivileged user
RUN adduser --disabled-password --gecos ‘’ myuser
# Add /app to python path
ENV PYTHONPATH="/app:${PYTHONPATH}"
# For Dash
EXPOSE 8050
# Run initial command
CMD bash
