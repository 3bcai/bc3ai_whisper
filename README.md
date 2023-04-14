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
