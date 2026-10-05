import json
import os
import time
import streamlit as st
from google import genai

# =========================================================
# PAGE
# =========================================================

st.set_page_config(
    page_title="AI Drama Story Generator",
    page_icon="🎬",
    layout="wide"
)

st.title("🎬 AI Drama Story Generator")

st.write(
    "ဇာတ်ကားတစ်ကားချင်းစီကို Notebook အဖြစ်သိမ်းပြီး "
    "အတွဲလိုက် Scene၊ Dialogue နှင့် Image Prompt များကို ဖန်တီးနိုင်ပါသည်။"
)

DATA_FILE = "drama_notebooks.json"


# =========================================================
# STORAGE
# =========================================================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                ensure_ascii=False,
                indent=2
            )
    except Exception as e:
        st.error(f"Data save error: {e}")


# =========================================================
# API CALL WITH RETRY
# =========================================================

def generate_with_retry(client, prompt, max_attempts=3):

    last_error = None

    for attempt in range(max_attempts):

        try:

            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )

            if not response.text:
                raise Exception(
                    "Gemini က စာပြန်မပေးပါ။"
                )

            return response.text

        except Exception as e:

            last_error = e
            error_text = str(e)

            # 503 / temporary unavailable
            if (
                "503" in error_text
                or "UNAVAILABLE" in error_text
                or "high demand" in error_text.lower()
            ):

                if attempt < max_attempts - 1:

                    wait_time = 5 * (attempt + 1)

                    st.warning(
                        f"⏳ Gemini server busy ဖြစ်နေပါတယ်။ "
                        f"{wait_time} စက္ကန့်စောင့်ပြီး "
                        f"ပြန်ကြိုးစားပါမယ်... "
                        f"({attempt + 1}/{max_attempts})"
                    )

                    time.sleep(wait_time)

                    continue

            raise e

    raise last_error


# =========================================================
# PARSE SCENES
# =========================================================

def parse_scenes(result):

    scenes = {}

    lines = result.splitlines()

    current_scene = None
    current_content = []

    for line in lines:

        stripped = line.strip()

        if stripped.startswith("===== SCENE "):

            if current_scene is not None:

                scenes[str(current_scene)] = (
                    "\n".join(current_content).strip()
                )

            number_text = (
                stripped
                .replace("===== SCENE ", "")
                .replace(" =====", "")
                .strip()
            )

            try:

                current_scene = int(number_text)
                current_content = []

            except ValueError:

                current_scene = None
                current_content = []

        elif current_scene is not None:

            if stripped.startswith(
                "===== NEXT VOLUME CONTINUITY ====="
            ):

                break

            current_content.append(line)

    if current_scene is not None:

        scenes[str(current_scene)] = (
            "\n".join(current_content).strip()
        )

    return scenes


# =========================================================
# CONTINUITY
# =========================================================

def get_continuity(result):

    marker = "===== NEXT VOLUME CONTINUITY ====="

    if marker in result:

        return result.split(
            marker,
            1
        )[1].strip()

    return ""


# =========================================================
# SESSION
# =========================================================

if "notebooks" not in st.session_state:
    st.session_state.notebooks = load_data()

if "current_notebook" not in st.session_state:
    st.session_state.current_notebook = ""

if "new_notebook" not in st.session_state:
    st.session_state.new_notebook = False


# =========================================================
# NOTEBOOK CREATION
# =========================================================

def create_notebook(name):

    name = name.strip()

    if not name:
        return False, "Notebook အမည်ထည့်ပါ။"

    if name in st.session_state.notebooks:
        return False, "ဒီ Notebook နာမည် ရှိပြီးသားပါ။"

    st.session_state.notebooks[name] = {
        "story": "",
        "characters": "",
        "language": "မြန်မာ (Burmese)",
        "custom_language": "",
        "scenes_per_volume": 150,
        "current_volume": 1,
        "last_scene": 0,
        "continuity": "",
        "volumes": {}
    }

    save_data(
        st.session_state.notebooks
    )

    st.session_state.current_notebook = name

    return True, "Notebook အသစ် ဖန်တီးပြီးပါပြီ။"


# =========================================================
# SIDEBAR - NOTEBOOKS
# =========================================================

st.sidebar.header("📓 Drama Notebooks")

notebook_names = list(
    st.session_state.notebooks.keys()
)

