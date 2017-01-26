# robotchem
Robot Chemistry coursework code written during my fourth year at Department of Chemistry, Imperial College London. 

The root directory contains code run on a Raspberry Pi, which serves as a calorimeter with PID-controlled Peltier heating plates and thermocouples.

The server_side directory is a Django project that provides back-end server support. It accepts measurements from Raspberry Pi and displays the data to the browser. Controls for the calorimeter also reside on the website.
