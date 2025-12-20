# bilingual_flashcards_from_docx.py
import base64
import streamlit as st
from docx import Document
import re
from gtts import gTTS
import io
import time

# 📂 Path to your text document
doc_path = "Flash Card Text.docx"

# Session state for audio control
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = None  # Store which audio is currently playing (card_index_lang)
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False

# 📖 Load text from Word document
def load_flashcards(doc_path):
    doc = Document(doc_path)
    flashcards = []
    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:  # skip empty lines
            continue
        
        # Split by " : " (space-colon-space) to handle the format correctly
        parts = text.split(" : ")
        
        if len(parts) >= 3:
            # Extract just the phrase (remove "Student:" or "Teacher:" prefix)
            english_full = parts[0].strip()
            english = re.sub(r'^(Student|Teacher):\s*', '', english_full)
            
            # Extract Arabic text from [text] format
            arabic_raw = parts[1].strip()
            arabic_match = re.search(r'\[(.*?)\]', arabic_raw)
            arabic = arabic_match.group(1) if arabic_match else arabic_raw
            
            # Get transliteration
            translit = parts[2].strip()
            
            flashcards.append((english, arabic, translit))
    
    return flashcards

# 🚫 Remove emojis from text using regex
def remove_emojis(text):
    """Remove all emojis from text using regex"""
    # Unicode ranges for emojis
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002500-\U00002BEF"  # Chinese characters and others
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001f926-\U0001f937"
        "\U00010000-\U0010ffff"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u200d"
        "\u23cf"
        "\u23e9"
        "\u231a"
        "\ufe0f"  # dingbats
        "\u3030"
        "]+", 
        flags=re.UNICODE
    )
    return emoji_pattern.sub(r'', text)

# 🔊 Generate audio file from text (without emojis)
def text_to_speech(text, lang="en"):
    """Convert text to speech and return audio bytes"""
    try:
        # Remove emojis from text before converting to speech
        clean_text = remove_emojis(text)
        
        # Clean up extra spaces that might be left after removing emojis
        clean_text = ' '.join(clean_text.split())
        
        # If the text becomes empty after removing emojis, use a fallback
        if not clean_text.strip():
            if lang == "en":
                clean_text = "No text available"
            else:
                clean_text = "لا يوجد نص"
            
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        audio_bytes = io.BytesIO()
        tts.write_to_fp(audio_bytes)
        audio_bytes.seek(0)
        return audio_bytes.getvalue()
    except Exception as e:
        st.error(f"Error generating audio: {e}")
        return None

# ⏹️ Stop audio function
def stop_audio():
    """Stop currently playing audio"""
    st.session_state.stop_requested = True
    st.session_state.audio_playing = None
    st.rerun()

