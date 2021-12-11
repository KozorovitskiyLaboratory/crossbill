# crossbill
Crossbill project covers an open access single objective light-sheet microscopy platform. This repository mainly covers the software aspect of this project. More details about this project is accessible at the accompanying BioRxiv pre-print here https://doi.org/10.1101/2021.04.30.442190


# Installation

OS dependence: Windows
(this dependence is due to the DAQ and stage drivers used in the current project)

#### Installation Pre-requisite
Install Instacal (from Measurement Computing) and MCL (MadCityLabs) drivers. This is not required for installation of *crossbill*, but is essential to successfully run the GUI. 

Try the following on the anaconda (https://www.anaconda.com/products/individual-d) commpand prompt. Note: Admin previledges are required on this command prompt to be able to create required environment.

#### 1. Building *crossbill* environment using setup file / pip:  

  Download crossbill repository, unzip it, get to the folder containing setup.cfg file and then use the following:
  ```
  conda create -n crossbill pip
  conda activate crossbill
  pip install -e . 
  ```

#### 2. Building *crossbill* environment line by line using conda:

  ```
  conda create -n crossbill python numpy pyqt qtpy qdarkstyle pip
  conda activate crossbill
  conda install -c conda-forge emoji
  pip install mcculw 
  python crossbill-mini.py
  ```

Once installed, get to the directory containing crossbill-mini.py file, and run it with python:
```
cd crossbill-mini
python crossbill-mini.py
```
Note: src folder contents may be required to be manually copied to the crossbill-mini folder if 2nd approach for installation was used. 

## crossbill-mini
This contains a python compatible GUI to provide software support for Crossbill microscope.
This is windows compatible. Compatibility to other OS is limited due to incorporated hardware drivers.

## rpi-pico-crossbill
This contains an arduino compatible code which can be uploaded to a Raspberry Pi Pico board to be used with Crossbill microscope.

## src
This folder has various functions/methods associated with DAQ and Stage.
