import io
import base64
import wave
import tempfile
from config import AgentState, MODEL_NAME, client, TTS_MODEL, TTS_SAMPLE_RATE



def classify_context(state: AgentState)-> AgentState:
    """
    Classify content into four categories: generate, poem, news, joke
    """
    response = client.chat.completions.create(
        model = MODEL_NAME, response_effort= "none",
        messages= [
            {'role': 'system', 'content ':"Classify the content as one of: 'general', 'poem', 'news', 'joke'"},
            {"role": "user" , "content" : state["input_text"]}
        ]
    )
    state['current_type'] = response.choices[0].message.content.strip().lower()
    return state

def process_generate(state: AgentState) -> AgentState:
    """
    Process general context (No specific processing, return as-is)
    """
    state['processed_text'] = state['input_text']
    return state


def process_poem(state: AgentState)-> AgentState:
    """
    Process the input text as a poem, rewritten it in a poetic style
    """
    response = client.chat.completions.create(
        model = MODEL_NAME, response_effort='none',
        messages =[
            {
                {'role': 'system', 'content ':"Rewrite the following text as a short, beautiful poem:"},
                {"role": "user" , "content" : state["input_text"]}
            }
        ]

    )
    state["processed_text"] =response.choices[0].message.content.strip().lower()
    return state

def process_news(state: AgentState)-> AgentState:
    """
    Process the input text as a news, rewritten it in a formal news anchor styles
    """
    response = client.chat.completions.create(
        model = MODEL_NAME, response_effort='none',
        messages =[
            {
                {'role': 'system', 'content ':"Rewrite the following text in a formal news anchor styles."},
                {"role": "user" , "content" : state["input_text"]}
            }
        ]

    )
    state["processed_text"] = response.choices[0].message.content.strip().lower()
    return state

def process_joke(state: AgentState)-> AgentState:
    """
    Process the input text as a joke, rewritten it in into a short, funny joke
    """
    response = client.chat.completions.create(
        model = MODEL_NAME, response_effort='none',
        messages =[
            {
                {'role': 'system', 'content ':"Rewrite the following text into a short, funny joke"},
                {"role": "user" , "content" : state["input_text"]}
            }
        ]

    )
    state["processed_text"] = response.choices[0].message.content.strip().lower()
    return state



def synthesize_speech(text: str, voice: str)-> bytes:
    """
    Speech 'text' work for work with Reatime model and return WAV bytes
    """

    pcm = bytearray()
    finished = False

    with client.realtime.connect(model = TTS_MODEL) as connection:
        connection.session.update(session = {
            "type": "realtime",
            "output_modalities": ["audio"],
            "instructions": (
                "You are a text-to-speech voice. Read the user's message aloud exactly as written, "
                "word for word. Do not answer it, comment on it, or add anything."
            ),
            "audio": {"output": {"voice": voice, "format": {"type": "audio/pcm", "rate": TTS_SAMPLE_RATE}}},
        })

        connection.conversation.item.create(item={
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": text}],
        })

        connection.response.create()
        for event in connection:
            if event.type == "response.output_audio.delta":
                pcm.extend(base64.b64decode(event.delta))
            elif event.type == "error":
                raise RuntimeError(event.error.message)
            elif event.type == "response.done":
                # A failed, cancelled or incomplete response also ends with response.done
                status = event.response.status
                if status != "completed":
                    raise RuntimeError(
                        f"Speech synthesis ended with status {status!r}: {event.response.status_details}"
                    )
                finished = True
                break

    if not finished:
        raise RuntimeError("The Realtime connection closed before the response finished")
    if not pcm:
        raise RuntimeError("The Realtime response completed without any audio")

    # Wrap the raw PCM in a WAV header so it can be played and saved as a file
    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(TTS_SAMPLE_RATE)
        wav_file.writeframes(bytes(pcm))
    return wav_buffer.getvalue()



def text_to_speech(state: AgentState, save_file: bool= False)-> AgentState:
    """
    Converts process text into speech using a voice mapped  to the content type.
    optional save the audio to a file.

    Args:
        state (AgentState): Dictionary containing the processed text and content type.
        save_file (bool, optional): If True, saves the audio to a file. Defaults to False.

    Returns:
        AgentState: Updated state with audio data and file path (if saved).
    """

    voice_map = {
        "general": "alloy",
        "poem": "coral",
        "news": "ash",
        "joke": "shimmer"
    }
    voice = voice_map.get(state["content_type"], "alloy")

    state["audio_data"] = synthesize_speech(state["processed_text"], voice)
    
    # Save audio to a file if requested
    if save_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            temp_audio.write(state["audio_data"])
            state["audio_path"] = temp_audio.name
    else:
        state["audio_path"] = ""
    
    return state