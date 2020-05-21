
import requests, json, pynetbox, re, netmiko, ncclient, argparse, getpass, sys
import time, xmltodict, os
from netmiko import ConnectHandler
from ncclient import manager
from ncclient.xml_ import *
from xml.etree import ElementTree

def get_arguments():
    parser = argparse.ArgumentParser(description='Command Line Driven Utility To Enable NETCONF\
        And MD-CLI on SROS Devices.')
    parser.add_argument("-n", "--node", help="Target NODE IP", required=False)
    parser.add_argument("-u", "--user", help="SSH Username",
                        required=False, default='admin')
    parser.add_argument("-p", "--port", help="NETCONF TCP Port",
                        required=False, default='830')
    args = parser.parse_args()
    return args

def get_ips_netbox(netboxserver,token,tag):
    ''' API call to Netbox and return a list of IP's filtered by a TAG.
    '''
    # Use the pynetbox API Client, to establish a connection.
    nb = pynetbox.api(url=netboxserver, token=token)

    # Extract a list of IP's addresses by the filtered TAG, '7750'.
    return nb.ipam.ip_addresses.filter(tag=[tag])

def send_cmmdz(node_conn, list_of_cmds):
    ''' This function will unpack the dictionary created for the remote host to establish a connection with
        and send a LIST of commands. The output will be printed to the screen.
        Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.
    '''
    try:
        x = node_conn.send_config_set(list_of_cmds)
        print(x)
    except Exception as e:
        print(f"Issue with list of cmdz, {e}")

def send_single(node_conn, command):
    ''' This function will unpack the dictionary created for the remote host to establish a connection with
        and send a single command. The output will be printed to the screen.
        Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.[]
    '''
    try:
        x = node_conn.send_command(command)
        print(x)
    except Exception as e:
        sys.exit(e)

def disconnect(node_conn):
    ''' This function will disconnect the open SSH Session.
    '''
    try:
        node_conn.disconnect()
    except Exception as e:
        print(e)

def netconfconn(args, ncusername, ncpassword):
    conn = manager.connect(host=args.node,
                           port=args.port,
                           username=ncusername,
                           password=ncpassword,
                           hostkey_verify=False,
                           device_params={'name': 'alu'})
    return conn

def saveFile(filename, contents):
    ''' Save the contents to a file in the PWD.
    '''
    try:
        f = open(filename, 'w+')
        f.write(contents)
        f.close()
    except Exception as e:
        print(e)

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print('Error: Creating directory. ' + directory)
        
def get_ip_only(ipadd):
    ''' This function will use REGEX to strip the subnet mask from an IP/MASK addy.
    '''
    try:
        ip = re.sub(r'/.+', '', str(ipadd))
        return ip
    except Exception as e:
        print(f"Issue striping subnetmask from {ipadd}, {e}")
        
def netconfconn(ip,ncusername,ncpassword):
    ''' This function establishes a NETCONF Connection.
    '''
    conn = manager.connect(host=ip,
        port='830',
        username=ncusername,
        password=ncpassword,
        hostkey_verify=False,
        device_params={'name':'alu'})
    return conn

def router_dict(args,ip,sshpass):
    '''Create a dictionary for our devices.
    '''
    router = {
        'device_type': 'alcatel_sros',
        'host': ip,
        'username': args.user,
        'password': sshpass,
    }
    return router


def netcbackup(ip, NETCONF_USER, NETCONF_PASS):
    ''' This function will establish a netconf connection and pull the running config. It will write a temp file,
    read it and convert the XML to a python dictionary. Once parsed, we'll pull the system name of the device
    and create a folder structure by hostname and backup the running config.
    '''
    try:
        # Now let's connect to the device via NETCONF and pull the config to validate
        nc = netconfconn(ip, NETCONF_USER, NETCONF_PASS)
        # Grab the running configuration on our device, as an NCElement.
        config = nc.get_config(source='running')
        # XML elemnent as a str.
        xmlconfig = to_xml(config.xpath('data')[0])
        # Write the running configuration to a temp-file (from the data/configure xpath).
        saveFile('temp-config.xml', xmlconfig)
        # Lets open the XML file, read it, and convert to a python dictionary and extract some info.
        with open('temp-config.xml', 'r') as temp:
            content = temp.read()
            xml = xmltodict.parse(content)
            sys_name = xml['data']['configure']['system']['name']
            createFolder(f"Configs/{sys_name}")
            saveFile(
                f"Configs/{sys_name}/{sys_name}.txt", xmlconfig)
    except Exception as e:
        print(f"{e}")
        
def main():
    
    args = get_arguments()
    
    # Establish some vars:
    TOKEN = '25dadb1b334048bddd9bc679cd4baf2a59d7a9f5'
    SR7750 = get_ips_netbox('http://192.168.0.34',TOKEN,'7750')

    # Define the NETCONF USERNAME / PASSWORD:
    NETCONF_USER = 'netconf'
    NETCONF_PASS = 'NCadmin123'
    
    # SSH PASSWORDS
    SSH_PASS = getpass.getpass()
    
    for x in SR7750:
        ip = get_ip_only(x)
        if '10' in ip:
            print(f'skipping {ip} - We do not want to edit nodes in this subnet.')
        elif '192' in ip:
            sros_conn = net_connect = ConnectHandler(**router_dict(args,ip,SSH_PASS))
            # Establish a list of pre and post check commands.
            print('Connecting to device and executing script...')
            send_single(sros_conn, 'show system information | match Name')
            enabled = sros_conn.send_command('show system netconf | match State')
            if 'Enabled' in enabled:
                print(f"{ip} already has NETCONF enabled. Moving on..")
                disconnect(sros_conn)
                time.sleep(2)
                print('\n')
                try:
                    netcbackup(ip, NETCONF_USER, NETCONF_PASS)
                except Exception as e:
                    print(f"{e}")
                continue
            else:
                enableNetconf = ['system security profile "netconf" netconf base-op-authorization lock',
                                'system security profile "netconf" netconf base-op-authorization kill-session',
                                f'system security user {NETCONF_USER} access netconf',
                                f'system security user {NETCONF_USER} password {NETCONF_PASS}',
                                f'system security user {NETCONF_USER} console member {NETCONF_USER}',
                                f'system security user {NETCONF_USER} console member "administrative"',
                                'system management-interface yang-modules nokia-modules',
                                'system management-interface yang-modules no base-r13-modules',
                                'system netconf auto-config-save',
                                'system netconf no shutdown',
                                'system management-interface cli md-cli auto-config-save',
                                'system management-interface configuration-mode model-driven']
                # Execute Script.
                send_cmmdz(sros_conn, enableNetconf)
                # Validate NETCONF is enabled and Operational.
                send_single(sros_conn, 'show system netconf')
                # Disconnect from the SSH Connection to our far-end remote device.
                # We need to disconnect to open the pipe for python3 to establish netconf connection.
                disconnect(sros_conn)
                time.sleep(2)
                try:
                    netcbackup(ip, NETCONF_USER, NETCONF_PASS)
                except Exception as e:
                    print(f"{e}")

if __name__ == "__main__":
    main()