if notebook_names:

    current_index = 0

    if (
        st.session_state.current_notebook
        in notebook_names
    ):
        current_index = notebook_names.index(
            st.session_state.current_notebook
        )

    selected_notebook = st.sidebar.selectbox(
        "ရှိပြီးသား ဇာတ်ကား",
        notebook_names,
        index=current_index
    )

    if (
        selected_notebook
        != st.session_state.current_notebook
    ):

        st.session_state.current_notebook = (
            selected_notebook
        )

        st.rerun()

else:

    st.sidebar.info(
        "Notebook မရှိသေးပါ။"
    )


if st.sidebar.button(
    "➕ New Notebook",
    use_container_width=True
):

    st.session_state.new_notebook = True


# =========================================================
# NEW NOTEBOOK
# =========================================================

if st.session_state.new_notebook:

    st.subheader("📓 ဇာတ်ကားအသစ်")

    new_name = st.text_input(
        "ဇာတ်ကား / Notebook အမည်",
        placeholder="ဥပမာ - မာနကြီးသောမင်းသမီး"
    )

    c1, c2 = st.columns(2)

    with c1:

        if st.button(
            "✅ ဖန်တီးမည်",
            use_container_width=True
        ):

            success, message = create_notebook(
                new_name
            )

            if success:

                st.session_state.new_notebook = False

                st.success(message)

                st.rerun()

            else:

                st.error(message)

    with c2:

        if st.button(
            "❌ Cancel",
            use_container_width=True
        ):

            st.session_state.new_notebook = False

            st.rerun()


# =========================================================
# CURRENT NOTEBOOK
# =========================================================

if not st.session_state.current_notebook:

    st.info(
        "📓 ဘယ်ဘက်က **New Notebook** ကိုနှိပ်ပြီး "
        "ဇာတ်ကားအသစ် စတင်ပါ။"
    )

    st.stop()


notebook = st.session_state.notebooks[
    st.session_state.current_notebook
]


# =========================================================
# GEMINI API
# =========================================================

st.sidebar.markdown("---")

st.sidebar.subheader("⚙️ Gemini Settings")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    placeholder="AIza..."
)

st.sidebar.caption(
    "API Key ကို ဒီနေရာမှာသာ ထည့်ပါ။"
)


# =========================================================
# LANGUAGE
# =========================================================

st.sidebar.markdown("---")

st.sidebar.subheader("🌐 Output Language")

languages = [
    "မြန်မာ (Burmese)",
    "中文 (Chinese)",
    "English",
    "ไทย (Thai)",
    "Other"
]

saved_language = notebook.get(
    "language",
    "မြန်မာ (Burmese)"
)

if saved_language not in languages:
    saved_language = "မြန်မာ (Burmese)"

language = st.sidebar.selectbox(
    "ဇာတ်လမ်း / Dialogue ဘာသာစကား",
    languages,
    index=languages.index(
        saved_language
    )
)

custom_language = notebook.get(
    "custom_language",
    ""
)

if language == "Other":

    custom_language = st.sidebar.text_input(
        "ဘာသာစကား",
        value=custom_language,
        placeholder="ဥပမာ - Korean"
    )


if language == "မြန်မာ (Burmese)":

    output_language = "Burmese (Myanmar language)"

elif language == "中文 (Chinese)":

    output_language = "Chinese (Simplified Chinese)"

elif language == "English":

    output_language = "English"

elif language == "ไทย (Thai)":

    output_language = "Thai"

else:

    output_language = (
        custom_language.strip()
        if custom_language.strip()
        else "the language specified by the user"
    )


# =========================================================
# NOTEBOOK TITLE
# =========================================================

st.header(
    f"📓 {st.session_state.current_notebook}"
)

st.caption(
    "ဒီ Notebook က ဒီဇာတ်ကားအတွက် သီးသန့်ဖြစ်ပါတယ်။"
)


# =========================================================
# STORY
# =========================================================

st.subheader("📖 ဇာတ်လမ်းအကြမ်း")

story = st.text_area(
    "ဇာတ်လမ်းအကြမ်း",
    value=notebook.get("story", ""),
    height=220,
    placeholder="""ဥပမာ -

မင်းသမီးက ချမ်းသာပြီး မာနကြီးတယ်။
မင်းသားက ဆင်းရဲပေမယ့် ရိုးသားတယ်။
အစပိုင်းမှာ မင်းသမီးက မင်းသားကို အထင်သေးတယ်။
နောက်ပိုင်းမှာ သူ့ရဲ့ စိတ်ကောင်းကို သိလာပြီး ချစ်မိသွားတယ်။"""
)


