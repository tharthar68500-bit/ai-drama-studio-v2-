import os
import json
import time
import re
import urllib.request
import urllib.error

import streamlit as st
from gtts import gTTS
from google import genai
from google.genai import types


# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="AI Drama Studio",
    page_icon="🎬",
    layout="wide",
)

st.title("🎬 AI Drama / Story Studio")

st.caption(
    "Story → Character → Episode → Scene → Dialogue → Voice → Kling Video"
)


# =========================================================
# DATA
# =========================================================

DATA_FILE = "drama_data.json"
OUTPUT_DIR = "generated_media"

os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_data():

    if os.path.exists(DATA_FILE):

        try:
            with open(
                DATA_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception:
            pass

    return {
        "notebooks": {
            "ဇာတ်လမ်းအသစ် (Notebook 1)": {
                "volume": 1,
                "characters": [],
                "episodes": {}
            }
        }
    }


def save_data():

    with open(
        DATA_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            st.session_state.data,
            f,
            ensure_ascii=False,
            indent=2
        )


if "data" not in st.session_state:

    st.session_state.data = load_data()


# =========================================================
# GEMINI HELPERS
# =========================================================

def get_client(api_key):

    return genai.Client(
        api_key=api_key.strip()
    )


def extract_json(text):

    text = (text or "").strip()

    if text.startswith("```"):

        text = re.sub(
            r"^```(?:json)?",
            "",
            text
        ).strip()

        text = re.sub(
            r"```$",
            "",
            text
        ).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start >= 0 and end >= 0:

        return json.loads(
            text[start:end + 1]
        )

    start = text.find("[")
    end = text.rfind("]")

    if start >= 0 and end >= 0:

        return json.loads(
            text[start:end + 1]
        )

    raise ValueError(
        "AI response ထဲမှာ JSON မတွေ့ပါ"
    )


# =========================================================
# GEMINI STORY GENERATOR
# =========================================================

def generate_story(
    api_key,
    model_name,
    story,
    scene_count,
    language
):

    client = get_client(api_key)

    existing_characters = (
        st.session_state.current_nb
        .get("characters", [])
    )

    character_text = json.dumps(
        existing_characters,
        ensure_ascii=False,
        indent=2
    )

    prompt = f"""
You are an expert drama screenwriter and story continuity manager.

Create one drama episode from the user's story idea.

OUTPUT LANGUAGE:
{language}

NUMBER OF SCENES:
{scene_count}

EXISTING CHARACTER DATABASE:
{character_text}

IMPORTANT:

1. Keep existing character names consistent.
2. Keep age, personality, appearance and clothing consistent.
3. Keep relationships consistent.
4. If a new character appears, add the character.
5. Each scene must connect naturally to the previous scene.
6. Dialogue must be natural and suitable for voice generation.
7. Image Prompt must describe the exact characters in the scene.
8. Video Prompt must describe:
   - character action
   - facial expression
   - emotion
   - camera movement
   - environment
   - lighting
   - cinematic style
9. Video Prompt should be suitable for Kling AI.
10. Image Prompt and Video Prompt should be written in English.
11. Dialogue and voice_text must use the selected output language.
12. Return ONLY valid JSON.

JSON FORMAT:

{{
  "characters": [
    {{
      "name": "",
      "age": "",
      "gender": "",
      "personality": "",
      "appearance": "",
      "clothing": "",
      "relationship": ""
    }}
  ],

  "scenes": [

    {{
      "scene": 1,
      "location": "",
      "time": "",
      "characters": [],
      "action": "",

      "dialogue": [

        {{
          "character": "",
          "text": ""
        }}

      ],

      "voice_text": "",

      "image_prompt": "",

      "video_prompt": ""

    }}

  ]
}}

USER STORY:

{story}
"""

    response = client.models.generate_content(
        model=model_name,
        contents=prompt
    )

    return extract_json(
        response.text
    )


# =========================================================
# VOICE
# =========================================================

def generate_voice(
    text,
    filename
):

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    tts = gTTS(
        text=text,
        lang="my"
    )

    tts.save(path)

    return path


# =========================================================
# KLING API
# =========================================================

KLING_BASE_URL = (
    "https://api-singapore.klingai.com"
)


def kling_request(
    method,
    endpoint,
    api_key,
    payload=None
):

    url = (
        KLING_BASE_URL
        + endpoint
    )

    headers = {
        "Authorization":
            f"Bearer {api_key.strip()}",
        "Content-Type":
            "application/json"
    }

    data = None

    if payload is not None:

        data = json.dumps(
            payload,
            ensure_ascii=False
        ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method
    )

    try:

        with urllib.request.urlopen(
            request,
            timeout=60
        ) as response:

            raw = response.read().decode(
                "utf-8"
            )

            return json.loads(raw)

    except urllib.error.HTTPError as e:

        body = e.read().decode(
            "utf-8",
            errors="replace"
        )

        raise RuntimeError(
            f"Kling API HTTP {e.code}: {body}"
        )

    except urllib.error.URLError as e:

        raise RuntimeError(
            f"Kling API Connection Error: {e}"
        )


# =========================================================
# CREATE KLING TASK
# =========================================================

def create_kling_video(
    api_key,
    prompt,
    duration,
    aspect_ratio,
    model_name,
    mode,
    sound
):

    duration = int(duration)

    # Kling currently supports 3-15 seconds.
    if duration < 3:

        raise ValueError(
            "Kling API မှာ 1 second မရသေးပါ။ "
            "5 seconds သို့မဟုတ် 10 seconds ကိုရွေးပါ။"
        )

    if duration > 15:

        raise ValueError(
            "Kling API duration maximum က 15 seconds ဖြစ်ပါတယ်။"
        )

    payload = {

        "model_name":
            model_name,

        "prompt":
            prompt[:2500],

        "negative_prompt":
            "",

        "duration":
            str(duration),

        "mode":
            mode,

        "sound":
            sound,

        "aspect_ratio":
            aspect_ratio,

        "callback_url":
            "",

        "external_task_id":
            ""
    }

    result = kling_request(
        "POST",
        "/v1/videos/text2video",
        api_key,
        payload
    )

    code = result.get(
        "code"
    )

    if code not in (0, None):

        raise RuntimeError(
            "Kling Task Create Error: "
            + str(
                result.get(
                    "message",
                    result
                )
            )
        )

    data = result.get(
        "data"
    ) or {}

    task_id = data.get(
        "task_id"
    )

    if not task_id:

        raise RuntimeError(
            "Kling Task ID မရပါ။\n\n"
            + json.dumps(
                result,
                ensure_ascii=False,
                indent=2
            )
        )

    return task_id


# =========================================================
# CHECK KLING TASK
# =========================================================

def get_kling_video(
    api_key,
    task_id
):

    result = kling_request(
        "GET",
        f"/v1/videos/text2video/{task_id}",
        api_key
    )

    data = result.get(
        "data"
    ) or {}

    status = data.get(
        "task_status"
    )

    return status, data, result


# =========================================================
# WAIT KLING VIDEO
# =========================================================

def wait_for_kling_video(
    api_key,
    task_id
):

    started = time.time()

    timeout_seconds = 900

    progress = st.progress(0)

    status_box = st.empty()

    while True:

        if (
            time.time()
            - started
            > timeout_seconds
        ):

            raise TimeoutError(
                "Kling Video generation timeout ဖြစ်သွားပါပြီ။"
            )

        status, data, result = get_kling_video(
            api_key,
            task_id
        )

        if status == "succeed":

            progress.progress(100)

            status_box.success(
                "✅ Kling Video ပြီးပါပြီ။"
            )

            task_result = (
                data.get(
                    "task_result"
                )
                or {}
            )

            videos = (
                task_result.get(
                    "videos"
                )
                or []
            )

            if not videos:

                raise RuntimeError(
                    "Kling Video URL မရပါ။\n\n"
                    + json.dumps(
                        result,
                        ensure_ascii=False,
                        indent=2
                    )
                )

            video = videos[0]

            video_url = (
                video.get("url")
                or
                video.get("watermark_url")
            )

            if not video_url:

                raise RuntimeError(
                    "Kling Video URL မတွေ့ပါ။"
                )

            return video_url

        if status == "failed":

            message = (
                data.get(
                    "task_status_msg"
                )
                or
                result.get(
                    "message"
                )
                or
                "Unknown error"
            )

            raise RuntimeError(
                f"Kling Video Failed: {message}"
            )

        elapsed = int(
            time.time()
            - started
        )

        progress.progress(
            min(
                95,
                5 + int(
                    elapsed / 8
                )
            )
        )

        status_box.info(
            "🎬 Kling Video ထုတ်နေပါတယ်... "
            f"{status or 'processing'} "
            f"({elapsed}s)"
        )

        time.sleep(8)


# =========================================================
# KLING VIDEO GENERATOR
# =========================================================

def generate_kling_video(
    api_key,
    prompt,
    duration,
    aspect_ratio,
    model_name,
    mode,
    sound
):

    task_id = create_kling_video(
        api_key=api_key,
        prompt=prompt,
        duration=duration,
        aspect_ratio=aspect_ratio,
        model_name=model_name,
        mode=mode,
        sound=sound
    )

    return wait_for_kling_video(
        api_key,
        task_id
    )


# =========================================================
# GEMINI VEO
# =========================================================

def generate_veo_video(
    api_key,
    video_model,
    prompt,
    filename,
    aspect_ratio
):

    client = get_client(
        api_key
    )

    operation = (
        client.models.generate_videos(
            model=video_model,
            prompt=prompt,
            config=types.GenerateVideosConfig(
                aspect_ratio=aspect_ratio,
                resolution="720p",
                number_of_videos=1
            )
        )
    )

    progress = st.empty()

    while not operation.done:

        progress.info(
            "🎬 Gemini Veo Video ထုတ်နေပါတယ်..."
        )

        time.sleep(10)

        operation = (
            client.operations.get(
                operation
            )
        )

    progress.empty()

    generated_videos = (
        getattr(
            operation.response,
            "generated_videos",
            None
        )
        or []
    )

    if not generated_videos:

        raise RuntimeError(
            "Veo က Video result မပြန်ပေးပါ။"
        )

    generated_video = (
        generated_videos[0]
    )

    path = os.path.join(
        OUTPUT_DIR,
        filename
    )

    client.files.download(
        file=generated_video.video,
        destination=path
    )

    return path


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header(
    "🔑 API Settings"
)


# ---------------------------------------------------------
# GEMINI
# ---------------------------------------------------------

st.sidebar.subheader(
    "🟢 Gemini"
)

gemini_api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password"
)

