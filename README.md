# transcription
for transcribing audio

Can run two ways. In the CLI which takes in entire directories or files of video or audio, and creates a csv - or by importing the function BC3AI_transcribe from main.py

csv format:
- file name | original language | translated language | translated transcription | original transcription


function use example:
```
from transcription import BC3AI_transcribe

results_dict = BC3AI_transcribe("path/to/audio/or/video_file.mp4")
```

NEED .ENV WITH:
 - DEEPL_KEY
 - DEEPL_API_DOMAIN

ALL ARGUEMENTS:

"dir", type=str, help="path to a directory of videos, to a audio or video file, or to a output folder to continue from. If continuation, do not feed any other arguements"
"--model", default="large-v2", help="name of the Whisper model to use"
"--device", default="cuda" if torch.cuda.is_available() else "cpu", help="device to use for PyTorch inference"
"--translation-lang", default="EN-US", help=f"language to translate to. must be one of the following: \n {[lang.code for lang in translator.get_target_languages()]}", choices=[lang.code for lang in translator.get_target_languages()])
"--force-og-lang", default="auto", help="override Whispers auto detection of language with a given shorthand lang representation. Ex: en")
"--ultra-off", action='store_true',help="Use this arg to use the faster translation")
'--timestamps',action='store_true',help="output timestamps in the resulting csv")
'--confidence-scores',action='store_true',help="output confidence scores in the resulting csv")
'--output-format', nargs='+',choices=["csv", "json"], default=["csv, json"])

If using the function you can use them when you call the function. Example:
```
from transcription import BC3AI_transcribe

results_dict = BC3AI_transcribe("path/to/audio/or/video_file.mp4", force_og_lang="ZH")
