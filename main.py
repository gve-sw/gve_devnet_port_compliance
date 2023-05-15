"""
CISCO SAMPLE CODE LICENSE Version 1.1 Copyright (c) 2022 Cisco and/or its affiliates

These terms govern this Cisco Systems, Inc. ("Cisco"), example or demo source code and its associated documentation (together, the "Sample Code"). By downloading, copying, modifying, compiling, or redistributing the Sample Code, you accept and agree to be bound by the following terms and conditions (the "License"). If you are accepting the License on behalf of an entity, you represent that you have the authority to do so (either you or the entity, "you"). Sample Code is not supported by Cisco TAC and is not tested for quality or performance. This is your only license to the Sample Code and all rights not expressly granted are reserved.
"""
import json
import requests
import re
from dnacentersdk import DNACenterAPI
import dnacentersdk
import time
import sys
# replace username with dnac username
username = ""
# replace password with dnac password
password = ""
# replace with dnac ip or hostname
base_url = "https://dnac.example.com"
template_file_name = sys.argv[1]
# template_file_name = "all_interfaces_template.json"
template_file = f"templates/{template_file_name}"



dnac = DNACenterAPI(
    base_url=base_url,
    username=username,
    password=password,
    verify=False
)

def get_all_devices():
    try:
        devices = dnac.devices.get_device_list()
        device_list = devices["response"]
        return device_list
    except requests.exceptions.RequestException as e:
        print(f"Error getting devices: {e}")
        return []


def get_device_interfaces(device_id):
    interfaces = dnac.devices.get_all_interfaces(device_id)

    return interfaces["response"]


def get_device_compliance(device_id, template):
    try:
        response = dnac.devices.get_device_config_by_id(device_id)
        default_interface_regex = '(interface .+?)(?=^!)'
        user_interface_regex = read_template_from_json(template_file)
        user_interface_regex_start = user_interface_regex['range']["start"]
        user_interface_regex_stop = user_interface_regex['range']["stop"]
        user_interface_regex = f"({user_interface_regex_start}[\s\S]*?)(?={user_interface_regex_stop})"

        config_str = response["response"]

        # Extract the interface configurations
        interface_blocks = re.findall(r''+user_interface_regex, config_str, re.MULTILINE | re.DOTALL)

        # Create a dictionary with interface name as key and interface configuration as value
        interface_dict = {}
        interface_exceptions = []
        for block in interface_blocks:
            is_except = False
            for line in template['exceptions']:
                exception = re.findall(r'' + line, block)
                if exception:
                    lines = block.strip().split('\n')
                    interface_name = lines[0].strip()
                    interface_exceptions.append(interface_name)
                    is_except = True
                    break
            if not is_except:
                lines = block.strip().split('\n')
                interface_name = lines[0].strip()
                lines.pop(0)
                lines = [x.strip(' ') for x in lines]

                # interface_config = '\n'.join(lines[1:])
                interface_dict[interface_name] = lines

        for interface in interface_exceptions:
            if interface in interface_dict.keys():
                del interface_dict[interface]
        return interface_dict
    except requests.exceptions.RequestException as e:
        print(f"Error getting device compliance: \n{e}")
        return {}


def check_compliance(device_config, template):
    non_compliant_configurations = []
    for key, value in template.items():
        if key not in device_config or device_config[key] != value:
            non_compliant_configurations.append((key, value, device_config.get(key)))
    return len(non_compliant_configurations) == 0


def read_template_from_json(filename):
    with open(filename, 'r') as jsonfile:
        template = json.load(jsonfile)
    return template


def write_template_file(config):
    template = read_template_from_json(filename="templates/interface_range_template.json")
    ordered_set = {}
    for interface in config:
        ordered_set[interface] = {}
        for configuration in template['configuration']:
            ordered_set[interface][configuration] = False
            if configuration in config[interface]:
                ordered_set[interface][configuration] = True

    with open("new_template.txt", "w") as f:
        for interface in config:
            if config[interface]:
                f.write(f"{interface}\n")
                for config_line in template["configuration"]:
                    if ordered_set[interface][config_line]:
                        f.write(f"\t\t{config_line}\n")


