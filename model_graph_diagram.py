
import json
import os

# For visualization, see:  https://observablehq.com/@azaroth42/hierarchical-edge-bundling

model_configs = {}

class_colors = {
	"Person": "#E02020", 
	"Group": "#E02020",
	"Activity": "#4050FF",
	"Place": "green",
	"Physical Thing": "#8B4513",
	"Textual Work": "orange",
	"Visual Work": "orange",
	"Observation": "#4050FF",
	"Provenance Activity": "#4050FF",
	"Modification": "#4050FF",
	"Instrument": "#8B4513",
	"Collection or Set": "orange",
	"Digital Resources": "purple"
}


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
			if not "_source" in dmn['name'] and not dmn['name'] == 'source':			
				for t in dmn['target']:
					try:
						config['resinst'][t].append(mypath)
					except:
						config['resinst'][t] = [mypath]
		traverse(config, o[1], mypath)


path = "/Users/rsanderson/Development/getty/arches/current/projects/arches-for-science-prj/afs/pkg/graphs/resource_models"

for m in os.listdir(path):
	if m.endswith('.json'):
		with open(os.path.join(path, m)) as fh:
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

	mname = model_configs[d]['name']
	h = {"name": mname, 'children': []}
	cl = info['nodes'][info['top']]['class']
	h['children'].append({"name": "_" + model_configs[d]['name'],'size':2000,'imports':[], 
		'color': class_colors.get(mname, "black"), 'description': cl})

	for (r, pths) in info['resinst'].items():
		if not r in model_configs:
			# inactive model
			continue
		for p in pths:		
			kn = "/".join(p[2::3])
			crmp = "/".join(p[::3])
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
				kid = {"name": kn, "size": 800, "imports": [f"arches.{rn}._{rn}"], 'color': class_colors.get(mname, "black"), 'description': crmp}
				h['children'].append(kid)
	heb['children'].append(h)

fh = open("d3_heb_afs.json", 'w')
fh.write(json.dumps(heb))
fh.close()
