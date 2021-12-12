# crossbill
Crossbill project covers an open access single objective light-sheet microscopy platform. 
This repository covers the software aspect of this project. More details about this project is accessible at the accompanying bioRxiv pre-print at doi: [10.1101/2021.04.30.442190](https://www.biorxiv.org/content/10.1101/2021.04.30.442190v1.full)

Caution: This project is still in alpha stage!

This is made available under the following license:
____________________________
MIT License

Copyright (c) 2021 Manish Kumar

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
____________________________

# Installation

OS dependence: Windows
(this dependence is due to the DAQ and stage drivers used in the current project)

#### Installation pre-requisite (hardware specific)
Install Instacal (from Measurement Computing) and MCL (MadCityLabs) drivers. This is not required for installation of *crossbill*, but is essential to successfully run the GUI. 

Try the following on the anaconda (https://www.anaconda.com/products/individual-d) commpand prompt. 

Note: Admin previledges are required on this command prompt to be able to create required environment.

`pip install` is most preferred, but alternate approaches are listed below:

#### Approach 1. Building *crossbill* environment using setup file / pip:  

  Download crossbill repository, unzip it, get to the folder containing setup.cfg file and then use the following:
  
  ```python
  conda create -n crossbill pip
  conda activate crossbill
  pip install -e . 
  ```

#### Approach 2. Building *crossbill* environment line by line using conda:

  ```python
  conda create -n crossbill python numpy pyqt qtpy qdarkstyle pip
  conda activate crossbill
  conda install -c conda-forge emoji
  pip install mcculw 
  ```

Once installed, get to the `crossbill-mini` directory (download it from github or zenodo), and run `crossbill-mini.py` file with python:

```python
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