# =========================================================
# CHARACTERS
# =========================================================

st.subheader("👥 Character Information")

characters = st.text_area(
    "ဇာတ်ကောင်အချက်အလက်",
    value=notebook.get("characters", ""),
    height=180,
    placeholder="""မင်းသမီး - မေသဇင်၊ အသက် ၂၃၊ ချမ်းသာ၊ မာနကြီး
မင်းသား - အောင်ခန့်၊ အသက် ၂၅၊ ဆင်းရဲသော်လည်း ရိုးသား
မင်းသမီးအဖေ - ဦးထွန်း
မင်းသမီးအမေ - ဒေါ်သီတာ"""
)


# =========================================================
# SCENE COUNT
# =========================================================

scene_options = list(
    range(5, 151, 5)
)

saved_scene_count = notebook.get(
    "scenes_per_volume",
    150
)

if saved_scene_count not in scene_options:
    saved_scene_count = 150

scene_count = st.selectbox(
    "🎬 အတွဲတစ်တွဲမှာ Scene",
    scene_options,
    index=scene_options.index(
        saved_scene_count
    )
)

st.caption(
    "ရွေးချယ်နိုင်သည် — "
    "5, 10, 15, 20 ... 150"
)


# =========================================================
# SAVE USER INPUT
# =========================================================

notebook["story"] = story
notebook["characters"] = characters
notebook["language"] = language
notebook["custom_language"] = custom_language
notebook["scenes_per_volume"] = scene_count

save_data(
    st.session_state.notebooks
)


# =========================================================
# CURRENT VOLUME
# =========================================================

current_volume = notebook.get(
    "current_volume",
    1
)

last_scene = notebook.get(
    "last_scene",
    0
)

st.markdown("---")

st.subheader(
    f"📚 အတွဲ {current_volume}"
)

st.info(
    f"နောက်ထုတ်မည့် Scene သည် "
    f"Scene {last_scene + 1} မှ "
    f"Scene {last_scene + scene_count} အထိ ဖြစ်မည်။"
)


# =========================================================
# GENERATE CURRENT VOLUME
# =========================================================

if st.button(
    f"🚀 အတွဲ {current_volume} "
    f"Scene {last_scene + 1}–"
    f"{last_scene + scene_count} ထုတ်မည်",
    use_container_width=True
):

    if not api_key.strip():

        st.error(
            "❌ Gemini API Key ထည့်ပါ။"
        )

    elif not story.strip():

        st.error(
            "❌ ဇာတ်လမ်းအကြမ်း ထည့်ပါ။"
        )

    elif (
        language == "Other"
        and not custom_language.strip()
    ):

        st.error(
            "❌ Other ဘာသာစကားအမည်ထည့်ပါ။"
        )

    else:

        first_scene = last_scene + 1
        final_scene = (
            last_scene + scene_count
        )

        client = genai.Client(
            api_key=api_key.strip()
        )

        prompt = f"""
You are a professional long-form drama writer.

Create Volume {current_volume}.

SCENE RANGE:
Scene {first_scene} to Scene {final_scene}

TOTAL NEW SCENES:
{scene_count}

OUTPUT LANGUAGE:
{output_language}

ORIGINAL STORY:
{story}

CHARACTER INFORMATION:
{characters}

PREVIOUS CONTINUITY:
{notebook.get("continuity", "")}

IMPORTANT RULES:

1. Write exactly Scene {first_scene} through Scene {final_scene}.
2. Do NOT restart scene numbering.
3. Continue directly from the previous volume.
4. Keep all character appearances consistent.
5. Keep personality consistent.
6. Keep relationships consistent.
7. Keep story continuity.
8. Every scene must move the story forward.
9. Dialogue must be in {output_language}.
10. Scene Description must be in {output_language}.
11. Character information must be in {output_language}.
12. Image Prompt must be in English.
13. Image Prompt must contain cinematic vertical 9:16.
14. Do not put dialogue inside Image Prompt.
15. Do not finish the entire story too early.

USE THIS FORMAT:

===== VOLUME {current_volume} =====

Volume Title:
...

Volume Summary:
...

===== SCENE {first_scene} =====

Scene Description:
...

Characters:
...

Dialogue:

Character Name:
"..."

Character Name:
"..."

Image Prompt:
Detailed cinematic vertical 9:16 image prompt in English.

Continue until:

===== SCENE {final_scene} =====

Then:

===== NEXT VOLUME CONTINUITY =====

Include:
- Character emotional states
- Relationships
- Important events
- Unresolved conflicts
- Important locations
- Important objects
- What should happen next
"""

        try:

            with st.spinner(
                f"⏳ Scene {first_scene}–"
                f"{final_scene} ရေးနေပါပြီ..."
            ):

                result = generate_with_retry(
                    client,
                    prompt
                )

            scenes = parse_scenes(
                result
            )

            continuity = get_continuity(
                result
            )

            notebook["volumes"][
                str(current_volume)
            ] = {
                "first_scene": first_scene,
                "last_scene": final_scene,
                "scene_count": scene_count,
                "scenes": scenes,
                "result": result,
                "continuity": continuity
            }

            notebook["continuity"] = continuity

            notebook["last_scene"] = final_scene

            save_data(
                st.session_state.notebooks
            )

            st.success(
                f"✅ အတွဲ {current_volume} "
                f"Scene {first_scene}–{final_scene} "
                "ပြီးပါပြီ။"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "❌ Gemini API Error"
            )

            st.code(
                str(e),
                language="text"
            )


