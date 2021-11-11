# crossbill
Crossbill project covers an open access single objective light-sheet microscopy platform. This repository mainly covers the software aspect of this project.

# Installation

#### 1. Building *crossbill* environment using setup file / pip:

  Try the following on the anaconda (https://www.anaconda.com/products/individual-d) commpand prompt. Note: Admin previledges are required on this command prompt to be able to create required environment.

  Download crossbill repository, unzip it, get to the folder containing setup.cfg file and then use the following:
  ```
  conda create -n crossbill pip
  conda activate crossbill
  pip install -e . 
  ```

#### 2. Building *crossbill* environment line by line using conda:

  Try the following on the anaconda (https://www.anaconda.com/products/individual-d) commpand prompt. Note: Admin previledges are required on this command prompt to be able to create required environment.

  ```
  conda create -n crossbill python numpy pyqt qtpy qdarkstyle pip
  conda activate crossbill
  conda install -c conda-forge emoji
  pip install mcculw 
  python crossbill-mini.py
  ```

Once installed, crossbill-mini UI can be run by the following:
```
cd crossbill-mini
python crossbill-mini.py
```

## crossbill-mini
This contains a python compatible GUI to provide software support for Crossbill microscope.
This is windows compatible. Compatibility to other OS is limited due to incorporated hardware drivers.

## rpi-pico-crossbill
This contains an arduino compatible code which can be uploaded to a Raspberry Pi Pico board to be used with Crossbill microscope.




