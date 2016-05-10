#coding=utf-8
#!/usr/bin/env python

from credentials import get_nova_credentials_v2
from credentials import get_credentials
from novaclient.client import Client as nova_client
from neutronclient.v2_0.client import Client as neutron_client
from utils import print_values

class CreateTopo:
	def __init__(topo,info):
		topo.info=info
		topo.subnet_route_route = len(info['link']['route_route'])
		topo.subnet_route_host = len(info['link']['route_host'])
		topo.subnet_num = topo.subnet_route_route+topo.subnet_route_host
		topo.router_num = info['routes']
		topo.network_id = u'' 
		topo.subnet_id = {}
		topo.subnet_cidr = {}
		topo.router_cidr = {}
		topo.ports_id = {}
		topo.router_id = {}
		topo.route_ip = {}
		topo.neutron_credentials = get_credentials()
		topo.nova_credentials = get_nova_credentials_v2()
		topo.neutron = neutron_client(**topo.neutron_credentials)
		topo.nova = nova_client(**topo.nova_credentials)
		for tmp in range(topo.subnet_num):
			topo.ports_id[tmp] = {}
		for tmp in range(topo.subnet_num):
			topo.route_ip[tmp] = {}
	def Create_net(topo):
		body_sample = {'network': {'name': topo.info['network'],
                   'admin_state_up': True}}
   		netw = topo.neutron.create_network(body=body_sample)
	   	net_dict = netw['network']
   		topo.network_id = net_dict['id']
		print('Network %s created' % topo.network_id)   
		
		subnet_list=[]
		for tmp in range(topo.subnet_num):
			subnet={'cidr':'10.1.'+str(tmp)+'.0/24',
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

	def Create_routers(topo):
		for tmp in range(topo.router_num):
			request = {'router': {'name': 'router'+str(tmp),
                        	  'admin_state_up': True}}
   			router = topo.neutron.create_router(request)
    			topo.router_id[tmp] = router['router']['id']
	def Create_ports(topo):
		for subnets in range(topo.subnet_route_route):
			ports_ip = {}
			for tmp in range(len(topo.info['link']['route_route'][subnets])):
				body_value = {'port':{
					'admin_state_up':True,
					'name':'n'+str(subnets)+'port'+str(tmp),
					'network_id':topo.network_id,
					'fixed_ips':[{'subnet_id':topo.subnet_id[subnets]}],
				}}
				port = topo.neutron.create_port(body=body_value)
				#print port
				port_id = port['port']['id']
				print port_id
				topo.ports_id[subnets][tmp] = port['port']['id']
				router = topo.info['link']['route_route'][subnets][tmp]
				topo.neutron.add_interface_router(\
					router = topo.router_id[router],
					body = {'port_id':port_id})
				ports_ip[router] = port['port']['fixed_ips'][0]['ip_address']
			for router_1 in topo.info['link']['route_route'][subnets]:
				for router_2 in topo.info['link']['route_route'][subnets]:
					if router_1 != router_2:
						topo.route_ip[router_1][router_2] = ports_ip[router_2]
		for subnets in range(topo.subnet_route_route,topo.subnet_num):
			for tmp in range(len(topo.info['link']['route_host'][subnets-topo.subnet_route_host])):
				if tmp == 0:
					body_value = {'port':{
						'admin_state_up':True,
						'fixed_ips':[{'subnet_id':topo.subnet_id[subnets],
							'ip_address':'10.1.'+str(subnets)+'.1'}],
						'name':'n'+str(subnets)+'port'+str(tmp),
						'network_id':topo.network_id,
					}}
					port = topo.neutron.create_port(body=body_value)
					port_id = port['port']['id']
					topo.ports_id[subnets][tmp] = port_id
					router = topo.info['link']['route_host'][subnets-topo.subnet_route_route][tmp]
					topo.neutron.add_interface_router(\
						router=topo.router_id[router],
						body={'port_id':port_id})
					topo.router_cidr[router] = topo.subnet_cidr[subnets]
			else:
				body_port = {'port':{
					'admin_state_up':True,
					'name':'n'+str(subnets)+'port'+str(tmp),
					'network_id':topo.network_id,
					'fixed_ips':[{'subnet_id':topo.subnet_id[subnets]}],
				}}
				port = topo.neutron.create_port(body=body_port)
				port_id = port['port']['id']
				topo.ports_id[subnets][tmp] = port_id
						

	def Create_vms(topo):
		for subnets in range(topo.subnet_route_route,topo.subnet_num):
			for tmp in range(1,len(topo.info['link']['route_host'][subnets-topo.subnet_route_route])):
				nics = [{'port-id':topo.ports_id[subnets][tmp]}]
				image = topo.nova.images.find(name = topo.info['image'])
				flavor = topo.nova.flavors.find(name = topo.info['flavor'])	
 				instance = topo.nova.servers.create(
					name = 'vm'+str(topo.info['link']['route_host'][subnets-topo.subnet_route_route][tmp]),
					flavor = flavor,
					image = image,
					key_name = 'keypair',
					nics = nics)
	def init_LinkGraph(topo):
		topo.LinkGraph = {}
		for router_1 in range(topo.info['routes']):
			topo.LinkGraph[router_1]={}
			for router_2 in range(topo.info['routes']):
				topo.LinkGraph[router_1][router_2] =  999999  #MAX
		for Link_Group in range(len(topo.info['link']['route_route'])):
			for router_1 in topo.info['link']['route_route'][Link_Group]:
				for router_2 in topo.info['link']['route_route'][Link_Group]:
					if router_1 != router_2:
						topo.LinkGraph[router_1][router_2] = 1
					else:
						topo.LinkGraph[router_1][router_2] = 0

	def init_nextHop(topo):
		topo.nextHop = {}
		for router in range(topo.info['routes']):
			topo.nextHop[router] = {}
	def BFS_routes(topo):
		nextHop = {}
		for router in range(topo.info['routes']):
			nextHop[router] = {}
		for bejin_router in range(topo.info['routes']):
			visited = {}
			queue = []
			for router in range(topo.info['routes']):
				visited[router] = False
			visited[bejin_router] = True
			for router in range(topo.info['routes']):
				if visited[router] == False and topo.LinkGraph[bejin_router][router] == 1:
					visited[router] = True
					nextHop[bejin_router][router] = router
			for router in range(topo.info['routes']):
				if visited[router] == True and bejin_router != router:
					queue.append(router)
					while(len(queue)!=0):
						tmp_router = queue.pop(0)
						for end_router in range(topo.info['routes']):
							if visited[end_router] == False and topo.LinkGraph[tmp_router][end_router] == 1:
								visited[end_router] = True
								queue.append(end_router)
								nextHop[bejin_router][end_router] = router
												
		topo.nextHop = nextHop
					        
			
	def add_routeTable(topo):
		for router_1 in range(topo.info['routes']):
			routes = []
			for router_2 in range(topo.info['routes']):
				if router_1 != router_2 and router_2 in topo.router_cidr.keys() and router_2 in topo.nextHop[router_2].keys():
					end_Cidr = topo.router_cidr[router_2]
					nextHop_ip = topo.route_ip[router_1][topo.nextHop[router_1][router_2]]
					routes.append({'destination':end_Cidr,'nexthop':nextHop_ip})
			body_routes = {'router':{'routes':routes}}
			topo.neutron.update_router(topo.router_id[router_1],body_routes)

if __name__=='__main__':
	info={'vms':4,
	'routes':4,
	'link':{'route_route':[(0,1),(1,2),(1,3)],
		'route_host':[(0,0),(1,1),(2,2),(3,3)]},
	'flavor':'m1.tiny',
	'network':'sample-net',
	'image':'cirros-0.3.4-x86_64'
	}

	topo = CreateTopo(info)
	topo.Create_net()
	topo.Create_routers()		
	topo.Create_ports()
	topo.Create_vms()
	topo.init_nextHop()
	topo.init_LinkGraph()
	topo.BFS_routes()
	topo.add_routeTable()
	#print topo.nextHop
