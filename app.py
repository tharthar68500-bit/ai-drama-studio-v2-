import json
import os
import streamlit as st
from google import genai

# =========================================================
# PAGE SETUP
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

# =========================================================
# NOTEBOOK STORAGE
# =========================================================

DATA_FILE = "drama_notebooks.json"


def load_notebooks():
    if not os.path.exists(DATA_FILE):
        return {}

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_notebooks(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


# =========================================================
# SESSION STATE
# =========================================================

if "notebooks" not in st.session_state:
    st.session_state.notebooks = load_notebooks()

if "current_notebook" not in st.session_state:
    st.session_state.current_notebook = ""

if "show_new_notebook" not in st.session_state:
    st.session_state.show_new_notebook = False


# =========================================================
# NOTEBOOK FUNCTIONS
# =========================================================

def create_notebook(name):
    name = name.strip()

    if not name:
        return False, "Notebook အမည်ထည့်ပါ။"

    if name in st.session_state.notebooks:
        return False, "ဒီနာမည်နဲ့ Notebook ရှိပြီးသားပါ။"

    st.session_state.notebooks[name] = {
        "story": "",
        "characters": "",
        "language": "မြန်မာ (Burmese)",
        "custom_language": "",
        "volume": 1,
        "scenes_per_volume": 150,
        "continuity": "",
        "volumes": {},
        "current_scenes": {}
    }

    save_notebooks(st.session_state.notebooks)

    st.session_state.current_notebook = name

    return True, "Notebook အသစ်ဖန်တီးပြီးပါပြီ။"


def get_current_notebook():
    name = st.session_state.current_notebook

    if not name:
        return None

    return st.session_state.notebooks.get(name)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("📓 Drama Notebooks")

notebook_names = list(
    st.session_state.notebooks.keys()
)

if notebook_names:

    selected_notebook = st.sidebar.selectbox(
        "ရှိပြီးသား ဇာတ်ကား",
        notebook_names,
        index=(
            notebook_names.index(
                st.session_state.current_notebook
            )
            if st.session_state.current_notebook in notebook_names
            else 0
        )
    )

    if selected_notebook != st.session_state.current_notebook:

        st.session_state.current_notebook = selected_notebook

        st.rerun()

else:

    st.sidebar.info(
        "Notebook မရှိသေးပါ။"
    )


if st.sidebar.button(
    "➕ New Notebook",
    use_container_width=True
):

    st.session_state.show_new_notebook = True


# =========================================================
# NEW NOTEBOOK
# =========================================================

if st.session_state.show_new_notebook:

    st.subheader("📓 ဇာတ်ကားအသစ်ဖန်တီးရန်")

    new_notebook_name = st.text_input(
        "ဇာတ်ကား / Notebook အမည်",
        placeholder="ဥပမာ - မာနကြီးသောမင်းသမီး"
    )

    col1, col2 = st.columns(2)

    with col1:

        if st.button(
            "✅ Notebook ဖန်တီးမည်",
            use_container_width=True
        ):

            success, message = create_notebook(
                new_notebook_name
            )

            if success:

                st.session_state.show_new_notebook = False

                st.success(message)

                st.rerun()

            else:

                st.error(message)

    with col2:

        if st.button(
            "❌ Cancel",
            use_container_width=True
        ):

            st.session_state.show_new_notebook = False

            st.rerun()


# =========================================================
# CURRENT NOTEBOOK
# =========================================================

notebook = get_current_notebook()

if notebook is None:

    st.info(
        "📓 အရင်ဆုံး ဘယ်ဘက်က **New Notebook** ကိုနှိပ်ပြီး "
        "ဇာတ်ကားအသစ်တစ်ကား ဖန်တီးပါ။"
    )

    st.stop()


st.sidebar.markdown("---")

st.sidebar.subheader("⚙️ Gemini Settings")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password",
    placeholder="AIza..."
)