gemini_model = st.sidebar.selectbox(
    "🧠 Story Model",
    [
        "gemini-3.8-flash",
        "gemini-3.7-flash",
        "gemini-3.1-pro-preview"
    ]
)

gemini_video_model = st.sidebar.selectbox(
    "🎬 Gemini Video Model",
    [
        "veo-3.1-generate-preview",
        "veo-3.1-lite-generate-preview"
    ]
)

gemini_ratio_label = (
    st.sidebar.selectbox(
        "📐 Gemini Video Ratio",
        [
            "16:9 — Landscape",
            "9:16 — Portrait"
        ],
        index=0
    )
)

gemini_aspect_ratio = (
    "16:9"
    if gemini_ratio_label.startswith("16:9")
    else "9:16"
)


# ---------------------------------------------------------
# KLING
# ---------------------------------------------------------

st.sidebar.markdown("---")

st.sidebar.subheader(
    "🟣 Kling API"
)

kling_api_key = st.sidebar.text_input(
    "Kling API Key",
    type="password",
    help="Kling Developer Platform မှ ရသော API Key"
)

kling_model = st.sidebar.selectbox(
    "Kling Video Model",
    [
        "kling-v3",
        "kling-v2-6"
    ]
)

kling_mode = st.sidebar.selectbox(
    "Kling Quality",
    [
        "std",
        "pro"
    ]
)

