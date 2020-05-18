# sros-enable-netconf
Programatically enable NETCONF and MD-CLI on SROS Devices.

This command line driven utility will programatically connect via an initial SSH session utilizing Netmiko to a far-end remote device.
A pre-compiled list of commands will be deployed to the individual device and enable NETCONF, as well as change from the Classic CLI 
to the new Model Driven CLI.

AFter the configuration changes are completed, the ssh session will be disconnected and a new connection on default NETCONF port 830,
will be established. A configuration backup will then be completed via the NETCONF, get.config and categorized by the system host name.

Although this tool is very useful in a lab environment, it has not been tested in production and it's part of a training excersice. 
This code will be re-constructed to use a list of devices from the NETBOX API.

The tool was built to follow a theoretical issue as part of a blog post:
https://adminsave.wordpress.com/2020/05/18/programatically-enable-netconf-and-md-cli-on-nokia-sros/
