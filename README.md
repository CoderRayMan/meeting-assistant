# Meeting Assistant Application
### Authors : Ankshuk Ray , Debarati Bannerjee
## Major Branches: 
    - main : this contains the ai assistant code assuming the translation and transcription is done.
    - dummy_meeting_application : this contains code of a dummy meeting application with transation and trancription ability.
## Setup:
    - run pip install -r requirements.txt
    - The application uses "Gemini" as LLM so follow thw Gemini config steps to get gemini config ready.
    - .run folder contains a set of configurations that gets aotu imported in PYCHARM.
    - the configurations has one server and three clients.
    - add a 'config.json' to the root
## Points to consider:
    - the application assumes the transcripts are done.
    - as a part of the application the transcription dummy is created manually by typing the transcription as it would come from the real time transcriber.
    - in the branch  "-b dummy_meeting_application" a sample code is provided to see how a real-time call can be translated and transcribed.
## Configuring Gemini :
    - Open 'https://aistudio.google.com/app/apikey' create a free API key.
    - Place a variable in the config JSON as "GEMINI_API_KEY".
-----
### config.json
```json
{

"GEMINI_API_KEY":"<Your Google-API key>",

"azure_speech_key":"Azure Speech Studio Key (Only to be used for the Dummy Meeting application)",

"azure_loc":"Azure location code (Only to be used for the Dummy Meeting application)",
"gcp_key_loc": ""

} 
```

