import json

with open('data/10-09-19.txt') as in_file:
    data = json.loads(in_file.readline().split('\t')[1])
    for p in data:
        print(data[p]['full_text'])

