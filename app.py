import base64
import io

import openai
import requests
import streamlit as st
from PIL import Image, ImageOps
from streamlit_drawable_canvas import st_canvas


def image_config():
    col1, col2 = st.columns(2)

    with col1:
        size = st.selectbox("Size", options=["256x256", "512x512", "1024x1024"])
    with col2:
        num = st.number_input("Number of generation", step=1, min_value=1, max_value=5)

    if size == "256x256":
        height = 256
        width = 256
    elif size == "512x512":
        height = 512
        width = 512
    elif size == "1024x1024":
        height = 1024
        width = 1024

    return num, height, width


if "all_text" not in st.session_state:
    st.session_state.all_text = []

with st.sidebar:
    st.title("OpenAI API Examples")
    api_key = st.text_input("OPEN_AI_KEY", type="password")
    mode = st.selectbox("モードを選択", options=["チャット", "音声合成", "音声認識", "画像生成", "画像入力"])

if api_key:
    openai.api_key = api_key

    if mode == "チャット":
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
        audio_prompt = st.text_input("Enter your prompt:", key="audio_prompt")
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
        image_mode = st.selectbox(
            "Mode", options=["Generation", "In Painting", "Variation"]
        )

        if image_mode == "Generation":
            height = 1024
            width = 1024
            image_prompt = st.text_input("Enter your prompt:", key="image_prompt")

            if st.button("Generate Image"):
                if image_prompt:
                    response = openai.images.generate(
                        model="dall-e-3",
                        prompt=image_prompt,
                        size=f"{height}x{width}",
                        quality="standard",
                        n=1,
                    )
                    image_url = response.data[0].url
                    st.image(image_url)

        elif image_mode == "In Painting":
            num, height, width = image_config()
            image_prompt = st.text_input("Enter your prompt:", key="image_prompt")

            base_image = st.file_uploader("Image", ["jpg", "png"])
            col1, col2 = st.columns(2)
            if base_image:
                image = Image.open(base_image).convert("RGBA")
                image = image.resize((width, height))

                with col1:
                    st.write("Original")
                    st.image(image)

                fill_color = "rgba(255, 255, 255, 0.0)"
                stroke_width = st.number_input(
                    "Brush Size", value=64, min_value=1, max_value=100
                )
                stroke_color = "rgba(255, 255, 255, 1.0)"
                bg_color = "rgba(0, 0, 0, 1.0)"
                drawing_mode = "freedraw"

                with col2:
                    st.write("Mask")
                    canvas_result = st_canvas(
                        fill_color=fill_color,
                        stroke_width=stroke_width,
                        stroke_color=stroke_color,
                        background_color=bg_color,
                        background_image=image,
                        update_streamlit=True,
                        height=height,
                        width=width,
                        drawing_mode=drawing_mode,
                        key="canvas",
                    )
                if canvas_result:
                    mask = canvas_result.image_data
                    mask = Image.fromarray(mask.astype("uint8"), mode="RGBA")

                    inverted_mask = ImageOps.invert(mask.split()[3])
                    back_im = image.copy()
                    back_im.putalpha(inverted_mask)

                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    image = buffered.getvalue()

                    buffered.seek(0)
                    back_im.save(buffered, format="PNG")
                    mask_data = buffered.getvalue()

                    if st.button("Generate Image"):
                        response = openai.images.edit(
                            model="dall-e-2",
                            image=image,
                            mask=mask_data,
                            prompt=image_prompt,
                            n=num,
                            size=f"{height}x{width}",
                        )

                        images = [data.url for data in response.data]
                        for image_url in images:
                            st.image(image_url)

        elif image_mode == "Variation":
            num, height, width = image_config()

            base_image = st.file_uploader(
                "Upload an base image", type=["jpg", "jpeg", "png"]
            )
            if base_image:
                image = Image.open(base_image)
                image = image.resize((width, height))
                st.image(base_image)

                if st.button("Generate Image"):
                    response = openai.images.create_variation(
                        image=base_image,
                        n=num,
                        size=f"{height}x{width}",
                    )
                    images = [data.url for data in response.data]

                    for image_url in images:
                        st.image(image_url)

    if mode == "画像入力":
        uploaded_file = st.file_uploader(
            "Upload an image to analyze", type=["jpg", "jpeg", "png"]
        )
        input_image_prompt = st.text_input(
            "Enter your prompt:", key="input_image_prompt"
        )
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
        if st.button("Enter your prompt:"):
            if uploaded_file:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai.api_key}"},
                    json=payload,
                ).json()
                st.write(response["choices"][0]["message"]["content"])

    if mode == "音声認識":
        st.write("作成中⛏")

else:
    st.info("👈OPEN_AI_KEYを入力してください。")
