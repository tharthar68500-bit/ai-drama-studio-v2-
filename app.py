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
    "ဇာတ်လမ်းအကြမ်းထည့်ပြီး အတွဲလိုက် Scene၊ Dialogue နှင့် "
    "Image Prompt များကို ဖန်တီးနိုင်ပါသည်။"
)

# =========================================================
# SESSION STATE
# =========================================================

if "volume" not in st.session_state:
    st.session_state.volume = 1

if "story_input" not in st.session_state:
    st.session_state.story_input = ""

if "characters" not in st.session_state:
    st.session_state.characters = ""

if "current_result" not in st.session_state:
    st.session_state.current_result = ""

if "scenes" not in st.session_state:
    st.session_state.scenes = {}

if "continuity" not in st.session_state:
    st.session_state.continuity = ""

if "has_generated" not in st.session_state:
    st.session_state.has_generated = False

# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.header("⚙️ Settings")

api_key = st.sidebar.text_input(
    "Gemini API Key",
    type="password"
)

# =========================================================
# LANGUAGE
# =========================================================

st.sidebar.markdown("---")
st.sidebar.subheader("🌐 Output Language")

language = st.sidebar.selectbox(
    "ဇာတ်လမ်း / Dialogue ဘာသာစကား",
    [
        "မြန်မာ (Burmese)",
        "中文 (Chinese)",
        "English",
        "ไทย (Thai)",
        "Other"
    ]
)

custom_language = ""

if language == "Other":
    custom_language = st.sidebar.text_input(
        "ဘာသာစကားအမည်ထည့်ပါ",
        placeholder="ဥပမာ - Korean"
    )

# =========================================================
# STORY INPUT
# =========================================================

st.subheader("📖 ဇာတ်လမ်းအကြမ်း")

story_input = st.text_area(
    "ဇာတ်လမ်းအကြမ်းထည့်ပါ",
    height=220,
    value=st.session_state.story_input,
    placeholder="""ဥပမာ -

မင်းသမီးက ချမ်းသာပြီး မာနကြီးတယ်။
မင်းသားက ဆင်းရဲပေမယ့် ရိုးသားပြီး ကြင်နာတတ်တယ်။
အစပိုင်းမှာ မင်းသမီးက မင်းသားကို အထင်သေးပြီး အနိုင်ကျင့်တယ်။
နောက်ပိုင်းမှာ မင်းသားရဲ့ စိတ်ကောင်းကို သိလာပြီး ချစ်မိသွားတယ်။

အချစ်၊ အထင်လွဲမှု၊ အဆင့်အတန်းကွာခြားမှု၊
မိသားစုပြဿနာနဲ့ ပြန်လည်သင့်မြတ်မှုတွေ ပါဝင်မယ်။"""
)

# =========================================================
# SCENE COUNT
# =========================================================

scene_count = st.selectbox(
    "🎬 အတွဲတစ်တွဲမှာ Scene ဘယ်နှစ်ခန်းထုတ်မလဲ?",
    [10, 20, 30, 40, 50],
    index=2
)

st.caption(
    f"ရွေးထားသောအရေအတွက်: Scene {scene_count} ခန်း | "
    "5 Scene စီ အုပ်စုခွဲပြီး Copy လုပ်နိုင်မည်"
)

# =========================================================
# CHARACTER INFORMATION
# =========================================================

st.subheader("👥 Character Information")

character_input = st.text_area(
    "ဇာတ်ကောင်အချက်အလက်",
    height=160,
    value=st.session_state.characters,
    placeholder="""ဥပမာ -

မင်းသမီး - မေသဇင်၊ အသက် ၂၃၊ ချမ်းသာသောမိသားစု၊ မာနကြီး
မင်းသား - အောင်ခန့်၊ အသက် ၂၅၊ ဆင်းရဲသော်လည်း ရိုးသား
မင်းသမီးအဖေ - ဦးထွန်း
မင်းသမီးအမေ - ဒေါ်သီတာ"""
)

# =========================================================
# CURRENT VOLUME
# =========================================================

st.markdown("---")

st.subheader(
    f"📚 လက်ရှိအတွဲ — အတွဲ {st.session_state.volume}"
)

# =========================================================
# LANGUAGE INSTRUCTION
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
# GENERATE BUTTON
# =========================================================

generate_button = st.button(
    f"🚀 အတွဲ {st.session_state.volume} "
    f"Scene {scene_count} ခန်း ထုတ်မည်",
    use_container_width=True
)

