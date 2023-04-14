import whisper
import deepl
import mimetypes
import os
import moviepy.editor as mp
from datetime import timedelta
import json
import time
from dotenv import load_dotenv
load_dotenv()
DEEPL_KEY = os.getenv("DEEPL_KEY")
translator = deepl.Translator(DEEPL_KEY)


def format_data(args, file_path, trans_lang, og_result, og_lang, translation_result):
    '''
    THIS WILL CHANGE TO FORMAT INTO CSV FORMAT
    '''
    output = {}

    # build dictionary
    output['File Name'] = os.path.basename(file_path)
    output['Original Language'] = og_lang
    output['Translated Language'] = trans_lang
    output['Translated Transcription'] = translation_result
    output['Original Transcription'] = og_result
    return output



def detect_language(audio_file_path, args, model):
    print("detecting language...")
    audio_file = mp.AudioFileClip(audio_file_path)

    if args["ultra_off"] == True or audio_file.duration < 30:
        audio = whisper.load_audio(audio_file_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(args["device"])
        _, probs = model.detect_language(mel)

        language = max(probs, key=probs.get)
        
    else:
        os.makedirs('temp_audio', exist_ok=True)
        n=30
        i = 0
        j = n
        master_probs = {}
        
        while j <= audio_file.duration:
            clips = audio_file.subclip(t_start=i, t_end=j)
            clip_path = f'temp_audio/{i}_{j}.wav'
            clips.write_audiofile(clip_path, logger=None)

            audio = whisper.load_audio(clip_path)
            audio = whisper.pad_or_trim(audio)
            mel = whisper.log_mel_spectrogram(audio).to(model.device)
            _, probs = model.detect_language(mel)
            if not master_probs:
                master_probs = probs
            master_probs = {k: master_probs.get(k, 0) + probs.get(k, 0) for k in set(master_probs) | set(probs)}

            i += n
            j += n
            os.remove(clip_path)


        language = max(master_probs, key=master_probs.get)
    language = language.upper()

    if language == "EN":
        language = "EN-US"
    print("Detected language: ", language)
    return language



def transcribe_file(file, args, model):
    """takes in a audio or video file, returns a og_lang transcription string, and the og_lang"""
    mimetypes.init()
    print(f"starting transcription of {file}")
    if mimetypes.guess_type(file)[0].split('/')[0] in ['audio']:
        audio_file = file
    elif mimetypes.guess_type(file)[0].split('/')[0] in ['video']:
        audio_file = os.path.basename(file)
        audio_file = f"{os.path.splitext(audio_file)[0]}.wav"
        try:
            clip = mp.VideoFileClip(file)
        except Exception as e:
            print(e)
            result, og_lang = "CORRUPT VIDEO FILE", "CORRUPT VIDEO FILE"
            return result, og_lang
        
        if clip.audio is not None:
            clip.audio.write_audiofile(audio_file, logger=None)
        else:
            result, og_lang = "", ""
            return result, og_lang
    else:
        #ERROR. NO NON VIDEO OR AUDIO SHOULD HAVE MADE IT HERE.
        raise AssertionError()

    if args['force_og_lang'] == 'auto':
        og_lang = detect_language(audio_file, args, model)
    else:
        og_lang = args['force_og_lang']
    

    options = {}
    options['language'] = "en" if og_lang == "EN-US" else og_lang

    # SPLIT AUDIO 
    mp_audio_file = mp.AudioFileClip(audio_file)
    os.makedirs('temp_audio', exist_ok=True)
    n=90
    i = 0
    j = n
    result = {'text': '', 'segments': [], 'language': []}
    if mp_audio_file.duration < n:
        result = whisper.transcribe(model, audio_file, verbose=False, **options)
    else:
        while j <= mp_audio_file.duration:
            clips = mp_audio_file.subclip(t_start=i, t_end=j)
            clip_path = f'temp_audio/{i}_{j}.wav'
            clips.write_audiofile(clip_path, logger=None)

            clip_trans = whisper.transcribe(model, clip_path, verbose=False, **options)

            if not clip_trans['text'] or clip_trans['text'] == "...":
                pass
            else:
                result['text'] += ' ' + clip_trans['text']
                
                for seg in clip_trans['segments']:
                    seg['start'] += i
                    result['segments'].append(seg)
                    result['language'].append(clip_trans['language'])

            i += n
            j += n
            os.remove(clip_path)

    if args["timestamps"] == True:
        if args["output_format"] == 'json':
            result['timestamp_og_text'] ={str(timedelta(seconds=round(d['start']))): {d['text']} for d in result['segments'] if d['text']}
        elif args["output_format"] == 'csv':
            result['timestamp_og_text'] = " ".join([f"{str(timedelta(seconds=round(d['start'])))}: {d['text']}\n" for d in result['segments'] if d['text']])

    if mimetypes.guess_type(file)[0].split('/')[0] in ['video']:
        os.remove(audio_file)

    return result, og_lang



def translate_string(og_result, args, language):
    """takes in a string, returns a transcription string in the given language"""
    print(f"Translating from {language} to {args['translation_lang']}")
    if not og_result['text']:
        return ""
    
    if args["timestamps"] == False:
        trans_strs = [og_result["text"]]
        while len(trans_strs[-1]) > 550:
            new_text = []

            for elem in trans_strs:
                edge = int(len(elem)/2)
                new_text.append(elem[0:edge])
                new_text.append(elem[edge:])
            trans_strs = new_text
    else:
        trans_strs = [[str(timedelta(seconds=round(d['start']))), d['text']] for d in og_result['segments']]

    translation = {} if args["output_format"] == 'json' else ""
    for i in trans_strs:
        if not i[1]:
            continue
        
        result = translator.translate_text(i[1], target_lang=args['translation_lang'])

        if args["timestamps"] == False:
            translation += result.text
        else:
            if args["output_format"] == 'json':
                translation[i[0]] = result.text
                
            elif args["output_format"] == 'csv':
                translation =  translation + i[0] + ': ' + result.text + '\n'

    return translation



def process_file(file_path, args, model):
    og_result, og_lang = transcribe_file(file_path, args, model)
    print(f"OG LANG: {og_lang}, OG LANG RESULT: {og_result['text'] if args['timestamps'] == False else og_result['timestamp_og_text']}")

    if args["translation_lang"] == og_lang:
        print("translation language is same as original language.")
        if args['timestamps'] == False:
            translation_result = og_result['text']
        else:
            translation_result = og_result['timestamp_og_text']
    else:
        translation_result = translate_string(og_result, args, og_lang)

    trans_lang = args["translation_lang"]
    print(f"TRANS LANG: {trans_lang}, TRANS RESULT: {translation_result}")

    og_result = og_result['text'] if args['timestamps'] == False else og_result['timestamp_og_text']
    data = format_data(args, file_path, trans_lang, og_result, og_lang, translation_result)
    return [data]
    

