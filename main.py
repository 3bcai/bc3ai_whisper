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
from src.whisper_functions import process_file
from dotenv import load_dotenv

load_dotenv()
DEEPL_KEY = os.getenv("DEEPL_KEY")
translator = deepl.Translator(DEEPL_KEY)



def arg_parser():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("dir", type=str, help="path to a directory of videos, to a audio or video file, or to a output folder to continue from. If continuation, do not feed any other arguements")
    parser.add_argument("--model", default="large-v2", help="name of the Whisper model to use")
    parser.add_argument("--device", default="cuda" if torch.cuda.is_available() else "cpu", help="device to use for PyTorch inference")
    parser.add_argument("--translation-lang", default="EN-US", help=f"language to translate to. must be one of the following: \n {[lang.code for lang in translator.get_target_languages()]}", choices=[lang.code for lang in translator.get_target_languages()])
    parser.add_argument("--force-og-lang", default="auto", help="override Whispers auto detection of language with a given shorthand lang representation. Ex: en")
    parser.add_argument("--ultra-off", action='store_true',help="Use this arg to use the faster translation")
    parser.add_argument('--timestamps',action='store_true',help="output timestamps in the resulting csv")
    parser.add_argument('--confidence-scores',action='store_true',help="output confidence scores in the resulting csv")
    parser.add_argument('--output-format', nargs='+',choices=["csv", "json"], default="csv")
    
    args = parser.parse_args().__dict__
    return args
    


if __name__ == "__main__":
    mimetypes.init()
    args = arg_parser()
    os.makedirs("output", exist_ok=True)

    # if dir is a continuation
    if os.path.basename(args['dir']) in os.listdir("output"):
        # can not change settings in a continuation
        assert len(sys.argv) <= 2, "can not change arguments in a continuation"

        dir_name=os.path.basename(args['dir'])
        output_dir = f"output/{dir_name}"

        df = pd.read_csv(f'{output_dir}/audio_transcriptions.csv')

        with open(f'{output_dir}/args.json') as user_file:
            args = json.load(user_file)
        print(f"Continuing generation of {os.path.basename(args['dir'])}")
    else:
        print("Creating new output...")
        assert args['model'] in whisper.available_models()

        dir_name = f"{os.path.basename(args['dir'])}: {datetime.now().strftime('%d:%m:%Y %H:%M:%S')}"
        output_dir = f"output/{dir_name}"

        os.makedirs(output_dir, exist_ok=True)
        with open(f"{output_dir}/args.json", "w") as fp:
            json.dump(args,fp) 
        df = pd.DataFrame(columns={'File Name': [], 'Original Language': [], 
                                'Translated Language': [], 'Translated Transcription': [], 'Original Transcription': []})
        df.to_csv(f'{output_dir}/audio_transcriptions.csv')

    print(f"Arguements for this output set: {args}")

    if os.path.isfile(args["dir"]):
        files = [args["dir"]]
    else:
        # Nested dir iter
        files = [os.path.join(subdir, file) for subdir, dirs, files in os.walk(args['dir']) for file in files if file not in list(df['File Name'])]

        # remove all non processable filetypes
        files = [file for file in files if mimetypes.guess_type(file)[0] != None if mimetypes.guess_type(file)[0].split('/')[0] in ['audio', 'video']]
        print(f"amount of files to process: {len(files)}")

    assert len(files) > 0, "No Videos To be Processed"
    assert args["translation_lang"] in [lang.code for lang in translator.get_target_languages()],f"TRANSLATION LANGUAGE NOT IN LANGUAGE CODES. MUST BE:\n{[lang.code for lang in translator.get_target_languages()]}"
    assert args["force_og_lang"] in [lang.code for lang in translator.get_source_languages()] or args["force_og_lang"] == 'auto', f"FORCED ORIGINAL LANGUAGE NOT IN LANGUAGE CODES. MUST BE:\n{[lang.code for lang in translator.get_source_languages()]}"
    
    model = whisper.load_model(args['model'], device=args['device'])

    for file in files:
            
        pd.DataFrame(process_file(file, args, model)).to_csv(f'{output_dir}/audio_transcriptions.csv', mode='a', header=False)