# 🎴 Display flashcards with voiceover
def show_flashcards(flashcards, reverse=False):
    st.title("📚 Bilingual Flashcards with Voiceover")
    st.write("🔹 Check the box below each card to reveal the translation and play sound.")
    st.write("🔁 Audio will loop until you click the Stop button.")
    
    # Global stop button in sidebar
    with st.sidebar:
        if st.session_state.audio_playing:
            st.warning(f"🔊 Currently playing: {st.session_state.audio_playing}")
            if st.button("⏹️ Stop All Audio", type="primary", use_container_width=True):
                stop_audio()
        else:
            st.info("No audio currently playing")
    
    for i, (english, arabic, translit) in enumerate(flashcards):
        with st.container():
            st.markdown('<div style="border:1px solid #ddd; padding:15px; border-radius:8px; margin-bottom:15px;">', unsafe_allow_html=True)
            
            if not reverse:
                # English → Arabic mode
                # English text in RED
                st.markdown(f'<h3 style="color:#FF0000;">🔹 <strong>{english}</strong></h3>', unsafe_allow_html=True)
                
                # English voice controls
                current_audio_id = f"card_{i}_en"
                is_playing = st.session_state.audio_playing == current_audio_id
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    voice_key = f"en_voice_{i}"
                    if st.button(f"🔊 Play English", key=voice_key, disabled=is_playing):
                        # Generate and store audio
                        audio_bytes = text_to_speech(english, lang="en")
                        if audio_bytes:
                            st.session_state[f"audio_{current_audio_id}"] = audio_bytes
                            st.session_state.audio_playing = current_audio_id
                            st.session_state.stop_requested = False
                            st.rerun()
                
                with col2:
                    if is_playing:
                        if st.button(f"⏹️ Stop", key=f"stop_en_{i}", type="secondary"):
                            stop_audio()
                
                # Show looping audio player if this audio is playing
                if is_playing and not st.session_state.stop_requested:
                    audio_bytes = st.session_state.get(f"audio_{current_audio_id}")
                    if audio_bytes:
                        # Create looping audio player
                        audio_html = f"""
                        <audio autoplay loop style="display:none;">
                        <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                        Your browser does not support the audio element.
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                        st.success("🔁 Playing English audio on loop...")
                
                if st.checkbox("Show Arabic & Transliteration", key=f"en_ar_{i}"):
                    # Arabic text in RED
                    st.markdown(
                        f"""
                        <div style='text-align:right; direction:rtl; font-size:32px; color:#FF0000; font-weight:bold; margin-top:15px;'>{arabic}</div>
                        <div style='text-align:left; font-size:18px; font-style:italic; color:#555; margin-top:10px;'>Transliteration: {translit}</div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # Arabic voice controls
                    current_audio_id_ar = f"card_{i}_ar"
                    is_playing_ar = st.session_state.audio_playing == current_audio_id_ar
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        voice_key = f"ar_voice_{i}"
                        if st.button(f"🔊 Play Arabic", key=voice_key, disabled=is_playing_ar):
                            audio_bytes = text_to_speech(arabic, lang="ar")
                            if audio_bytes:
                                st.session_state[f"audio_{current_audio_id_ar}"] = audio_bytes
                                st.session_state.audio_playing = current_audio_id_ar
                                st.session_state.stop_requested = False
                                st.rerun()
                    
                    with col2:
                        if is_playing_ar:
                            if st.button(f"⏹️ Stop", key=f"stop_ar_{i}", type="secondary"):
                                stop_audio()
                    
                    # Show looping audio player if Arabic audio is playing
                    if is_playing_ar and not st.session_state.stop_requested:
                        audio_bytes = st.session_state.get(f"audio_{current_audio_id_ar}")
                        if audio_bytes:
                            # Create looping audio player
                            audio_html = f"""
                            <audio autoplay loop style="display:none;">
                            <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                            Your browser does not support the audio element.
                            </audio>
                            """
                            st.markdown(audio_html, unsafe_allow_html=True)
                            st.success("🔁 Playing Arabic audio on loop...")
            
            else:
                # Arabic → English mode
                # Arabic text in RED
                st.markdown(
                    f"<div style='text-align:right; direction:rtl; font-size:32px; color:#FF0000; font-weight:bold;'>{arabic}</div>",
                    unsafe_allow_html=True
                )
                
                # Arabic voice controls (first)
                current_audio_id = f"card_{i}_ar_first"
                is_playing = st.session_state.audio_playing == current_audio_id
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    voice_key = f"ar_voice_first_{i}"
                    if st.button(f"🔊 Play Arabic", key=voice_key, disabled=is_playing):
                        audio_bytes = text_to_speech(arabic, lang="ar")
                        if audio_bytes:
                            st.session_state[f"audio_{current_audio_id}"] = audio_bytes
                            st.session_state.audio_playing = current_audio_id
                            st.session_state.stop_requested = False
                            st.rerun()
                
                with col2:
                    if is_playing:
                        if st.button(f"⏹️ Stop", key=f"stop_ar_first_{i}", type="secondary"):
                            stop_audio()
                
                # Show looping audio player if this audio is playing
                if is_playing and not st.session_state.stop_requested:
                    audio_bytes = st.session_state.get(f"audio_{current_audio_id}")
                    if audio_bytes:
                        # Create looping audio player
                        audio_html = f"""
                        <audio autoplay loop style="display:none;">
                        <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                        Your browser does not support the audio element.
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                        st.success("🔁 Playing Arabic audio on loop...")
                
                if st.checkbox("Show English & Transliteration", key=f"ar_en_{i}"):
                    # English text in RED
                    st.markdown(
                        f"""
                        <div style='text-align:left; font-size:28px; color:#FF0000; font-weight:bold; margin-top:15px;'>{english}</div>
                        <div style='text-align:left; font-size:18px; font-style:italic; color:#555; margin-top:10px;'>Transliteration: {translit}</div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                    # English voice controls (second)
                    current_audio_id_en = f"card_{i}_en_second"
                    is_playing_en = st.session_state.audio_playing == current_audio_id_en
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        voice_key = f"en_voice_second_{i}"
                        if st.button(f"🔊 Play English", key=voice_key, disabled=is_playing_en):
                            audio_bytes = text_to_speech(english, lang="en")
                            if audio_bytes:
                                st.session_state[f"audio_{current_audio_id_en}"] = audio_bytes
                                st.session_state.audio_playing = current_audio_id_en
                                st.session_state.stop_requested = False
                                st.rerun()
                    
                    with col2:
                        if is_playing_en:
                            if st.button(f"⏹️ Stop", key=f"stop_en_second_{i}", type="secondary"):
                                stop_audio()
                    
                    # Show looping audio player if English audio is playing
                    if is_playing_en and not st.session_state.stop_requested:
                        audio_bytes = st.session_state.get(f"audio_{current_audio_id_en}")
                        if audio_bytes:
                            # Create looping audio player
                            audio_html = f"""
                            <audio autoplay loop style="display:none;">
                            <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                            Your browser does not support the audio element.
                            </audio>
                            """
                            st.markdown(audio_html, unsafe_allow_html=True)
                            st.success("🔁 Playing English audio on loop...")
            
            st.markdown('</div>', unsafe_allow_html=True)