# =========================================================
# CURRENT VOLUME DISPLAY
# =========================================================

volumes = notebook.get(
    "volumes",
    {}
)

if str(current_volume) in volumes:

    volume_data = volumes[
        str(current_volume)
    ]

    scenes = volume_data.get(
        "scenes",
        {}
    )

    scene_numbers = sorted(
        [int(x) for x in scenes.keys()]
    )

    st.markdown("---")

    st.subheader(
        f"🎬 အတွဲ {current_volume} "
        f"— Scene {len(scene_numbers)} ခန်း"
    )

    # 5 scenes per group
    for start in range(
        0,
        len(scene_numbers),
        5
    ):

        group = scene_numbers[
            start:start + 5
        ]

        first = group[0]
        last = group[-1]

        group_text = ""

        for number in group:

            group_text += (
                f"===== SCENE {number} =====\n\n"
                f"{scenes[str(number)]}\n\n"
            )

        st.markdown(
            f"### 📦 Scene {first} – {last}"
        )

        # Streamlit automatically provides Copy
        st.code(
            group_text,
            language="text"
        )


# =========================================================
# VOLUME HISTORY
# =========================================================

if volumes:

    st.markdown("---")

    st.subheader("📚 အတွဲမှတ်တမ်း")

    volume_numbers = sorted(
        [int(x) for x in volumes.keys()]
    )

    selected_volume = st.selectbox(
        "ကြည့်မည့်အတွဲ",
        volume_numbers,
        index=len(volume_numbers) - 1
    )

    selected_data = volumes[
        str(selected_volume)
    ]

    selected_scenes = selected_data.get(
        "scenes",
        {}
    )

    selected_numbers = sorted(
        [int(x) for x in selected_scenes.keys()]
    )

    for start in range(
        0,
        len(selected_numbers),
        5
    ):

        group = selected_numbers[
            start:start + 5
        ]

        group_text = ""

        for number in group:

            group_text += (
                f"===== SCENE {number} =====\n\n"
                f"{selected_scenes[str(number)]}\n\n"
            )

        st.code(
            group_text,
            language="text"
        )


# =========================================================
# NEXT VOLUME
# =========================================================

