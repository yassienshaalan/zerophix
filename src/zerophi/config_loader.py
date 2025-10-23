import yaml

def load_config(p):
    return yaml.safe_load(open(p,'r',encoding='utf-8'))
