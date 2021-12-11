# crossbill-mini

Here we have a GUI along with all the required functions/libraries to provide software support for Crossbill.

dependencies folder contains dll files for MadCityLabs stage

icons folder contains icons for the crossbill-mini GUI


Crossbill mini has DAQ and stage control and works in conjunction with any external mode of camera control.

How to get started?

Try the following on the anaconda (https://www.anaconda.com/products/individual-d) commpand prompt.
Note: Admin previledges are required on this command prompt to be able to create required environment. 

Once `crossbill` is installed , get to the directory containing `crossbill-mini.py` file, and run it with python:
```python
cd crossbill-mini
python crossbill-mini.py
```
```python
conda create -n crossbill python numpy pyqt qtpy qdarkstyle pip
conda activate crossbill
conda install -c conda-forge emoji
pip install mcculw 
python Crossbill_mini.py
```

Congratulations if you could get to the crossbill mini GUI without any errors.

mcculw is meant for the Measurement Computing DAQ board. Instacal must be pre-installed before actually using the DAQ hardware.

Stage will work only if MadCityLabs drivers are properly installed.
