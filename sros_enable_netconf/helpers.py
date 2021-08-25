"""Helper functions."""
import logging
import os
import sys
from typing import Dict

from ncclient import manager


def create_folder(directory: str):
    """Create directory

    Args:
        directory (str): Directory path
    """

    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print(f"Error: Creating directory: {directory}")


def save_file(filename: str, contents: str, mode: str):
    """Save the contents to a file in the PWD.

    Args:
        filename (str): [description]
        contents (str): [description]
        mode (str): [description]
    """
    try:
        with open(filename, mode, encoding="utf-8") as file:
            file.write(contents)
    except Exception as res_err:
        print(res_err)


def netmiko_logging():
    """Netmiko Logging - This creates a Log file under a new 'Logging' folder."""
    create_folder("logging")
    save_file("logging/netmikolog.txt", "", "a+")

    logging.basicConfig(filename="logging/netmikolog.txt", level=logging.DEBUG)
    logging.getLogger("netmiko")


def send_commands(node_conn, list_of_cmds):

    """This function will unpack the dictionary created for the remote host to establish a connection with
    and send a LIST of commands. The output will be printed to the screen.
    Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.
    """
    try:
        return node_conn.send_config_set(list_of_cmds, cmd_verify=False)
    except Exception as res_err:
        print(f"{res_err} Issue with set-list of commands")


def send_single(node_conn, command, use_ttp: bool = False):
    """This function will unpack the dictionary created for the remote host to establish a connection with
    and send a single command. The output will be printed to the screen.
    Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.[]
    """
    try:
        return node_conn.send_command(command, use_ttp=use_ttp, ttp_template=None)
    except Exception as res_err:
        sys.exit(res_err)


def disconnect(node_conn):
    """[summary]

    Args:
        node_conn ([type]): [description]
    """
    try:
        node_conn.disconnect()
    except Exception as res_err:
        print(res_err)


def netconfconn(args, ncusername, ncpassword):
    """[summary]

    Args:
        args ([type]): [description]
        ncusername ([type]): [description]
        ncpassword ([type]): [description]

    Returns:
        [type]: [description]
    """
    conn = manager.connect(
        host=args.node,
        port=args.port,
        username=ncusername,
        password=ncpassword,
        hostkey_verify=False,
        device_params={"name": "sros"},
        timeout=300,
    )
    return conn


def get_netconf_config(args: Dict, ncusername: str, ncpassword: str):
    """[summary]

    Args:
        args (Dict): [description]
        ncusername (str): [description]
        ncpassword (str): [description]
    """

    # Now let's connect to the device via NETCONF and pull the config to validate.
    nc_conn = netconfconn(args, ncusername, ncpassword)
    # Retrieve the XML Config
    config = nc_conn.get_config(source="running")
    # Close NETCONF session
    nc_conn.close_session()
    # save_file("temp-config.xml", str(config), mode="w+")
    return str(config)