if str(current_volume) in volumes:

    st.markdown("---")

    next_volume = current_volume + 1

    next_first_scene = (
        notebook.get("last_scene", 0) + 1
    )

    next_last_scene = (
        next_first_scene + scene_count - 1
    )

    st.subheader(
        "📚 ဇာတ်လမ်းဆက်ရန်"
    )

    st.caption(
        f"အတွဲ {next_volume} → "
        f"Scene {next_first_scene}–"
        f"{next_last_scene}"
    )

    if st.button(
        f"📚 အတွဲ {next_volume} ဆက်လက်ထုတ်ရန်",
        use_container_width=True
    ):

        if not api_key.strip():

            st.error(
                "❌ Gemini API Key ထည့်ပါ။"
            )

        else:

            client = genai.Client(
                api_key=api_key.strip()
            )

            first_scene = (
                notebook.get("last_scene", 0) + 1
            )

            final_scene = (
                first_scene + scene_count - 1
            )

            prompt = f"""
Continue the drama story.

PREVIOUS VOLUME:
Volume {current_volume}

NEW VOLUME:
Volume {next_volume}

NEW SCENE RANGE:
Scene {first_scene} to Scene {final_scene}

OUTPUT LANGUAGE:
{output_language}

ORIGINAL STORY:
{notebook.get("story", "")}

CHARACTER INFORMATION:
{notebook.get("characters", "")}

PREVIOUS CONTINUITY:
{notebook.get("continuity", "")}

RULES:

1. Continue directly from the previous volume.
2. Scene numbering MUST continue from Scene {first_scene}.
3. Write exactly Scene {first_scene} through Scene {final_scene}.
4. Do not restart at Scene 1.
5. Keep character appearance consistent.
6. Keep personality consistent.
7. Keep relationships consistent.
8. Continue unresolved conflicts naturally.
9. Dialogue must be in {output_language}.
10. Scene Description must be in {output_language}.
11. Character information must be in {output_language}.
12. Image Prompt must be English.
13. Image Prompt must contain cinematic vertical 9:16.
14. Every scene must move the story forward.

USE EXACT FORMAT:

===== VOLUME {next_volume} =====

Volume Title:
...

Volume Summary:
...

===== SCENE {first_scene} =====

Scene Description:
...

Characters:
...

Dialogue:

Character Name:
"..."

Character Name:
"..."

Image Prompt:
Detailed cinematic vertical 9:16 image prompt in English.

Continue until:

===== SCENE {final_scene} =====

Then:

===== NEXT VOLUME CONTINUITY =====

Write the information required for the next volume.
"""

            try:

                with st.spinner(
                    f"⏳ အတွဲ {next_volume} "
                    f"Scene {first_scene}–"
                    f"{final_scene} ရေးနေပါပြီ..."
                ):

                    result = generate_with_retry(
                        client,
                        prompt
                    )

                scenes = parse_scenes(
                    result
                )

                continuity = get_continuity(
                    result
                )

                notebook["volumes"][
                    str(next_volume)
                ] = {
                    "first_scene": first_scene,
                    "last_scene": final_scene,
                    "scene_count": scene_count,
                    "scenes": scenes,
                    "result": result,
                    "continuity": continuity
                }

                notebook["continuity"] = continuity

                notebook["current_volume"] = (
                    next_volume
                )

                notebook["last_scene"] = (
                    final_scene
                )

                save_data(
                    st.session_state.notebooks
                )

                st.success(
                    f"✅ အတွဲ {next_volume} "
                    f"Scene {first_scene}–"
                    f"{final_scene} ပြီးပါပြီ။"
                )

                st.rerun()

            except Exception as e:

                st.error(
                    "❌ အတွဲဆက်တဲ့အချိန် "
                    "Gemini API Error ဖြစ်ပါတယ်။"
                )

                st.code(
                    str(e),
                    language="text"
                )


# =========================================================
# CHARACTER MEMORY
# =========================================================

if notebook.get("characters"):

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "👥 Character Memory"
    )

    st.sidebar.text_area(
        "သိမ်းထားသော Character Information",
        value=notebook.get(
            "characters",
            ""
        ),
        height=250,
        disabled=True
    )


# =========================================================
# CONTINUITY
# =========================================================

if notebook.get("continuity"):

    st.markdown("---")

    with st.expander(
        "🔗 နောက်အတွဲ Continuity"
    ):

        st.write(
            notebook.get(
                "continuity",
                ""
            )
        )


# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "🎬 Stage 1 — "
    "Notebook → Story → Volume → Scenes → Dialogue → Image Prompts"
)
# ==========================================
# 🎬 AI VIDEO GENERATOR
# ==========================================

import time
import streamlit as st

# Runway SDK
try:
    from runwayml import RunwayML, TaskFailedError
    RUNWAY_AVAILABLE = True
except ImportError:
    RUNWAY_AVAILABLE = False


# ==========================================
# 🎬 VIDEO GENERATOR UI
# ==========================================

st.markdown("---")
st.subheader("🎬 ဇာတ်ညွှန်းများမှ AI Video အော်တိုထုတ်လုပ်ခြင်း")


# ==========================================
# 1. VIDEO API PROVIDER
# ==========================================

