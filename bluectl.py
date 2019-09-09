#!/usr/bin/env python
# coding: utf-8

import argparse
import os, sys
import subprocess
import time
import re


class SubcommandHelpFormatter(argparse.RawDescriptionHelpFormatter):

    def _format_action(self, action):
        """Remove metavars at help screen"""
        parts = super(argparse.RawDescriptionHelpFormatter, self)._format_action(action)
        if action.nargs == argparse.PARSER:
            parts = "\n".join(parts.split("\n")[1:])
        return parts
    
    def add_usage(self, usage, actions, groups, prefix=''):
        """Remove usage prefix at usage help section"""
        #if prefix is None:
        #    prefix = ''
        return super(SubcommandHelpFormatter, self).add_usage(usage, actions, groups, prefix='')


class Return(Exception):
    pass


def checkRoot():
    """Check if script was run as root"""
    
    if not os.geteuid() == 0:
        sys.exit("You must be root to run this command, please use sudo and try again.")


def changeBluetoothService(enable=True):
    """Check/Change status of bluetooth service"""
    
    #blueServiceStatus = os.popen('systemctl status bluetooth.service').read()
    ServStatStdout = execCommand('systemctl status bluetooth.service')
    
    if enable:
        if not 'active (running)' in ServStatStdout:
            checkRoot()
            #blueServiceStatus = os.popen('sudo systemctl start bluetooth.service').read()
            blueServStartStdout = execCommand('sudo systemctl start bluetooth.service')
        return
    
    if not enable:
        if not 'inactive (dead)' in ServStatStdout:
            checkRoot()
            #blueServiceStatus = os.popen('sudo systemctl stop bluetooth.service').read()
            blueServStopStdout = execCommand('sudo systemctl stop bluetooth.service')
        return


def getControllers():
    """Get list of available bluetooth controllers"""
    
    # Check enabled bluetooth service
    changeBluetoothService(enable=True)
    
    #proc = os.popen('bluetoothctl list').read()
    blueListStdout = execCommand('bluetoothctl list')
    
    # Get controller's MAC and name to list
    cntList = list()
    for line in blueListStdout.splitlines():
        lst = line.split()
        del lst[0]
        del lst[-1]
        
        if lst:
            cntList.append(lst)
    
    return cntList


def checkMACAddress(MACAddress):
    """Check correct format of given MAC address"""
    
    MACPattern = re.compile('^[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}:[a-fA-F0-9]{2}$')
    MACMatch = MACPattern.match(MACAddress)
    
    return MACPattern.match(MACAddress)


def getDevices():
    """Scan for available bluetooth devices and returns list with names and MACs"""
    
    scannedDevices = list()
    
    proc = subprocess.Popen('bluetoothctl scan on', shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=8192, universal_newlines=True)
    
    time.sleep(10)
    
    proc.stdin.write('scan off')
    
    try:
        stdout, stderr = proc.communicate()
    except subprocess.TimeoutExpired:
        proc.kill()
        stdout, stderr = proc.communicate()

    ansiEscapePattern = re.compile(r'\x1B[@-_][0-?]*[ -/]*[@-~]')
    stdout = ansiEscapePattern.sub('', stdout)
    
    #deviceNamePattern = re.compile('^\[NEW\] Device [A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2}:[A-F0-9]{2} ')
    
    for line in stdout.split('\n'):
        if '[NEW] Device' in line:
            device = list()
            device.append(line[13:31])
            device.append(line[31:])
            scannedDevices.append(device)
    
    return scannedDevices


def execCommand(command: str):
    """Executes given shell command and returns str output"""
    
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    return stdout.decode("utf-8")


