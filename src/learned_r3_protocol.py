import json
from src.learned_r3_weight import OUT

def load_design():
    cfg=json.loads((OUT/'frozen_design.json').read_text())
    amendment=json.loads((OUT/'amendment_01.json').read_text())
    cfg.update(amendment['protocol_overrides']);cfg['source_sha256'].update(amendment['source_sha256']);return cfg
