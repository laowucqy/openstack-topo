#coding=utf-8
#!/usr/bin/env python

from neutronclient.v2_0 import client
import novaclient.v1_1.client as nvclient
from credentials import get_credentials
from credentials import get_nova_credentials
from credentials import get_nova_credentials_v2
from utils import print_values_server

class CreateTopo:
	def __init__(topo,info):
		topo.info=info
		topo.subnet_route_route = len(info['link']['route_route'])
		topo.subnet_route_host = len(info['link']['route_host'])
		topo.subnet_num = topo.subnet_route_route+topo.subnet_route_host
		topo.route_num = info['routes']
		topo.network_id = u'' 
		topo.subnet_id = {}
		topo.subnet_cidr = {}
		topo.neutron_credentials = get_credentials()
		topo.neutron = client.Client(**topo.neutron_credentials)
		topo.router_id = {}
	def Create_net(topo):
		body_sample = {'network': {'name': topo.info['network'],
                   'admin_state_up': True}}
   		netw = topo.neutron.create_network(body=body_sample)
	   	net_dict = netw['network']
   		topo.network_id = net_dict['id']
		print('Network %s created' % topo.network_id)   
		
		subnet_list=[]
		for tmp in range(topo.subnet_num):
			subnet={'cidr':'10.0.'+str(tmp)+'.0/24',
				'ip_version':4,
				'network_id':topo.network_id,
				'name':'subnet'+str(tmp)}
			subnet_list.append(subnet)
		body_create_subnet={'subnets':subnet_list}
		subnet=topo.neutron.create_subnet(body=body_create_subnet)
		#print subnet
		for tmp in range(topo.subnet_num):
			#tmp=int(tmp)
			topo.subnet_id[tmp]=subnet['subnets'][tmp]['id']
			topo.subnet_cidr[tmp]=subnet['subnets'][tmp]['cidr']
			print topo.subnet_id[tmp]
			print topo.subnet_cidr[tmp]

	def Create_routes(topo):
		for tmp in range(topo.route_num):
			request = {'router': {'name': 'router'+str(tmp),
                        	  'admin_state_up': True}}
   			router = topo.neutron.create_router(request)
    			topo.router_id[tmp] = router['router']['id']

if __name__=='__main__':
	info={'vms':2,
	'routes':2,
	'link':{'route_route':[(0,1)],
		'route_host':[(1,1),(0,0)]},
	'flavor':'m1.tiny',
	'network':'sample-net',
	'image':'cirros-0.3.4-x86_64-disk'
	}

	topo = CreateTopo(info)
	topo.Create_net()
	topo.Create_routes()		
