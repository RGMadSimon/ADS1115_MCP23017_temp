# I2C READING THREAD
#i2cdetect -y 1      command to detect i2c devices
import sys
import board
import busio
import time
import math
import struct
import os
import ctypes
#from I2C_lib import*
from ADC_lib import*
from CMPSS_lib import*
from IGS_lib import*

class I2CClass():

    def __init__(self, i2c):
        self.i2c = i2c
        self.ADCOneAN0 = 0
        self.CMPSSHeading = 0
        self.accXaxis = 0


    def getI2Cconnection():
        i2c = busio.I2C(board.SCL, board.SDA)
        return i2c


    def  detectI2cDevice(self, addr):
        for i2cDevice in self.i2c.scan():
            if i2cDevice == addr:
                #print("i2C module: " + hex(addr) + " found")
                return True
        return False
    

    def  detectI2cDevices(self):
        adcModuleOneFound = False
        cmpssModuleOneFound = False
        igsModuleOneFound = False
        for i2cDevice in self.i2c.scan():
            if i2cDevice == 0x49:
                print("ADC module One found")
                adcModuleOneFound = True
            if i2cDevice == 0x0d:
                print("compass module found")
                cmpssModuleOneFound = True
            if i2cDevice == 0x68:
                print("igs module found")
                igsModuleOneFound = True
        # ALERT USER ABOUT MODULES NOT FOUND
        if not adcModuleOneFound:
            print("Could not find ADC module One (0x49)")
        if not cmpssModuleOneFound:
            print("Could not find compass module (0x0d)")
        if not igsModuleOneFound:
            print("Could not find IGS module (0x68)")


    def initADC(self):
        global adcMuxSelect
        global adcProgGain
        global adcMode
        global adcDataRate
        global adcComparatorConfig
        #ADC config register setup for first conversion
        adcMuxSelect = adcMuxSelectAN0
        adcProgGain = adcPlusMinus4Volts
        adcMode = adcSingleShotConversion
        adcDataRate = adcDataRate128sps
        adcComparatorConfig = adcComparatorOn


    def initCMPSS(self):
        global cmpssMode
        global cmpssODR
        global cmpssRNG
        global cmpssOSR
        #Compass control register setup
        cmpssMode = cmpssModeContinuous
        cmpssODR = cmpssOutputDataRate10Hz
        cmpssRNG = cmpssFieldRange2G
        cmpssOSR = cmpssOSR512

    def initIGS(self):
        global igsPWR_MGMT_1
        #IGS power management register setup
        igsPWR_MGMT_1 = 0x00 #sleep -> off
        if self.detectI2cDevice(igsModuleAddress):
            time.sleep(0.1)
            #reset IGS module
            self.i2c.writeto(igsModuleAddress, bytearray([igsPWR_MGMT_1_Address, 0x80]))
            time.sleep(0.1)
            #turn off sleep mode
            self.i2c.writeto(igsModuleAddress, bytearray([igsPWR_MGMT_1_Address, igsPWR_MGMT_1]))
            time.sleep(0.1)



    def readAllDevices(self):
        # GET DATA FROM ADC MODULE ONE (0x49)
        #if adcModuleOneFound:
        if self.detectI2cDevice(0x49):
            #WRITE TO CONFIG REGISTER ***********************
            #compose ADC register address byte
            adcRegisterAddress = adcConfigRegisterAddress

            #compose ADC CONFIG register
            adcConfigRegister = (0x1 << 15) | (adcMuxSelect << 12) | (adcProgGain << 9) | (adcMode << 8) | (adcDataRate << 5) | (adcComparatorConfig)
            adcConfigRegisterMSB = adcConfigRegister >> 8
            adcConfigRegisterLSB = adcConfigRegister & 0xff

            
            self.i2c.writeto(adcModuleOneAddress, bytearray([adcRegisterAddress, adcConfigRegisterMSB, adcConfigRegisterLSB]))


            time.sleep(0.1)


            #WRITE TO ADDRESS REGISTER ***********************
            #compose ADC register address byte
            adcRegisterAddress = adcConversionRegisterAddress

            self.i2c.writeto(adcModuleOneAddress, bytearray([adcRegisterAddress]))

            #time.sleep(0.1)


            #READ FROM CONVERSION REGISTER  ******************
            result = bytearray(2)
            self.i2c.readfrom_into(adcModuleOneAddress, result)

            convResult = result[1] | result[0]<< 8
            self.ADCOneAN0 = convResult * 0.000125
            #print(self.ADCOneAN0)
            #time.sleep(0.1)

        # GET DATA FROM COMPASS
        if self.detectI2cDevice(0x0d):
            cmpssControlRegister = (cmpssOSR << 6) | (cmpssRNG << 4) | (cmpssODR << 2) | (cmpssMode)
            #if not cmpssConfigDone:
            #time.sleep(0.1)

            # write control register
            self.i2c.writeto(cmpssModuleAddress, bytearray([cmpssControlRegisterAddress, cmpssControlRegister]))
            # write set/reset period register
            #i2c.writeto(cmpssModuleAddress, bytearray([cmpssSetResetPeriodAddress, 0x1]))

            #cmpssConfigDone = True
            #time.sleep(0.1)
            self.i2c.writeto(cmpssModuleAddress, bytearray([cmpssOutXaxisLSBAddress]))
            time.sleep(0.1)
            result = bytearray(6)
            self.i2c.readfrom_into(cmpssModuleAddress, result)
            bytesResult1 = (result[1] << 8) | (result[0])
            bytesResult2 = (result[3] << 8) | (result[2])
            bytesResult3 = (result[5] << 8) | (result[4])
            
            #2's complement
            if (bytesResult1 & (1 << (16 - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
                bytesResult1 = bytesResult1 - (1 << 16)        # compute negative value
            if (bytesResult2 & (1 << (16 - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
                bytesResult2 = bytesResult2 - (1 << 16)        # compute negative value
            if (bytesResult3 & (1 << (16 - 1))) != 0: # if sign bit is set e.g., 8bit: 128-255
                bytesResult3 = bytesResult3 - (1 << 16)        # compute negative value


            bytesResult1 = bytesResult1 - 1050
            #bytesResult2 = bytesResult2 - 0

            xAxis = bytesResult1
            yAxis = bytesResult2
            hypothenuse = math.sqrt(xAxis*xAxis + yAxis*yAxis)
            sinOfAngle = yAxis / hypothenuse
            cosOfAngle = xAxis / hypothenuse     

            a_acos = math.acos(cosOfAngle)
            if sinOfAngle < 0:
                angle = math.degrees(-a_acos) % 360
            else: 
                angle = math.degrees(a_acos)
            self.CMPSSHeading = angle
            #print(f'{intResult1:x}')
            #print(bytesResult1)
            #print("  axis1:" + str(bytesResult1) + "  axis2:" + str(bytesResult2) + "  axis3:" + str(bytesResult3) + "      HEADING:" + str(angle))
            #print("      HEADING:" + str(angle))
        
        if self.detectI2cDevice(igsModuleAddress):
            #select accelerator X axis MSB
            self.i2c.writeto(igsModuleAddress, bytearray([0x3B]))
            time.sleep(0.1)
            result = bytearray(2)
            #read accelerator X axis MSB
            self.i2c.readfrom_into(igsModuleAddress, result)
            self.accXaxis = int.from_bytes(result, byteorder='big', signed=True) - (pow(2, 15))
            time.sleep(0.1)
            
            self.i2c.writeto(igsModuleAddress, bytearray([igsPWR_MGMT_1_Address, 0x00]))
            #print("IGS PRESENT")