def selectOption(title: str, data: list, datapos: int):
    """Implements user input in form of selecting an option from datalist"""

    print(title)

    if not data:
        selItemNo = input('No devices found (r=retry, q=quit): ')
        if selItemNo == 'r':
            return -1
        if selItemNo == 'q':
            return -2
        while not selItemNo in ('r', 'q'):
            selItemNo = input('Wrong option\nNo devices found (r=retry, q=quit): ')
            if selItemNo == 'r':
                return -1
            if selItemNo == 'q':
                return -2
    
    else:
        for i, item in enumerate(data, start=1):
            datastring = str()
            for pos in datapos:
                datastring += item[pos]
                datastring += ' '
            print(str(i) + '. ' + datastring)
        selItemNo = input('Select your choice (r=retry, q=quit): ')
        if selItemNo == 'r':
            return -1
        if selItemNo == 'q':
            return -2

        while (not selItemNo.isdigit()) or (int(selItemNo) < 1) or (int(selItemNo) > len(data)):
            selItemNo = input('Wrong option\nSelect your choice (r=retry, q=quit): ')
            if selItemNo == 'r':
                return -1
            if selItemNo == 'q':
                return -2
    
    return int(selItemNo) - 1


def confirmOption(method, title: str, datapos: int, message=None):
    """Executes given method to get datalist, calls selectOptions on the datalist and
       implements retry/quit options on the chosen result"""
    
    if message:
        print('\n'+message+'\n')
    data = method()
    
    itemNo = selectOption(title, data, datapos)
    
    if itemNo == -2:
        raise Return
        return
    
    while itemNo == -1:
        if message:
            print('\n'+message+'\n')
        data = method()
        itemNo = selectOption(title, data, datapos)
        if itemNo == -2:
            raise Return
            return
    
    return data[itemNo][0]


def getPairConDevices():
    """Returns lists of connected and paired devices"""
    
    # Enable bluetooth service if not enabled
    changeBluetoothService(enable=True)
    
    # List available bluetooth devices
    blueDevices = execCommand('bluetoothctl devices')
    
    # parse available devices to list
    availDevices = list()
    for device in blueDevices.split('\n'):
        if 'Device' in device:
            deviceList = list()
            deviceList.append(device[25:])
            deviceList.append(device[7:24])
            availDevices.append(deviceList)
    
    # check paired and connected devices
    pairedDevices = list()
    connectedDevices = list()
    for device in availDevices:
        deviceInfo = execCommand('bluetoothctl info {}'.format(device[1]))
        if 'Paired: yes' in deviceInfo:
            pairedDevices.append(device)
        if 'Connected: yes' in deviceInfo:
            connectedDevices.append(device)
    
    return pairedDevices, connectedDevices


def createProfile():
    """Create new bluetooth profile"""
    
    checkRoot()
    
    print('Creating new bluetooth profile\n')
    
    # Enable bluetooth service if not enabled
    changeBluetoothService(enable=True)
    
    # Choose bluetooth controller
    try:
        cntMAC = confirmOption(getControllers, '***Available bluetooth controllers***', (1,))
    except Return:
        return
    
    # Select bluetooth controller
    blueSelectStdout = execCommand('bluetoothctl select {}'.format(cntMAC))
    
    # Power on bluetooth controller, choose pairing agent
    bluePoweronStdout = execCommand('bluetoothctl power on')
    blueAgentonStdout = execCommand('bluetoothctl agent on')
    blueDefagentStdout = execCommand('bluetoothctl default-agent')
    
    
    # Scan for bluetooth devices and choose one 
    try:
        deviceMAC = confirmOption(getDevices, '***Available bluetooth devices***', (1,0), message='Scanning for bluetooth devices...')
    except Return:
        return
    
    # Pair device
    # TO DO: Implement pairing with pin/confirmation
    print('\nPairing...\n')
    pairStdout = execCommand('bluetoothctl pair {}'.format(deviceMAC))
    while not 'Pairing successful' in pairStdout:
        print(pairStdout[:-1])
        pairNextOpt = input('\33[97m(press r for retry or q to quit): ')
        
        while pairNextOpt not in ('r', 'q'):
            pairNextOpt = input('\33[97m(press r for retry or q to quit): ')
    
        if pairNextOpt == 'q':
            return
        
        elif pairNextOpt == 'r':
            print('\nPairing...\n')
            pairStdout = execCommand('bluetoothctl pair {}'.format(deviceMAC))
        
    print('Pairing successful')
    
    # Create new profile file
    print('\n***Create name of new profile***')
    profileName = input('Profile name: ')
    
    with open('/etc/bluectl/'+profileName, 'wt') as profileFile:
        os.chmod('/etc/bluectl/'+profileName, 0o600)
        profileFile.write('Controller={}\n'.format(cntMAC))
        profileFile.write('Device={}\n'.format(deviceMAC))
        profileFile.write('Name={}\n'.format(profileName))
    
    print('\nProfile was successfully created\n')
    
    return


