🔊 Enhanced Voice Assistant with Gradio UI

This project implements a voice-enabled conversational AI assistant using:

    SpeechRecognition for capturing user speech

    gTTS + pygame for text-to-speech responses

    Transformers (Hugging Face) for:

        Sentiment analysis (distilbert)

        Text generation (distilgpt2)

    Wikipedia API for answering knowledge-based queries

    Gradio for an interactive web-based UI

💡 Key Features:

    Real-time speech recognition and response

    Intent detection (e.g., time, weather, joke, greetings, wiki)

    Sentiment analysis of user input

    Dynamic response generation via NLP

    Voice playback using gTTS + pygame

    Interactive Gradio interface with visual listening/speaking indicators

🧠 Main Components:

    EnhancedVoiceAssistant: Core class handling speech, NLP, logic

    create_enhanced_interface(): Builds the Gradio UI for real-time use

    Threaded speaking and listening for smoother UX

✅ Usage:

Run the script to launch a web-based voice assistant interface that listens to the user, understands intent, generates context-aware responses, and speaks back—all in one loop.
