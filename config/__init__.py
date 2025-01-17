import os
import yaml

with open(os.path.join("config.yaml"), 'r', encoding='utf-8') as file:
    appconf = yaml.safe_load(file)