kling_sound = st.sidebar.selectbox(
    "Kling Sound",
    [
        "off",
        "on"
    ]
)

kling_default_ratio = st.sidebar.selectbox(
    "Kling Video Ratio",
    [
        "9:16",
        "16:9"
    ]
)

st.sidebar.info(
    "Gemini = Story / Dialogue\n\n"
    "Kling = Video"
)


# =========================================================
# NOTEBOOK
# =========================================================

st.sidebar.markdown("---")

st.sidebar.header(
    "📁 Notebooks"
)

notebook_names = list(
    st.session_state.data[
        "notebooks"
    ].keys()
)

selected_notebook = (
    st.sidebar.selectbox(
        "Notebook ရွေးပါ",
        notebook_names
    )
)

new_notebook = (
    st.sidebar.text_input(
        "➕ Notebook အသစ်"
    )
)

if st.sidebar.button(
    "Notebook ဖန်တီးမည်"
):

    if (
        new_notebook
        and
        new_notebook
        not in st.session_state.data[
            "notebooks"
        ]
    ):

        st.session_state.data[
            "notebooks"
        ][new_notebook] = {

            "volume": 1,

            "characters": [],

            "episodes": {}
        }

        save_data()

        st.rerun()


st.session_state.current_nb = (
    st.session_state.data[
        "notebooks"
    ][selected_notebook]
)

