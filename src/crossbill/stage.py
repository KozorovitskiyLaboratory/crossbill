""" 
Control functions for MCL translation stage.
Author: Manish Kumar, Northwestern University
Started: October, 2020
Last modified: December, 2020

This module file consists of a MCLMicroDrive class. Import this module and make use of this class to interact with the translation stage. 
More classes can be added to support more tanslation stages.
"""

class MCL_MicroDrive():
    """
    A class to initialize Mad City Labs translation stage. This has been tested with 2-axis (YX) encoder-less MMP series translation stage
    The class can be easily modified for 3-axis stages. 

    Step size: 95 nm, Range: ~25 mm 

    List of functions:
    - stage_connect  
    - stage_disconnect  
    - stage_getcurrentposition    
    - _stage_center
    - stage_moveY
    - stage_moveX
    - stage_halt
    - stage_wait    

    List of variables:
    - stage_YXposition 
    """

    def __init__(self):
        """ 
        Default function to initialize variables to be used in the PiUsb class.
        """       
        self.msg = ""    
        try:            
            self.MCLMicroDriveDll = ctypes.WinDLL(os.path.join(os.path.dirname(__file__),"dependencies/x86/","MicroDrive.dll"))
            self.msg += "Identified 32-bit MadCityLabs (MCL) DLL ...\n"
        except:
            try:
                self.MCLMicroDriveDll = ctypes.WinDLL(os.path.join(os.path.dirname(__file__),"dependencies/x64/","MicroDrive.dll"))
                self.msg += "Identified 64-bit MadCityLabs (MCL) DLL ...\n"
            except:
                self.msg += "\U000026A0 Could not identify any MCL DLL files. Ensure that DLL files exist in the expected paths ...\n"

        #python variables
        self.stage_YXposition = [0.0,0.0] #list of two floats. index 0: Axis-1/Y & index 1: Axis-2/X
        self.MicroStepSize = 0.0 #microstep size in µm 
        self.Xoffset = 0
        self.Yoffset = 0

        # Error dictionary
        self.errorDictionary = {0: 'MCL_SUCCESS',
                                -1: 'MCL_GENERAL_ERROR',
                                -2: 'MCL_DEV_ERROR',
                                -3: 'MCL_DEV_NOT_ATTACHED',
                                -4: 'MCL_USAGE_ERROR',
                                -5: 'MCL_DEV_NOT_READY',
                                -6: 'MCL_ARGUMENT_ERROR',
                                -7: 'MCL_INVALID_AXIS',
                                -8: 'MCL_INVALID_HANDLE'}        
         

    def stage_connect(self):        
        try:
            self.stage_handle = self.MCLMicroDriveDll.MCL_InitHandle()
            if self.stage_handle > 0:
                self.msg += 'Connected to MCL stage with Serial#: '+ str(self.MCLMicroDriveDll.MCL_GetSerialNumber(self.stage_handle)) +'\n'
                self.msg += 'This stage has been assigned handle: ' + str(self.stage_handle) +'\n'
                FirmwareVersion = ctypes.pointer(ctypes.c_short())
                profile = ctypes.pointer(ctypes.c_short())
                errorNum = self.MCLMicroDriveDll.MCL_GetFirmwareVersion(FirmwareVersion, profile, self.stage_handle)                
                # self.msg += 'MCL product firmware details. Version number: ' + str(FirmwareVersion.contents.value) + ' and profile number: ' + str(profile.contents.value) +'\n'              
                if errorNum != 0:
                    self.msg += '\U000026A0 Error while fetching MCL device info: ' + self.errorDictionary[errorNum] +'\n'
                del errorNum, profile, FirmwareVersion

                DLLversion = ctypes.pointer(ctypes.c_short())
                DLLrevision = ctypes.pointer(ctypes.c_short())
                self.MCLMicroDriveDll.MCL_DLLVersion(DLLrevision,DLLrevision)
                # self.msg += 'MCL DLL details. Version: ' + str(DLLversion.contents.value) + ' and revision: ' + str(DLLrevision.contents.value) +'\n'
                del DLLrevision,DLLversion

                FullStepSize = ctypes.pointer(ctypes.c_double()) #mm
                errorNum = self.MCLMicroDriveDll.MCL_GetFullStepSize(FullStepSize, self.stage_handle)                
                if errorNum != 0:
                    self.msg += '\U000026A0 Error while fetching MCL FullStepSize info: ' + self.errorDictionary[errorNum] +'\n'
                del errorNum   
                
                
                encoderRes = ctypes.pointer(ctypes.c_double()) #µm
                MicrostepSize = ctypes.pointer(ctypes.c_double()) #mm
                maxVelocity = ctypes.pointer(ctypes.c_double()) #mm/s
                maxVel2axis = ctypes.pointer(ctypes.c_double()) #mm/s
                maxVel3axis = ctypes.pointer(ctypes.c_double()) #mm/s
                minVelocity = ctypes.pointer(ctypes.c_double()) #mm/s
                errorNum = self.MCLMicroDriveDll.MCL_MDInformation(encoderRes,MicrostepSize,maxVelocity,maxVel2axis,maxVel3axis,minVelocity,self.stage_handle)                
                if errorNum != 0:
                    self.msg += '\U000026A0 Error while fetching MCL MDInfo: ' + self.errorDictionary[errorNum] +'\n'
                else:
                    pass 
                    # self.msg += 'MCL stage motor properties: '
                    # self.msg += '\nencoderResolution = ' + str(encoderRes.contents.value) + ' µm'
                    self.msg += ' \nMicrostep size = ' + str(MicrostepSize.contents.value*1e3) + ' µm'
                    self.msg += ' \nFullstep size = %f µm' %(FullStepSize.contents.value*1e3)
                    # self.msg += ' \nmaxVelocity = ' + str(maxVelocity.contents.value) + ' mm/s'
                    # self.msg += ' \nmaxVel2axis = ' + str(maxVel2axis.contents.value) + ' mm/s'
                    # self.msg += ' \nmaxVel3axis = ' + str(maxVel3axis.contents.value) + ' mm/s'
                    # self.msg += ' \nminVelocity = ' + str(minVelocity.contents.value) + ' mm/s' +'\n'
                self.MicroStepSize = MicrostepSize.contents.value*1e3 #in µm
                self.FullStepSize = FullStepSize.contents.value*1e3 #in µm
                del errorNum, encoderRes, MicrostepSize, maxVelocity, minVelocity, maxVel2axis, maxVel3axis, FullStepSize                
            else:
                self.msg += '\U000026A0 MCL stage connection failed. Is the device detectable?' +'\n'
        except:
            self.msg += "\U000026A0 ERROR: Could not get MCL stage handle. Are MCL drivers installed?"   


    def stage_recenter(self):
        """
        Re-center sequence for the stage.
        """        
        self.stage_moveY(-30000,3.00) #force reverse limit on Y axis
        self.stage_wait()
        self.msg += '1/4: Hit reverse limit on y-axis ...'
        self.stage_moveX(-30000,3.00) #force reverse limit on X axis
        self.stage_wait()
        self.msg += '2/4: Hit reverse limit on x-axis ...'        
        self.stage_moveY(12700,4.0) #move by half inch (half range) to reach center    
        self.stage_wait()    
        self.msg += '3/4: Centered y-axis ...'
        self.stage_moveX(12700,4.0) #move by half inch (half range) to reach center    
        self.stage_wait()    
        self.msg += '4/4: Centered x-axis ...'
        self.stage_getcurrentposition()
        self.Yoffset = self.stage_YXposition[0] #subtract this offset from reported position to get actual position
        self.Xoffset = self.stage_YXposition[1]


    def stage_disconnect(self):
        '''
        Disconnect stage
        '''
        self.stage_halt()        
        self.MCLMicroDriveDll.MCL_ReleaseHandle(self.stage_handle)
        self.stage_handle = None
        self.msg += 'MCL stage disconnected ...\n'

        
    def stage_halt(self):
        '''
        Halt moving stage 
        '''        
        status = ctypes.pointer(ctypes.c_ushort()) #unsigned short pointer
        errorNum = self.MCLMicroDriveDll.MCL_MDStop(status, self.stage_handle)        
        if errorNum != 0:
            self.msg += '\U000026A0 Error while stopping stage: ' + self.errorDictionary[errorNum] 
        del status, errorNum


    def stage_wait(self):
        """
        Wait for the previous move to finish
        """
        errorNum = self.MCLMicroDriveDll.MCL_MicroDriveWait(self.stage_handle)
        if errorNum != 0:
            self.msg += '\U000026A0 Error while waiting for the stage move to finish: ' + self.errorDictionary[errorNum]
        del errorNum


    def stage_getcurrentposition(self):
        '''
        Position in µm since the beginning of the program.
        Position updates in self.stage_YXposition variable. 
        Warning! Call it only when stage has finished moving. 
        Call self.stage_wait() prior to this function.       
        '''        
        YmicroSteps = ctypes.pointer(ctypes.c_int())
        XmicroSteps = ctypes.pointer(ctypes.c_int())

        Yaxis = ctypes.c_uint(1) #Axis-1 is Y-axis in our SOPi microscope's lab co-ordinates
        Xaxis = ctypes.c_uint(2) 
        
        errorNum = self.MCLMicroDriveDll.MCL_MDCurrentPositionM(Xaxis, XmicroSteps, self.stage_handle)
        if errorNum != 0:
            self.msg += '\n\n\U000026A0 Error while locating X position: ' + self.errorDictionary[errorNum]
        errorNum = self.MCLMicroDriveDll.MCL_MDCurrentPositionM(Yaxis, YmicroSteps, self.stage_handle)
        if errorNum != 0:
            self.msg += '\n\n\U000026A0 Error while locating Y position: ' + self.errorDictionary[errorNum]
        
        self.stage_YXposition[0] = round(float(YmicroSteps.contents.value*self.MicroStepSize - self.Yoffset),5) #in µm
        self.stage_YXposition[1] = round(float(XmicroSteps.contents.value*self.MicroStepSize - self.Xoffset),5) #in µm
        del Xaxis, Yaxis, errorNum, XmicroSteps, YmicroSteps

    def stage_moveYX(self, y, x, velocity):
        """
        y, x: float (distance to move in µm)
            y: axis-1 (bottom stage) & x: axis-2 (top stage)
        velocity: float (in mm/s)
        """        
        #zero correction - smallest move length can not be less than 1 microstep
        if abs(x) < self.MicroStepSize:
            x = self.MicroStepSize
        if abs(y) < self.MicroStepSize:
            y = self.MicroStepSize
        x = float(x*1e-3) #convert into mm
        y = float(y*1e-3)
        try:
            errorNum = self.MCLMicroDriveDll.MCL_MDMoveThreeAxes(ctypes.c_uint(2),ctypes.c_double(velocity), ctypes.c_double(x),
                                                ctypes.c_uint(1),ctypes.c_double(velocity), ctypes.c_double(y),
                                                ctypes.c_uint(3),ctypes.c_double(velocity), ctypes.c_double(0), self.stage_handle)
            if errorNum != 0:
                self.msg += '\n\n\U000026A0 Error while moving: ' + self.errorDictionary[errorNum]
            del errorNum           
            self.stage_getcurrentposition() #update current position to self.stage_YXposition variable 
        except:
            self.msg += '\n\n\U000026A0 Error: Invalid entry for moving stage or connection lost!'

    def stage_moveY(self, y, velocity):
        """
        y: float (Unit: µm. Distance to move along y axis/Axis-1)            
        velocity: float (in mm/s)
        """        
        y = float(y*1e-3) #convert into mm
        try:
            errorNum = self.MCLMicroDriveDll.MCL_MDMove(ctypes.c_uint(1),ctypes.c_double(velocity), ctypes.c_double(y), self.stage_handle)
            if errorNum != 0:
                self.msg += '\n\n\U000026A0 Error while moving: ' + self.errorDictionary[errorNum]
            del errorNum 
        except:
            self.msg += '\n\n\U000026A0 Error in moving stage along Y-axis/axis-1 or connection lost!'

    def stage_moveX(self, x, velocity):
        """
        x: float (Unit: µm. Distance to move along x axis/Axis-2)
        velocity: float (in mm/s)
        """        
        x = float(x*1e-3) #convert into mm
        try:
            errorNum = self.MCLMicroDriveDll.MCL_MDMove(ctypes.c_uint(2),ctypes.c_double(velocity), ctypes.c_double(x), self.stage_handle)
            if errorNum != 0:
                self.msg += '\n\n\U000026A0 Error while moving: ' + self.errorDictionary[errorNum]
            del errorNum            
        except:
            self.msg += '\n\n\U000026A0 Error in moving stage along X-axis/axis-2 or connection lost!'

    def stage_singlestepY(self, direction):
        """
        direction: int 
            +1: move forward
            -1: move reverse       
        """        
        try:
            errorNum = self.MCLMicroDriveDll.MCL_MDSingleStep(ctypes.c_uint(1),ctypes.c_int(direction), self.stage_handle)
            if errorNum != 0:
                self.msg += '\n\n\U000026A0 Error while single stepping along Y: ' + self.errorDictionary[errorNum]
            del errorNum            
        except:
            self.msg += '\n\n\U000026A0 Error in single stepping stage along Y-axis/axis-1 or connection lost!'

    def stage_singlestepX(self, direction):
        """
        direction: int 
            +1: move forward
            -1: move reverse       
        """        
        try:
            errorNum = self.MCLMicroDriveDll.MCL_MDSingleStep(ctypes.c_uint(2),ctypes.c_int(direction), self.stage_handle)
            if errorNum != 0:
                self.msg += '\n\n\U000026A0 Error while single stepping along X: ' + self.errorDictionary[errorNum]
            del errorNum             
        except:
            self.msg += '\n\n\U000026A0 Error in single stepping stage along X-axis/axis-2 or connection lost!'
    

#if being used as a module, then import required libraries
if __name__ != "main":
    import ctypes, time, pathlib, os, emoji
