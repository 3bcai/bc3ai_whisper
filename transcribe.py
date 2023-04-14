import argparse
import os
import torch
from datetime import datetime
import pandas as pd
import json
import sys
import mimetypes
import whisper
import deepl
from .src.whisper_functions import process_file
from dotenv import load_dotenv

load_dotenv()
DEEPL_KEY = os.getenv("DEEPL_KEY")
translator = deepl.Translator(DEEPL_KEY)






def bc3ai_whisper(file_path, model="large-v2", device='cuda', translation_lang="EN-US", force_og_lang='auto',
                     ultra_off=False, timestamps=True, confidence_scores = False, output_format='json'):
    
    assert os.path.isfile(file_path)
    assert device in ['cuda', 'cpu']
    assert output_format in ['json']
    assert model in whisper.available_models()
    assert translation_lang in [lang.code for lang in translator.get_target_languages()],f"TRANSLATION LANGUAGE NOT IN LANGUAGE CODES. MUST BE:\n{[lang.code for lang in translator.get_target_languages()]}"
    assert force_og_lang in [lang.code for lang in translator.get_source_languages()] or force_og_lang == 'auto', f"FORCED ORIGINAL LANGUAGE NOT IN LANGUAGE CODES. MUST BE:\n{[lang.code for lang in translator.get_source_languages()]}"
    assert mimetypes.guess_type(file_path)[0].split('/')[0] in ['audio', 'video']

    args = {
        "dir": file_path, "model": model, "device": device, "translation_lang": translation_lang,
        "force_og_lang": force_og_lang, "ultra_off":ultra_off, "timestamps": timestamps, "confidence-scores": confidence_scores, "output_format": output_format}
    
    model = whisper.load_model(args['model'], device=args['device'])

    result = process_file(file_path, args, model)
    return result