# 🚀 Run the app
if __name__ == "__main__":
    try:
        flashcards = load_flashcards(doc_path)
        
        if not flashcards:
            st.warning("⚠️ No flashcards loaded. Check document format.")
        else:
            st.success(f"✅ Loaded {len(flashcards)} flashcards with voiceover!")
            
            # Voiceover settings
            with st.expander("⚙️ Voice Settings"):
                st.info("Note: Voice synthesis uses Google Text-to-Speech (gTTS)")
                st.write("✅ Emojis are automatically removed from voice output")
                st.write("🔁 Audio loops continuously until Stop button is clicked")
                st.write("Example: 'Hello 👋' will speak as 'Hello'")
                st.write("English voice: Standard English TTS")
                st.write("Arabic voice: Standard Arabic TTS")
                st.write("Internet connection is required for voice generation.")
            
            # Preview first parsed card
            with st.expander("🔍 Preview first card with voice"):
                en, ar, tr = flashcards[0]
                st.markdown(f'<span style="color:#FF0000; font-weight:bold;">English (display): {en}</span>', unsafe_allow_html=True)
                st.text(f"English (for voice): {remove_emojis(en)}")
                
                # Preview English audio with loop
                preview_audio_id = "preview_en"
                is_preview_playing = st.session_state.audio_playing == preview_audio_id
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔊 Play English", key="preview_en", disabled=is_preview_playing):
                        audio_bytes = text_to_speech(en, lang="en")
                        if audio_bytes:
                            st.session_state[f"audio_{preview_audio_id}"] = audio_bytes
                            st.session_state.audio_playing = preview_audio_id
                            st.session_state.stop_requested = False
                            st.rerun()
                
                with col2:
                    if is_preview_playing:
                        if st.button("⏹️ Stop", key="stop_preview_en", type="secondary"):
                            stop_audio()
                
                # Show looping audio player for preview
                if is_preview_playing and not st.session_state.stop_requested:
                    audio_bytes = st.session_state.get(f"audio_{preview_audio_id}")
                    if audio_bytes:
                        audio_html = f"""
                        <audio autoplay loop style="display:none;">
                        <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                        st.success("🔁 Playing English preview on loop...")
                
                st.markdown(f'<div style="text-align:right; direction:rtl; color:#FF0000; font-weight:bold;">Arabic (display): {ar}</div>', unsafe_allow_html=True)
                st.text(f"Arabic (for voice): {remove_emojis(ar)}")
                
                # Preview Arabic audio with loop
                preview_audio_id_ar = "preview_ar"
                is_preview_playing_ar = st.session_state.audio_playing == preview_audio_id_ar
                
                col1, col2 = st.columns([1, 1])
                with col1:
                    if st.button("🔊 Play Arabic", key="preview_ar", disabled=is_preview_playing_ar):
                        audio_bytes = text_to_speech(ar, lang="ar")
                        if audio_bytes:
                            st.session_state[f"audio_{preview_audio_id_ar}"] = audio_bytes
                            st.session_state.audio_playing = preview_audio_id_ar
                            st.session_state.stop_requested = False
                            st.rerun()
                
                with col2:
                    if is_preview_playing_ar:
                        if st.button("⏹️ Stop", key="stop_preview_ar", type="secondary"):
                            stop_audio()
                
                # Show looping audio player for Arabic preview
                if is_preview_playing_ar and not st.session_state.stop_requested:
                    audio_bytes = st.session_state.get(f"audio_{preview_audio_id_ar}")
                    if audio_bytes:
                        audio_html = f"""
                        <audio autoplay loop style="display:none;">
                        <source src="data:audio/mp3;base64,{base64.b64encode(audio_bytes).decode()}" type="audio/mp3">
                        </audio>
                        """
                        st.markdown(audio_html, unsafe_allow_html=True)
                        st.success("🔁 Playing Arabic preview on loop...")
                
                st.text(f"Transliteration: {tr}")
        
        mode = st.radio("Choose mode:", ["English → Arabic", "Arabic → English"])
        reverse = mode == "Arabic → English"
        show_flashcards(flashcards, reverse=reverse)
        
    except FileNotFoundError:
        st.error(f"❌ File not found: `{doc_path}`")
        st.info("Update the `doc_path` variable with the correct path.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