current_nb = (
    st.session_state.current_nb
)


# =========================================================
# MAIN HEADER
# =========================================================

st.subheader(
    f"📖 {selected_notebook} "
    f"— Episode {current_nb['volume']}"
)


# =========================================================
# TABS
# =========================================================

tab1, tab2, tab3, tab4 = st.tabs(
    [
        "✍️ Story",
        "👥 Characters",
        "🎬 Scenes",
        "🎙️ Voice / Video"
    ]
)


# =========================================================
# STORY TAB
# =========================================================

with tab1:

    story_input = st.text_area(
        "✍️ ဇာတ်လမ်းအကြမ်း",
        height=220,
        placeholder=(
            "ဥပမာ - ချမ်းသာတဲ့ မိန်းကလေးတစ်ယောက်က "
            "ဆင်းရဲတဲ့ ယောကျ်ားလေးကို အစပိုင်းမှာ "
            "အထင်သေးပေမယ့်..."
        )
    )

    col1, col2 = st.columns(2)

    with col1:

        scene_count = st.selectbox(
            "Scene အရေအတွက်",
            [
                5,
                10,
                15,
                30,
                50
            ],
            index=1
        )

    with col2:

        output_language = (
            st.selectbox(
                "Dialogue Language",
                [
                    "မြန်မာ",
                    "English",
                    "中文",
                    "ไทย"
                ]
            )
        )


    if st.button(
        "🚀 AI ဇာတ်လမ်း + Scene + Dialogue ထုတ်မည်",
        type="primary",
        use_container_width=True
    ):

        if not gemini_api_key:

            st.error(
                "Gemini API Key ထည့်ပါ။"
            )

        elif not story_input.strip():

            st.error(
                "ဇာတ်လမ်းအကြမ်းထည့်ပါ။"
            )

        else:

            try:

                with st.spinner(
                    "🤖 Gemini က ဇာတ်လမ်းတည်ဆောက်နေပါတယ်..."
                ):

                    result = generate_story(
                        gemini_api_key,
                        gemini_model,
                        story_input,
                        scene_count,
                        output_language
                    )


                # -----------------------------------------
                # CHARACTER DATABASE UPDATE
                # -----------------------------------------

                for character in (
                    result.get(
                        "characters",
                        []
                    )
                ):

                    old = next(
                        (
                            c
                            for c
                            in current_nb[
                                "characters"
                            ]
                            if c.get(
                                "name"
                            )
                            ==
                            character.get(
                                "name"
                            )
                        ),
                        None
                    )

                    if old:

                        old.update(
                            character
                        )

                    else:

                        current_nb[
                            "characters"
                        ].append(
                            character
                        )


                # -----------------------------------------
                # SAVE EPISODE
                # -----------------------------------------

                episode_number = (
                    current_nb[
                        "volume"
                    ]
                )

                current_nb[
                    "episodes"
                ][
                    str(episode_number)
                ] = {

                    "story_input":
                        story_input,

                    "scenes":
                        result.get(
                            "scenes",
                            []
                        )
                }

                save_data()

                st.success(
                    f"✅ Episode {episode_number} "
                    f"အတွက် "
                    f"{len(result.get('scenes', []))} "
                    f"Scenes ထွက်ပါပြီ။"
                )

            except Exception as e:

                st.error(
                    f"❌ Gemini Error: {e}"
                )


    if st.button(
        "📚 Episode အသစ်သို့ ဆက်မည်"
    ):

        current_nb[
            "volume"
        ] += 1

        save_data()

        st.success(
            f"Episode "
            f"{current_nb['volume']} "
            f"သို့ ပြောင်းပြီးပါပြီ။"
        )

        st.rerun()