# =========================================================
# GENERATE CURRENT VOLUME
# =========================================================

if generate_button:

    if not api_key.strip():

        st.error(
            "❌ ဘယ်ဘက် Settings မှာ Gemini API Key ထည့်ပါ။"
        )

    elif not story_input.strip():

        st.error(
            "❌ ဇာတ်လမ်းအကြမ်း အရင်ထည့်ပါ။"
        )

    elif language == "Other" and not custom_language.strip():

        st.error(
            "❌ Other ရွေးထားသောကြောင့် ဘာသာစကားအမည်ထည့်ပါ။"
        )

    else:

        try:
            # Save user information
            st.session_state.story_input = story_input
            st.session_state.characters = character_input

            client = genai.Client(
                api_key=api_key.strip()
            )

            prompt = f"""
You are a professional drama story writer.

Create Volume {st.session_state.volume}
of the user's drama story.

TOTAL SCENES:
{scene_count}

OUTPUT LANGUAGE:
{output_language}

IMPORTANT LANGUAGE RULE:
- Scene Description must be written in {output_language}.
- Dialogue must be written in {output_language}.
- Episode/Volume Summary must be written in {output_language}.
- Character descriptions must be written in {output_language}.
- Image Prompt MUST be written in English because it will later be used with image generation AI.

STORY:
{story_input}

CHARACTER INFORMATION:
{character_input}

PREVIOUS VOLUME CONTINUITY:
{st.session_state.continuity}

IMPORTANT STORY RULES:

1. Write exactly Scene 1 through Scene {scene_count}.
2. Do not skip scene numbers.
3. Every scene must connect naturally to the previous scene.
4. Keep character appearance consistent.
5. Keep character personality consistent.
6. Keep relationships consistent.
7. Do not suddenly change a character's personality.
8. Do not end the entire story early.
9. Build the story naturally toward future volumes.
10. The final scene must leave a clear continuation point for the next volume.
11. Each scene should contain meaningful story progression.
12. Dialogue must match the characters and situation.
13. Image prompts must describe the characters consistently.
14. Image prompts must include cinematic vertical 9:16.
15. Do not put dialogue inside the Image Prompt.
16. Do not write explanations outside the requested format.

USE THIS EXACT FORMAT:

===== VOLUME {st.session_state.volume} =====

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
Include character appearance, clothing, location, lighting,
emotion, camera composition and cinematic details.

===== SCENE 2 =====

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

Continue exactly the same format until:

===== SCENE {scene_count} =====

Then write:

===== NEXT VOLUME CONTINUITY =====

Write the important information that must be remembered
for the next volume:
- Character emotional states
- Relationships
- Important events
- Unresolved conflicts
- Important locations
- Important objects
- What should happen next
"""

            with st.spinner(
                f"⏳ အတွဲ {st.session_state.volume} "
                f"Scene {scene_count} ခန်း ရေးနေပါပြီ..."
            ):

                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )

                result = response.text

            # Save complete result
            st.session_state.current_result = result
            st.session_state.has_generated = True

            # =================================================
            # PARSE SCENES
            # =================================================

            scenes = {}

            lines = result.splitlines()

            current_scene = None
            current_content = []

            for line in lines:

                stripped = line.strip()

                if stripped.startswith("===== SCENE "):

                    if current_scene is not None:
                        scenes[current_scene] = "\n".join(
                            current_content
                        ).strip()

                    number_text = stripped.replace(
                        "===== SCENE ", ""
                    ).replace(
                        " =====", ""
                    ).strip()

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
                scenes[current_scene] = "\n".join(
                    current_content
                ).strip()

            st.session_state.scenes = scenes

            # =================================================
            # SAVE CONTINUITY
            # =================================================

            continuity_marker = (
                "===== NEXT VOLUME CONTINUITY ====="
            )

            if continuity_marker in result:

                st.session_state.continuity = (
                    result.split(
                        continuity_marker,
                        1
                    )[1].strip()
                )

            st.success(
                f"✅ အတွဲ {st.session_state.volume} "
                f"Scene {scene_count} ခန်း ထွက်လာပါပြီ။"
            )

        except Exception as e:

            st.error(
                "❌ AI ထုတ်တဲ့အချိန်မှာ Error ဖြစ်ပါတယ်။"
            )

            st.code(
                str(e),
                language="text"
            )

# =========================================================
# DISPLAY RESULTS
# =========================================================