def deploy_template(device_id):
    # print(device_id)
    project_name = "DNAC_802dot1_Compliance"
    template_name = "802dot1_compliance"
    try:
        ### PROJECT CREATION
        dnac.configuration_templates.create_project(name=project_name)
        time.sleep(5)
    except dnacentersdk.exceptions.ApiError as e:
        if "exists" in str(e):
            print("Project already exists, continuing template deployment...")

    project = dnac.configuration_templates.get_projects(name=project_name)
    project_id = project[0]["id"]
    with open("new_template.txt", "r") as f:
        data = f.read()

    try:
        ## TEMPLATE CREATION
        task = dnac.configuration_templates.create_template(project_id=project_id, name=template_name, templateContent=data, softwareType="IOS", deviceTypes=[{"productFamily":"Switches and Hubs"}], language="JINJA")
        # print(task)
        task_completed = dnac.task.get_task_by_id(task_id=task['response']['taskId'])['response']['progress']

        #VERSION TEMPLATE
        templates = dnac.configuration_templates.gets_the_templates_available(project_id=project_id,
                                                                                  un_committed=True)
        for template in templates:
            if template['name'] == template_name:
                template_id = template['templateId']

    except dnacentersdk.exceptions.ApiError as e:
        if 'exists' in str(e):
            print("Template already exists...")
            templates = dnac.configuration_templates.gets_the_templates_available(project_id=project_id,
                                                                                  un_committed=True)
            for template in templates:
                if template['name'] == template_name:
                    template_id = template['templateId']
            update_template = dnac.configuration_templates.update_template(name=template_name,project_id=project_id, id=template_id,templateContent=data, softwareType="IOS", deviceTypes=[{"productFamily":"Switches and Hubs"}], language="JINJA")


    ## VERSION TEMPLATE
    dnac.configuration_templates.version_template(templateId=template_id, comments=f"Template versioned for device id: {device_id}")
    template_version_id = dnac.configuration_templates.get_template_details(template_id=template_id, latest_version=True)['id']
    ## Deploy Template
    target = [{"id": device_id, "type": "MANAGED_DEVICE_UUID", "versionedTemplateId": template_version_id}]
    task = dnac.configuration_templates.deploy_template_v2(forcePushTemplate=True, templateId=template_id, targetInfo=target)
    # print(task)
    task_id = task['response']['taskId']
    # print(task_id)
    try:
        task_progress = dnac.task.get_task_by_id(task_id=task_id)
        # print(task_progress)
        deployment_id = task_progress['response']['progress'].partition("Template Deployemnt Id: ")[2]
        task_progress = dnac.configuration_templates.get_template_deployment_status(deployment_id)
    except dnacentersdk.exceptions.ApiError as e:
        if "404" in str(e):
            print("Retrying in 5 seconds")
            time.sleep(5)
            task_progress = dnac.task.get_task_by_id(task_id=task_id)
            deployment_id = task_progress['response']['progress'].partition("Template Deployemnt Id: ")[2]
            task_progress = dnac.configuration_templates.get_template_deployment_status(deployment_id)
            # print(task_progress)
    while task_progress['devices'][0]['status'] == "IN_PROGRESS":
        print("Deployment In Progress..")
        time.sleep(5)
        task_progress = dnac.configuration_templates.get_template_deployment_status(deployment_id)

    print(task_progress['devices'][0]['status'] + " - " + task_progress['devices'][0]['detailedStatusMessage'])

def main():
    template = read_template_from_json(template_file)

    # Initialize compliant and non-compliant device lists
    compliant_devices = []
    non_compliant_devices = []

    # all_devices = input("Check all devices? (y/n): ").lower() == 'y'
    all_devices = "y"
    if all_devices:
        devices = get_all_devices()
        device_ids = [device["id"] for device in devices]
    else:
        device_ids = input("Enter device IDs, separated by commas: ").split(',')
        device_ids = [device_id.strip() for device_id in device_ids]

    for device_id in device_ids:
        device_config = get_device_compliance(device_id, template)
        new_config = {k: set(device_config[k]) for k in device_config}
        new_template = set(template['configuration'])
        # print(new_config)
        # print(new_template)
        differences = {}
        for interface in new_config:
            differences[interface] = new_template - new_config[interface]
        # print(differences)
        # input()
        is_different = False
        for interface in differences:
            if differences[interface]:
                is_different = True
                break
        if is_different:
            print(f"\nDevice {device_id} is NOT COMPLIANT with the template. Performing configuration change...")
            non_compliant_devices.append(device_id)
            write_template_file(differences)
            deploy_template(device_id)
        else:
            compliant_devices.append(device_id)
            print(f"\nDevice {device_id} is COMPLIANT with the template. Skipping to next device...")
            continue



    # Print the compliant and non-compliant device lists
    print("\nCompliant Devices:")
    print(compliant_devices)

    print("\nNon-Compliant Devices:")
    print(non_compliant_devices)


if __name__ == "__main__":
    main()

