from openai import OpenAI
import time
from pygame import mixer
import os
from dotenv import load_dotenv
import httpx
from httpx import HTTPTransport

# Load environment variables from .env file
load_dotenv()

#https://platform.openai.com/playground/assistants
# Initialize the client and mixer


# Fetch API key from environment variables
api_key = os.getenv('API_KEY')

# Configure the proxy
proxy_url = os.getenv("PROXY")

# Create a custom transport with the proxy configuration
transport = httpx.HTTPTransport(proxy=httpx.Proxy(url=proxy_url))

# Initialize the custom HTTP client with the transport
http_client = httpx.Client(transport=transport)

# Initialize the OpenAI client
client = OpenAI(
    default_headers={"OpenAI-Beta": "assistants=v2"},
    api_key=api_key,
    http_client=http_client
)

mixer.init()



# Retrieve the assistant and thread
assistant = client.beta.assistants.retrieve(os.getenv('ASSISTANT_ID'))

client.beta.assistants.update(
    assistant_id=assistant.id,
    tool_resources={"file_search": {"vector_store_ids": []}}
)

thread = client.beta.threads.retrieve(thread_id=os.getenv('THREAD_ID'))
# thread = client.beta.threads.create()

def ask_question_memory(question):
    global thread
    client.beta.threads.messages.create(thread.id, role="user", content=question)
    run = client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant.id)
    
    while (run_status := client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)).status != 'completed':
        if run_status.status == 'failed':
            return "The run failed."
        time.sleep(1)
    
    messages = client.beta.threads.messages.list(thread_id=thread.id)
    return messages.data[0].content[0].text.value

def generate_tts(sentence, speech_file_path):
    response = client.audio.speech.create(model="tts-1", voice="echo", input=sentence)
    response.stream_to_file(speech_file_path)
    return str(speech_file_path)

def play_sound(file_path):
    mixer.music.load(file_path)
    mixer.music.play()

def TTS(text):
    speech_file_path = generate_tts(text, "speech.mp3")
    play_sound(speech_file_path)
    while mixer.music.get_busy():
        time.sleep(1)
    mixer.music.unload()
    os.remove(speech_file_path)
    return "done"

if __name__ == "__main__":
    question = "make it slightly vary every time"
    response = ask_question_memory(question)
    print(response)