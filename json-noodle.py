import json
data = {}
data['ABC'] = {'XYZ': 123, 'EFG': 456}
print(json.dumps(data))

def xyz(key):
    return (key[0], key[1]['XYZ'])

subset = dict(map(xyz, data.items()))
print(json.dumps(subset))

subset2 = dict(map(lambda s : (s[0], s[1]['XYZ']), data.items()))
print(json.dumps(subset2))
