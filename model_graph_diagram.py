
import json
import os


# data = d3.json("https://raw.githubusercontent.com/azaroth42/experiments/master/d3_heb2.json")

model_configs = {}

def make_readable(prop):
	prop = prop.replace('http://www.cidoc-crm.org/cidoc-crm/', 'crm:')
	prop = prop.replace('https://linked.art/ns/terms/', 'la:')
	return prop

def traverse(config, node, path):
	info = config['nodes'][node]
	for o in info['out']:
		mypath = path[:]
		dmn = config['nodes'][o[1]]
		mypath.extend([o[0], dmn['class'], dmn['name']])
		if dmn['datatype'] in ['resource-instance', 'resource-instance-list'] and dmn['target']:
			if dmn['name'] != "source":			
				for t in dmn['target']:
					try:
						config['resinst'][t].append(mypath)
					except:
						config['resinst'][t] = [mypath]
		traverse(config, o[1], mypath)


for m in os.listdir('models'):
	with open(f"models/{m}") as fh:
		js = json.load(fh)

		graph = js['graph'][0]

		if not graph['isactive']:
			continue

		me = graph['root']['graph_id']
		model_configs[me] = {"name": graph['root']['name'], "top": graph['root']['nodeid'], "resinst": {}}
		nodes = graph['nodes']
		edges = graph['edges']

		node_info = {}
		for n in nodes:
			try:
				target = n['config']['graphid']
			except:
				target = None
			node_info[n['nodeid']] = {
				'class': make_readable(n['ontologyclass']),
				'name': n['name'],
				'datatype': n['datatype'],
				'target': target,
				'in': [], 'out': []}

		for e in edges:
			dmn = e['domainnode_id']
			rng = e['rangenode_id']
			prop = make_readable(e['ontologyproperty'])
			node_info[dmn]['out'].append((prop, rng))
			node_info[rng]['in'].append((prop, dmn))

		model_configs[me]['nodes'] = node_info

		traverse(model_configs[me], model_configs[me]['top'], [])


# Now generate diagram

uuid_map = {}
x = 1
heb = {'name': 'arches', 'children': []}

for d in model_configs.keys():
	uuid_map[d] = x
	nm = model_configs[d]['name']
	x += 1

for (d, info) in model_configs.items():

	h = {"name": model_configs[d]['name'], 'children': []}
	h['children'].append({"name": "_" + model_configs[d]['name'],'size':2000,'imports':[]})

	for (r, pths) in info['resinst'].items():
		if not r in model_configs:
			# inactive model
			continue
		for p in pths:		
			kn = "/".join(p[2::3])
			kn = kn[0].upper() + kn[1:]
			rn = model_configs[r]['name']
			done = 0
			for k in h['children']:
				# check if already exists
				if k['name'] == kn:
					k['imports'].append(f"arches.{rn}._{rn}")
					done = 1
					break
			if not done:
				kid = {"name": kn, "size": 800, "imports": [f"arches.{rn}._{rn}"]}
				h['children'].append(kid)
	heb['children'].append(h)

fh = open("d3_heb2.json", 'w')
fh.write(json.dumps(heb))
fh.close()
