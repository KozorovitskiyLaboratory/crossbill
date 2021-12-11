"""
The main Crossbill-mini file
This relies on daq and stage modules on hardware front.

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
"""

from PyQt5 import QtCore, QtGui, QtWidgets
from crossbillUI import Ui_MainWindow
#from crossbillcfgUI import Ui_cfgDialog
from crossbill.stage import MCL_MicroDrive
from crossbill.daq import MCCdaq
import math, re, json, numpy, traceback, emoji, traceback
from datetime import datetime 

class WorkerSignals(QtCore.QObject):
    '''
    Defines the signals available from a running worker thread.
    '''
    finished = QtCore.pyqtSignal()
    error = QtCore.pyqtSignal()  

class Worker(QtCore.QRunnable):
    '''
    Worker thread.
    Input
    --------
    fn: function to run inside thread

    Output
    --------
    None
    '''
    def __init__(self, fn):
        super(Worker, self).__init__()        
        self.fn = fn        
        self.signals = WorkerSignals() #inherit worker signals  
        self.errormsg = ""    

    def run(self):        
        try:
            self.fn()
        except:
            # print('Error in evaluating '+self.fn.__name__) 
            self.errormsg = traceback.format_exc()
            print(self.errormsg) #print error message in the terminal 
            self.signals.error.emit()
        finally:
            # print('Finished evaluating '+self.fn.__name__) 
            self.signals.finished.emit()  # Done



