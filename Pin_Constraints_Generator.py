import os
import re
# Read in netlist
# Parse netlist for reference designators

NETLIST_FILE = "dialcnet.dat"
REFERNCE_DESIGNATOR = "U2"
OUTPUT_CSV_FILE = "FPGA_PINLIST.csv"
OUTPUT_XDC_FILE = "FPGA_PINLIST.xdc"
DCI_NETS_FILE = "NetsNeedingDCI.txt"
INPUT_PINOUT_FILE = "xcau7psbvc484pkg.txt"
IGNORED_BANKS = ("0", "NA")
BANK_VOLTAGES = {"65": "1.8", "66" : "1.8", "84": "3.3", "85": "3.3", "86": "3.3", "104": "3.3", "105": "3.3", "106": "3.3", "124": "1.8", "0": "1.8", "NA": "NA"}
IOSTANDARD_18 = "LVCMOS18"
IOSTANDARD_33 = "LVCMOS33"
DCI_CALIBRATION_PIN = "VRP"

# Delete previous output files
if os.path.isfile(OUTPUT_CSV_FILE) == True:
    os.remove(OUTPUT_CSV_FILE)
if os.path.isfile(OUTPUT_XDC_FILE) == True:
    os.remove(OUTPUT_XDC_FILE)

DCINets = []
NetsNeedingDCIFile = open(DCI_NETS_FILE, 'r')
for line in NetsNeedingDCIFile:
    DCINets.append(line.strip())

# Create a list of all nets connected to REFERENCE_DESIGNATOR
Connectivity = {}
NetlistFile = open(NETLIST_FILE, "r")
FirstLine = True
for line in NetlistFile:
    if FirstLine == True:
        FirstLine = False
        continue
    if line.strip() == "END CONCISE NET LIST":
        continue
    Net = line.split()[0]
    Reference_Designator = line.split()[1]
    Pin = line.split()[2]
    if REFERNCE_DESIGNATOR == Reference_Designator:
        Connectivity[Pin] = Net

# Create a list of all pins that should get constraints
PinlistFile = open(INPUT_PINOUT_FILE, "r")
PinSpecifics = {}
PinCount = 0
ExpectedPinCount = 0
for line in PinlistFile:
    if line[0:2] == "--":
        continue
    if len(line.split()) == 5 and line.split()[0] == "Total" and line.split()[1] == "Number" and line.split()[2] == "of" and line.split()[3] == "Pins":
        ExpectedPinCount = line.split()[4]
        continue
    if len(line.split()) != 6:
        continue
    PinCount = PinCount + 1
    Pin = line.split()[0]
    PinName = line.split()[1]
    Bank = line.split()[3]
    Type = line.split()[4]
    PinSpecifics[Pin] = {'PinName' : PinName, 'Bank' : Bank,'Type' : Type, 'BankVoltage' : BANK_VOLTAGES[Bank]}

if int(ExpectedPinCount) != PinCount:
    print("Pin counts don't match")
    exit()

# Create output files
OutputCSVFile = open(OUTPUT_CSV_FILE, "w")
OutputCSVFile.write("Pin,Net Name,IO Voltage\n")
for pin in Connectivity:
    if PinSpecifics[pin]['Bank'] in IGNORED_BANKS:
        continue
    if Connectivity[pin][0] == '+':
        OutputCSVFile.write(pin + ",'" + Connectivity[pin] + "," + PinSpecifics[pin]['BankVoltage'] + "\n")
    else:
        OutputCSVFile.write(pin + "," + Connectivity[pin] + "," + PinSpecifics[pin]['BankVoltage'] + "\n")
OutputCSVFile.close()

# Create output files
OutputXDCFile = open(OUTPUT_XDC_FILE, "w")
for pin in Connectivity:
    if PinSpecifics[pin]['Bank'] in IGNORED_BANKS:
        continue
    if PinSpecifics[pin]['Type'] == "NA":
        continue
    if PinSpecifics[pin]['Type'] == "CONFIG":
        continue
    if PinSpecifics[pin]['Type'] == "GTH" and Connectivity[pin] == "GND":
        print ("Ignoring : " + PinSpecifics[pin]['Type'] + " : " + Connectivity[pin])
        continue
    if re.search(DCI_CALIBRATION_PIN, PinSpecifics[pin]['PinName']) != None:
        print ("Ignoring : " + PinSpecifics[pin]['Type'] + " : " + Connectivity[pin])
    if re.search("VREF", PinSpecifics[pin]['PinName']):
        print ("Ignoring : " + PinSpecifics[pin]['Type'] + " : " + Connectivity[pin])
    iostandard = "Unknown"
    if (PinSpecifics[pin]['BankVoltage'] == "3.3"):
        iostandard = IOSTANDARD_33
    if (PinSpecifics[pin]['BankVoltage'] == "1.8"):
        iostandard = IOSTANDARD_18
    if Connectivity[pin] in DCINets:
        iostandard = "LVDCI_18"   
    OutputXDCFile.write("set_property -dict { PACKAGE_PIN " + pin + " IOSTANDARD " + iostandard + " } ")
    OutputXDCFile.write("[get_ports { " + Connectivity[pin] + " }]\n")
OutputXDCFile.close()

NetlistFile.close()