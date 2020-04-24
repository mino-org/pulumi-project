import pulumi
import pulumi_azure as azure

ADMIN_USER_NAME = 'azureuser'
ADMIN_PASSWORD = '1qazZAQ!1qazZAQ!'
RESOURCE_GROUP = {
    'name': '',
    'location': ''
}
VIRTUAL_NETWORK = {
    'name': '',
    'addr_space': '10.0.0.0/16'
}
SUBNETS = [
    {
        'name': 'dmz',
        'addr_prefix': '10.0.0.0/24'
    },
    {
        'name': 'mz',
        'addr_prefix': '10.0.1.0/24'
    }
]
NSGS = [
    {
        'name': 'dmz'
    },
    {
        'name': 'mz'
    }
]
STORAGE_ACCOUNT = {
    'name': ''
}
VIRTUAL_MACHINES = [
    {
        'name': '',
        'os_type': 'Windows',
        'location': '',
        'size': 'Standard_D2_v3',
        'public': True
    },
    {
        'name': '',
        'os_type': 'Windows',
        'location': '',
        'size': 'Standard_D2_v3',
        'public': False
    }
]

def NewResourceGroup(index=int, name=str, location='japaneast'):
    return azure.core.ResourceGroup(
        f'rg{index}',
        name=name,
        location=location
    )

def NewVirtualNetwork(rg, index=int, name=str, addr_spaces=list):
    return azure.network.VirtualNetwork(
        f'vnet{index}',
        name=name,
        location=rg.location,
        resource_group_name=rg.name,
        address_spaces=addr_spaces
    )

def NewSubnet(rg, vnet, index=int, name=str, addr_prefix=str):
    return azure.network.Subnet(
        f'subnet{index}',
        name=name,
        resource_group_name=rg.name,
        virtual_network_name=vnet.name,
        address_prefix=addr_prefix
    )

def NewNSG(rg, index=int, name=str):
    return azure.network.NetworkSecurityGroup(
        f'nsg{index}',
        name=name,
        location=rg.location,
        resource_group_name=rg.name
    )

def AssociateSubnetNSG(subnet, nsg, index=int):
    return azure.network.SubnetNetworkSecurityGroupAssociation(
        f'assoc_subnet_nsg{index}',
        subnet_id=subnet.id,
        network_security_group_id=nsg.id
    )

def NewNIC(rg, subnet, index=int, vm_name=str):
    return azure.network.NetworkInterface(
        f'nic{index}',
        name=f'{vm_name}-nic',
        location=rg.location,
        resource_group_name=rg.name,
        ip_configurations=[{
            'name': f'{vm_name}-ipconfig',
            'subnet_id': subnet.id,
            'privateIpAddressAllocation': 'Dynamic'
        }]
    )

def NewNICwithPublicIP(rg, subnet, public_ip, index=int, vm_name=str):
    return azure.network.NetworkInterface(
        f'nic{index}',
        name=f'{vm_name}-nic',
        location=rg.location,
        resource_group_name=rg.name,
        ip_configurations=[{
            'name': f'{vm_name}-ipconfig',
            'subnet_id': subnet.id,
            'privateIpAddressAllocation': 'Dynamic',
            'publicIpAddressId': public_ip.id
        }]
    )

def NewPublicIP(rg, index=int, vm_name=str):
    return azure.network.PublicIp(
        f'public_ip{index}',
        name=f'{vm_name}-pip',
        location=rg.location,
        resource_group_name=rg.name,
        allocation_method='Static',
        sku='Standard'
    )

def NewStorage(rg, index=int, name=str):
    return azure.storage.Account(
        f'storage{index}',
        name=name,
        location=rg.location,
        resource_group_name=rg.name,
        account_tier='Standard',
        account_kind='Storage',
        account_replication_type='LRS',
        enable_https_traffic_only=True
    )

def NewWindowsVM(rg, nic, storage, index=int, name=str, size='Standard_D2s_v3', username='azureuser', password=str):
    return azure.compute.VirtualMachine(
        f'vm{index}',
        name=name,
        location=rg.location,
        resource_group_name=rg.name,
        vm_size=size,
        network_interface_ids=[nic.id],
        delete_os_disk_on_termination=True,
        storage_image_reference={
            'publisher': 'MicrosoftWindowsServer',
            'offer': 'WindowsServer',
            'sku': '2019-Datacenter',
            'version': 'latest'
        },
        storage_os_disk={
            'name': f'{name}-os',
            'managed_disk_type': 'Standard_LRS',
            'caching': 'ReadWrite',
            'create_option': 'FromImage'
        },
        os_profile={
            'computer_name': name,
            'admin_username': username,
            'admin_password': password
        },
        os_profile_windows_config={
            'timezone': 'Tokyo Standard Time',
            'provision_vm_agent': True
        },
        boot_diagnostics={
            'enabled': True,
            'storageUri': storage.primary_blob_endpoint
        }
    )

rg = NewResourceGroup(index=0, name=RESOURCE_GROUP['name'], location=RESOURCE_GROUP['location'])
vnet = NewVirtualNetwork(rg=rg, index=0, name=VIRTUAL_NETWORK['name'], addr_spaces=[VIRTUAL_NETWORK['addr_space']])
subnets = [NewSubnet(rg=rg, vnet=vnet, index=SUBNETS.index(subnet), name=subnet['name'], addr_prefix=subnet['addr_prefix']) for subnet in SUBNETS]
subnet_dmz = subnets[0]
subnet_mz = subnets[1]
nsgs = [NewNSG(rg=rg, index=NSGS.index(nsg), name=nsg['name']) for nsg in NSGS]
assoc_subnet_nsg = [AssociateSubnetNSG(subnet=subnets[index], nsg=nsgs[index], index=index) for index in range(2)]
public_ip = NewPublicIP(rg=rg, index=0, vm_name=VIRTUAL_MACHINES[0]['name'])
storage = NewStorage(rg=rg, index=0, name=STORAGE_ACCOUNT['name'])

for vm in VIRTUAL_MACHINES:
    if (vm['public']):
        nic = NewNICwithPublicIP(rg=rg, index=VIRTUAL_MACHINES.index(vm), vm_name=vm['name'], subnet=subnets[VIRTUAL_MACHINES.index(vm)], public_ip=public_ip)
    else:
    nic = NewNIC(rg=rg, index=VIRTUAL_MACHINES.index(vm), vm_name=vm['name'], subnet=subnets[VIRTUAL_MACHINES.index(vm)])
    vm = NewWindowsVM(rg=rg, index=VIRTUAL_MACHINES.index(vm), name=vm['name'], storage=storage, nic=nic, size=vm['size'], username=ADMIN_USER_NAME, password=ADMIN_PASSWORD)
