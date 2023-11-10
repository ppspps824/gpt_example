import base64
import io

import openai
import requests
import streamlit as st

if "all_text" not in st.session_state:
    st.session_state.all_text = []

with st.sidebar:
    st.title("OpenAI API Examples")
    api_key = st.text_input("OPEN_AI_KEY", type="password")
    mode = st.selectbox("モードを選択", options=["チャット", "音声合成", "画像生成", "画像入力"])

if api_key:
    openai.api_key = api_key

    if mode == "チャット":
        # GPT-4 Turbo Example
        st.header("GPT-4 Turbo チャット")
        user_prompt = st.chat_input("user:")
        assistant_text = ""

        for text_info in st.session_state.all_text:
            with st.chat_message(text_info["role"], avatar=text_info["role"]):
                st.write(text_info["role"] + ":\n\n" + text_info["content"])

        if user_prompt:
            with st.chat_message("user", avatar="user"):
                st.write("user" + ":\n\n" + user_prompt)

            st.session_state.all_text.append({"role": "user", "content": user_prompt})

            if len(st.session_state.all_text) > 10:
                st.session_state.all_text.pop(1)

            response = openai.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=st.session_state.all_text,
                stream=True,
            )
            with st.chat_message("assistant", avatar="assistant"):
                place = st.empty()
                for chunk in response:
                    content = chunk.choices[0].delta.content
                    if content:
                        assistant_text += content
                        place.write("assistant" + ":\n\n" + assistant_text)

            st.session_state.all_text.append(
                {"role": "assistant", "content": assistant_text}
            )

    if mode == "音声合成":
        st.header("音声合成")
        audio_prompt = st.text_input(
            "Enter your prompt:", value="エンジニアにとって再利用性・汎用性の高い情報が集まる場をつくろう"
        )
        model = st.selectbox("Model", options=["tts-1", "tts-1-hd"])
        voice = st.selectbox(
            "Voice", options=["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        )

        if audio_prompt:
            response = openai.audio.speech.create(
                model=model,
                voice=voice,
                input=audio_prompt,
            )

            # Convert the binary response content to a byte stream
            byte_stream = io.BytesIO(response.content)

            st.audio(byte_stream)

    if mode == "画像生成":
        # Image Generation Example
        st.header("画像生成")
        image_prompt = st.text_input("Enter your prompt:")
        hight = st.number_input("hight", value=512, min_value=128)
        width = st.number_input("width", value=512, min_value=128)
        if st.button("Generate Image"):
            if image_prompt:
                response = openai.images.generate(
                    prompt=image_prompt,
                    size=f"{hight}x{width}",
                    quality="standard",
                    n=1,
                )
                image_url = response.data[0].url
                st.image(image_url)

    if mode == "画像入力":
        # Image Input Example
        st.header("画像入力")
        uploaded_file = st.file_uploader(
            "Upload an image to analyze", type=["jpg", "jpeg", "png"]
        )
        input_image_prompt = st.text_input("Enter your prompt:")
        if uploaded_file:
            st.image(uploaded_file)
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": input_image_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64.b64encode(uploaded_file.getvalue()).decode()}"
                                },
                            },
                        ],
                    }
                ],
                "max_tokens": 300,
            }
        if st.button("Analyze Image"):
            if uploaded_file:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai.api_key}"},
                    json=payload,
                ).json()
                st.write(response["choices"][0]["message"]["content"])
else:
    st.info("👈OPEN_AI_KEYを入力してください。")
