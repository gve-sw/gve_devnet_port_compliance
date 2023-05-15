# gve_devnet_port_compliance
This repository gives an example on how you can use the DNA Center APIs to assure configuration compliance for interfaces on a device. Compliance is based on templates that can be created and stored in the "templates" directory.


## Contacts
* Charles Llewellyn
*  Rey Diaz

## Solution Components
* DNAC
* Python
* Linux/IOS OS

## Linux Setup (Tested on CentOS7)
### Configuring Linux
	1. Ensure interfaces are up on linux using the "nmcli d" command
		○ If interfaces are down you can run the "ifup [interface name]"
	2. Run the command sudo yum update
		a. Yum Update will update the installed packages on a CENTOS system, and update to the latest python version on the system.
	3. Install python3 using the command "sudo yum install python3"
	4. Install git using the command "sudo yum install git"
	5. Clone the repository using "git clone [repository_url]"
	6. Go into the cloned directory using "cd [directory_name]"
	7. Install the python requirements using "pip install -r requirements.txt"
    8. Run the script manually using "python main.py [template_name]"


### Configuring Cron for Polling
	1. To edit the crontab file type "crontab -e"
	2. Write the cronjob to run the script on an interval
		a. crontab.guru[https://crontab.guru/] is a great website for validating cronjob syntax
 Example Crontab File (main.py & template directory is located in /home/ directory):
 
 ```
 59 15 * * 5 /usr/bin/python3 /home/main.py all_interfaces_template.json > /home/cron.log  2>&1
 ```

## Template Construction

Templates can be compartmentalized into three sections.

The initial section is the "Range" section. This is where you define the interfaces that you want to be captured.
The "start" key signifies the point from where you want to begin capturing interfaces.
The "stop" key indicates the point at which you want to end the interface capture. By default, this is set to "!" to ensure the entire interface is captured.

In the following example, a regular expression is employed to begin capturing all interfaces that include either FastEthernet or GigabitEthernet.

```
    "range": {
      "start": "interface (?:FastEthernet|GigabitEthernet)[\\d\\/]+",
      "stop": "!"
    }
```


The second section is the "Configuration" section.
This section is used to dictate the configuration lines that must be included in the range of interfaces specified.

If the existing interface configuration doesn't include all the configuration lines from the "configuration" section of the template, any omitted configuration lines will be automatically added to the interface.

```
 "configuration": [
      "switchport mode access",
      "switchport access vlan 10",
      "authentication host-mode multi-domain",
      "authentication order dot1x mab",
      "authentication priority dot1x mab",
      "authentication port-control auto",
      "authentication periodic",
      "authentication timer reauthenticate server",
      "mab",
      "dot1x pae authenticator",
      "dot1x timeout tx-period 10",
      "spanning-tree portfast"
    ]
```

The final section of the configuration template is the "exceptions" section.
If the existing interface configuration includes any line listed in the Exceptions section, the interface will automatically be skipped and won't receive any updates.

  ```
  "exceptions": [
    "switchport access vlan (?:998|999|1127|210[0-9])",
    "vrf forwarding Mgmt-vrf",
    "ip address"
  ]
  ```

### Note: When using a regular expression with capture group(s), each capture group must be ignored by starting them with the expression "?:". Capture groups are denoted by parentheses ().

## Installation/Configuration
Install requirements:

```pip install -r requirements.txt```

Inside of main.py:
```python
# DNAC server IP and Username and Password
username = "dnac_username"
password = "dnac_password"
base_url = "dnac_host"

```


## Usage

When running this script, you must specifiy the name of the template that you would like to run.
The "templates" folder is checked to see if that template exists, and if it does, it will run the script using the specified template.

To launch script:


    $ python main.py [template name]



# Screenshots
![/IMAGES/0image.png](/IMAGES/0image.png)

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.md)

### CODE_OF_CONDUCT

Our code of conduct is available [here](CODE_OF_CONDUCT.md)

### CONTRIBUTING

See our contributing guidelines [here](CONTRIBUTING.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.
