"""Helper functions."""
import logging
import os
import sys

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

    """Netmiko Logging - This creates a Log file (NetmikoLog.txt) under a new 'Logging' folder.. Does not overwrite (a+).
    Log must end in .txt file as the program won't allow two .log files in the CWD.
    """
    create_folder("logging")
    save_file("logging/netmikolog.txt", "", "a+")

    logging.basicConfig(filename="logging/netmikolog.txt", level=logging.DEBUG)
    logging.getLogger("netmiko")


def send_cmmdz(node_conn, list_of_cmds):

    """This function will unpack the dictionary created for the remote host to establish a connection with
    and send a LIST of commands. The output will be printed to the screen.
    Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.
    """
    try:
        return node_conn.send_config_set(list_of_cmds, cmd_verify=False)
    except Exception as res_err:
        print(f"{res_err} Issue with set-list of commands")


def send_single(node_conn, command):
    """This function will unpack the dictionary created for the remote host to establish a connection with
    and send a single command. The output will be printed to the screen.
    Establish the 'node_conn' var first by unpacking the device connection dictionary. Pass it in as an args.[]
    """
    try:
        return node_conn.send_command(command)
    except Exception as res_err:
        sys.exit(res_err)


def disconnect(node_conn):
    try:
        node_conn.disconnect()
    except Exception as res_err:
        print(res_err)


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
