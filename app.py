import base64

import openai
import requests
import streamlit as st

openai.api_key = st.secrets["OPEN_AI_KEY"]

# Streamlit UI
st.title("OpenAI API Examples with Streamlit")

mode = st.selectbox("モードを選択", options=["チャット", "画像生成", "画像入力"])


if mode == "チャット":
    # GPT-4 Turbo Example

    st.header("GPT-4 Turbo Text Completion")
    user_prompt = st.text_input("Enter your prompt for GPT-4 Turbo:")
    new_place = st.empty()
    text = ""
    if st.button("Generate Text"):
        if user_prompt:
            response = openai.chat.completions.create(
                model="gpt-4-1106-preview",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_prompt},
                ],
                stream=True,
            )
            for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    text += content
                    new_place.write(text)


if mode == "画像生成":
    # Image Generation Example
    st.header("Image Generation")
    image_prompt = st.text_input("Enter your prompt for image generation:")
    hight = st.number_input("hight", value=512, min_value=128)
    width = st.number_input("width", value=512, min_value=128)
    if st.button("Generate Image"):
        if image_prompt:
            response = openai.images.generate(
                prompt=image_prompt, size=f"{hight}x{width}", quality="standard", n=1
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
