import netmiko, ncclient, argparse, getpass, sys, time, xmltodict, os
from netmiko import ConnectHandler
from ncclient import manager
from ncclient.xml_ import *
from xml.etree import ElementTree

def get_arguments():
    parser = argparse.ArgumentParser(description='Command Line Driven Utility To Enable NETCONF\
        On SROS Devices And MD-CLI.')
    parser.add_argument("-n", "--node", help="Target NODE IP", required=True)
    parser.add_argument("-u", "--user", help="SSH Username", required=False, default='admin')
    parser.add_argument("-p", "--port", help="NETCONF TCP Port", required=False, default='830')
    args = parser.parse_args()
    return args

# Lets make it easier to send and receive the output to the screen.
# We'll create a function to pass in a list of commands as arguements.

def send_cmmdz(node_conn,list_of_cmds):
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
        print (x)
    except Exception as e:
        sys.exit(e)
        
def disconnect(node_conn):
    try:
        node_conn.disconnect()
    except Exception as e:
        print(e)    
            
def netconfconn(args,ncusername,ncpassword):
    conn = manager.connect(host=args.node,
                           port=args.port,
                           username=ncusername,
                           password=ncpassword,
                           hostkey_verify=False,
                           device_params={'name':'alu'})
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
def main():
    # Extract the Arguements from ARGSPARSE:
    args = get_arguments()
    
    # Define the NETCONF USERNAME / PASSWORD:
    NETCONF_USER = 'netconf'
    NETCONF_PASS = 'NCadmin123'

    # # Create a dictionary for our device.
    sros = {
        'device_type': 'alcatel_sros',
        'host': args.node,
        'username': args.user,
        'password': getpass.getpass(),
    }
    # Pass in the dict and create the connection.
    sros_conn = net_connect = ConnectHandler(**sros)

   # Establish a list of pre and post check commands.
    print('Connecting to device and executing script...')
    send_single(sros_conn, 'show system information | match Name')
    send_single(sros_conn, 'show system netconf | match State')

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
    send_single(sros_conn,'show system netconf')
    
    # Disconnect from the SSH Connection to our far-end remote device.
    # We need to disconnect to open the pipe for python3 to establish netconf connection.
    
    disconnect(sros_conn)
    time.sleep(2)
        
   
    try:
        # Now let's connect to the device via NETCONF and pull the config to validate.

        nc = netconfconn(args, NETCONF_USER, NETCONF_PASS)
        
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

            createFolder('Configs')
            saveFile(f"Configs/{sys_name}.txt", xmlconfig)
            
    except Exception as e:
        print(f"Issue with NETCONF connection, {e}")
    
    
if __name__ == "__main__":
    main()