def startProfile(profileName):
    """Connect to existing bluetooth profile"""
    
    checkRoot()

    # Enable bluetooth service if not enabled
    changeBluetoothService(enable=True)
    
    # Check if profile file exists
    if not os.path.isfile('/etc/bluectl/'+profileName):
        print('Profile with given name does not exist.')
        return

    # Load profile
    with open('/etc/bluectl/'+profileName, 'rt') as profileFile:
        for line in profileFile.readlines():
            if 'Controller=' in line:
                cntMAC = line.replace('Controller=', '').replace('\n', '')
            if 'Device=' in line:
                deviceMAC = line.replace('Device=', '').replace('\n', '')
        
        if not (checkMACAddress(cntMAC) or checkMACAddress(deviceMAC)):
            print('Profile file is corrupted. Please remove and create this profile again.')
            return
    
    print('\nStarting bluetooth profile\n')
    
    # Choose bluetooth controller
    blueSelectStdout = execCommand('bluetoothctl select {}'.format(cntMAC))
    
    # Power on bluetooth controller
    bluePoweronStdout = execCommand('bluetoothctl power on')
    
    # Connect bluetooth device
    blueConnectStdout = execCommand('bluetoothctl connect {}'.format(deviceMAC))
    
    if not 'Connection successful' in blueConnectStdout:
        print(blueConnectStdout)
        print('Is device powered on in the vicinity?\n')
        return
    
    print('Profile was successfully started\n')
    
    return


def stopProfile(profileName):
    """Disconnect bluetooth profile"""
    
    checkRoot()

    # Enable bluetooth service if not enabled
    changeBluetoothService(enable=True)
    
    # Check if profile file exists
    if not os.path.isfile('/etc/bluectl/'+profileName):
        print('Profile with given name does not exist.')
        return

    # Load profile
    with open('/etc/bluectl/'+profileName, 'rt') as profileFile:
        for line in profileFile.readlines():
            if 'Controller=' in line:
                cntMAC = line.replace('Controller=', '').replace('\n', '')
            if 'Device=' in line:
                deviceMAC = line.replace('Device=', '').replace('\n', '')
        
        if not (checkMACAddress(cntMAC) or checkMACAddress(deviceMAC)):
            print('Profile file is corrupted. Please remove and create this profile again.')
            return
    
    print('\nStoping bluetooth profile\n')
    
    # Choose bluetooth controller
    blueSelectStdout = execCommand('bluetoothctl select {}'.format(cntMAC))
    
    # Power on bluetooth controller
    bluePoweronStdout = execCommand('bluetoothctl power on')
    
    # Disconnect bluetooth device
    blueDisconnectStdout = execCommand('bluetoothctl disconnect {}'.format(deviceMAC))
    
    if not 'Successful disconnected' in blueDisconnectStdout:
        print(blueDisconnectStdout)
        print('Is device connected?\n')
        return
    
    print('Profile was successfully stopped\n')
    
    return