st.sidebar.caption(
    "API Key ကို ဒီနေရာမှာပဲ ထည့်ပါ။ "
    "Code ထဲမှာ Key ကို မရေးထားပါ။"
)


# =========================================================
# LANGUAGE
# =========================================================

st.sidebar.markdown("---")

st.sidebar.subheader("🌐 Output Language")

language_options = [
    "မြန်မာ (Burmese)",
    "中文 (Chinese)",
    "English",
    "ไทย (Thai)",
    "Other"
]

current_language = notebook.get(
    "language",
    "မြန်မာ (Burmese)"
)

language = st.sidebar.selectbox(
    "ဇာတ်လမ်း / Dialogue ဘာသာစကား",
    language_options,
    index=(
        language_options.index(current_language)
        if current_language in language_options
        else 0
    )
)

custom_language = notebook.get(
    "custom_language",
    ""
)

if language == "Other":

    custom_language = st.sidebar.text_input(
        "ဘာသာစကားအမည်",
        value=custom_language,
        placeholder="ဥပမာ - Korean"
    )


# =========================================================
# SAVE LANGUAGE
# =========================================================

notebook["language"] = language
notebook["custom_language"] = custom_language

save_notebooks(
    st.session_state.notebooks
)


# =========================================================
# OUTPUT LANGUAGE
# =========================================================

if language == "မြန်မာ (Burmese)":

    output_language = "Burmese (Myanmar language)"

elif language == "中文 (Chinese)":

    output_language = "Chinese (Simplified Chinese)"

elif language == "English":

    output_language = "English"

elif language == "ไทย (Thai)":

    output_language = "Thai"

else:

    if custom_language.strip():

        output_language = custom_language.strip()

    else:

        output_language = "the language specified by the user"


# =========================================================
# NOTEBOOK TITLE
# =========================================================

st.header(
    f"📓 {st.session_state.current_notebook}"
)

st.caption(
    "ဒီ Notebook က ဒီဇာတ်ကားအတွက် သီးသန့်သိမ်းထားပါသည်။"
)


# =========================================================
# STORY INPUT
# =========================================================

st.subheader("📖 ဇာတ်လမ်းအကြမ်း")

story_input = st.text_area(
    "ဇာတ်လမ်းအကြမ်းထည့်ပါ",
    height=220,
    value=notebook.get("story", ""),
    placeholder="""ဥပမာ -

မင်းသမီးက ချမ်းသာပြီး မာနကြီးတယ်။
မင်းသားက ဆင်းရဲပေမယ့် ရိုးသားပြီး ကြင်နာတတ်တယ်။
အစပိုင်းမှာ မင်းသမီးက မင်းသားကို အထင်သေးပြီး အနိုင်ကျင့်တယ်။
နောက်ပိုင်းမှာ မင်းသားရဲ့ စိတ်ကောင်းကို သိလာပြီး ချစ်မိသွားတယ်။

အချစ်၊ အထင်လွဲမှု၊ အဆင့်အတန်းကွာခြားမှု၊
မိသားစုပြဿနာနဲ့ ပြန်လည်သင့်မြတ်မှုတွေ ပါဝင်မယ်။"""
)


# =========================================================
# CHARACTER INFORMATION
# =========================================================

st.subheader("👥 Character Information")