# =========================================================
# CHARACTER TAB
# =========================================================

with tab2:

    st.subheader(
        "👥 Character Database"
    )

    if not current_nb[
        "characters"
    ]:

        st.info(
            "Character မရှိသေးပါ။ "
            "Story Generate လုပ်ပါ။"
        )

    else:

        for character in (
            current_nb[
                "characters"
            ]
        ):

            with st.expander(
                "👤 "
                +
                character.get(
                    "name",
                    "Unknown"
                )
            ):

                st.write(
                    "**အသက်:** "
                    + str(
                        character.get(
                            "age",
                            ""
                        )
                    )
                )

                st.write(
                    "**Gender:** "
                    + str(
                        character.get(
                            "gender",
                            ""
                        )
                    )
                )

                st.write(
                    "**Personality:** "
                    + str(
                        character.get(
                            "personality",
                            ""
                        )
                    )
                )

                st.write(
                    "**Appearance:** "
                    + str(
                        character.get(
                            "appearance",
                            ""
                        )
                    )
                )

                st.write(
                    "**Clothing:** "
                    + str(
                        character.get(
                            "clothing",
                            ""
                        )
                    )
                )

                st.write(
                    "**Relationship:** "
                    + str(
                        character.get(
                            "relationship",
                            ""
                        )
                    )
                )


# =========================================================
# SCENES TAB
# =========================================================

with tab3:

    episode_key = str(
        current_nb[
            "volume"
        ]
    )

    episode = (
        current_nb[
            "episodes"
        ].get(
            episode_key
        )
    )

    if not episode:

        st.info(
            "အရင်ဆုံး Story Generate လုပ်ပါ။"
        )

    else:

        st.subheader(
            f"🎬 Episode {episode_key} "
            f"— "
            f"{len(episode['scenes'])} Scenes"
        )

        for scene in (
            episode[
                "scenes"
            ]
        ):

            scene_no = scene.get(
                "scene",
                "?"
            )

            with st.expander(
                f"🎬 Scene {scene_no}"
            ):

                st.write(
                    "📍 **Location:**",
                    scene.get(
                        "location",
                        ""
                    )
                )

                st.write(
                    "🕐 **Time:**",
                    scene.get(
                        "time",
                        ""
                    )
                )

                st.write(
                    "🎭 **Action:**",
                    scene.get(
                        "action",
                        ""
                    )
                )

                st.markdown(
                    "### 💬 Dialogue"
                )

                for d in (
                    scene.get(
                        "dialogue",
                        []
                    )
                ):

                    st.markdown(
                        f"**{d.get('character', '')}:** "
                        f"{d.get('text', '')}"
                    )

                st.markdown(
                    "### 🖼️ Image Prompt"
                )

                st.code(
                    scene.get(
                        "image_prompt",
                        ""
                    ),
                    language="text"
                )

                st.markdown(
                    "### 🎥 Video Prompt"
                )

                st.code(
                    scene.get(
                        "video_prompt",
                        ""
                    ),
                    language="text"
                )

                st.markdown(
                    "### 🎙️ Voice Text"
                )

                st.code(
                    scene.get(
                        "voice_text",
                        ""
                    ),
                    language="text"
                )


# =========================================================
# VOICE / VIDEO TAB
# =========================================================