def status():
    """Search and displays connected devices"""

    # Get paired and connected devices
    pairedDevices, connectedDevices = getPairConDevices()
    
    # Print connected devices
    if connectedDevices:
        connectedDevicesPrint = ''
        for device in connectedDevices:
            connectedDevicesPrint += device[0] + ' (' + device[1] + '), '
        connectedDevicesPrint = connectedDevicesPrint[:-2]
    else:
        connectedDevicesPrint = 'None'
    print('\nConnected devices:', connectedDevicesPrint, '\n')
    
    # Print paired devices
    if pairedDevices:
        pairedDevicesPrint = ''
        for device in pairedDevices:
            pairedDevicesPrint += device[0] + ' (' + device[1] + '), '
        pairedDevicesPrint = pairedDevicesPrint[:-2]
    else:
        pairedDevicesPrint = 'None'
    print('Paired devices:', pairedDevicesPrint, '\n')
    
    return


def stopAll():
    """Stop any profile connected"""
    
    # Get paired and connected devices
    pairedDevices, connectedDevices = getPairConDevices()
    
    print('\nStoping bluetooth profiles\n')
    
    if connectedDevices:
        
        # Power on bluetooth controller
        bluePoweronStdout = execCommand('bluetoothctl power on')
        
        for device in connectedDevices:

            # Disconnect bluetooth device
            blueDisconnectStdout = execCommand('bluetoothctl disconnect {}'.format(device[1]))

            if not 'Successful disconnected' in blueDisconnectStdout:
                print(blueDisconnectStdout)
                print('Is device connected?\n')
            else:
                print('Device {} was successfully stopped\n'.format(device[0]))
    
    return


def main():
     
    # create main parser
    parser = argparse.ArgumentParser(prog='bluectl', usage='bluectl', description='This utility allows managing profiles of bluetooth devices as well as connecting them to bluetooth adapter. Functionality is based on bluetoothctl tool.', formatter_class=SubcommandHelpFormatter)

    # create parser for subcommands
    subparser = parser.add_subparsers(dest='cmd', description='Subcommands are launched as \'bluectl cmd [arg]\'.\nFor information on using subcommands, see \'bluectl cmd -h\'')

    # create subcommand
    parser_create = subparser.add_parser('create', usage='bluectl create', description='Creates new bluetooth profile.\nAttempts to pair chosen controller with given bluetooth device.\nIf successful, profile details are stored in /etc/bluectl/[profilename] file', help='Create new profile', formatter_class=SubcommandHelpFormatter)

    # status subscommand
    parser_status = subparser.add_parser('status', usage='bluectl status', help='Show connected and paired devices', description='Show connected and paired devices', formatter_class=SubcommandHelpFormatter)

    # start subcommand
    parser_start = subparser.add_parser('start', usage='bluectl start [profile]', description='Connect selected profile', help='Connect selected profile', formatter_class=SubcommandHelpFormatter)
    parser_start.add_argument('profile', type=str, nargs=1, help='name of registered device')

    # stop subcommand
    parser_stop = subparser.add_parser('stop', usage='bluectl stop [profile]', description='Disconnect selected profile', help='Disconnect selected profile', formatter_class=SubcommandHelpFormatter)
    parser_stop.add_argument('profile', type=str, nargs=1, help='name of registered device')
    
    # stop_all subcommand
    parser_stopall = subparser.add_parser('stop-all', usage='bluectl stop-all', help='Disconnect any profile', description='Disconnect any profile', formatter_class=SubcommandHelpFormatter)

    # print help in case no argument
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    arguments = parser.parse_args()

    if arguments.cmd == 'create':
        createProfile()
    elif arguments.cmd == 'start':
        startProfile(arguments.profile[0])
    elif arguments.cmd == 'stop':
        stopProfile(arguments.profile[0])
    elif arguments.cmd == 'stop-all':
        stopAll()
    elif arguments.cmd == 'status':
        status()
    
    #print(arguments)


if __name__ == "__main__":
    
    main()

