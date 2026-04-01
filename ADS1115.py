# ADC DECLARATIONS***************************************************
#declare ADC module read/write bit values
adcModuleRead = 1
adcModuleWrite = 0
#declare ADC module addresses
adcModuleOneAddress = 0x49
#declare ADC module register addresses
config_register_address = 0x1
conversion_register_address = 0x0
#declare ADC mux constants to point at each of the four channels
adcMuxSelectAN0 = 0x04
adcMuxSelectAN1 = 0x05
adcMuxSelectAN2 = 0x06
adcMuxSelectAN3 = 0x07
#declare ADC gain constants for confgi register
adcPlusMinus4Volts = 0x1
adcPlusMinus2Volts = 0x2
adcPlusMinus1Volts = 0x3
adcPlusMinus05Volts = 0x4
#declare ADC mode constant
adcSingleShotConversion = 0x1
adcContinuousConversion = 0x0
#declare ADC data rate constant
adcDataRate128sps = 0x4
adcDataRate16sps = 0x1
#declare ADC comparator config bits
adcComparatorOn = 0x8
adcComparatorOff = 0x3
#declare ADC comparator thresholds so ALERT/RDY pin functions only as conversion ready pin
adcHI_TRES = 0x8000
adcLO_TRES = 0x0000

def flip_msb_lsb(value):
    return ((value << 8) & 0xFF00) | ((value >> 8) & 0xFF)

def config_register_compose(mux_select, prog_gain, adc_mode, data_rate, comparator_config):
        config_register = (0x1 << 15) | (mux_select << 12) | (prog_gain << 9) | (adc_mode << 8) | (data_rate << 5) | (comparator_config)
        return config_register