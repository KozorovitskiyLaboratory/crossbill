"""
Control functions for DAQ davice.

This file consists of classes. Each class represents a DAQ device. 
Currently included class is for MCC DAQ.
More classes can be added to support more DAQ devices.

mcc daq with windows Ref. https://www.mccdaq.com/pdfs/manuals/Mcculw_WebHelp/ULStart.htm 

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
from mcculw import ul
from mcculw.ul import ULError
from mcculw.enums import BoardInfo, InfoType, InterfaceType, ULRange, ErrorCode, ScanOptions, FunctionType, Status 
from time import sleep 
import emoji
# import matplotlib.pyplot as plt 

import numpy as np
import ctypes, time, pathlib, os

class MCCdaq:
    """
    A class to add and control MCC DAQ device.

    Consists of following functions/methods:
    daq_connectboard: connect to DAQ device
    daq_update_scanoption: update scan option to single or continuous
    daq_update_signals: push fresh signal to DAQ board
    daq_deinit_device: De-initialize DAQ device
    """    
    def __init__(self):
        """
        Default initialization function for MCC DAQ board
        """        
        ul.ignore_instacal() #ignore pre-exisitng instacal record of identified devices
        self.dev_list = ul.get_daq_device_inventory(InterfaceType.USB) #get identified USB DAQ devices inventory         
        if len(self.dev_list) > 0:
            board_num = 0
            #list identified devices
            for device in self.dev_list:     
                self.msg += f"Found {str(device)} with serial# {device.unique_id} as board# {board_num} \n"
                board_num += 1
            self.max_board_num = len(self.dev_list)
        else:
            self.max_board_num = 0
            self.msg += '\U000026A0 No USB DAQ device detected\n'


    def daq_connectboard(self, board_num):
        """
        Function to initialize a board as current DAQ device
        
        board_num: int 
            value: 0 and higher 
            select the DAQ board number to initialize I/O
        """
        try:
            self.board_num = int(abs(board_num)) #ensure positive integer
        except:
            self.board_num = 0
            self.msg = "\U000026A0 Invalid entry for board number detected. Reset to 0 ..."

        if self.board_num < self.max_board_num:
            try:                
                device = self.dev_list[self.board_num]
                ul.create_daq_device(self.board_num, device) #create device to enable DAQ I/O functions 
                self.low_chan = 0
                self.high_chan = int(ul.get_config(InfoType.BOARDINFO, self.board_num, 0, BoardInfo.NUMDACHANS))-1
                self.msg += f"Board# {self.board_num} initialized\n"
                self.daq_update_scanoption(1) #scan continuously by default 
                return True
            except:
                self.msg += "\U000026A0 Error in selecting DAQ device. Wrong board number or lost connection.\n"
                return False
        else:
            self.msg += "\U000026A0 Error: out of bound entry for board number.\n"
            return False
        

    def daq_update_scanoption(self, option):
        """
        Function to update the scan option of DAQ board

        option: int
            0: single scan
            1: loop/continuous scan
        """
        if option == 0:
            self.scan_option = ScanOptions.BACKGROUND #| ScanOptions.SIMULTANEOUS
            self.msg += 'Going to scan once ...\n'
        elif option == 1:
            self.scan_option = ScanOptions.CONTINUOUS | ScanOptions.BACKGROUND #| ScanOptions.SIMULTANEOUS
            self.msg += 'Going to scan continuously ...\n'
        else:
            self.msg += "\U000026A0 Error updating scan option. Retry!\n"


    def daq_load_signals(self, V1_range, V1_offset, VPS, V2_range, V2_offset, FPS, V4, points_per_ramp, activetrigger_option):
        """
        A function to load new signals to windows memory. 
        This memory can later be accessed my DAQ to push AO signals out.
        Note: This function is adapted for Prime95B to match the rolling shutter rate (10 µs per width pixel, 83.333 Hz DSLM)

        V1_range: float
        V1_offset: float
        VPS: float/int
        V2_range: float
        V2_offset: float
        FPS: int (fixed at 80 Hz!)
        V4: float
        points_per_ramp: int     
        activetrigger_option: bool

        Ch0: V1_range, V1_offset and VPS define the signal going to G1 galvo for lateral sweep of light-sheet
        Ch1: V2_range, V2_offset, camera sensor read speed and points_per_ramp define the signal going to G2 galso for DSLM style light-sheet creation        
        Ch2: FPS and activetrigger_option define TTL signal for Camera frame-rate control
        Ch3: V4 defines the voltage signal controlling laser selection and on/off duration
        points_per_ramp dictates how many points make up single ramp signal for G2
        """
        
        if (FPS/VPS).is_integer(): 
            #limit V1 and V2 signals
            V1_min = max(V1_offset - V1_range/2, -10)
            V1_max = min(V1_offset + V1_range/2, +10)
            V2_min = max(V2_offset - V2_range/2, -10)
            V2_max = min(V2_offset + V2_range/2, +10)

            self.daq_rate = points_per_ramp*80 #number of D/A point output per second per channel #80 Hz is the sweep rate for Prime95b 
            #max allowed rate is 100KS/s per channel for USB-3101FS
            if self.daq_rate > 96000:
                self.daq_rate = 96000 
                points_per_ramp = int(self.daq_rate/80) #galvo specific for DSLM
            points_per_exposure = int(self.daq_rate/FPS) #Camera trigger specific for number of planes
            num_imageplanes = round(FPS/VPS) # number of oblique image planes per sweep
            points_down_ramp = int(points_per_ramp*0.04) # number of points in down-ramp (this is opposite rolling shutter direction)
            points_up_ramp = points_per_ramp - points_down_ramp # number of points in up-ramp (this is along rolling shutter direction)
            if VPS < 1:
                time = round(1/VPS) #total time for D/A points to output                 
                ramp = np.linspace(V1_max, V1_min, num_imageplanes, endpoint=True)
                signal1 = np.empty([points_per_ramp*int(80/FPS)*num_imageplanes]) #start with an empty signal - must get polulated in next steps
                for iter in range (num_imageplanes):
                    upsignal = np.repeat(ramp[iter], points_up_ramp*int(80/FPS))
                    if iter == (num_imageplanes-1):
                        downsignal = np.linspace(ramp[iter], ramp[0], points_down_ramp*int(80/FPS), endpoint=True)                        
                    else:                        
                        downsignal = np.linspace(ramp[iter], ramp[iter+1], points_down_ramp*int(80/FPS), endpoint=True)
                    signal1[iter*points_per_ramp*int(80/FPS):(iter+1)*points_per_ramp*int(80/FPS)] = np.hstack((upsignal,downsignal)) #Ch0: light-sheet lateral sweep (SOPi) galvo signal 
                # signal1 = np.repeat(ramp, points_per_ramp*int(80/FPS)) #Ch0: light-sheet lateral sweep (SOPi) galvo signal 
                upramp = np.linspace(V2_min,V2_max,points_up_ramp,endpoint=True)
                downramp = np.linspace(V2_max,V2_min,points_down_ramp,endpoint=True)        
                signal2 = np.tile( np.hstack(( upramp,downramp )), 80*time) #Ch1: DSLM galvo signal
                if activetrigger_option:
                    signal3 = np.tile( np.hstack(( np.zeros(1), 5.0*np.ones(int(points_per_exposure/2-1)),np.zeros(int(points_per_exposure/2)) )), FPS*time) #Ch2: Cam trigger active
                    self.msg += 'DAQ trigger output is ACTIVE\n'
                else:
                    signal3 = np.tile(np.zeros(points_per_exposure), FPS*time) # zeros / no cam trigger
                    self.msg += 'DAQ trigger output DEACTIVATED\n'
                signal4 = V4*np.ones(self.daq_rate*time)
                signal4[-1] = 0 #end with a zero voltage to signal off
                del ramp
            else:
                ramp = np.linspace(V1_min, V1_max, num_imageplanes, endpoint=True)
                signal1 = np.empty([points_per_ramp*int(80/FPS)*num_imageplanes]) #start with an empty signal - must get polulated in next steps
                for iter in range (num_imageplanes):
                    upsignal = np.repeat(ramp[iter], points_up_ramp*int(80/FPS))
                    if iter == (num_imageplanes-1):
                        downsignal = np.linspace(ramp[iter], ramp[0], points_down_ramp*int(80/FPS), endpoint=True)                        
                    else:                        
                        downsignal = np.linspace(ramp[iter], ramp[iter+1], points_down_ramp*int(80/FPS), endpoint=True)
                    signal1[iter*points_per_ramp*int(80/FPS):(iter+1)*points_per_ramp*int(80/FPS)] = np.hstack((upsignal,downsignal))
                # signal1 = np.tile(np.repeat(ramp, points_per_ramp*int(80/FPS)), 1) #Ch0: G1 for light-sheet sweep
                upramp = np.linspace(V2_min,V2_max,points_up_ramp,endpoint=True)
                downramp = np.linspace(V2_max,V2_min,points_down_ramp,endpoint=True) 
                signal2 = np.tile( np.hstack(( upramp,downramp )) , num_imageplanes*int(80/FPS))  #Ch1: G2 for DSLM
                if activetrigger_option:
                    signal3 = np.tile( np.hstack(( np.zeros(1), 5.0*np.ones(int(points_per_exposure/2-1)),np.zeros(int(points_per_exposure/2)) )), num_imageplanes) #Ch2: Cam trigger
                    self.msg += 'DAQ trigger output is ACTIVE\n'
                else:
                    signal3 = np.tile(np.zeros(points_per_exposure), num_imageplanes)
                    self.msg += 'DAQ trigger output DEACTIVATED\n'
                signal4 = V4*np.ones(int(self.daq_rate/VPS))
                signal4[-1] = 0 #end with a zero voltage to signal off
                del ramp
            # plt.plot(signal1)
            # plt.show()
            signals = np.zeros(4*len(signal1)) # 4 times to accomodate all signals 1 to 4 together
            # merge 4 signals in alternate fashion: 1,2,3,4,  1,2,3,4, ... 
            signals[::4] = signal1
            signals[1::4] = signal2
            signals[2::4] = signal3
            signals[3::4] = signal4      
            del signal1, signal2, signal3, signal4

            # if older signal data exists, clean it
            try:
                if self.data_array:
                    self.daq_free_memory()
            except:
                self.msg += 'This must be the 1st run of DAQ device in the current session ... otherwise something went wrong with DAQ memory ...\n'

            self.msg += '*****************************************************************************************\n'
            self.msg += 'Calculating and populating a new DAQ signal to windows memory .... please be patient ....\n'
            self.msg += '*****************************************************************************************\n'
            self.num_points = len(signals)

            self.memhandle = ul.win_buf_alloc(self.num_points) #windows buffer allocation 
            self.data_array = ctypes.cast(self.memhandle, ctypes.POINTER(ctypes.c_ushort))
            if not self.memhandle:
                self.msg += "\U000026A0 Error: Failed to allocate memory for DAQ output.\n"
            #Calculate and store the waveform
            for i in range(0, self.num_points):
                #We need bit value for voltage V. This is 32768 + V*3061.8 Or, 2^15*(1+V/Vmax) where Vmax = 10.7 volts
                self.data_array[i] = np.int(np.around(32768 + signals[i] * 3061.8)) 
            self.msg += 'Done with loading signals in the system memory ...... \n'
        else:
            self.msg += '\U000026A0 Error: incompatible FPS & VPS combination. Ensure FPS is an integer multiple of VPS.\n'

    def daq_push_signals(self,continuousscan_option):
        """
        A function to push AO signals through DAQ board.
        Make sure to run daq_load_signals prior to this function to ensure windows memory is loaded with useful signals to output

        continuousscan_option: bool
            it defines if the signal will keep looping or execute once
            True: keep looping
            False: execute once
        """
        # output new signals
        try:
            self.ul_range = ULRange.BIP10VOLTS #usually ignored
            self.msg += 'Pushed a new AO signal through DAQ board ...'
            if continuousscan_option:
                self.msg += 'looping continuously\n'
                ul.a_out_scan(self.board_num, self.low_chan, self.high_chan, self.num_points, self.daq_rate,
                    self.ul_range, self.memhandle, ScanOptions.CONTINUOUS | ScanOptions.BACKGROUND | ScanOptions.SIMULTANEOUS) #remove simultaneous option?
            else:
                self.msg += 'once\n'
                ul.a_out_scan(self.board_num, self.low_chan, self.high_chan, self.num_points, self.daq_rate,
                    self.ul_range, self.memhandle, ScanOptions.BACKGROUND | ScanOptions.SIMULTANEOUS) #remove simultaneous option?
        except ULError as e:                
            print("\U000026A0 A UL error occurred with MCC DAQ. Code: " + str(e.errorcode) + " Message: " + e.message) 
            self.msg += "\U000026A0 A UL error occurred with MCC DAQ. Code: " + str(e.errorcode) + " Message: " + e.message

    def daq_free_memory(self):
        """
        A function to free up the system meory so a new signal can get loaded. 
        It frees self.memhandle and self.data_array. Run it before any 2nd+ run of daq_load_signals function. 
        """
        try:
            ul.win_buf_free(self.memhandle)
            self.data_array = None
            self.msg += 'Freed up old system memory for DAQ device ....\n'
        except:
            self.msg += '\U000026A0 Could not free old system memory for DAQ device ...\n'


        
    def daq_wait(self):
        """
        A function to ensure that the DAQ runs till end of signal.
        Useful to make a thread wait for completion. 
        """        
        status = Status.RUNNING
        while status == Status.RUNNING:               
            sleep(0.05)
            status, _, _ = ul.get_status(self.board_num, FunctionType.AOFUNCTION) 
    
    def daq_terminate_signal(self):
        """
        A function to terminate looping signal in DAQ board.
        """        
        self.status, _, _ = ul.get_status(self.board_num, FunctionType.AOFUNCTION)
        if self.status == Status.RUNNING:
            try:
                ul.stop_background(self.board_num,FunctionType.AOFUNCTION)
                ul.a_out(self.board_num,channel=0,ul_range=ULRange.BIP10VOLTS, data_value=np.int(32768)) #set channel to zero
                ul.a_out(self.board_num,channel=1,ul_range=ULRange.BIP10VOLTS, data_value=np.int(32768)) #set channel to zero
                ul.a_out(self.board_num,channel=2,ul_range=ULRange.BIP10VOLTS, data_value=np.int(32768)) #set channel to zero
                ul.a_out(self.board_num,channel=3,ul_range=ULRange.BIP10VOLTS, data_value=np.int(32768)) #set channel to zero
                self.msg += 'Stopped old backgroung DAQ task\n'
            except:
                self.msg+= '\U000026A0 Error in stopping old background DAQ task\n'

    def daq_disconnect(self):
        """
        A function for DAQ de-initialization.
        """
        try:
            self.daq_free_memory()
            ul.release_daq_device(self.board_num)
            del self.dev_list
            self.msg += 'DAQ device de-initialized.\n'
        except:
            self.msg += '\U000026A0 Error in DAQ device de-initialization.\n'