character_input = st.text_area(
    "ဇာတ်ကောင်အချက်အလက်",
    height=180,
    value=notebook.get("characters", ""),
    placeholder="""ဥပမာ -

မင်းသမီး - မေသဇင်၊ အသက် ၂၃၊ ချမ်းသာသောမိသားစု၊ မာနကြီး
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

current_scene_count = notebook.get(
    "scenes_per_volume",
    150
)

if current_scene_count not in scene_options:
    current_scene_count = 150

scene_count = st.selectbox(
    "🎬 အတွဲတစ်တွဲမှာ Scene ဘယ်နှစ်ခန်းထုတ်မလဲ?",
    scene_options,
    index=scene_options.index(
        current_scene_count
    )
)

st.caption(
    f"Scene {scene_count} ခန်း | "
    "ရွေးချယ်နိုင်သောအရေအတွက် 5 → 10 → 15 → ... → 150"
)


# =========================================================
# CURRENT VOLUME
# =========================================================

current_volume = notebook.get(
    "volume",
    1
)

st.markdown("---")

st.subheader(
    f"📚 လက်ရှိအတွဲ — အတွဲ {current_volume}"
)


# =========================================================
# SAVE BASIC DATA
# =========================================================

notebook["story"] = story_input
notebook["characters"] = character_input
notebook["scenes_per_volume"] = scene_count

save_notebooks(
    st.session_state.notebooks
)


# =========================================================
# GENERATE CURRENT VOLUME
# =========================================================

if st.button(
    f"🚀 အတွဲ {current_volume} — "
    f"Scene {scene_count} ခန်း ထုတ်မည်",
    use_container_width=True
):

    if not api_key.strip():

        st.error(
            "❌ Gemini API Key ထည့်ပါ။"
        )

    elif not story_input.strip():

        st.error(
            "❌ ဇာတ်လမ်းအကြမ်း ထည့်ပါ။"
        )

    elif language == "Other" and not custom_language.strip():

        st.error(
            "❌ Other ရွေးထားသောကြောင့် "
            "ဘာသာစကားအမည်ထည့်ပါ။"
        )

    else:

        try:

            client = genai.Client(
                api_key=api_key.strip()
            )

            prompt = f"""
You are a professional long-form drama story writer.

Create Volume {current_volume}
of the user's drama story.

TOTAL SCENES:
{scene_count}

OUTPUT LANGUAGE:
{output_language}

LANGUAGE RULES:
- Scene Description must be written in {output_language}.
- Dialogue must be written in {output_language}.
- Volume Summary must be written in {output_language}.
- Character descriptions must be written in {output_language}.
- Image Prompt MUST be written in English.

ORIGINAL STORY:
{story_input}

CHARACTER INFORMATION:
{character_input}

PREVIOUS VOLUME CONTINUITY:
{notebook.get("continuity", "")}

IMPORTANT:

1. Write exactly {scene_count} scenes.
2. Number scenes from Scene 1 to Scene {scene_count}.
3. Do not skip scene numbers.
4. Every scene must connect naturally.
5. Keep character appearance consistent.
6. Keep character personality consistent.
7. Keep relationships consistent.
8. Do not randomly change the story.
9. Do not finish the whole story too early.
10. Leave a continuation point for the next volume.
11. Every scene must have meaningful story progression.
12. Dialogue must match the situation.
13. Image Prompts must maintain character appearance.
14. Image Prompts must be cinematic vertical 9:16.
15. Do not put dialogue inside Image Prompts.

USE EXACT FORMAT:

===== VOLUME {current_volume} =====

Volume Title:
...

Volume Summary:
...

===== SCENE 1 =====

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

Continue the exact same format until:

===== SCENE {scene_count} =====

Then write:

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

            with st.spinner(
                f"⏳ အတွဲ {current_volume} "
                f"Scene {scene_count} ခန်း ရေးနေပါပြီ..."
            ):

                response = client.models.generate_content(
                    model="gemini-3.8-flash",
                    contents=prompt
                )

                result = response.text

            # =================================================
            # PARSE SCENES
            # =================================================

            scenes = {}

            lines = result.splitlines()

            current_scene = None
            current_content = []

            for line in lines:

                stripped = line.strip()

                if stripped.startswith(
                    "===== SCENE "
                ):

                    if current_scene is not None:

                        scenes[current_scene] = (
                            "\n".join(
                                current_content
                            ).strip()
                        )

                    number_text = (
                        stripped
                        .replace(
                            "===== SCENE ",
                            ""
                        )
                        .replace(
                            " =====",
                            ""
                        )
                        .strip()
                    )

                    try:

                        current_scene = int(
                            number_text
                        )

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

                scenes[current_scene] = (
                    "\n".join(
                        current_content
                    ).strip()
                )


            # =================================================
            # CONTINUITY
            # =================================================

            continuity_marker = (
                "===== NEXT VOLUME CONTINUITY ====="
            )

            continuity = ""

            if continuity_marker in result:

                continuity = (
                    result.split(
                        continuity_marker,
                        1
                    )[1].strip()
                )


            # =================================================
            # SAVE VOLUME
            # =================================================

            notebook["volumes"][
                str(current_volume)
            ] = {
                "result": result,
                "scenes": scenes,
                "scene_count": scene_count,
                "continuity": continuity
            }

            notebook["continuity"] = continuity

            notebook["volume"] = current_volume

            notebook["scenes_per_volume"] = scene_count

            save_notebooks(
                st.session_state.notebooks
            )

            st.success(
                f"✅ အတွဲ {current_volume} "
                f"Scene {scene_count} ခန်း "
                "အောင်မြင်စွာ ထုတ်ပြီးပါပြီ။"
            )

            st.rerun()

        except Exception as e:

            st.error(
                "❌ AI ထုတ်တဲ့အချိန် Error ဖြစ်ပါတယ်။"
            )

            st.code(
                str(e),
                language="text"
            )


# =========================================================
# LOAD CURRENT VOLUME
# =========================================================

volumes = notebook.get(
    "volumes",
    {}
)

current_volume_data = volumes.get(
    str(current_volume)
)

if current_volume_data:

    scenes = current_volume_data.get(
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

    # =====================================================
    # GROUP 5 SCENES
    # =====================================================

    for start in range(
        0,
        len(scene_numbers),
        5
    ):

        group_numbers = scene_numbers[
            start:start + 5
        ]

        first_scene = group_numbers[0]
        last_scene = group_numbers[-1]

        group_text = ""

        for number in group_numbers:

            group_text += (
                f"===== SCENE {number} =====\n\n"
                f"{scenes[str(number)]}\n\n"
            )

        st.markdown(
            f"### 📦 Scene {first_scene} – {last_scene}"
        )

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

    selected_history_volume = st.selectbox(
        "ကြည့်ချင်သောအတွဲ",
        volume_numbers,
        index=len(volume_numbers) - 1
    )

    history_data = volumes[
        str(selected_history_volume)
    ]

    history_scenes = history_data.get(
        "scenes",
        {}
    )

    history_numbers = sorted(
        [int(x) for x in history_scenes.keys()]
    )

    for start in range(
        0,
        len(history_numbers),
        5
    ):

        group_numbers = history_numbers[
            start:start + 5
        ]

        group_text = ""

        for number in group_numbers:

            group_text += (
                f"===== SCENE {number} =====\n\n"
                f"{history_scenes[str(number)]}\n\n"
            )

        st.code(
            group_text,
            language="text"
        )


# =========================================================
# NEXT VOLUME
# =========================================================

if current_volume_data:

    st.markdown("---")

    st.subheader(
        "📚 ဇာတ်လမ်းဆက်ရန်"
    )

    next_volume = current_volume + 1

    if st.button(
        f"📚 အတွဲ {next_volume} ဆက်လက်ထုတ်ရန်",
        use_container_width=True
    ):

        if not api_key.strip():

            st.error(
                "❌ Gemini API Key ထည့်ပါ။"
            )

        else:

            try:

                client = genai.Client(
                    api_key=api_key.strip()
                )

                previous_continuity = notebook.get(
                    "continuity",
                    ""
                )

                prompt = f"""
Continue the user's drama story.

PREVIOUS VOLUME:
Volume {current_volume}

NEW VOLUME:
Volume {next_volume}

Write exactly {scene_count} scenes.

OUTPUT LANGUAGE:
{output_language}

ORIGINAL STORY:
{notebook.get("story", "")}

CHARACTER INFORMATION:
{notebook.get("characters", "")}

PREVIOUS VOLUME CONTINUITY:
{previous_continuity}

RULES:

1. Continue directly from Volume {current_volume}.
2. Do NOT restart the story.
3. Keep all existing characters consistent.
4. Keep appearance consistent.
5. Keep personality consistent.
6. Keep relationships consistent.
7. Continue unresolved conflicts naturally.
8. Dialogue must be in {output_language}.
9. Scene Description must be in {output_language}.
10. Character information must be in {output_language}.
11. Image Prompt must be in English.
12. Image Prompt must contain cinematic vertical 9:16.
13. Write exactly Scene 1 through Scene {scene_count}.
14. Do not skip scene numbers.
15. Every scene must move the story forward.
16. Do not finish the whole story unless appropriate.
17. End with continuity for the following volume.

USE EXACT FORMAT:

===== VOLUME {next_volume} =====

Volume Title:
...

Volume Summary:
...

===== SCENE 1 =====

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

===== SCENE {scene_count} =====

Then:

===== NEXT VOLUME CONTINUITY =====

Write the important information needed for the next volume.
"""

                with st.spinner(
                    f"⏳ အတွဲ {next_volume} "
                    "ဆက်ရေးနေပါပြီ..."
                ):

                    response = client.models.generate_content(
                        model="gemini-3.8-flash",
                        contents=prompt
                    )

                    result = response.text


                # =================================================
                # PARSE NEW VOLUME
                # =================================================

                new_scenes = {}

                lines = result.splitlines()

                current_scene = None
                current_content = []

                for line in lines:

                    stripped = line.strip()

                    if stripped.startswith(
                        "===== SCENE "
                    ):

                        if current_scene is not None:

                            new_scenes[
                                current_scene
                            ] = "\n".join(
                                current_content
                            ).strip()

                        number_text = (
                            stripped
                            .replace(
                                "===== SCENE ",
                                ""
                            )
                            .replace(
                                " =====",
                                ""
                            )
                            .strip()
                        )

                        try:

                            current_scene = int(
                                number_text
                            )

                            current_content = []

                        except ValueError:

                            current_scene = None
                            current_content = []

                    elif current_scene is not None:

                        if stripped.startswith(
                            "===== NEXT VOLUME CONTINUITY ====="
                        ):

                            break

                        current_content.append(
                            line
                        )

                if current_scene is not None:

                    new_scenes[
                        current_scene
                    ] = "\n".join(
                        current_content
                    ).strip()


                # =================================================
                # NEW CONTINUITY
                # =================================================

                continuity_marker = (
                    "===== NEXT VOLUME CONTINUITY ====="
                )

                new_continuity = ""

                if continuity_marker in result:

                    new_continuity = (
                        result.split(
                            continuity_marker,
                            1
                        )[1].strip()
                    )


                # =================================================
                # SAVE NEW VOLUME
                # =================================================

                notebook["volumes"][
                    str(next_volume)
                ] = {
                    "result": result,
                    "scenes": new_scenes,
                    "scene_count": scene_count,
                    "continuity": new_continuity
                }

                notebook["continuity"] = (
                    new_continuity
                )

                notebook["volume"] = next_volume

                save_notebooks(
                    st.session_state.notebooks
                )

                st.success(
                    f"✅ အတွဲ {next_volume} "
                    "အောင်မြင်စွာ ဆက်ရေးပြီးပါပြီ။"
                )

                st.rerun()


            except Exception as e:

                st.error(
                    "❌ နောက်အတွဲဆက်တဲ့အချိန် "
                    "Error ဖြစ်ပါတယ်။"
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
        "🔗 နောက်အတွဲအတွက် Continuity"
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
