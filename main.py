import json
import requests
import webbrowser
import pyaudio
from vosk import Model, KaldiRecognizer


MODEL_PATH = r"F:\codework\vosk-model-small-en-us-0.15"
API_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"

audio = pyaudio.PyAudio()
model = Model(MODEL_PATH)
recognizer = KaldiRecognizer(model, 16000)

stream = audio.open(
    format=pyaudio.paInt16,
    channels=1,
    rate=16000,
    input=True,
    frames_per_buffer=4096
)
stream.start_stream()

# 保存当前查询的单词数据
current_word = None

def speak(text):
    import pyttsx3
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    # 选择英文语音
    voices = engine.getProperty('voices')
    for voice in voices:
        if 'en' in str(voice.languages):
            engine.setProperty('voice', voice.id)
            break
    engine.say(text)
    engine.runAndWait()
    engine.stop()

def get_word_data(word):
    """从词典API获取单词数据"""
    global current_word
    try:
        url = API_URL + word.lower()
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()[0]
        meanings = data["meanings"][0]
        definition = meanings["definitions"][0]["definition"]
        example = meanings["definitions"][0].get("example", "No example available.")
        current_word = {
            "word": data["word"],
            "phonetic": data.get("phonetic", ""),
            "definition": definition,
            "example": example,
            "url": f"https://dictionaryapi.dev/?q={word.lower()}"
        }
        return True
    except Exception as e:
        print(f"API Error: {e}")
        current_word = None
        return False

def save_word():
    """保存单词信息到文件"""
    if not current_word:
        return False
    try:
        with open("word_list.txt", "a", encoding="utf-8") as f:
            f.write(f"{current_word['word']}: {current_word['definition']}\n")
        return True
    except:
        return False

def process_command(command_text):
    global current_word
    text = ""
    command_parts = command_text.split()

    # 1. 查找单词
    if len(command_parts) >= 2 and command_parts[0] == "find":
        word = command_parts[1]
        if get_word_data(word):
            text = f"Found definition for {current_word['word']}."
        else:
            text = "Word not found."

    # 2. 读单词释义
    elif command_text == "meaning":
        if current_word:
            text = current_word["definition"]
        else:
            text = "Please find a word first."

    # 3. 读例句
    elif command_text == "example":
        if current_word:
            text = current_word["example"]
        else:
            text = "Please find a word first."

    # 4. 打开词典链接
    elif command_text == "link":
        if current_word:
            webbrowser.open(current_word["url"])
            text = "Opening dictionary link."
        else:
            text = "Please find a word first."

    # 5. 保存单词
    elif command_text == "save":
        if save_word():
            text = "Word saved to file."
        else:
            text = "Failed to save word."

    else:
        text = "Command not recognized."

    print("Reply:", text)
    speak(text)


def main():
    print("Dictionary assistant started. Speak English commands.")
    try:
        while True:
            data = stream.read(4096)
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                command = result.get("text", "").strip()
                if command:
                    print("You said:", command)
                    process_command(command)
    except KeyboardInterrupt:
        print("\nAssistant stopped.")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()