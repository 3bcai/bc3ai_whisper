import whisper
from googletrans import Translator
import mimetypes
import os
import moviepy.editor as mp
import json

translator = Translator()



def format_data(file_path, trans_lang, og_result, og_lang, translation_result):
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
    return [output]



def detect_language(audio_file_path, args, model):

    audio_file = mp.AudioFileClip(audio_file_path)
    with open('lang_codes.json') as user_file:
        lang_codes = json.load(user_file)

    if args["ultra_off"] == True or audio_file.duration < 30:
        audio = whisper.load_audio(audio_file_path)
        audio = whisper.pad_or_trim(audio)
        mel = whisper.log_mel_spectrogram(audio).to(args["device"])
        _, probs = model.detect_language(mel)
        # only include languages that can be translated
        probs = {k: master_probs[k] for k in master_probs.keys() if k in lang_codes.keys()}
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

        # only include languages that can be translated
        master_probs = {k: master_probs[k] for k in master_probs.keys() if k in lang_codes.keys()}
        language = max(master_probs, key=master_probs.get)

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
        clip = mp.VideoFileClip(file)
        if clip.audio is not None:
            clip.audio.write_audiofile(audio_file, logger=None)
    else:
        #ERROR. NO NON VIDEO OR AUDIO SHOULD HAVE MADE IT HERE.
        raise AssertionError()

    if args['force_og_lang'] == 'auto':
        og_lang = detect_language(audio_file, args, model)
    else:
        og_lang = args['force_og_lang']

    options = {}
    options['language'] = og_lang

    result = whisper.transcribe(model, audio_file, verbose=False, **options)
    return result['text'], og_lang



def translate_string(og_result, args, language):
    """takes in a string, returns a transcription string in the given language"""
    print(f"Translating from {language} to {args['translation_lang']}")
    if not og_result:
        return ""
    result = translator.translate(text=og_result, dest=args['translation_lang'], src=language)
    result = result.text
    return result



def process_file(file_path, args, model):
    og_result, og_lang = transcribe_file(file_path, args, model)
    print(f"OG LANG: {og_lang}, OG LANG RESULT: {og_result}")

    if args["translation_lang"] == og_lang:
        translation_result = og_result
    else:
        translation_result = translate_string(og_result, args, og_lang)

    trans_lang = args["translation_lang"]
    print(f"TRANS LANG: {trans_lang}, TRANS RESULT: {translation_result}")

    df_row = format_data(file_path, trans_lang, og_result, og_lang, translation_result)
    return df_row
    