video_provider = st.selectbox(
    "🤖 Video API ရွေးပါ",
    [
        "Runway",
        "Luma",
        "Kling",
    ],
)


# ==========================================
# 2. API KEY
# ==========================================

video_api_key = st.text_input(
    f"🔑 {video_provider} API Key",
    type="password",
)


# ==========================================
# 3. VIDEO INPUT MODE
# ==========================================

input_mode = st.radio(
    "🎥 Video ထုတ်မည့်နည်း",
    [
        "Text → Video",
        "Image → Video",
    ],
    horizontal=True,
)


# ==========================================
# 4. IMAGE URL
# ==========================================

image_url = ""

if input_mode == "Image → Video":

    image_url = st.text_input(
        "🖼️ Reference Image URL",
        placeholder="https://example.com/scene1.jpg",
    )

    st.caption(
        "Image → Video အတွက် HTTPS image URL ထည့်ပါ။"
    )


# ==========================================
# 5. VIDEO PROMPTS
# ==========================================

videos_input_text = st.text_area(
    "📝 Video Prompts များ",
    placeholder=(
        "Scene 1: A young woman walks through a Chinese-style courtyard, "
        "cinematic camera movement, natural body movement.\n\n"
        "Scene 2: A young man looks at her from across the courtyard, "
        "emotional close-up, subtle camera movement."
    ),
    height=250,
)


# ==========================================
# 6. VIDEO SETTINGS
# ==========================================

col1, col2 = st.columns(2)

with col1:

    aspect_ratio = st.selectbox(
        "📱 Video Ratio",
        [
            "9:16",
            "16:9",
            "1:1",
        ],
    )


with col2:

    duration = st.selectbox(
        "⏱️ Duration",
        [
            5,
            10,
        ],
    )


# ==========================================
# 7. STYLE
# ==========================================

style = st.text_input(
    "🎨 Video Style",
    value=(
        "cinematic Chinese drama style, "
        "realistic characters, natural movement, "
        "dramatic lighting, detailed environment, "
        "smooth cinematic camera movement"
    ),
)


# ==========================================
# 8. RATIO CONVERTER
# ==========================================

def runway_ratio(ratio):

    if ratio == "9:16":
        return "720:1280"

    elif ratio == "16:9":
        return "1280:720"

    else:
        return "960:960"


# ==========================================
# 9. CLEAN PROMPTS
# ==========================================

def clean_video_prompts(text):

    lines = text.split("\n")

    prompts = []

    for line in lines:

        cleaned = line.strip()

        if not cleaned:
            continue

        if cleaned.startswith("==="):
            continue

        if cleaned.startswith("---"):
            continue

        prompts.append(cleaned)

    return prompts


# ==========================================
# 10. RUNWAY VIDEO GENERATOR
# ==========================================

def generate_runway_video(
    api_key,
    prompt,
    ratio,
    video_duration,
    reference_image=None,
):

    if not RUNWAY_AVAILABLE:

        raise RuntimeError(
            "runwayml package မရှိသေးပါ။ "
            "Replit မှာ runwayml package ထည့်ပေးပါ။"
        )

    try:

        client = RunwayML(
            api_key=api_key
        )

        # --------------------------------------
        # Image → Video
        # --------------------------------------

        if reference_image:

            task = client.image_to_video.create(
                model="gen4.5_turbo",
                prompt_image=reference_image,
                prompt_text=prompt,
                ratio=runway_ratio(ratio),
                duration=int(video_duration),
            ).wait_for_task_output()

        # --------------------------------------
        # Text → Video
        # --------------------------------------

        else:

            task = client.text_to_video.create(
                model="gen4.5_turbo",
                prompt_text=prompt,
                ratio=runway_ratio(ratio),
                duration=int(video_duration),
            ).wait_for_task_output()

        # --------------------------------------
        # Result
        # --------------------------------------

        if task.output:

            return task.output[0]

        raise RuntimeError(
            "Video URL မရရှိသေးပါ။"
        )

    except TaskFailedError as e:

        raise RuntimeError(
            f"Runway Video Generation Failed: {e}"
        )

    except Exception as e:

        raise RuntimeError(
            f"Runway API Error: {e}"
        )


# ==========================================
# 11. VIDEO GENERATE BUTTON
# ==========================================

