"""Programmatically Enable NETCONF on SROS Device."""
import argparse
import getpass
import os

import xmltodict
from netmiko import ConnectHandler

from sros_enable_netconf.helpers import (
    create_folder,
    disconnect,
    get_netconf_config,
    netmiko_logging,
    save_file,
    send_commands,
    send_single,
)

# Define the NETCONF USERNAME / PASSWORD, PICK UP ENV VARS OR USE DEFAULT.
NETCONF_USER = os.getenv("NETCONF_USER", "netconf")
NETCONF_PASS = os.getenv("NETCONF_PASS", "NCadmin123")
BACKUP_PATH = os.getenv("BACKUP_PATH", "backups")


def get_arguments():
    """Get argparse arguments."""
    parser = argparse.ArgumentParser(
        description="Command Line Driven Utility To Enable NETCONF\
        And MD-CLI on SROS Devices."
    )
    parser.add_argument("-n", "--node", help="Target NODE IP", required=True)
    parser.add_argument("-u", "--user", help="SSH Username", required=False, default="admin")
    parser.add_argument("-p", "--port", help="NETCONF TCP Port", required=False, default="830")
    args = parser.parse_args()
    return args


def main():
    """Execute main function."""
    # Extract the Arguements from ARGSPARSE:
    args = get_arguments()
    # start logging
    netmiko_logging()
    # Create a dictionary for our device.
    sros = {
        "device_type": "alcatel_sros",
        "host": args.node,
        "username": args.user,
        "password": getpass.getpass(),
        "response_return": None,
    }
    # Pass in the dict and create the connection.
    sros_conn = ConnectHandler(**sros)
    # Establish a list of pre and post check commands.
    print("Connecting to device and executing script...")

    if "Enabled" in send_single(sros_conn, "show system netconf | match State"):
        print("Netconf already enabled on this device. Disconnecting.")
        disconnect(sros_conn)
    else:
        enable_netconf = [
            '/configure system security profile "netconf" netconf base-op-authorization lock',
            '/configure system security profile "netconf" netconf base-op-authorization kill-session',
            f"/configure system security user netconf access {NETCONF_USER}",
            f"/configure system security user netconf password {NETCONF_PASS}",
            f"/configure system security user netconf console member {NETCONF_USER}",
            "/configure system security user netconf console member 'administrative'",
            "/configure system management-interface yang-modules nokia-modules",
            "/configure system management-interface yang-modules no base-r13-modules",
            "/configure system netconf auto-config-save",
            "/configure system netconf no shutdown",
            "/configure system management-interface cli no cli-engine",
            "/configure system management-interface cli md-cli auto-config-save",
            "/configure system management-interface configuration-mode model-driven",
        ]

        # Execute Script.
        send_commands(sros_conn, enable_netconf)
        # Validate NETCONF is enabled and Operational.
        # send_single(sros_conn, "show system netconf")
        # Disconnect from the SSH Connection to our far-end remote device.
        # We need to disconnect to open the pipe for python3 to establish netconf connection.
        disconnect(sros_conn)

    try:
        config = get_netconf_config(args, NETCONF_USER, NETCONF_PASS)
        xml_config = xmltodict.parse(str(config))
        sys_name = xml_config["rpc-reply"]["data"]["configure"]["system"]["name"]
        create_folder(f"{BACKUP_PATH}/{sys_name}")
        save_file(f"backups/{sys_name}/{sys_name}.txt", str(config), mode="w+")
        print(f"Backed up XML Config: backups/{sys_name}/{sys_name}.txt")
    except Exception as err_exc:
        print(f"Error while attempting to get NETCONF config: {err_exc}")


if __name__ == "__main__":
    main()
