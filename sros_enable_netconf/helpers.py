"""Helper functions."""
import logging
import os
import sys

import netmiko
from ncclient import manager
from ncclient.xml_ import *


def create_folder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print("Error: Creating directory. " + directory)


def save_file(filename, contents):
    """Save the contents to a file in the PWD."""
    try:
        f = open(filename, "w+")
        f.write(contents)
        f.close()
    except Exception as e:
        print(e)


def netmiko_logging():

    """Netmiko Logging - This creates a Log file (NetmikoLog.txt) under a new 'Logging' folder.. Does not overwrite (a+).
    Log must end in .txt file as the program won't allow two .log files in the CWD.
    """
    create_folder("Logging")
    open("logging/NetmikoLog.txt", "a+")
    logging.basicConfig(filename="Logging/NetmikoLog.txt", level=logging.DEBUG)
    logger = logging.getLogger("netmiko")


def send_cmmdz(node_conn, list_of_cmds):

    """This function will unpack the dictionary created for the remote host to establish a connection with
    and send a LIST of commands. The output will be printed to the screen.
    Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.
    """
    try:
        x = node_conn.send_config_set(list_of_cmds, cmd_verify=False)
        print(x)
    except Exception as e:
        print(
            f"{e} Issue with set-list of commands. {e}\n\
Possibly running MD-CLI already."
        )


def send_single(node_conn, command):
    """This function will unpack the dictionary created for the remote host to establish a connection with
    and send a single command. The output will be printed to the screen.
    Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.[]
    """
    try:
        x = node_conn.send_command(command)
        print(x)
    except Exception as e:
        sys.exit(e)


def disconnect(node_conn):
    try:
        node_conn.disconnect()
    except Exception as e:
        print(e)


def netconfconn(args, ncusername, ncpassword):
    conn = manager.connect(
        host=args.node,
        port=args.port,
        username=ncusername,
        password=ncpassword,
        hostkey_verify=False,
        device_params={"name": "alu"},
    )
    return conn
