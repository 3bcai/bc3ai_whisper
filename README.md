# transcription
for transcribing directories or files of audio or video. 

## Differences between bc3ai_whisper and normal whisper

 - Addresses the main shortcomings of raw Whisper usage. Splits audio into 30 second clips (can be changed by changing "n" variable) to prevent model hallucinations ruining a transcript.
 - When translating language, scans the entire clip and takes average prediction to determine language instead of only first 30 seconds like normal Whisper.
 - Works on entire directories of audio or video.
 - Outputs with checkpoints to a output folder containing cleaned results in csv or JSON format.
 - Can be imported as a function or ran in CLI
 - Utilizes DeepL for much higher quality translations, instead of Whispers subpar translator. 

Can run two ways. In the CLI which takes in entire directories or files of video or audio, and creates a csv - or by importing the function BC3AI_transcribe from main.py

csv format:
- file name | original language | translated language | translated transcription | original transcription


## Examples:

cli main use example from root dir:
```
python main.py path/to/dir/of/videos/or/audio --timestamps --force-og-lang EN
```
If using the function you can use them when you call the function. Example:
```
from bc3ai_whisper import BC3AI_transcribe

results_dict = BC3AI_transcribe("path/to/audio/or/video_file.mp4", force_og_lang="ZH")
```
## Install
 - pip install requirements.txt

## Requirements
 - Python 3.9 (Does not work with 3.11 and above for now because of Whisper limitations)
 - NEED .ENV WITH:
   - DEEPL_KEY
   - DEEPL_API_DOMAIN


ALL ARGUEMENTS:
```
"dir", type=str, help="path to a directory of videos, to a audio or video file, or to a output folder to continue from. If continuation, do not feed any other arguements"
"--model", default="large-v2", help="name of the Whisper model to use"
"--device", default="cuda" if torch.cuda.is_available() else "cpu", help="device to use for PyTorch inference"
"--translation-lang", default="EN-US", help=f"language to translate to. must be one of the following: \n {[lang.code for lang in translator.get_target_languages()]}", choices=[lang.code for lang in translator.get_target_languages()])
"--force-og-lang", default="auto", help="override Whispers auto detection of language with a given shorthand lang representation. Ex: en")
"--ultra-off", action='store_true',help="Use this arg to use the faster translation")
'--timestamps',action='store_true',help="output timestamps in the resulting csv")
'--confidence-scores',action='store_true',help="output confidence scores in the resulting csv")
'--output-format', nargs='+',choices=["csv", "json"], default=["csv, json"])
```