with tab4:

    episode_key = str(
        current_nb[
            "volume"
        ]
    )

    episode = (
        current_nb[
            "episodes"
        ].get(
            episode_key
        )
    )

    if not episode:

        st.info(
            "အရင်ဆုံး Story Generate လုပ်ပါ။"
        )

    else:

        st.subheader(
            "🎙️ Voice / 🎬 Video"
        )

        # =================================================
        # IMPORTANT:
        # ONLY ONE SCENE IS SELECTED
        # =================================================

        scene_numbers = [
            s.get(
                "scene"
            )
            for s in episode[
                "scenes"
            ]
        ]

        selected_scene = (
            st.selectbox(
                "🎬 Video ထုတ်မယ့် Scene တစ်ခုရွေးပါ",
                scene_numbers
            )
        )

        scene = next(
            s
            for s in episode[
                "scenes"
            ]
            if s.get(
                "scene"
            )
            ==
            selected_scene
        )


        st.info(
            f"🎬 အခု Scene {selected_scene} "
            "တစ်ခန်းတည်းကိုပဲ Video API ဆီပို့ပါမယ်။ "
            "Scene အားလုံးကို အလိုအလျောက် မထုတ်ပါ။"
        )


        # =================================================
        # IMAGE PROMPT
        # =================================================

        st.markdown(
            "### 🖼️ Image Prompt"
        )

        image_prompt = st.text_area(
            "Image Prompt",
            value=scene.get(
                "image_prompt",
                ""
            ),
            height=180,
            key=f"image_prompt_{selected_scene}"
        )


        # =================================================
        # VIDEO PROMPT
        # =================================================

        st.markdown(
            "### 🎥 Video Prompt"
        )

        video_prompt = st.text_area(
            "Video Prompt",
            value=scene.get(
                "video_prompt",
                ""
            ),
            height=220,
            key=f"video_prompt_{selected_scene}"
        )


        # =================================================
        # VOICE
        # =================================================

        st.markdown(
            "### 🎙️ Voice Text"
        )

        edited_voice = st.text_area(
            "အသံထွက်မယ့်စာသား",
            value=scene.get(
                "voice_text",
                ""
            ),
            height=150,
            key=f"voice_text_{selected_scene}"
        )


        if st.button(
            "🔊 ဒီ Scene အတွက် MP3 ထုတ်မည်",
            use_container_width=True
        ):

            if not edited_voice.strip():

                st.error(
                    "Voice Text မရှိပါ။"
                )

            else:

                try:

                    filename = (
                        f"episode_"
                        f"{current_nb['volume']}"
                        f"_scene_"
                        f"{selected_scene}"
                        f"_voice.mp3"
                    )

                    with st.spinner(
                        "🎙️ Voice ထုတ်နေပါတယ်..."
                    ):

                        audio_path = (
                            generate_voice(
                                edited_voice,
                                filename
                            )
                        )

                    st.success(
                        "✅ MP3 ထွက်ပါပြီ။"
                    )

                    st.audio(
                        audio_path,
                        format="audio/mp3"
                    )

                except Exception as e:

                    st.error(
                        f"❌ Voice Error: {e}"
                    )


        # =================================================
        # KLING VIDEO
        # =================================================

        st.markdown("---")

        st.markdown(
            "## 🟣 Kling API Video"
        )


        kling_duration = (
            st.selectbox(
                "⏱️ Duration",
                [
                    1,
                    5,
                    10
                ],
                index=1,
                key=f"kling_duration_{selected_scene}"
            )
        )


        if kling_duration == 1:

            st.warning(
                "⚠️ 1 second ကို UI မှာ ထည့်ပေးထားပါတယ်။ "
                "ဒါပေမယ့် Kling API က လက်ရှိ "
                "3–15 seconds ကိုပဲ လက်ခံပါတယ်။ "
                "Kling Video ထုတ်ဖို့ 5 သို့ 10 ကိုရွေးပါ။"
            )


        kling_ratio = (
            st.selectbox(
                "📱 Video Ratio",
                [
                    "9:16",
                    "16:9"
                ],
                index=(
                    0
                    if kling_default_ratio
                    == "9:16"
                    else 1
                ),
                key=f"kling_ratio_{selected_scene}"
            )
        )


        kling_sound_scene = (
            st.selectbox(
                "🔊 Kling Native Sound",
                [
                    "off",
                    "on"
                ],
                index=(
                    0
                    if kling_sound
                    == "off"
                    else 1
                ),
                key=f"kling_sound_{selected_scene}"
            )
        )


        # =================================================
        # KLING BUTTON
        # =================================================

        if st.button(
            "🚀 ဒီ Scene တစ်ခုတည်းကို Kling နဲ့ Video ထုတ်မည်",
            type="primary",
            use_container_width=True
        ):

            if not kling_api_key.strip():

                st.error(
                    "❌ Kling API Key မထည့်ရသေးပါ။ "
                    "Sidebar → Kling API Key မှာ ထည့်ပါ။"
                )

            elif not video_prompt.strip():

                st.error(
                    "❌ Video Prompt မရှိပါ။"
                )

            elif kling_duration == 1:

                st.error(
                    "❌ Kling API မှာ 1 second မရသေးပါ။ "
                    "5 seconds ကိုရွေးပါ။"
                )

            else:

                try:

                    # Save edited prompts
                    scene[
                        "image_prompt"
                    ] = image_prompt

                    scene[
                        "video_prompt"
                    ] = video_prompt

                    scene[
                        "voice_text"
                    ] = edited_voice

                    save_data()


                    # -------------------------------------
                    # ONLY ONE SCENE IS SENT
                    # -------------------------------------

                    with st.spinner(
                        f"🎬 Scene {selected_scene} "
                        "တစ်ခန်းတည်းကို Kling ဆီပို့နေပါတယ်..."
                    ):

                        video_url = (
                            generate_kling_video(
                                api_key=kling_api_key,
                                prompt=video_prompt,
                                duration=kling_duration,
                                aspect_ratio=kling_ratio,
                                model_name=kling_model,
                                mode=kling_mode,
                                sound=kling_sound_scene
                            )
                        )


                    if not video_url:

                        raise RuntimeError(
                            "Kling က Video URL မပြန်ပေးပါ။"
                        )


                    # -------------------------------------
                    # SAVE KLING RESULT
                    # -------------------------------------

                    if (
                        "video_results"
                        not in scene
                    ):

                        scene[
                            "video_results"
                        ] = {}


                    scene[
                        "video_results"
                    ][
                        "kling"
                    ] = video_url


                    scene[
                        "video_results"
                    ][
                        "kling_duration"
                    ] = kling_duration


                    scene[
                        "video_results"
                    ][
                        "kling_ratio"
                    ] = kling_ratio


                    save_data()


                    st.success(
                        f"✅ Scene {selected_scene} "
                        "Kling Video အောင်မြင်ပါပြီ။"
                    )


                    st.markdown(
                        "### 🎞️ Kling Video"
                    )

                    st.video(
                        video_url
                    )


                except Exception as e:

                    st.error(
                        "❌ Kling Video Error"
                    )

                    st.code(
                        str(e),
                        language="text"
                    )


        # =================================================
        # OLD KLING RESULT
        # =================================================

        saved_results = (
            scene.get(
                "video_results",
                {}
            )
        )

        if isinstance(
            saved_results,
            dict
        ):

            saved_kling_url = (
                saved_results.get(
                    "kling"
                )
            )

            if saved_kling_url:

                st.markdown(
                    "### 🎞️ နောက်ဆုံး Kling Video"
                )

                st.video(
                    saved_kling_url
                )


        # =================================================
        # GEMINI VEO OPTIONAL
        # =================================================

        st.markdown("---")

        st.markdown(
            "## 🟢 Gemini Veo Video (Optional)"
        )

        veo_prompt = st.text_area(
            "Veo Video Prompt",
            value=scene.get(
                "video_prompt",
                ""
            ),
            height=180,
            key=f"veo_prompt_{selected_scene}"
        )


        if st.button(
            "🎬 Gemini Veo နဲ့ Video ထုတ်မည်",
            use_container_width=True
        ):

            if not gemini_api_key.strip():

                st.error(
                    "Gemini API Key ထည့်ပါ။"
                )

            elif not veo_prompt.strip():

                st.error(
                    "Veo Video Prompt မရှိပါ။"
                )

            else:

                try:

                    filename = (
                        f"episode_"
                        f"{current_nb['volume']}"
                        f"_scene_"
                        f"{selected_scene}"
                        f"_veo.mp4"
                    )

                    with st.spinner(
                        "🎬 Gemini Veo Video ထုတ်နေပါတယ်..."
                    ):

                        veo_path = (
                            generate_veo_video(
                                gemini_api_key,
                                gemini_video_model,
                                veo_prompt,
                                filename,
                                gemini_aspect_ratio
                            )
                        )

                    st.success(
                        "✅ Gemini Veo Video ပြီးပါပြီ။"
                    )

                    st.video(
                        veo_path
                    )

                except Exception as e:

                    st.error(
                        "❌ Veo Video Error\n\n"
                        + str(e)
                    )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.info(
    "💡 Video Button ကိုနှိပ်တဲ့အခါ "
    "ရွေးထားတဲ့ Scene တစ်ခန်းတည်းကိုသာ "
    "Kling API ဆီပို့ပါတယ်။ "
    "Scene 8 ခန်းရှိလို့ Video 8 ခု အလိုအလျောက် "
    "ထုတ်မှာမဟုတ်ပါ။"
)