if st.session_state.scenes:

    st.markdown("---")

    st.subheader(
        f"🎬 အတွဲ {st.session_state.volume} "
        f"— Scene {scene_count} ခန်း"
    )

    scene_numbers = sorted(
        st.session_state.scenes.keys()
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
                f"{st.session_state.scenes[number]}\n\n"
            )

        st.markdown(
            f"### 📦 Scene {first_scene} – {last_scene}"
        )

        # Copy button is provided by Streamlit
        st.code(
            group_text,
            language="text"
        )

# =========================================================
# NEXT VOLUME BUTTON
# =========================================================

if st.session_state.has_generated:

    st.markdown("---")

    st.subheader("📚 ဇာတ်လမ်းဆက်ရန်")

    if st.button(
        f"📚 အတွဲ {st.session_state.volume + 1} ဆက်ရန်",
        use_container_width=True
    ):

        if not api_key.strip():

            st.error(
                "❌ Gemini API Key ထည့်ထားရန်လိုပါသည်။"
            )

        else:

            try:

                old_volume = st.session_state.volume

                # Increase volume
                st.session_state.volume += 1

                client = genai.Client(
                    api_key=api_key.strip()
                )

                prompt = f"""
Continue the drama story from Volume {old_volume}
into Volume {st.session_state.volume}.

Write exactly {scene_count} scenes.

OUTPUT LANGUAGE:
{output_language}

ORIGINAL STORY:
{st.session_state.story_input}

CHARACTER INFORMATION:
{st.session_state.characters}

CONTINUITY FROM PREVIOUS VOLUME:
{st.session_state.continuity}

IMPORTANT:

1. Continue directly from the previous volume.
2. Do not restart the story.
3. Do not introduce unnecessary new characters.
4. Keep all existing characters consistent.
5. Keep appearance consistent.
6. Keep personality consistent.
7. Keep relationships consistent.
8. Dialogue must be in {output_language}.
9. Scene Description must be in {output_language}.
10. Character information must be in {output_language}.
11. Image Prompt must be in English.
12. Image Prompt must contain cinematic vertical 9:16.
13. Write exactly Scene 1 through Scene {scene_count}.
14. Each scene must move the story forward.
15. Do not finish the entire story unless this is clearly the final volume.
16. End with continuity for the next volume.

USE EXACT FORMAT:

===== VOLUME {st.session_state.volume} =====

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

Continue until Scene {scene_count}.

===== NEXT VOLUME CONTINUITY =====

Write the continuity information for the next volume.
"""

                with st.spinner(
                    f"⏳ အတွဲ {st.session_state.volume} "
                    f"ကို အတွဲ {old_volume} ကနေ ဆက်ရေးနေပါပြီ..."
                ):

                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=prompt
                    )

                    result = response.text

                st.session_state.current_result = result

                # =================================================
                # PARSE NEW SCENES
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

                st.session_state.scenes = scenes

                # =================================================
                # UPDATE CONTINUITY
                # =================================================

                continuity_marker = (
                    "===== NEXT VOLUME CONTINUITY ====="
                )

                if continuity_marker in result:

                    st.session_state.continuity = (
                        result.split(
                            continuity_marker,
                            1
                        )[1].strip()
                    )

                st.success(
                    f"✅ အတွဲ {st.session_state.volume} "
                    f"ကို အောင်မြင်စွာ ဆက်ရေးပြီးပါပြီ။"
                )

            except Exception as e:

                # If generation failed, restore old volume number
                st.session_state.volume = old_volume

                st.error(
                    "❌ နောက်အတွဲဆက်တဲ့အချိန် Error ဖြစ်ပါတယ်။"
                )

                st.code(
                    str(e),
                    language="text"
                )

# =========================================================
# CHARACTER MEMORY
# =========================================================

if st.session_state.characters:

    st.sidebar.markdown("---")

    st.sidebar.subheader(
        "👥 Character Memory"
    )

    st.sidebar.text_area(
        "သိမ်းထားသော Character Information",
        value=st.session_state.characters,
        height=250,
        disabled=True
    )

# =========================================================
# CONTINUITY VIEW
# =========================================================

if st.session_state.continuity:

    st.markdown("---")

    with st.expander(
        "🔗 နောက်အတွဲအတွက် Continuity ကိုကြည့်ရန်"
    ):

        st.write(
            st.session_state.continuity
        )

# =========================================================
# FOOTER
# =========================================================

st.markdown("---")

st.caption(
    "🎬 Stage 1 — Story → Volume → Scenes → Dialogue → Image Prompts"
)
