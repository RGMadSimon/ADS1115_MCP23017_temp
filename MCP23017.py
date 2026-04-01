
# One register (IOCON) is shared between the two ports
# Keep IOCON.BANK = 0
MCP23017_IODIRA_ADDR = 0X0 # all inputs by default (1)
MCP23017_IPOLA_ADDR = 0x2 # polarity by default is 0 -not inverted
MCP23017_INTENA_ADDR = 0X4 # interrupt enable
MCP23017_GPIOA_ADDR = 0X12 # gpio

MCP23017_IOCON_ADDR = 0Xa # config register - common to both ports


