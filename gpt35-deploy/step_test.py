from topic_module_light import TopicModuleLight
from setup import read_yaml


config = 'config/topic_module_config.yaml'


user_input = 'I have 187 devices that show as potentially vulnerable to the PSIRT cisco-sa-iosxe-webui-privesc-j22SaA4z. How can I confirm vulnerability to this PSIRT that allows a remote, unauthenticated attacker to create an account on an affected device with privilege level 15 access and can then use that account to gain control of the affected device?'

# user_input = 'One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the pubd process is consuming the majority of memory.  Is this a bug?'


config_output = read_yaml(config)
templates = {key: read_yaml(value) for key, value in config_output.get('template', {}).items()}
tmp = TopicModuleLight(config_output, templates)
topic_module_output = tmp.run_light(user_input)
print(f'type(topic_module_output): {type(topic_module_output)}')
# import pdb;pdb.set_trace()
for key, value in topic_module_output.items():
    print(f'{key}: {value}')

print('Done')

"""
"""