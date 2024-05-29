import streamlit as st
from openai import OpenAI
from audiorecorder import audiorecorder
import numpy as np
import os
from datetime import datetime
from gtts import gTTS
import base64

def STT(audio):
    filename = "input.mp3"
    wav_file = open(filename, "wb")
    wav_file.write(audio.tobytes())
    wav_file.close()

    audio_file = open(filename,"rb")
    transcript = client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                  )
    audio_file.close()

    os.remove(filename)
    return transcript["text"]

def ask_gpt(prompt, model):
    response = client.chat.completions.create(messages= prompt, model=model)
    system_messages = response.choices[0].message
    return system_messages.content

def TTS(response):
    filename = "output.mp3"
    tts = gTTS(text=response, lang='ko')
    tts.save(filename)

    with open(filename, 'rb') as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f"""
            <audio autoplay="True">
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
            </audio>
            """
        st.markdown(md, unsafe_allow_html=True,)
    os.remove(filename)

def main():
    st.set_page_config(
        page_title="Voice Chat Secretary"
        ,layout="wide"
    )

    st.header("Voice Chat Secretary")

    st.markdown("---")

    with st.expander("About VoiChat Secretary", expanded=True):
        st.write(
            """
            - The UI of the Voice Secretary program utilized streamlit.
            - STT utilized OpenAI's Whisper AI. 
            - The answers utilized OpenAI's GPT model. 
            - TTS utilized Google's Google Translate TTS. 
            """
        )
    
    st.markdown("")

    if "chat" not in st.session_state:
        st.session_state["chat"] = []

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role":"system",
            "content":"You are a thoughtful secretary. Respond to all input in 25 words an answer in korea"}]
    
    if "check_audio" not in st.session_state:
        st.session_state["check_audio"] = []

    with st.sidebar:

        OpenAI.api_key = st.text_input(label="OpenAI API Key"
                                       ,placeholder="Enter your API Key"
                                       ,value=""
                                       ,type="password")

        client = OpenAI.api_key

        st.markdown("---")

        model = st.radio(label="GPT Model", options=["gpt-4", "gpt-3.5-turbo"])

        st.markdown("---")

        if st.button(label="Reset"):
            st.session_state["chat"] = []
            st.session_state["messages"] = [{"role":"system",
                "content":"You are a thoughtful secretary. Respond to all input in 25 words an answer in korea"}]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("질문하기")
        audio = audiorecorder("click to record","recording...")
        if len(audio) > 0 and not np.array_equal(audio,
                        st.session_state["check_audio"]):
            st.audio(audio.tobytes())
            
            question = STT(audio)

            now = datetime.now().strftime("%H:%M")

            st.session_state["chat"] = st.session_state["chat"] + [("user", now, question)]

            st.session_state["messages"] = st.session_state["messages"] + [{"role":"user","content":question}]
    
            st.session_state["check_audio"] = audio
            
            flag_start = True

    with col2:
        st.subheader("질문/답변")

        if flag_start:
            response = ask_gpt(st.session_state["messages"],model)
            st.session_state["messages"] = st.session_state["messages"] + [{"role":"system","content":response}]
            now = datetime.now().strftime("%H:%M")
            st.session_state["chat"] = st.session_state["chat"] + [("bot", now, response)]

            for sender, time, message in st.session_state["chat"]:
                if sender == "user":
                    st.write(f'<div style="display:flex;align-items:center;"><div style="background-clor:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',unsafe_allow_html=True)
                    st.write("")
                else:
                     st.write(f'<div style="display:flex;align-items:center;justify-content:flex-end;"><div style="background-clor:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div><div style="font-size:0.8rem;color:gray;">{time}</div></div>',unsafe_allow_html=True)
                     st.write("")
    
            TTS(response)

if __name__=="__main__":
    main()