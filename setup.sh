#!/bin/bash

# Fix versions
sudo pip uninstall -y oslo.config dnspython
sudo pip install -Iv oslo.config==2.5.0
sudo pip install zipp==0.5.0 configparser==3.5 dnspython==1.16.0

# Install dependencies
sudo apt install python-matplotlib -y
sudo pip install Flask SQLAlchemy Flask-SQLAlchemy

# Install g3_payless library
sudo python setup.py install