class myWindow(QtWidgets.QMainWindow, Ui_MainWindow, MCCdaq, MCL_MicroDrive): 
    def __init__(self, parent=None): 
        QtWidgets.QMainWindow.__init__(self, parent=parent) 
        self.setupUi(self)   
        
        #A timer enabled continuous update of UI
        self.UItimer = QtCore.QTimer()        
        self.UItimer.setInterval(100) # interval in milli secodns
        self.UItimer.timeout.connect(self.updateUI)
        self.UItimer.start()

        self.msg = ""

        self.threadpool = QtCore.QThreadPool()
        self.threadpool.setExpiryTimeout(50) #expiry time in ms for unused threads

        ############## Initialize/connect CFG tab functionalities ##############               
        self.G1vpd_lineEdit.textEdited.connect(self.galvo1param)
        self.G2vpd_lineEdit.textEdited.connect(self.galvo2param)
        self.pxsize_lineEdit.textEdited.connect(self.cameraparam)
        self.widthpx_lineEdit.textEdited.connect(self.cameraparam)
        self.heightpx_lineEdit.textEdited.connect(self.cameraparam)
        self.MO1make_comboBox.currentIndexChanged.connect(self.mo1param)
        self.MO1mag_comboBox.currentIndexChanged.connect(self.mo1param)
        self.MO2make_comboBox.currentIndexChanged.connect(self.mo2param)
        self.MO2mag_comboBox.currentIndexChanged.connect(self.mo2param)
        self.MO3make_comboBox.currentIndexChanged.connect(self.mo3param)
        self.MO3mag_comboBox.currentIndexChanged.connect(self.mo3param)
        self.TL1_lineEdit.textEdited.connect(self.opticsparam)
        self.TL2_lineEdit.textEdited.connect(self.opticsparam)
        self.TL3_lineEdit.textEdited.connect(self.opticsparam)
        self.SL1_lineEdit.textEdited.connect(self.opticsparam)
        self.SL2_lineEdit.textEdited.connect(self.opticsparam)
        self.SL3_lineEdit.textEdited.connect(self.opticsparam)
        self.cfgload_pushButton.clicked.connect(self.cfgload)
        self.cfgsave_pushButton.clicked.connect(self.cfgsave)
        self.cfgdone_pushButton.clicked.connect(self.cfgdone)
        

        ############## DAQ UI initialization ##############       

        self.connect_daq_pushButton.clicked.connect(self.connectvsdisconnectdaq)
        self.scanrange1_lineEdit.setEnabled(False)
        self.offset1_lineEdit.setEnabled(False)
        self.VPS_comboBox.setEnabled(False)
        self.scanrange2_lineEdit.setEnabled(False)
        self.offset2_lineEdit.setEnabled(False)
        self.TTLfreq_comboBox.setEnabled(False)
        self.laser_comboBox.setEnabled(False)        
        self.daq_trigenable_radioButton.setChecked(True)
        self.daq_trigenable_radioButton.setEnabled(False)
        self.scanrange1_lineEdit.returnPressed.connect(lambda: self.pushnewdaqsignal(True))
        self.offset1_lineEdit.returnPressed.connect(lambda: self.pushnewdaqsignal(True))
        self.VPS_comboBox.activated.connect(lambda: self.pushnewdaqsignal(True))
        self.scanrange2_lineEdit.returnPressed.connect(lambda: self.pushnewdaqsignal(True))
        self.offset2_lineEdit.returnPressed.connect(lambda: self.pushnewdaqsignal(True))
        self.TTLfreq_comboBox.activated.connect(lambda: self.pushnewdaqsignal(True))
        self.daq_trigenable_radioButton.toggled.connect(lambda: self.pushnewdaqsignal(True))
        self.laser_comboBox.activated.connect(lambda: self.pushnewdaqsignal(True))

        self.daqthread_count = 0


        ############## Stage UI initialization ##############
       
        self.connect_stage_pushButton.pressed.connect(self.connectvsdisconnectstage)
        self.recenter_pushButton.pressed.connect(self.recenterstage)
        self.recenter_pushButton.setEnabled(False)
        self.velocity_comboBox.activated.connect(self.velocitystage)
        self.velocity_comboBox.setEnabled(False)
        self.movestep_lineEdit.textChanged.connect(self.movestepstage)
        self.movestep_lineEdit.setEnabled(False)
        self.stepenable_radioButton.toggled.connect(self.movestepenablestage)
        self.haltstage_Button.pressed.connect(self.haltstage)
        self.haltstage_Button.setEnabled(False)
        self.Xpos_pushButton.pressed.connect(self.Xpos_movestage)
        self.Xpos_pushButton.released.connect(self.specialhalt)
        self.Xneg_pushButton.pressed.connect(self.Xneg_movestage)
        self.Xneg_pushButton.released.connect(self.specialhalt)
        self.Ypos_pushButton.pressed.connect(self.Ypos_movestage)
        self.Ypos_pushButton.released.connect(self.specialhalt)
        self.Yneg_pushButton.pressed.connect(self.Yneg_movestage)
        self.Yneg_pushButton.released.connect(self.specialhalt)
        self.Xpos_pushButton.setEnabled(False)
        self.Xneg_pushButton.setEnabled(False)
        self.Ypos_pushButton.setEnabled(False)
        self.Yneg_pushButton.setEnabled(False)
        self.Xpos_lim_pushButton.setCheckable(True)
        self.Xneg_lim_pushButton.setCheckable(True)
        self.Ypos_lim_pushButton.setCheckable(True)
        self.Yneg_lim_pushButton.setCheckable(True)
        self.Xpos_lim_pushButton.clicked.connect(self.Xposbuttonaction)
        self.Xneg_lim_pushButton.clicked.connect(self.Xnegbuttonaction)
        self.Ypos_lim_pushButton.clicked.connect(self.Yposbuttonaction)
        self.Yneg_lim_pushButton.clicked.connect(self.Ynegbuttonaction)
        self.Xpos_lim_pushButton.setEnabled(False)
        self.Xneg_lim_pushButton.setEnabled(False)
        self.Ypos_lim_pushButton.setEnabled(False)
        self.Yneg_lim_pushButton.setEnabled(False)
        self.reset_stagelimit_pushButton.pressed.connect(self.resetstagelimit)
        self.reset_stagelimit_pushButton.setEnabled(False) 
        self.stagethread_count = 0    

        ############## Imaging mode initialization ##############
        self.timedelay_lineEdit.textChanged.connect(self.timedelay)
        self.imaging_mode_comboBox.currentIndexChanged.connect(self.selectimagingmode)
        self.mode_fun_scantime_lineEdit.textChanged.connect(self.functionalimagingscantime)
        self.mode_fun_StartStop_pushButton.pressed.connect(self.startfunctionalimaging)
        self.mode_struct_Yrange_lineEdit.textChanged.connect(self.structuralYrange)
        self.mode_struct_Xrange_lineEdit.textChanged.connect(self.structuralXrange)
        self.mode_struc_StartStop_pushButton.pressed.connect(self.startstructualimaging)

    ##############  CFG tab functions ##############
    
    def galvo1param(self):
        if not self.G1vpd_lineEdit.text() == "":
            try:
                self.g1vpd = abs(float(self.G1vpd_lineEdit.text()))
                if self.g1vpd > 2:
                            QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get damaged ...")
            except:
                self.g1vpd = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid G1", "Enter a positive float value ...")
                self.G1vpd_lineEdit.setText("")
        else:
            self.g1vpd = None

    def galvo2param(self):
        if not self.G2vpd_lineEdit.text() == "":
            try:
                self.g2vpd = abs(float(self.G2vpd_lineEdit.text()))
                if self.g2vpd > 2:
                            QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
            except:
                self.g2vpd = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid G2", "Enter a positive float value ...")
                self.G2vpd_lineEdit.setText("")
        else:
            self.g2vpd = None

    def cameraparam(self):
        if not self.pxsize_lineEdit.text() == "":
            try:
                self.pxsize = abs(float(self.pxsize_lineEdit.text()))
                if self.pxsize > 20:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "Did you mean to enter such a large pixel size? Check again ...")
            except:
                self.pxsize = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid entry detected.", "Enter a positive float value ...")
                self.pxsize_lineEdit.setText("")
        else:
            self.pxsize = None
        if not self.widthpx_lineEdit.text() == "":
            try:
                self.widthpx = abs(int(self.widthpx_lineEdit.text()))
                if self.widthpx > 6000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "Did you mean to enter such a large number of pixels along width? Check again ...")
            except:
                self.widthpx = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid entry detected.", "Enter a positive integer value ...")
                self.widthpx_lineEdit.setText("")
        else:
            self.widthpx = None
        if not self.heightpx_lineEdit.text() == "":
            try:
                self.heightpx = abs(int(self.heightpx_lineEdit.text()))
                if self.heightpx > 6000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "Did you mean to enter such a large number of pixels along height? Check again ...")
            except:
                self.heightpx = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid entry detected.", "Enter a positive integer value ...")
                self.heightpx_lineEdit.setText("")
        else:
            self.heightpx = None

    def mo1param(self):
        if self.MO1make_comboBox.currentIndex() == 0:
            self.mo1tlfl = 200
        elif self.MO1make_comboBox.currentIndex() == 1:
            self.mo1tlfl = 200
        elif self.MO1make_comboBox.currentIndex() == 2:
            self.mo1tlfl = 200
        elif self.MO1make_comboBox.currentIndex() == 3:
            self.mo1tlfl = 180
        else:
            self.mo1tlfl = 165        
        self.mo1mag =  int(re.sub(r"\D", "", self.MO1mag_comboBox.currentText()))
    
    def mo2param(self):
        if self.MO2make_comboBox.currentIndex() == 0:
            self.mo2tlfl = 200
        elif self.MO2make_comboBox.currentIndex() == 1:
            self.mo2tlfl = 200
        elif self.MO2make_comboBox.currentIndex() == 2:
            self.mo2tlfl = 200
        elif self.MO2make_comboBox.currentIndex() == 3:
            self.mo2tlfl = 180
        else:
            self.mo2tlfl = 165        
        self.mo2mag =  int(re.sub(r"\D", "", self.MO2mag_comboBox.currentText()))

    def mo3param(self):
        if self.MO3make_comboBox.currentIndex() == 0:
            self.mo3tlfl = 200
        elif self.MO3make_comboBox.currentIndex() == 1:
            self.mo3tlfl = 200
        elif self.MO3make_comboBox.currentIndex() == 2:
            self.mo3tlfl = 200
        elif self.MO3make_comboBox.currentIndex() == 3:
            self.mo3tlfl = 180
        else:
            self.mo3tlfl = 165        
        self.mo3mag =  int(re.sub(r"\D", "", self.MO3mag_comboBox.currentText()))

    def opticsparam(self):
        try:
            if self.TL1_lineEdit.text():
                self.tl1fl = abs(float(self.TL1_lineEdit.text()))
                if self.tl1fl > 2000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
            else:
                self.tl1fl = None
        except:
            self.tl1fl = None
            QtWidgets.QMessageBox.about(self, "Error! Invalid TL1", "Enter a positive float value ...")
            self.TL1_lineEdit.setText("")
        try:
            if self.TL2_lineEdit.text():
                self.tl2fl = abs(float(self.TL2_lineEdit.text()))
                if self.tl2fl > 2000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
            else:
                self.tl2fl = None
        except:
            self.tl2fl = None
            QtWidgets.QMessageBox.about(self, "Error! Invalid TL2", "Enter a positive float value ...")
            self.TL2_lineEdit.setText("")
        try:
            if self.TL3_lineEdit.text():
                self.tl3fl = abs(float(self.TL3_lineEdit.text()))
                if self.tl3fl > 2000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
            else:
                self.tl3fl = None
        except:
            self.tl3fl = None
            QtWidgets.QMessageBox.about(self, "Error! Invalid TL3", "Enter a positive float value ...")
            self.TL3_lineEdit.setText("")
        
        #register a SL only if it is enabled else set to None
        if self.SL1_lineEdit.isEnabled(): 
            try:
                if self.SL1_lineEdit.text():
                    self.sl1fl = abs(float(self.SL1_lineEdit.text()))
                    if self.sl1fl > 2000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
                else:
                    self.sl1fl = None
            except:
                self.sl1fl = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid SL1", "Enter a positive float value ...")
                self.SL1_lineEdit.setText("")
        if self.SL2_lineEdit.isEnabled():
            try:
                if self.SL2_lineEdit.text():
                    self.sl2fl = abs(float(self.SL2_lineEdit.text()))
                    if self.sl2fl > 2000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
                else:
                    self.sl2fl = None
            except:
                self.sl2fl = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid SL2", "Enter a positive float value ...")
                self.SL2_lineEdit.setText("")
        if self.SL3_lineEdit.isEnabled():
            try:
                if self.SL3_lineEdit.text():
                    self.sl3fl = abs(float(self.SL3_lineEdit.text()))
                    if self.sl3fl > 2000:
                        QtWidgets.QMessageBox.about(self, "Warning! Unusually large entry detected.", "If you proceed the connected hardware might get affected ...")
                else:
                    self.sl3fl = None
            except:
                self.sl3fl = None
                QtWidgets.QMessageBox.about(self, "Error! Invalid SL3", "Enter a positive float value ...")
                self.SL3_lineEdit.setText("")

    def cfgload(self):        
        filename,_ = QtWidgets.QFileDialog.getOpenFileName(None,'Load From','',"JSON Files (*.json);;All Files(*)") #SaveFileName (None, 'Save As', '', "JSON Files (*.json);;All Files (*)")
        if filename:
            try:
                with open(filename, "r") as cfg_jsonfile:
                    cfg_dict = json.load(cfg_jsonfile)
                # print(cfg_dict)
                #overwrite the UI with new entry from dictionary file
                # self.opmsopi_comboBox.setCurrentIndex(cfg_dict["lightsheet_mode"])
                # self.galvonum_comboBox.setCurrentIndex(cfg_dict["galvo_num"])
                self.G1vpd_lineEdit.setText(str(cfg_dict["g1vpd"]))
                self.G2vpd_lineEdit.setText(str(cfg_dict["g2vpd"]))
                self.pxsize_lineEdit.setText(str(cfg_dict["cam_pxsize"]))
                self.widthpx_lineEdit.setText(str(cfg_dict["width_pixels"]))
                self.heightpx_lineEdit.setText(str(cfg_dict["height_pixels"]))
                self.MO1make_comboBox.setCurrentIndex(cfg_dict["mo1index"])
                self.MO1mag_comboBox.setCurrentIndex(cfg_dict["mo1magindex"])
                self.MO2make_comboBox.setCurrentIndex(cfg_dict["mo2index"])
                self.MO2mag_comboBox.setCurrentIndex(cfg_dict["mo2magindex"])
                self.MO3make_comboBox.setCurrentIndex(cfg_dict["mo3index"])
                self.MO3mag_comboBox.setCurrentIndex(cfg_dict["mo3magindex"])
                self.TL1_lineEdit.setText(str(cfg_dict["tl1fl"]))
                self.TL2_lineEdit.setText(str(cfg_dict["tl2fl"]))
                self.TL3_lineEdit.setText(str(cfg_dict["tl3fl"]))
                self.SL1_lineEdit.setText(str(cfg_dict["sl1fl"]))
                self.SL2_lineEdit.setText(str(cfg_dict["sl2fl"]))
                self.SL3_lineEdit.setText(str(cfg_dict["sl3fl"]))
                QtWidgets.QMessageBox.about(self, "Remember!", "Verify form entries and click Done button ...")
            except:
                QtWidgets.QMessageBox.about(self, "Error!", "Could not load the .json file. Retry ...")
            

    def cfgsave(self):
        #ensure all the values are in:
        self.galvo1param()
        self.galvo2param()
        self.cameraparam()
        self.mo1param()
        self.mo2param()
        self.mo3param()
        self.opticsparam()
        #define a dictionary of all the values
        cfg_dict = {                     
                    "g1vpd": self.g1vpd,
                    "g2vpd": self.g2vpd,
                    "cam_pxsize": self.pxsize,
                    "width_pixels": self.widthpx,
                    "height_pixels": self.heightpx,
                    "mo1index": self.MO1make_comboBox.currentIndex(),
                    "mo1tlfl": self.mo1tlfl,
                    "mo1magindex": self.MO1mag_comboBox.currentIndex(),
                    "mo1mag": self.mo1mag,
                    "mo2index": self.MO2make_comboBox.currentIndex(),
                    "mo2tlfl": self.mo2tlfl,
                    "mo2magindex": self.MO2mag_comboBox.currentIndex(),
                    "mo2mag": self.mo2mag,
                    "mo3index": self.MO3make_comboBox.currentIndex(),
                    "mo3tlfl": self.mo3tlfl,
                    "mo3magindex": self.MO3mag_comboBox.currentIndex(),
                    "mo3mag": self.mo3mag,
                    "sl1fl": self.sl1fl,
                    "sl2fl": self.sl2fl,
                    "sl3fl": self.sl3fl,
                    "tl1fl": self.tl1fl,
                    "tl2fl": self.tl2fl,
                    "tl3fl": self.tl3fl
                    }
        # print(cfg_dict) #print dictionary
        # save the disctionary as a .json file
        filename,_ = QtWidgets.QFileDialog.getSaveFileName(None, 'Save As', '', "JSON Files (*.json);;All Files (*)")
        if filename:
            try:
                with open(filename, "w+") as file:
                    json.dump(cfg_dict, file)
            except:
                QtWidgets.QMessageBox.about(self, "Error! File Saving.", "Could not save the file. Retry ...")

    def cfgdone(self):   
        #ensure all the entered values are available as self. python variables:
        self.galvo1param()
        self.galvo2param()
        self.cameraparam()
        self.mo1param()
        self.mo2param()
        self.mo3param()
        self.opticsparam()     
        #change tab and enable fields
        self.tabWidget.setCurrentIndex(1)
        self.imaging_mode_groupBox.setEnabled(True)


        # self.close() #close dialog window
    
    ############## DAQ UI functions ##############

    def connectvsdisconnectdaq(self):
        if self.connect_daq_pushButton.text() == 'Connect':            
            self.initdaq()
        else:
            # Disconnect daq
            self.connect_daq_pushButton.setText('Connect')
            self.daq_terminate_signal() #terminate running DAQ signal     
            self.daq_wait()             #ensure remaining trace of signal to finish
            self.daq_disconnect()
            self.daqstatus_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.scanrange1_lineEdit.setEnabled(False)
            self.offset1_lineEdit.setEnabled(False)
            self.VPS_comboBox.setEnabled(False)
            self.scanrange2_lineEdit.setEnabled(False)
            self.offset2_lineEdit.setEnabled(False)
            self.TTLfreq_comboBox.setEnabled(False)
            self.laser_comboBox.setEnabled(False)

    def initdaq(self):
        self.msg += "Identifying DAQ board ...\n"
        MCCdaq.__init__(self) # run DAQ __init__ method
        self.daqthread_count = 0 #A variable to keep track of DAQ threadcount
        self.loadnewdaqsignalflag = True #a flag to enable loading of a new signal in system memory
        if self.daq_connectboard(0): #load configuration file
            try:
                self.daqstatus_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Green_btn.png"))
                self.connect_daq_pushButton.setText('Disconnect')
                self.scanrange1_lineEdit.setEnabled(True)
                self.offset1_lineEdit.setEnabled(True)
                self.VPS_comboBox.setEnabled(True)
                self.scanrange2_lineEdit.setEnabled(True)
                self.offset2_lineEdit.setEnabled(True)
                self.TTLfreq_comboBox.setEnabled(True)
                self.daq_trigenable_radioButton.setEnabled(True)
                self.laser_comboBox.setEnabled(True)   
                #populate fields with default values
                self.scanrange1_lineEdit.setText('100')
                self.offset1_lineEdit.setText('0')
                self.VPS_comboBox.setCurrentIndex(4)
                self.scanrange2_lineEdit.setText('220')
                self.offset2_lineEdit.setText('0')
                self.TTLfreq_comboBox.setCurrentIndex(5)
                #push the DAQ signal
                self.continuousscan_option = True 
                self.pushnewdaqsignal(True)
            except: #if could not load all parameters from configuration file
                self.connect_daq_pushButton.setText('Disconnect')
                self.connectvsdisconnectdaq()
        else:
            self.daqstatus_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.connect_daq_pushButton.setText('Connect')
            self.scanrange1_lineEdit.setEnabled(False)
            self.offset1_lineEdit.setEnabled(False)
            self.VPS_comboBox.setEnabled(False)
            self.scanrange2_lineEdit.setEnabled(False)
            self.offset2_lineEdit.setEnabled(False)
            self.TTLfreq_comboBox.setEnabled(False)
            self.laser_comboBox.setEnabled(False)            
            QtWidgets.QMessageBox.about(self, "Error! No DAQ device detected", "Connect DAQ device to PC before proceeding ...")
        

    def pushnewdaqsignal(self, loadnewdaqsignalflag):
        """
        A function to translate DAQ distance parameters into voltage, populate system memory and *push* the signal out through a new thread.

        loadnewdaqsignalflag: Bool
            It defines if a new signal will get loaded in the memory before pushing the output signal

        self.daqhasupdatedsignal flag (in the body of this function) keeps track of signal update status
        """   
        #Freeze UI interaction during DAQ update
        self.daqhasupdatedsignal = False
        self.scanrange1_lineEdit.setEnabled(False)
        self.offset1_lineEdit.setEnabled(False)
        self.VPS_comboBox.setEnabled(False)
        self.scanrange2_lineEdit.setEnabled(False)
        self.offset2_lineEdit.setEnabled(False)
        self.TTLfreq_comboBox.setEnabled(False)
        self.laser_comboBox.setEnabled(False)
        
        if loadnewdaqsignalflag:
            FPS = int(self.TTLfreq_comboBox.currentText())
            VPS = float(self.VPS_comboBox.currentText())
            if (FPS/VPS).is_integer():
                pass
            else:
                self.msg += '\U000026A0 Incompatible VPS FPS combination! Resetting values to default ...'
                self.VPS_comboBox.setCurrentIndex(4)
                self.TTLfreq_comboBox.setCurrentIndex(5)
        else:
            pass 

        import traceback
        try:
            if self.daqcfgmaths():            
                updatedaq_worker = Worker(lambda: self._pushdaqsignalnow(loadnewdaqsignalflag))
                updatedaq_worker.signals.finished.connect(self._donewithdaqupdate)        
                updatedaq_worker.signals.error.connect(lambda: self.errorindaqupdate(updatedaq_worker.errormsg))    
                self.threadpool.start(updatedaq_worker)
        except Exception as e: 
            print(e)
            traceback.print_exc()
        
    def _pushdaqsignalnow(self, loadnewdaqsignalflag):
        self.daqthread_count += 1  
        if loadnewdaqsignalflag:      
            V1_range = int(self.scanrange1_lineEdit.text())*self.g1vpd*self.g1dpµm  #*G1_µm2mechRot*G1_mechRot2v
            V1_offset = int(self.offset1_lineEdit.text())*self.g1vpd*self.g1dpµm  #*G1_µm2mechRot*G1_mechRot2v
            V2_range = int(self.scanrange2_lineEdit.text())*self.g2vpd*self.g2dpµm  #*G2_µm2mechRot*G2_mechRot2v
            V2_offset = int(self.offset2_lineEdit.text())*self.g2vpd*self.g2dpµm  #*G2_µm2mechRot*G2_mechRot2v
            VPS = float(self.VPS_comboBox.currentText())
            FPS = int(self.TTLfreq_comboBox.currentText())
            V4 = float(1.5*(int(self.laser_comboBox.currentIndex())))

            # number of pixels along camera width (longer dim / X-axis), ensure even
            if self.widthpx % 2 == 0:
                points_per_ramp = int(self.widthpx/6) # div by 6 because pencil beam lateral FWHM covers more than 12 pixels at once
            else:
                points_per_ramp = int((self.widthpx-1)/6)
            #if 2nd galvo is absent, no need to go super fine in sampling
            if V2_range == 0:
                points_per_ramp = 200

            activetrigger_option = self.daq_trigenable_radioButton.isChecked()
            self.daq_load_signals(V1_range,V1_offset,VPS,V2_range,V2_offset,FPS,V4, points_per_ramp, activetrigger_option)
        #ensure older thread(s) get(s) closed
        self.daq_terminate_signal()
        while True:
            time.sleep(0.1) #wait till only 1 thread (current one) is running
            if self.daqthread_count == 1:
                time.sleep(0.1) #additional wait to be safe - sufficient or add a bit more? 
                break
        self.daq_push_signals(self.continuousscan_option)
        
        #Re-enable user interaction once DAQ is updated
        self.scanrange1_lineEdit.setEnabled(True)
        self.offset1_lineEdit.setEnabled(True)
        self.VPS_comboBox.setEnabled(True)
        self.scanrange2_lineEdit.setEnabled(True)
        self.offset2_lineEdit.setEnabled(True)
        self.TTLfreq_comboBox.setEnabled(True)
        self.laser_comboBox.setEnabled(True) 
        if loadnewdaqsignalflag:
            self.daqhasupdatedsignal = True #inform that daq has updated        
        #make the thread wait till signal has finished running
        self.daq_wait() 

    def _donewithdaqupdate(self):
        self.daqthread_count -= 1
        # self.msg += 'Just terinated an old DAQ signal thread'


    def errorindaqupdate(self,errormsg):
        self.msg += '\U000026A0 Error in updating DAQ signal!\n'
        self.msg += errormsg
        self.daqthread_count -= 1


    def daqcfgmaths(self):
        try:
            #Use CFG variables from the form entry
            self.g1vpd = self.g1vpd
            self.g2vpd = self.g2vpd
            self.g1dpµm = math.degrees(math.atan(self.mo1mag*self.tl1fl/(2*self.mo1tlfl*self.sl1fl*1000))) #mech rot angle per µm scan range 
            self.g2dpµm = math.degrees(math.atan(self.mo1mag*self.tl1fl*self.sl2fl/(2*self.mo1tlfl*self.sl1fl*self.sl3fl*1000)))       
            self.pxsize = self.pxsize
            self.heightpx = self.heightpx
            self.widthpx = self.widthpx 
            #calculate overall magnification of the SOPi system
            self.SOPimag = self.mo1mag*self.tl1fl/self.mo1tlfl #1st sub-system magnification
            self.SOPimag *= self.sl2fl/self.sl1fl #SOPi scan engine magnification
            self.SOPimag /= self.mo2mag*self.tl2fl/self.mo2tlfl #2nd sub-system magnification
            self.SOPimag *= self.mo3mag*self.tl3fl/self.mo3tlfl #3rd sub-system magnification
            #get X axis field of view
            self.SOPi_Xfov = int(self.widthpx*self.pxsize/self.SOPimag)
            # self.msg += 'Configuration has successfully passed values to the main UI\n'
            return True
        except:
            QtWidgets.QMessageBox.about(self, "Error!", "\nCan not start DAQ. Something went wrong with CFG file values. Try again ...")    
            return False # exit DAQ if scaling factors are unknown
        
    
    
    ############## Stage UI functions ##############

    def connectvsdisconnectstage(self):
        if self.connect_stage_pushButton.text() == 'Connect':  
            try:
                self.initializationstage()
            except Exception:
                self.msg += '\n'
                self.msg += traceback.format_exc()
        else:
            self.connect_stage_pushButton.setText('Connect')
            self.stage_disconnect()
            self.stagestatus_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Gray_btn.png"))
            self.recenter_pushButton.setEnabled(False)
            self.velocity_comboBox.setEnabled(False)            
            self.movestep_lineEdit.setEnabled(False)
            self.haltstage_Button.setEnabled(False)
            self.Xpos_pushButton.setEnabled(False)
            self.Xneg_pushButton.setEnabled(False)
            self.Ypos_pushButton.setEnabled(False)
            self.Yneg_pushButton.setEnabled(False)

    def initializationstage(self):
        MCL_MicroDrive.__init__(self)
        MCL_MicroDrive.stage_connect(self)
        self.stagethread_count = 0 #to keep count of the stage threads
        if self.stage_handle > 0:
            self.stagestatus_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Green_btn.png"))
            self.connect_stage_pushButton.setText('Disconnect')
            self.recenter_pushButton.setEnabled(True)
            self.velocity_comboBox.setEnabled(True)
            if self.stepenable_radioButton.isChecked():
                self.movestep_lineEdit.setEnabled(True)
            self.haltstage_Button.setEnabled(True)
            self.Xpos_pushButton.setEnabled(True)
            self.Xneg_pushButton.setEnabled(True)
            self.Ypos_pushButton.setEnabled(True)
            self.Yneg_pushButton.setEnabled(True)
        else:
            self.stagestatus_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.connect_stage_pushButton.setText('Connect')            
            self.recenter_pushButton.setEnabled(False)
            self.velocity_comboBox.setEnabled(False)
            self.movestep_lineEdit.setEnabled(False)
            self.haltstage_Button.setEnabled(False)
            self.Xpos_pushButton.setEnabled(False)
            self.Xneg_pushButton.setEnabled(False)
            self.Ypos_pushButton.setEnabled(False)
            self.Yneg_pushButton.setEnabled(False)   
            QtWidgets.QMessageBox.about(self, "Error! No stage detected", "\nConnect stage to PC (USB), and power outlet before proceeding ...")    

    def recenterstage(self):        
        stagerecenter_worker = Worker(self.recenternowstage)
        stagerecenter_worker.signals.error.connect(lambda: self.recentererrorstage(stagerecenter_worker.errormsg))
        stagerecenter_worker.signals.finished.connect(self.recentercompletestage)
        self.msg += "Stage re-centering is starting. May take 10+ seconds. Please be patient ..."
        self.threadpool.start(stagerecenter_worker)

    def recenternowstage(self):
        self.stagethread_count += 1
        self.recenter_pushButton.setEnabled(False)
        self.Xpos_pushButton.setEnabled(False)
        self.Xneg_pushButton.setEnabled(False)
        self.Ypos_pushButton.setEnabled(False)
        self.Yneg_pushButton.setEnabled(False)
        self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
        self.stage_recenter() #recenter stage

    def recentererrorstage(self,errormsg):
        self.msg += "\U000026A0 Error in re-centering the stage.\n"
        self.msg += errormsg
        self.movecompletestage()

    def recentercompletestage(self):
        self.movecompletestage()

    def velocitystage(self):
        self.stage_velocity = float(self.velocity_comboBox.currentText())

    def movestepstage(self):
        """ Reads movestep_lineEdit text and updates self.movestepum """
        try:
            self.movestepum = float(self.movestep_lineEdit.text())
        except:
            self.msg += "\U000026A0 Invalid entry for stage move stepsize. Resetting to default value ..."
            self.movestep_lineEdit.setText("100")  
            self.movestepum = float(self.movestep_lineEdit.text())        

    def movestepenablestage(self):        
        if self.stepenable_radioButton.isChecked():
            self.movestep_lineEdit.setEnabled(True)             
        else:            
            self.movestep_lineEdit.setEnabled(False)

    def haltstage(self):
        try:
            self.stage_halt()
            self.stage_getcurrentposition()
            positiontext = '('+ str(round(self.stage_YXposition[0],2)) + ',' + str(round(self.stage_YXposition[1],2)) + ') µm'
            self.location_display_label.setText(positiontext)
            if self.stagethread_count == 0:
                self.stagethread_count += 1 #adding one just to compensate for 1 subtraction in movecompletestage()
            self.movecompletestage() #notify the end of running move/thread 
        except:
            self.msg += '\U000026A0 Failed while halting the MCL stage. Likely, connection lost!\n'
            self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))


    def Xpos_movestage(self):
        self.velocitystage() #ensure self.stage_velocity is available 
        if self.stepenable_radioButton.isChecked():
            self.movestepstage()   
            self.velocitystage()
            self.x = self.movestepum
            self.y = 0
            self.freezemotionstage()
            stagemotion_worker = Worker(self.movenowstage)
            stagemotion_worker.signals.error.connect(lambda: self.moveerrorstage(stagemotion_worker.errormsg))
            stagemotion_worker.signals.finished.connect(self.movecompletestage)  
            self.threadpool.start(stagemotion_worker)
        else:
            self.movestepum = 12700 - self.stage_YXposition[1]            
            self.velocitystage()
            self.x = self.movestepum            
            self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.stage_moveX(self.x, self.stage_velocity) 
         

    def Xneg_movestage(self):
        if self.stepenable_radioButton.isChecked():
            self.movestepstage()   
            self.velocitystage()
            self.x = -1*self.movestepum
            self.y = 0
            self.freezemotionstage()
            stagemotion_worker = Worker(self.movenowstage)
            stagemotion_worker.signals.error.connect(lambda: self.moveerrorstage(stagemotion_worker.errormsg))
            stagemotion_worker.signals.finished.connect(self.movecompletestage)  
            self.threadpool.start(stagemotion_worker)
        else:
            self.movestepum = 12700 - self.stage_YXposition[1]
            self.velocitystage()
            self.x = -1*self.movestepum            
            self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.stage_moveX(self.x, self.stage_velocity)
        

    def Ypos_movestage(self):
        if self.stepenable_radioButton.isChecked():
            self.movestepstage()   
            self.velocitystage()
            self.y = self.movestepum
            self.x = 0
            self.freezemotionstage()
            stagemotion_worker = Worker(self.movenowstage)
            stagemotion_worker.signals.error.connect(lambda: self.moveerrorstage(stagemotion_worker.errormsg))
            stagemotion_worker.signals.finished.connect(self.movecompletestage)  
            self.threadpool.start(stagemotion_worker)          
        else:
            self.movestepum = 12700 - self.stage_YXposition[0]
            self.velocitystage()
            self.y = self.movestepum            
            self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.stage_moveY(self.y, self.stage_velocity)

    def Yneg_movestage(self):
        if self.stepenable_radioButton.isChecked():
            self.movestepstage()   
            self.velocitystage()
            self.y = -1*self.movestepum
            self.x = 0
            self.freezemotionstage()
            stagemotion_worker = Worker(self.movenowstage)
            stagemotion_worker.signals.error.connect(lambda: self.moveerrorstage(stagemotion_worker.errormsg))
            stagemotion_worker.signals.finished.connect(self.movecompletestage)  
            self.threadpool.start(stagemotion_worker)
        else:
            self.movestepum = 12700 - self.stage_YXposition[0]
            self.velocitystage()
            self.y = -1*self.movestepum            
            self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
            self.stage_moveY(self.y, self.stage_velocity)
    
    def movenowstage(self):
        # self.msg += "Running thread "+ str(self.threadpool.activeThreadCount()) + " (max. allowed " + str(self.threadpool.maxThreadCount()) + ")"
        self.stagethread_count += 1
        if self.stagethread_count == 1:            
            if self.x == 0:
                self.stage_moveY(self.y, self.stage_velocity)
            else:
                self.stage_moveX(self.x, self.stage_velocity)
            self.stage_wait()
        else:
            self.msg += '\U000026A0 Stage is already busy, try to move after previous move has finished!\n'
        
    def movecompletestage(self):
        self.unfreezemotionstage()
        self.stage_getcurrentposition() 
        positiontext = '('+ str(round(self.stage_YXposition[0],2)) + ',' + str(round(self.stage_YXposition[1],2)) + ') µm'
        self.location_display_label.setText(positiontext)
        self.stagethread_count -= 1

    def freezemotionstage(self):
        self.recenter_pushButton.setEnabled(False)
        self.Xpos_pushButton.setEnabled(False)
        self.Xneg_pushButton.setEnabled(False)
        self.Ypos_pushButton.setEnabled(False)
        self.Yneg_pushButton.setEnabled(False)
        self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Red_btn.png"))
    
    def unfreezemotionstage(self):
        self.recenter_pushButton.setEnabled(True)
        self.Xpos_pushButton.setEnabled(True)
        self.Xneg_pushButton.setEnabled(True)
        self.Ypos_pushButton.setEnabled(True)
        self.Yneg_pushButton.setEnabled(True)
        self.stagemotion_LED.setPixmap(QtGui.QPixmap(":/icons/icons/Green_btn.png"))


    def moveerrorstage(self,errormsg):        
        self.msg += "\U000026A0 Error in moving stage!"
        self.msg += errormsg
        self.stagethread_count -= 1


    def specialhalt(self):
        """
        A modified halt which works in jog mode. Corresponding Button release calls this halt function. 
        """
        if not self.stepenable_radioButton.isChecked():
            self.haltstage() #location update is integrated in this function 
        # self.stagethread_count -= 1

           
        
    ############## Imaging mode UI functions ##############

    def browsesavelocation(self):
        pathname = QtWidgets.QFileDialog.getExistingDirectory(self,"Camera Save Folder Location")#, options=QtWidgets.QFileDialog.DontUseNativeDialog)
        if pathname:
            self.filesaveloc_lineEdit.setText(pathname)


    def changefilenameprefix(self):
        self.FileNamePrefix = "" #reset to empty 
        if self.date_checkBox.isChecked():
            self.FileNamePrefix += datetime.now().strftime('%b%d-%Y_')
        if self.time_checkBox.isChecked():
            self.FileNamePrefix += datetime.now().strftime('%H%M%S_')
        try:
            self.FileNamePrefix += self.filename_lineEdit.text() + '_'           
        except:
            pass
        txt = ""
        try:
            txt += str(round(float(self.ExpTime_lineEdit.text()),2)) + 'ms_' 
        except:
            pass 
        if self.imaging_mode_comboBox.currentIndex() > 0:
                txt += self.scanrange1_lineEdit.text() + 'um_' 
                txt += self.TTLfreq_comboBox.currentText() + 'fps_' + self.VPS_comboBox.currentText() + 'VPS_'
        self.FileNamePrefix += txt  
        if self.imaging_mode_comboBox.currentIndex() == 1:
            self.FileNamePrefix += 'functional_' + self.mode_fun_scantime_lineEdit.text() + 's_'
        elif self.imaging_mode_comboBox.currentIndex() == 2:
            self.FileNamePrefix += 'structural_' + str(self.Y_steps) + str(self.X_steps) + '_'
        elif self.imaging_mode_comboBox.currentIndex() == 3:
            self.FileNamePrefix += 'timelapse_'
        

    # index 1 = Functional imaging, and 2 = Structural imaging
    def selectimagingmode(self):
        self.imagingmodeUItimer = QtCore.QTimer()        
        self.imagingmodeUItimer.setInterval(100) # interval in milli secodns
        self.imagingmodeUItimer.timeout.connect(self.updateimagingmodeUI)

        self.resetstagelimit()
        self.Xpos_lim_pushButton.setEnabled(False)
        self.Xneg_lim_pushButton.setEnabled(False)
        self.Ypos_lim_pushButton.setEnabled(False)
        self.Yneg_lim_pushButton.setEnabled(False)
        self.reset_stagelimit_pushButton.setEnabled(False)

        if self.imaging_mode_comboBox.currentIndex() == 1:
            self.functional_groupBox.setEnabled(True)
            self.structural_groupBox.setEnabled(False)
            
            if self.connect_daq_pushButton.text() == 'Connect':
                self.msg += '\U000026A0 DAQ device is disconnected! Please ensure it is connected before proceeding ....\n'
                QtWidgets.QMessageBox.about(self, "Error! No DAQ detected", "Connect DAQ before proceeding ...")
                self.imaging_mode_comboBox.setCurrentIndex(0)    
            
            self.msg += '\U000026A0 Please ensure camera it is connected elsewhere before proceeding ....\n'
            QtWidgets.QMessageBox.about(self, "Warning! Camera must be enabled", "If camera is not trigger ready then no images will get captured ...")
                        
            #if required devices are connected, update text box
            if self.imaging_mode_comboBox.currentIndex() == 1:
                self.mode_fun_scantime_lineEdit.setText('10')  #default scan-time is 10 s
                self.functionalimagingscantime() #enable scan-time lineEdit for Functional UI box             
                self.imagingmodeUItimer.start()
            else:
                self.imagingmodeUItimer.stop()

        elif self.imaging_mode_comboBox.currentIndex() == 2:
            #enable structural imaging box
            self.functional_groupBox.setEnabled(False)
            self.structural_groupBox.setEnabled(True)
            
            #enable set limit buttons (in Stage UI)
            self.Xpos_lim_pushButton.setEnabled(True)
            self.Xneg_lim_pushButton.setEnabled(True)
            self.Ypos_lim_pushButton.setEnabled(True)
            self.Yneg_lim_pushButton.setEnabled(True)
            self.reset_stagelimit_pushButton.setEnabled(True)
            
            #Check daq,stage,camera connection status
            if self.connect_daq_pushButton.text() == 'Connect':
                self.msg += '\U000026A0 DAQ device is disconnected! Please ensure it is connected before proceeding ....\n'
                QtWidgets.QMessageBox.about(self, "Error! No DAQ detected", "Connect DAQ before proceeding ...")
                self.imaging_mode_comboBox.setCurrentIndex(0) #can't do imaging without daq
            if self.connect_stage_pushButton.text() == 'Connect':
                self.msg += '\U000026A0 Stage is disconnected! Please ensure it is connected before proceeding ....\n'
                QtWidgets.QMessageBox.about(self, "Error! No stage detected", "Connect stage before proceeding ...")
                self.imaging_mode_comboBox.setCurrentIndex(0) #can't do imaging without stage
                
            #if required devices are connected, update text box
            if self.imaging_mode_comboBox.currentIndex() == 2:
                # Autofill default values for Xrange and Yrange
                txt = self.scanrange1_lineEdit.text()
                self.mode_struct_Yrange_lineEdit.setText(txt)                          
                self.mode_struct_Xrange_lineEdit.setText(str(self.SOPi_Xfov))
                del txt              
                self.imagingmodeUItimer.start()
            else:
                self.imagingmodeUItimer.stop() 
        else:
            self.functional_groupBox.setEnabled(False)
            self.structural_groupBox.setEnabled(False)


    def timedelay(self):
        try:
            self.timedelay = int(self.timedelay_lineEdit.text())
        except:
            self.timedelay = 0
            self.msg += '\U000026A0 Invalid time-delay entry! An integer was expected.'
        self.timedelay_lineEdit.setText(str(self.timedelay))

    def functionalimagingscantime(self):
        """
        Enable functional mode scan-time lineEdit, fetch scan-time, and update number of camera frames
        """
        try:
            self.scantime = abs(int(self.mode_fun_scantime_lineEdit.text()))            
        except:            
            QtWidgets.QMessageBox.about(self, "Error! Invalid scan-time entered", "Invalid scan-time entry detected. Resetting to 10 ...")            
            self.scantime = 10 #default scan-time
            self.mode_fun_scantime_lineEdit.setText(str(self.scantime)) #update scan-time entry with default
        total_frames = int(self.TTLfreq_comboBox.currentText())*self.scantime #calculate num frames        
        self.functionalcamframes_label.setText('#frames ' + str(total_frames)) #update displayed total num frames in UI 

    def startfunctionalimaging(self):        
        functionalimaging_worker = Worker(self.start_functionalimaging_thread)
        functionalimaging_worker.signals.finished.connect(self.finished_functionalimaging_thread)
        functionalimaging_worker.signals.error.connect(lambda: self.error_functionalimaging_thread(functionalimaging_worker.errormsg)) 
        if self.mode_fun_StartStop_pushButton.text() == 'Start':
            self.mode_fun_StartStop_pushButton.setText('Stop')
            self.threadpool.start(functionalimaging_worker)
        else:
            self.stop_functionalimaging()

    def start_functionalimaging_thread(self):
        """
        Functional (or time-lapse) imaging thread. Consists of a sequence of actions:
        1. enable DAQ for continuous/single scan and ensure no trigger output        
        2. enable DAQ trigger o/p - and wait for camera to finish acquisition 
        """
        self.msg += '******************************************************\n'
        self.msg += 'Starting functional imaging thread now ...\n'

        # 1. Ensure DAQ o/p is set for looping/single as per the application
        # Ensure DAQ o/p is silent by the end of this step as to not enable untimed camera frame acquisition
        self.daq_terminate_signal() #terminate signal
        if self.timedelay_radioButton.isChecked():
            self.continuousscan_option = False #continuous looping disabled - used inside DAQ thread
            self.msg += 'DAQ is all set for time-lapse imaging ....\n'            
        else:
            self.continuousscan_option = True #continuous looping enabled - used inside DAQ thread
            self.msg += 'DAQ is all set for functional imaging ....\n'          
                
            
        # 2. Output DAQ signal WITH TRIGGER and wait till acquisition is finished
         
        if self.timedelay_radioButton.isChecked(): 
            # time-lapse imaging with a delay           
            for i in range(int(self.num_sweeps)):
                if self.mode_fun_StartStop_pushButton.text() == 'Stop':
                    if not self.daq_trigenable_radioButton.isChecked():
                        #if trigger box is unchecked, check it to generate DAQ signal
                        self.daqhasupdatedsignal = False # this will become true once DAQ updates in another thread
                        self.daq_trigenable_radioButton.setChecked(True) #will generate toggle signal and new DAQ o/p without trigger
                        while not self.daqhasupdatedsignal: 
                            #wait till new signal loads in memory
                            time.sleep(0.1)
                        print("1")
                    else:
                        #if trigger box is checked, just push a new signal
                        self.pushnewdaqsignal(False)
                        print("2")
                    #wait till completion of sweep because self.continuousscan_option was set to false above (in step 1 for time-lapse)
                    while True: 
                        time.sleep(0.1)     
                        if self.daqthread_count == 0:
                            break            
                    time.sleep(self.timedelay) #add time delay on top
                    self.msg += f"Done with {i+1} out of {int(self.num_sweeps)} sweeps in time-lapse \n"
                else:
                    self.msg += f"Failed with {i+1} out of {int(self.num_sweeps)} sweeps in time-lapse \n"                
        else:
            # functional imaging without any delay
            if not self.daq_trigenable_radioButton.isChecked():
                #if trigger box is unchecked, check it to generate DAQ signal
                self.daqhasupdatedsignal = False # this will become true once DAQ updates in another thread
                self.daq_trigenable_radioButton.setChecked(True) #will generate toggle signal and new DAQ o/p with trigger
                while not self.daqhasupdatedsignal: 
                    #wait till new signal loads in memory
                    time.sleep(0.1)
            else:
                #if trigger box is checked, just push a new signal
                self.pushnewdaqsignal(False) #push new daq but no need to look for new signal 
            t0 = time.time()
            self.msg += 'DAQ trigger signal is working with camera now .... \n'
            #wait till scan time has elapsed
            while (time.time()-t0) < (self.scantime):
                time.sleep(0.1)         
        self.msg += 'Assigned time has elapsed. DAQ trigger is terminating now. \n'
        self.daq_terminate_signal()
        self.continuousscan_option = True # Fall back to the default continuous looping option - used inside DAQ thread

    def stop_functionalimaging(self):
        self.mode_fun_StartStop_pushButton.setText('Start')
        self.mode_fun_StartStop_pushButton.setEnabled(False) #disable button push press till other threads stop
        self.msg += '\U000026A0 Functional imaging was stopped abruptly!\n'       
        # self.mode_fun_StartStop_pushButton.setEnabled(True)

    def finished_functionalimaging_thread(self):
        self.msg += 'Done with the functional imaging thread. ....\n'
        self.mode_fun_StartStop_pushButton.setText('Start')
        self.mode_fun_StartStop_pushButton.setEnabled(True)
    
    def error_functionalimaging_thread(self,errormsg):
        QtWidgets.QMessageBox.about(self, "Error! during functional imaging", "Could not execute the assigned functional imaging ...")
        self.msg += '\U000026A0 Error during functional imaging thread execution.\n'
        self.msg += errormsg
        self.mode_fun_StartStop_pushButton.setText('Start')
        self.mode_fun_StartStop_pushButton.setEnabled(True)

    def structuralYrange(self):
        """
        Function to handle update in the Yrange lineEdit form inside structural imaging mode
        """
        try:
            self.Yrange = int(self.mode_struct_Yrange_lineEdit.text())   
        except:         
            txt = self.scanrange1_lineEdit.text()   
            QtWidgets.QMessageBox.about(self, "Error! Invalid Y range entered", "Invalid Y range entry detected. Resetting to " + txt +" ...")            
            self.mode_struct_Yrange_lineEdit.setText(txt)
            self.Yrange = int(txt)
            del txt
        sopi_range = int(self.scanrange1_lineEdit.text())
        self.Y_steps,Y_rem = divmod(self.Yrange, sopi_range)
        self.Y_steps = int(self.Y_steps)
        if Y_rem > 0: self.Y_steps += 1 #overcompensate for the remainder
        # print(self.Y_steps)

    def structuralXrange(self):
        """
        Function to handle update in the Xrange lineEdit form inside structural imaging mode
        """
        try:
            self.Xrange = int(self.mode_struct_Xrange_lineEdit.text())        
        except:         
            self.Xrange = self.SOPi_Xfov #SOPi X-FOV is default Xrange 
            QtWidgets.QMessageBox.about(self, "Error! Invalid X range entered", "Invalid X range entry detected. Resetting to " + str(self.Xrange) +" ...")            
            self.mode_struct_Xrange_lineEdit.setText(str(self.Xrange))
        self.X_steps,X_rem = divmod(self.Xrange, self.SOPi_Xfov) 
        self.X_steps = int(self.X_steps)
        if X_rem > 0: self.X_steps += 1
        # print(self.X_steps)

    def startstructualimaging(self):
        structuralimaging_worker = Worker(self.start_structuralimaging_thread)
        structuralimaging_worker.signals.finished.connect(self.finished_structuralimaging_thread)
        structuralimaging_worker.signals.error.connect(lambda: self.error_structuralimaging_thread(structuralimaging_worker.errormsg)) 
        self.structuralYrange() #get Yrange
        self.structuralXrange() #get Xrange 
        if self.mode_struc_StartStop_pushButton.text() == 'Start':
            QtWidgets.QMessageBox.about(self, "Warning! camera must be enabled", "If camera is not trigger ready then no images will get captured ...")
            self.mode_struc_StartStop_pushButton.setText('Stop')
            self.threadpool.start(structuralimaging_worker)
        else:            
            self.stop_structuralimaging()  

    def start_structuralimaging_thread(self):  
        """
        Structural imaging thread. Consists of a sequence of actions:
        1. DAQ should be ready for single sweep, cam trigger and other o/p should remain silent
        2. Move stage to the starting position i.e. to self.yneg_lim,self.xneg_lim
        3. Loop in for the actual imaging 
        """

        # 1. DAQ should be ready for single sweep, cam trigger should remain silent
        self.daq_terminate_signal() #terminate signal
        self.continuousscan_option = False #continuous looping disabled 

        self.msg += '******************************************************\n'
        self.msg += 'Starting structural imaging thread now ...\n'

        # 2. Move stage to the starting position i.e. to self.yneg_lim,self.xneg_lim
        # Move stage (along Y-axis) and wait till done
        self.msg += 'Moving stage to the starting position ...\n'
        if not self.stepenable_radioButton.isChecked():
            self.stepenable_radioButton.setChecked(True) #ensure step move is enabled
        try:
            _ = float(self.yneg_lim)  
            if abs(self.yneg_lim-self.stage_YXposition[0]) >= 0.1:          
                self.movestep_lineEdit.setText(str(self.yneg_lim-self.stage_YXposition[0]))  #update movestep size for +y-axis
                self.Ypos_movestage() #y-move
                self.msg += 'Moving stage along y-axis... \n'
                while True: # wait till the end of stage motion
                    time.sleep(0.1)
                    # print(str(self.stagethread_count),end=', ')
                    if self.stagethread_count == 0:
                        break  
            self.msg += 'Stage is at the starting position along y-axis ...\n'
            # print(self.yneg_lim-self.stage_YXposition[0])
        except:
            self.msg += "Stage was already at the starting position along y-axis.\n"

        # Move stage (along X-axis) and wait till done
        try:
            _ = float(self.xneg_lim)
            if abs(self.xneg_lim-self.stage_YXposition[1]) >= 0.1:
                self.movestep_lineEdit.setText(str(self.xneg_lim-self.stage_YXposition[1]))  #update movestep size for +x-axis                
                self.Xpos_movestage() #x-move
                self.msg += 'Moving stage along x-axis... \n'
                while True: # wait till the end of stage motion
                    time.sleep(0.1)
                    if self.stagethread_count == 0:
                        break
            self.msg += 'Stage is at the starting position along x-axis ...\n'
        except:
            self.msg += "Stage was already at the starting position along x-axis.\n"

        # 3. Ensure DAQ trigger o/p is enabled and o/p is set for once (non-looping)
        # Ensure DAQ o/p is silent by the end of this step as to not enable untimed camera frame acquisition
        # if not self.daq_trigenable_radioButton.isChecked():
        #     self.daqhasupdatedsignal = False # this will become true once DAQ updates in another thread
        #     self.daq_trigenable_radioButton.setChecked(True) #will generate toggle signal and new DAQ o/p without trigger
        #     while not self.daqhasupdatedsignal: #wait till new signal loads in memory
        #         time.sleep(0.1)
        # self.daq_terminate_signal() #terminate daq signal
        # self.continuousscan_option = False #non-looping o/p 
        self.msg += 'DAQ is all set for structural imaging ....\n' 

        # 3. Update num frames and do the acquisition        
        # DAQ o/p is silent so camera will wait for trigger signal from DAQ
        self.structuralcamframes_label.setText(str(int((self.X_steps)*(self.Y_steps)*int(self.TTLfreq_comboBox.currentText())/float(self.VPS_comboBox.currentText())))) 
        sopi_range = int(self.scanrange1_lineEdit.text()) #to be used for stage Y motion step size
        # Do loop action for X_steps and Y_steps 
        self.msg += 'Starting a total of %d runs ... \n' %(self.X_steps*self.Y_steps)
        i = 0 #count number of loop runs
        for _ in range (self.X_steps):
            for _ in range (self.Y_steps):
                i += 1 #loop count increment
                # filename = str(i)+str(j) #use this to write image filename 
                if self.mode_struc_StartStop_pushButton.text() == 'Stop':
                    # Push single loop with daq trigger and wait till done
                    if not self.daq_trigenable_radioButton.isChecked():
                        #if trigger box is unchecked, check it to generate DAQ signal
                        self.daq_trigenable_radioButton.setChecked(True) #will generate toggle signal and new DAQ o/p with trigger                        
                    else:
                        #if trigger box is checked, just push a new signal
                        self.pushnewdaqsignal(False) #no need to calculate/load a new signal - just push existing one
                    #wait till DAQ signal runs once
                    while True:                    
                        time.sleep(0.1)
                        if self.daqthread_count == 0:
                            break
                    self.msg += f'####### Finished step {i} out of {self.Y_steps*self.X_steps}. ({self.Y_steps},{self.X_steps}) #######\n'
                    self.msg += f'####### Total# trigger(s): {i*int(int(self.TTLfreq_comboBox.currentText())/float(self.VPS_comboBox.currentText()))} #######\n'
                    # Move stage (along Y-axis) and wait till done
                    self.movestep_lineEdit.setText(str(sopi_range))  #update movestep size for +y-axis                
                    self.Ypos_movestage() #forward y-move first    
                    self.msg += 'Moving stage along y-axis... \n' 
                    while True: # wait till the end of stage motion (end of motion makes the stage thread count 0)
                        time.sleep(0.1)
                        if self.stagethread_count == 0:
                            break  
            if self.mode_struc_StartStop_pushButton.text() == 'Stop':
                #move BACK to starting y point and wait till done (provided stop button was not pressed)
                self.movestep_lineEdit.setText(str(sopi_range*self.Y_steps))  #update movestep size for -y-axis
                self.Yneg_movestage() #move along -y
                self.msg += 'Moving stage along y-axis... \n'
                while True: 
                        time.sleep(0.1)
                        if self.stagethread_count == 0:
                            break
                #move one step along x and wait till done
                self.movestep_lineEdit.setText(str(self.SOPi_Xfov*1.0))  #update movestep size for +x-axis. SOPi % of FOV as per the camera sensor size
                self.Xpos_movestage()
                self.msg += 'Moving stage along x-axis... \n'
                while True: 
                        time.sleep(0.1)
                        if self.stagethread_count == 0:
                            break
        #compensate for X-moves performed in above loop
        if self.mode_struc_StartStop_pushButton.text() == 'Stop':
            self.movestep_lineEdit.setText(str(self.SOPi_Xfov*1.0*self.X_steps))  #update movestep size for -x-axis. SOPi FOV as per the camera sensor size
            self.Xneg_movestage()
            self.msg += 'Moving stage along x-axis... \n'
            while True:
                    time.sleep(0.1)
                    if not self.stagethread_count > 0:
                        break            
        # Stop recording        
        # Enable continuous loop for DAQ and end
        self.continuousscan_option = True
        # loadnewdaqsignalflag = False
        # self.pushnewdaqsignal(loadnewdaqsignalflag)

    def finished_structuralimaging_thread(self):
        self.msg += 'Done with structural imaging thread.\n'
        self.mode_struc_StartStop_pushButton.setText('Start')

    def error_structuralimaging_thread(self, errormsg):
        self.msg += '\U000026A0 Error in executing structural imaging thread.\n'
        self.msg += errormsg
        self.mode_struc_StartStop_pushButton.setText('Start')

    def stop_structuralimaging(self):   
        self.mode_struc_StartStop_pushButton.setText('Start')   
        #stop DAQ signal is taken care of in the main structural imaging thread - it stops at end of single sweep
        self.haltstage() #halt stage

    def resetstagelimit(self):
        if self.Xpos_lim_pushButton.isChecked():
            self.Xpos_lim_pushButton.setChecked(False)
            self.xpos_lim = None
        if self.Xneg_lim_pushButton.isChecked():
            self.Xneg_lim_pushButton.setChecked(False)
            self.xneg_lim = None
        if self.Ypos_lim_pushButton.isChecked():
            self.Ypos_lim_pushButton.setChecked(False)
            self.ypos_lim = None
        if self.Yneg_lim_pushButton.isChecked():
            self.Yneg_lim_pushButton.setChecked(False)
            self.yneg_lim = None

    def Xposbuttonaction(self):
        if self.Xpos_lim_pushButton.isChecked():
            self.xpos_lim = self.stage_YXposition[1] 
        else:
            self.xpos_lim = None
    
    def Xnegbuttonaction(self):
        if self.Xneg_lim_pushButton.isChecked():
            self.xneg_lim = self.stage_YXposition[1] 
        else:
            self.xneg_lim = None

    def Yposbuttonaction(self):
        if self.Ypos_lim_pushButton.isChecked():
            self.ypos_lim = self.stage_YXposition[0] 
        else:
            self.ypos_lim = None
        
    def Ynegbuttonaction(self):
        if self.Yneg_lim_pushButton.isChecked():
            self.yneg_lim = self.stage_YXposition[0] 
        else:
            self.yneg_lim = None        

    def updateimagingmodeUI(self):
        if self.imaging_mode_comboBox.currentIndex() >= 1:
            # check time delay status
            if self.timedelay_radioButton.isChecked():
                self.timedelay_lineEdit.setEnabled(True)
                self.mode_fun_scantime_lineEdit.setEnabled(False)
            else:
                self.timedelay_lineEdit.setEnabled(False)
                self.mode_fun_scantime_lineEdit.setEnabled(True)
            num_planes = int(int(self.TTLfreq_comboBox.currentText())/float(self.VPS_comboBox.currentText()))
            txt = str(num_planes) 
            txt += ' planes at '
            txt += self.VPS_comboBox.currentText()
            txt += ' VPS ('
            if self.imaging_mode_comboBox.currentIndex() == 1:
                #functional imaging 
                self.num_sweeps = self.scantime*float(self.VPS_comboBox.currentText())
                txt += str(self.num_sweeps)
            else:
                #structural imaging has no scan-time.
                txt += 'NN'
            txt += ' sweeps)'
            self.mode_fun_label.setText(txt)
            txt = 'Scan-step: '
            # num_planes = int(int(self.TTLfreq_comboBox.currentText())/float(self.VPS_comboBox.currentText()))
            sopi_range = int(self.scanrange1_lineEdit.text())
            fine_step = round(float(sopi_range/num_planes),3)
            txt += str(fine_step)
            txt += ' µm & scan-range:'
            self.mode_struc_label.setText(txt)     

            #keep updating total frames in UI in imaging mode
            if self.imaging_mode_comboBox.currentIndex() == 1:            
                total_frames = int(self.TTLfreq_comboBox.currentText())*self.scantime
                self.functionalcamframes_label.setText('#frames ' + str(total_frames))
            elif self.imaging_mode_comboBox.currentIndex() == 2:
                self.structuralYrange() #get Yrange
                self.structuralXrange() #get Xrange 
                total_frames = int((self.X_steps)*(self.Y_steps)*int(self.TTLfreq_comboBox.currentText())/float(self.VPS_comboBox.currentText()))
                self.structuralcamframes_label.setText('#frames ' + str(total_frames))
            else:
                total_frames = 0
                self.functionalcamframes_label.setText('#frames ' + str(total_frames))
                self.structuralcamframes_label.setText('#frames ' + str(total_frames))

        #In structural mode, calculate Yrange and Xrange based on set limits and fill those in
        if self.imaging_mode_comboBox.currentIndex() == 2:       
            try:
                val = self.ypos_lim - self.yneg_lim            
                self.mode_struct_Yrange_lineEdit.setText(str(int(val)))
                val = None
            except:
                pass
            try:
                val = self.xpos_lim - self.xneg_lim            
                self.mode_struct_Xrange_lineEdit.setText(str(int(val)))
                val = None
            except:
                pass


    ############## Common functions ##############

    def updateUI(self):
        self.updateTextBrowser() #keep refrshing the log
        self.updatethreadcounts() #track thread counts for cam, daq and stage

    def updateTextBrowser(self):    
        if self.msg != "":
            self.txt = self.msg
            self.textBrowser.append(datetime.now().strftime('%H:%M:%S: ')+self.txt)
            self.textBrowser.moveCursor(QtGui.QTextCursor.End)
            self.msg = ""                                
    
    def updatethreadcounts(self):    
        try:
            if str(self.daqthread_count) != self.DAQthreadCount_lineEdit.text():
                self.DAQthreadCount_lineEdit.setText(str(self.daqthread_count))
                if self.daqthread_count > 1:
                    self.DAQthreadCount_lineEdit.setStyleSheet("color: rgb(250, 0, 0);")
                    self.msg += '\U000026A0 Two or more DAQ threads running simultaneously .... \n'
                else:
                    self.DAQthreadCount_lineEdit.setStyleSheet("color: rgb(128, 128, 128);")
        except:
            self.DAQthreadCount_lineEdit.setText('0')
        try:
            if str(self.stagethread_count) != self.StageThreadCount_lineEdit.text():
                self.StageThreadCount_lineEdit.setText(str(self.stagethread_count))
                if self.stagethread_count > 1:
                    self.StageThreadCount_lineEdit.setStyleSheet("color: rgb(250, 0, 0);")
                    self.msg += '\U000026A0 Two or more stage threads running simultaneously .... \n'
                else:
                    self.StageThreadCount_lineEdit.setStyleSheet("color: rgb(128, 128, 128);")
        except:
            self.StageThreadCount_lineEdit.setText('0')

if __name__ == "__main__":
    import sys, traceback, time, qdarkstyle
    app = QtWidgets.QApplication(sys.argv)
    # setup stylesheet for dark theme
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    w = myWindow()
    w.show()
    sys.exit(app.exec_())
