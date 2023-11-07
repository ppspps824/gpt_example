import base64

import openai
import requests
import streamlit as st

# openai.api_key = st.secrets["OPEN_AI_KEY"]

if "all_text" not in st.session_state:
    st.session_state.all_text = []

with st.sidebar:
    st.title("OpenAI API Examples")
    api_key = st.text_input("OPEN_AI_KEY")
    mode = st.selectbox("モードを選択", options=["チャット", "画像生成", "画像入力"])

if api_key:
    openai.api_key = api_key

    if mode == "チャット":
        # GPT-4 Turbo Example
        st.header("GPT-4 Turbo Text Completion")
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

    if mode == "画像生成":
        # Image Generation Example
        st.header("Image Generation")
        image_prompt = st.text_input("Enter your prompt for image generation:")
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
        st.header("Image Input")
        uploaded_file = st.file_uploader(
            "Upload an image to analyze", type=["jpg", "jpeg", "png"]
        )
        prompt = st.text_input("Enter your prompt for GPT-4 Vision:")
        if uploaded_file:
            st.image(uploaded_file)
            payload = {
                "model": "gpt-4-vision-preview",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
    st.info("OPEN_AI_KEYを入力してください。")
