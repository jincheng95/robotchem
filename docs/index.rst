.. Roboflux documentation master file, created by
   sphinx-quickstart on Wed Jan 18 22:06:24 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. toctree::
   :hidden:

   self

###########################
RoboFlux Code Documentation
###########################

A Raspberry Pi powered differential scanning calorimeter with Internet remote control functionality.

This document is semi-automatically generated with Sphinx from documentation string within the code.
The doc strings within the code are very detailed and explain various functions and methods
without examining the code block itself.
However if you would like, next to this documentation,
there will be links to view the source code.
The source code for this project is also available on the
`robotchem GitHub repository <https://github.com/jincheng95/robotchem>`_.

There are mainly three parts of code to make this project possible.

Raspberry pi code
=================
Hardware control, temperature ramp, PID control and data upload on the raspberry pi.

Written and tested on Python 3.6 with ``asyncio`` module for asynchronicity.
Also makes use of the following Python libraries:

* ``RPi.GPIO``, the GPIO board control library from raspberry pi
* ``dateutil``, a date and time parser that converts a Python ``datetime`` object to a string
* ``Adafruit_ADS1x15``, analog-to-digital converter info reader
* and many other standard Python libraries.

.. toctree::
   :caption: Raspberry Pi Documentation

   Hardware controls, hardware.py <source/hardware.rst>
   Classes, classes.py <source/classes.rst>
   Utility, utils.py <source/utils.rst>
   Main module, main.py <source/main.rst>
   Settings files <source/settings.rst>

File Structure
--------------

.. code-block:: none

   .
   ├── __init__.py
   ├── classes.py
   ├── dependencies.txt
   ├── from_hayley_unchanged
   │   ├── DSC.py
   │   ├── Heat_to_setpoint_lily.py
   │   └── pid.py
   ├── hardware.py
   ├── local_settings.py
   ├── main.py
   ├── settings.py
   ├── tree.txt
   └── utils.py


Web Server
==========
Manages a database of calorimetry job measurements. Responsible for facilitating the exchange of
information and instructions between user and the raspberry pi.

Powered by Django 1.10.

.. toctree::
   :caption: Django Server Documentation

   Database models <source/models.rst>
   JSON serializers <source/serializers.rst>
   HTTP Response logic <source/views.rst>

File Structure
--------------
.. code-block:: none

   server_side/
   ├── app
   ├── controls
   │   ├── __init__.py
   │   ├── admin.py
   │   ├── apps.py
   │   ├── models.py
   │   ├── serializers.py
   │   └── views.py
   ├── manage.py
   ├── package.json
   ├── rfsite
   │   ├── __init__.py
   │   ├── local_settings.py
   │   ├── production_settings.py
   │   ├── settings.py
   │   ├── urls.py
   │   └── wsgi.py
   ├── static
   │   ├── bundle.js
   │   └── bundle.js.map
   ├── stats.json
   ├── templates
   │   ├── index.html
   │   ├── run_completion_email_body.txt
   │   └── run_completion_email_title.txt
   ├── webpack.config.js
   └── webpack.production.config.js


Javascript
==========
This is run natively on a user's browser and mainly for website aesthetics and function.
Javascript modules are not documented here because it is largely framework dependent and not part of the course.

Powered by React 0.15 and written in Javascript ES2015, bundling and minification by Webpack, npm and Babel.

File Structure
--------------

.. code-block:: none

   server_side/app/
   ├── components
   │   ├── TwoColumnRow.js
   │   ├── access.js
   │   ├── controls.js
   │   ├── loading.js
   │   ├── main.js
   │   ├── refreshing.js
   │   ├── run
   │   │   ├── lineplot.js
   │   │   ├── plotcontainer.js
   │   │   ├── plottoolbar.js
   │   │   ├── run.js
   │   │   └── simpletooltip.js
   │   ├── start.js
   │   └── status.js
   ├── containers
   │   ├── allrunscontainer.js
   │   ├── calibratecontainer.js
   │   ├── defaultcontainer.js
   │   └── runcontainer.js
   ├── index.js
   └── utils
       ├── humanize_axes.js
       ├── list_of_colors.js
       ├── round_to_2dp.js
       ├── units.js
       └── validate_email.js