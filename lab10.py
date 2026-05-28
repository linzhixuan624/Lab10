import json
import requests
import pyttsx3
import pyaudio
from vosk import Model, KaldiRecognizer


MODEL_PATH = r"F:\codework\vosk-model-small-en-us-0.15"
USER_API_URL = "https://randomuser.me/api/"

# 初始化音频与Vosk
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

current_user = None

# 语音播报（每次重新初始化，解决只响一次问题）
def speak(text):
    engine = pyttsx3.init()
    engine.setProperty('rate', 150)
    voices = engine.getProperty('voices')
    for v in voices:
        if 'en' in str(v.languages):
            engine.setProperty('voice', v.id)
            break
    engine.say(text)
    engine.runAndWait()
    engine.stop()

# 获取随机用户信息
def get_random_user():
    global current_user
    try:
        resp = requests.get(USER_API_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()["results"][0]
        current_user = {
            "name": f"{data['name']['first']} {data['name']['last']}",
            "country": data["location"]["country"],
            "gender": data["gender"],
            "age": data["dob"]["age"],
            "city": data["location"]["city"],
            "photo_url": data["picture"]["large"]
        }
        return True
    except Exception as e:
        print(e)
        return False

# 保存头像图片
def save_photo():
    if not current_user:
        return False
    try:
        resp = requests.get(current_user["photo_url"], timeout=10)
        with open("user_photo.jpg", "wb") as f:
            f.write(resp.content)
        return True
    except:
        return False

# 英文口令处理
def process_command(cmd):
    if "create" in cmd:
        if get_random_user():
            text = "User created."
        else:
            text = "Create failed."

    elif "name" in cmd:
        if current_user:
            text = current_user["name"]
        else:
            text = "No user yet."

    elif "country" in cmd:
        if current_user:
            text = current_user["country"]
        else:
            text = "No user yet."

    elif "profile" in cmd:
        if current_user:
            text = f"{current_user['name']}, {current_user['age']} years old."
        else:
            text = "No user yet."

    elif "save" in cmd:
        if save_photo():
            text = "Photo saved."
        else:
            text = "Save failed."

    else:
        text = "Command not recognized."

    print("Reply:", text)
    speak(text)

def main():
    print("Assistant started, use English commands.")
    try:
        while True:
            data = stream.read(4096)
            if recognizer.AcceptWaveform(data):
                res = json.loads(recognizer.Result())
                text = res.get("text", "").strip()
                if text:
                    print("You said:", text)
                    process_command(text)
    except KeyboardInterrupt:
        print("\nExit program.")
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

if __name__ == "__main__":
    main()