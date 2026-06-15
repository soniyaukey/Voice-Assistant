import gradio as gr
import speech_recognition as sr
from gtts import gTTS
import os
import tempfile
from transformers import pipeline
from datetime import datetime
import random
import wikipedia
import warnings
import time
import pygame
import threading

# Suppress unnecessary warnings
warnings.filterwarnings("ignore")

# Initialize pygame for audio playback
pygame.mixer.init()


class EnhancedVoiceAssistant:
    def __init__(self):
        # Initialize speech recognition
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.is_speaking = False

        # Set up NLP models
        self.setup_nlp_models()

        # Conversation history
        self.conversation_history = []

    def setup_nlp_models(self):
        """Initialize NLP models with error handling"""
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english"
            )
            print(" Sentiment analyzer loaded")
        except Exception as e:
            print(f"Could not load sentiment analyzer: {e}")
            self.sentiment_analyzer = None

        try:
            self.text_generator = pipeline(
                "text-generation",
                model="distilgpt2"
            )
            print(" Text generator loaded")
        except Exception as e:
            print(f" Could not load text generator: {e}")
            self.text_generator = None

    def text_to_speech(self, text: str) -> str:
        """Convert text to speech using gTTS"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(fp.name)
                return fp.name
        except Exception as e:
            print(f"Error in TTS: {e}")
            return None

    def play_audio(self, audio_file: str):
        """Play audio file and clean up"""
        try:
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.music.unload()
        finally:
            try:
                os.unlink(audio_file)
            except:
                pass

    def speak(self, text: str) -> str:
        """Speak text with visual feedback"""
        self.is_speaking = True
        audio_file = self.text_to_speech(text)
        if audio_file:
            self.play_audio(audio_file)
        self.is_speaking = False
        return "Speaking complete" if audio_file else " TTS failed"

    def listen(self, duration: int = 5) -> tuple:
        """Listen with visual feedback"""
        self.is_listening = True
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio = self.recognizer.listen(source, timeout=duration, phrase_time_limit=10)

            text = self.recognizer.recognize_google(audio)
            status = " Speech recognized"
        except sr.WaitTimeoutError:
            text, status = "", " Listening timeout"
        except sr.UnknownValueError:
            text, status = "", " Could not understand audio"
        except sr.RequestError as e:
            text, status = "", f" API error: {str(e)}"
        except Exception as e:
            text, status = "", f" Error: {str(e)}"

        self.is_listening = False
        return text, status

    def detect_intent(self, text: str) -> str:
        """Enhanced intent detection"""
        text = text.lower()
        if not text:
            return "unknown"

        if any(word in text for word in ["time", "clock"]):
            return "time"
        elif any(word in text for word in ["weather", "temperature"]):
            return "weather"
        elif any(word in text for word in ["joke", "funny"]):
            return "joke"
        elif any(word in text for word in ["wikipedia", "what is", "who is"]):
            return "wiki"
        elif any(word in text for word in ["hello", "hi", "hey"]):
            return "greeting"
        elif "your name" in text:
            return "name"
        else:
            return "general"

    def generate_response(self, text: str) -> tuple:
        """Generate contextual response"""
        intent = self.detect_intent(text)

        # Sentiment analysis
        sentiment = {"label": "neutral", "score": 0.0}
        if self.sentiment_analyzer:
            try:
                sentiment = self.sentiment_analyzer(text)[0]
            except:
                pass

        metadata = {
            "intent": intent,
            "sentiment": sentiment,
            "timestamp": datetime.now().isoformat()
        }

        # Generate response based on intent
        if intent == "time":
            response = f"It's {datetime.now().strftime('%I:%M %p')} right now."
        elif intent == "joke":
            jokes = [
                "Why did the scarecrow win an award? Because he was outstanding in his field!",
                "What do you call a fake noodle? An impasta!",
                "How do you organize a space party? You planet!"
            ]
            response = random.choice(jokes)
        elif intent == "greeting":
            response = random.choice([
                "Hello there! How can I help you today?",
                "Hi! What can I do for you?",
                "Hey! Nice to talk to you."
            ])
        elif intent == "name":
            response = "I'm your friendly voice assistant!"
        elif intent == "wiki":
            try:
                query = text.replace("wikipedia", "").replace("what is", "").strip()
                if query:
                    summary = wikipedia.summary(query, sentences=2)
                    response = f"Here's what I found: {summary}"
                else:
                    response = "What would you like me to look up?"
            except:
                response = "Sorry, I couldn't find information about that."
        else:
            if self.text_generator:
                try:
                    generated = self.text_generator(
                        text,
                        max_length=60,
                        num_return_sequences=1,
                        temperature=0.7
                    )
                    response = generated[0]['generated_text']
                except:
                    response = "I'm happy to help with anything you need!"
            else:
                response = "How can I assist you today?"

        return response, metadata

    def converse(self, duration: int = 5) -> dict:
        """Complete conversation cycle"""
        # Listen phase
        user_input, listen_status = self.listen(duration)

        if not user_input:
            return {
                "user_input": "",
                "response": "I didn't catch that. Could you repeat?",
                "listen_status": listen_status,
                "speak_status": ""
            }

        # Generate response
        response, metadata = self.generate_response(user_input)

        # Store conversation
        self.conversation_history.append({
            "user": user_input,
            "assistant": response,
            "metadata": metadata
        })

        # Speak response (in background)
        def speak_in_thread():
            self.speak(response)

        speak_thread = threading.Thread(target=speak_in_thread)
        speak_thread.start()

        return {
            "user_input": user_input,
            "response": response,
            "listen_status": listen_status,
            "speak_status": "🔊 Speaking...",
            "is_listening": False,
            "is_speaking": True
        }


def create_enhanced_interface():
    """Create Gradio interface with improved UI"""
    assistant = EnhancedVoiceAssistant()

    css = """
    .listening { animation: pulse 1.5s infinite; }
    .speaking { animation: pulse 1s infinite; }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
    .user-text { color: #4a6fa5; }
    .assistant-text { color: #6a4a8c; }
    """

    with gr.Blocks(css=css, title="Enhanced Voice Assistant") as demo:
        gr.Markdown("""
        # 🎤 Enhanced Voice Assistant
        A conversational AI with natural speech capabilities
        """)

        with gr.Row():
            with gr.Column(scale=1):
                duration_slider = gr.Slider(3, 10, value=5, label="Listening Duration (sec)")
                start_btn = gr.Button("🎙 Start Conversation", variant="primary")

                # Visual indicators
                listening_indicator = gr.HTML(
                    "<div id='listen-indicator'>🔴 Ready</div>"
                )
                speaking_indicator = gr.HTML(
                    "<div id='speak-indicator'>🔵 Silent</div>"
                )

            with gr.Column(scale=2):
                # Conversation display
                conversation = gr.Chatbot(
                    label="Conversation",
                    bubble_full_width=False
                )

                # Status displays
                status_display = gr.Textbox(
                    label="Status",
                    interactive=False,
                    placeholder="System messages will appear here..."
                )

        # State components
        current_state = gr.State({
            "is_listening": False,
            "is_speaking": False
        })

        def update_ui(user_input, response, listen_status, speak_status, state):
            """Update all UI components"""
            # Update conversation
            conversation_update = [(user_input, response)] if user_input else []

            # Update indicators
            listen_class = "listening" if state["is_listening"] else ""
            speak_class = "speaking" if state["is_speaking"] else ""

            listen_html = f"<div class='{listen_class}'>🔴 {'Listening...' if state['is_listening'] else 'Ready'}</div>"
            speak_html = f"<div class='{speak_class}'>🔵 {'Speaking...' if state['is_speaking'] else 'Silent'}</div>"

            return {
                conversation: conversation_update,
                status_display: listen_status,
                listening_indicator: listen_html,
                speaking_indicator: speak_html,
                current_state: state
            }

        def conversation_handler(duration):
            """Handle full conversation cycle"""
            result = assistant.converse(duration)
            return update_ui(
                result["user_input"],
                result["response"],
                result["listen_status"],
                result["speak_status"],
                {
                    "is_listening": assistant.is_listening,
                    "is_speaking": assistant.is_speaking
                }
            )

        # Event handlers
        start_btn.click(
            fn=conversation_handler,
            inputs=[duration_slider],
            outputs=[
                conversation,
                status_display,
                listening_indicator,
                speaking_indicator,
                current_state
            ]
        )

    return demo


if __name__ == "__main__":
    print(" Launching Enhanced Voice Assistant...")
    print(" First run may take time to download models")

    try:
        demo = create_enhanced_interface()
        demo.launch()
    except Exception as e:
        print(f"Error launching app: {e}")
