import base64
import io
import os
from tempfile import NamedTemporaryFile

import openai
import requests
import streamlit as st
from PIL import Image, ImageOps
from st_audiorec import st_audiorec
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
    mode = st.selectbox("モードを選択", options=["チャット", "音声合成", "音声認識", "画像生成", "画像認識"])

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
            with st.spinner("生成中..."):
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
            "Mode", options=["Generation", "In Painting", "Variation", "Upgrade"]
        )

        if image_mode == "Generation":
            height = 1024
            width = 1024
            image_prompt = st.text_input("Enter your prompt:", key="image_prompt")

            if st.button("Generate Image"):
                if image_prompt:
                    with st.spinner("生成中..."):
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
                        with st.spinner("生成中..."):
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
            image = st.file_uploader(
                "Upload an base image", type=["jpg", "jpeg", "png"]
            )
            if image:
                st.image(image)
                image = Image.open(image)
                image = image.resize((width, height))

            if st.button("Generate Image"):
                if image:
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    image = buffered.getvalue()
                    with st.spinner("生成中..."):
                        response = openai.images.create_variation(
                            image=image,
                            n=num,
                            size=f"{height}x{width}",
                        )
                        images = [data.url for data in response.data]

                        for image_url in images:
                            st.image(image_url)

        elif image_mode == "Upgrade":
            height = 1024
            width = 1024
            drawing_mode = st.selectbox("Drawing tool:", ("freedraw", "transform"))
            stroke_width = st.slider("Stroke width: ", 1, 25, 3)

            if drawing_mode == "point":
                point_display_radius = st.slider("Point display radius: ", 1, 25, 3)
            stroke_color = st.color_picker("Stroke color hex: ")
            bg_color = st.color_picker("Background color hex: ", "#eee")
            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 1.0)",  # Fixed fill color with some opacity
                stroke_width=stroke_width,
                stroke_color=stroke_color,
                background_color=bg_color,
                update_streamlit=True,
                height=512,
                width=512,
                drawing_mode=drawing_mode,
                point_display_radius=point_display_radius
                if drawing_mode == "point"
                else 0,
                key="canvas",
            )
            if canvas_result:
                image = canvas_result.image_data
                image = Image.fromarray(image.astype("uint8"), mode="RGBA")

            title = st.text_input("title:")
            color=st.selectbox("Color",options=["モノクロ","カラー"])
            style = st.selectbox("Style",options=["イラスト","写真","アイコン","絵画"])
            num = st.number_input("Number of generation", step=1, min_value=1, max_value=5)

            if st.button("Upgrade Image"):
                if image:
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    image = buffered.getvalue()
                    base_prompt = """
                    instructions:入力された画像と説明を理解し、より詳細な画像を生成するためのプロンプトテキストを生成すること。画像が非常に簡素なものであってもできる限りの特徴を捉え、最大限に想像力を働かせて表現してください。
                    例えば、描かれているものが人物が動物か無機物か、性別、年齢、数、向き、時間帯、屋外か室内か、天気、季節、雰囲気など。
                    attention:説明等は不要ですので、必ずプロンプトテキストのみ出力してください。
                    """
                    payload = {
                        "model": "gpt-4-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": base_prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{base64.b64encode(image).decode()}"
                                        },
                                    },
                                ],
                            }
                        ],
                        "max_tokens": 300,
                    }
                    with st.spinner("生成中..."):
                        response = requests.post(
                            "https://api.openai.com/v1/chat/completions",
                            headers={"Authorization": f"Bearer {openai.api_key}"},
                            json=payload,
                        ).json()
                        response_text = response["choices"][0]["message"]["content"]
                        image_prompt=f"""
                        title:{title}
                        details:{response_text}
                        style:{style}
                        color:{color}
                        """
                        st.write(image_prompt)
                        response = openai.images.generate(
                            model="dall-e-3",
                            prompt=image_prompt,
                            size=f"{height}x{width}",
                            quality="standard",
                            n=num
                        )
                        images = [data.url for data in response.data]

                        for image_url in images:
                            st.image(image_url)

    if mode == "画像認識":
        uploaded_file = st.file_uploader(
            "Upload an image to analyze", type=["jpg", "jpeg", "png"]
        )
        base_prompt = "Please describe in detail what the image looks like.Look carefully at the number of objects, type (human, animal, object, etc.), expression, background, location, country, brightness, weather and time of day, indoor or outdoor, period, and atmosphere."
        input_image_prompt = st.text_area(
            "Enter your prompt:", key="input_image_prompt", value=base_prompt
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
        if st.button("Submit"):
            if uploaded_file:
                with st.spinner("生成中..."):
                    response = requests.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai.api_key}"},
                        json=payload,
                    ).json()
                    st.write(response["choices"][0]["message"]["content"])

    if mode == "音声認識":
        audio_mode = st.selectbox("Mode", options=["Recording", "File"])

        if audio_mode == "Recording":
            wav_audio_data = st_audiorec()
        elif audio_mode == "File":
            if upload_file := st.file_uploader("Audio", ["mp3", "wav"]):
                st.audio(upload_file)
                wav_audio_data = upload_file.getvalue()

        if st.button("Submit"):
            if wav_audio_data:
                with NamedTemporaryFile(
                    delete=False, suffix=f".{upload_file.type.split('/')[1]}"
                ) as temp_file:
                    temp_file.write(wav_audio_data)
                    temp_file.flush()

                    with open(temp_file.name, "rb") as audio_file:
                        with st.spinner("生成中..."):
                            transcript = openai.audio.transcriptions.create(
                                model="whisper-1",
                                file=audio_file,
                                response_format="text",
                            )
                            st.write(transcript)

else:
    st.info("👈OPEN_AI_KEYを入力してください。")