if st.button(
    "🚀 Video အားလုံးကို အော်တိုထုတ်မည်",
    type="primary",
):

    # --------------------------------------
    # API KEY CHECK
    # --------------------------------------

    if not video_api_key:

        st.error(
            f"❌ {video_provider} API Key ထည့်ပေးပါ။"
        )

    # --------------------------------------
    # PROMPT CHECK
    # --------------------------------------

    elif not videos_input_text.strip():

        st.error(
            "❌ Video Prompt မရှိသေးပါ။"
        )

    # --------------------------------------
    # IMAGE CHECK
    # --------------------------------------

    elif (
        input_mode == "Image → Video"
        and not image_url.strip()
    ):

        st.error(
            "❌ Image → Video ရွေးထားတဲ့အတွက် "
            "Reference Image URL ထည့်ပေးပါ။"
        )

    else:

        prompts_list = clean_video_prompts(
            videos_input_text
        )

        if not prompts_list:

            st.warning(
                "⚠️ Video Prompt မတွေ့ပါ။"
            )

        else:

            total_videos = len(
                prompts_list
            )

            st.info(
                f"🎬 စုစုပေါင်း Scene "
                f"{total_videos} ခုကို ထုတ်လုပ်မည်။"
            )

            progress_bar = st.progress(0)

            status_text = st.empty()

            generated_videos = []


            # ==================================
            # 🎬 AUTO VIDEO QUEUE
            # ==================================

            for index, prompt_text in enumerate(
                prompts_list
            ):

                scene_number = index + 1

                status_text.markdown(
                    f"🔄 **Scene {scene_number} / "
                    f"{total_videos}** ကို ထုတ်လုပ်နေပါပြီ..."
                )


                # ----------------------------------
                # FINAL PROMPT
                # ----------------------------------

                final_prompt = (
                    f"{style}. "
                    f"{prompt_text}"
                )


                try:

                    # ==================================
                    # RUNWAY
                    # ==================================

                    if video_provider == "Runway":

                        video_url = (
                            generate_runway_video(
                                api_key=video_api_key,
                                prompt=final_prompt,
                                ratio=aspect_ratio,
                                video_duration=duration,
                                reference_image=(
                                    image_url
                                    if input_mode
                                    == "Image → Video"
                                    else None
                                ),
                            )
                        )


                    # ==================================
                    # LUMA
                    # ==================================

                    elif video_provider == "Luma":

                        st.warning(
                            "⚠️ Luma API adapter ကို "
                            "ဒီ version မှာ မဖွင့်ထားသေးပါ။"
                        )

                        video_url = None


                    # ==================================
                    # KLING
                    # ==================================

                    elif video_provider == "Kling":

                        st.warning(
                            "⚠️ Kling API adapter ကို "
                            "ဒီ version မှာ မဖွင့်ထားသေးပါ။"
                        )

                        video_url = None


                    # ==================================
                    # VIDEO SUCCESS
                    # ==================================

                    if video_url:

                        generated_videos.append(
                            {
                                "scene": scene_number,
                                "prompt": prompt_text,
                                "url": video_url,
                            }
                        )

                        st.success(
                            f"✅ Scene {scene_number} "
                            "Video ထွက်လာပါပြီ!"
                        )

                        st.video(
                            video_url
                        )

                    else:

                        st.warning(
                            f"⚠️ Scene {scene_number} "
                            "Video မရသေးပါ။"
                        )


                except Exception as e:

                    st.error(
                        f"❌ Scene {scene_number} "
                        f"အမှားဖြစ်ပါတယ်:\n\n{e}"
                    )


                # ----------------------------------
                # PROGRESS
                # ----------------------------------

                progress_bar.progress(
                    (index + 1)
                    / total_videos
                )


            # ==================================
            # COMPLETE
            # ==================================

            if generated_videos:

                st.success(
                    f"🎉 {len(generated_videos)} ခု "
                    "Video ထုတ်လုပ်ပြီးပါပြီ!"
                )

                st.markdown("---")

                st.subheader(
                    "📥 ထွက်လာသော Video များ"
                )


                for video in generated_videos:

                    st.markdown(
                        f"### 🎬 Scene "
                        f"{video['scene']}"
                    )

                    st.video(
                        video["url"]
                    )

                    st.markdown(
                        f"[⬇️ Scene "
                        f"{video['scene']} "
                        f"Video Download]"
                        f"({video['url']})"
                    )

            else:

                st.warning(
                    "⚠️ Video တစ်ခုမှ မထွက်သေးပါ။"
                )
