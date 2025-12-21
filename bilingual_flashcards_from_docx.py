# bilingual_flashcards_from_docx.py
import base64
import streamlit as st
from docx import Document
import re
from gtts import gTTS
import io
import time
import random
import json
from datetime import datetime

# 📂 Path to your text document
doc_path = "Flash Card Text.docx"

# Session state initialization
if 'audio_playing' not in st.session_state:
    st.session_state.audio_playing = None
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False
if 'quiz_answers' not in st.session_state:
    st.session_state.quiz_answers = {}
if 'quiz_feedback' not in st.session_state:
    st.session_state.quiz_feedback = {}
if 'quiz_started' not in st.session_state:
    st.session_state.quiz_started = False
if 'quiz_completed' not in st.session_state:
    st.session_state.quiz_completed = False
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0
if 'quiz_flashcards' not in st.session_state:
    st.session_state.quiz_flashcards = []
if 'quiz_type' not in st.session_state:
    st.session_state.quiz_type = "English to Arabic"

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

# 🔊 Generate combined audio file (English followed by Arabic)
def generate_combined_audio(english_text, arabic_text):
    """Generate audio with English first, then Arabic"""
    try:
        # Generate English audio
        english_audio = text_to_speech(english_text, lang="en")
        
        # Generate Arabic audio
        arabic_audio = text_to_speech(arabic_text, lang="ar")
        
        if english_audio and arabic_audio:
            # Combine the audio bytes (simple concatenation)
            combined_bytes = english_audio + arabic_audio
            return combined_bytes
        else:
            return None
    except Exception as e:
        st.error(f"Error generating combined audio: {e}")
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
                
                col1, col2, col3 = st.columns([1, 1, 1])
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
                
                with col3:
                    # Download combined audio button
                    download_key = f"download_{i}"
                    combined_audio = generate_combined_audio(english, arabic)
                    if combined_audio:
                        filename = f"flashcard_{i+1}_english_arabic.mp3"
                        b64 = base64.b64encode(combined_audio).decode()
                        href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}" style="text-decoration:none;">'
                        st.markdown(f'{href}<button style="background-color:#4CAF50; color:white; padding:5px 10px; border:none; border-radius:5px; cursor:pointer;">⬇️ Download Audio</button></a>', unsafe_allow_html=True)
                
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
                
                col1, col2, col3 = st.columns([1, 1, 1])
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
                
                with col3:
                    # Download combined audio button
                    download_key = f"download_reverse_{i}"
                    combined_audio = generate_combined_audio(english, arabic)
                    if combined_audio:
                        filename = f"flashcard_{i+1}_arabic_english.mp3"
                        b64 = base64.b64encode(combined_audio).decode()
                        href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}" style="text-decoration:none;">'
                        st.markdown(f'{href}<button style="background-color:#4CAF50; color:white; padding:5px 10px; border:none; border-radius:5px; cursor:pointer;">⬇️ Download Audio</button></a>', unsafe_allow_html=True)
                
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

# 📝 Quiz functionality - SIMPLIFIED without scoring
def show_quiz(flashcards):
    st.title("📝 Language Learning Quiz")
    
    if not st.session_state.quiz_started:
        st.write("Test your knowledge with this interactive quiz!")
        st.write("You'll get immediate feedback after each answer.")
        st.write(f"Total flashcards available: {len(flashcards)}")
        
        col1, col2 = st.columns(2)
        with col1:
            quiz_type = st.selectbox(
                "Select quiz type:",
                ["English to Arabic", "Arabic to English", "Mixed"]
            )
        with col2:
            num_questions = st.slider(
                "Number of questions:",
                min_value=3,
                max_value=min(20, len(flashcards)),
                value=min(10, len(flashcards))
            )
        
        if st.button("🚀 Start Quiz", type="primary"):
            st.session_state.quiz_started = True
            st.session_state.quiz_completed = False
            st.session_state.quiz_answers = {}
            st.session_state.quiz_feedback = {}
            st.session_state.current_question_index = 0
            
            # Select random flashcards for the quiz
            if len(flashcards) <= num_questions:
                quiz_flashcards = flashcards.copy()
            else:
                quiz_flashcards = random.sample(flashcards, num_questions)
            
            st.session_state.quiz_flashcards = quiz_flashcards
            st.session_state.quiz_type = quiz_type
            st.rerun()
    
    else:
        quiz_flashcards = st.session_state.quiz_flashcards
        quiz_type = st.session_state.quiz_type
        current_index = st.session_state.current_question_index
        
        if not st.session_state.quiz_completed:
            # Show progress at the top (removed score)
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("Questions", f"{current_index + 1}/{len(quiz_flashcards)}")
            with col2:
                percentage = ((current_index) / len(quiz_flashcards)) * 100 if quiz_flashcards else 0
                st.metric("Progress", f"{percentage:.0f}%")
            
            st.markdown("---")
            
            if current_index < len(quiz_flashcards):
                english, arabic, translit = quiz_flashcards[current_index]
                question_num = current_index + 1
                
                st.subheader(f"Question {question_num} of {len(quiz_flashcards)}")
                
                # Determine question type for this specific question
                if quiz_type == "English to Arabic":
                    # Always English to Arabic
                    question_direction = "English to Arabic"
                    question_text = english
                    correct_answer = arabic
                    answer_type = "Arabic"
                    
                    st.markdown(f'<h3 style="color:#FF0000;">English: <strong>{english}</strong></h3>', unsafe_allow_html=True)
                    st.write(f"What is the {answer_type} translation?")
                    
                elif quiz_type == "Arabic to English":
                    # Always Arabic to English
                    question_direction = "Arabic to English"
                    question_text = arabic
                    correct_answer = english
                    answer_type = "English"
                    
                    st.markdown(f'<div style="text-align:right; direction:rtl; font-size:28px; color:#FF0000; font-weight:bold;">Arabic: {arabic}</div>', unsafe_allow_html=True)
                    st.write(f"What is the {answer_type} translation?")
                    
                else:  # Mixed quiz - random for each question
                    # For mixed quiz, we need to decide direction for this specific question
                    if random.choice([True, False]):
                        # English to Arabic for this question
                        question_direction = "English to Arabic"
                        question_text = english
                        correct_answer = arabic
                        answer_type = "Arabic"
                        
                        st.markdown(f'<h3 style="color:#FF0000;">English: <strong>{english}</strong></h3>', unsafe_allow_html=True)
                        st.write(f"What is the {answer_type} translation?")
                    else:
                        # Arabic to English for this question
                        question_direction = "Arabic to English"
                        question_text = arabic
                        correct_answer = english
                        answer_type = "English"
                        
                        st.markdown(f'<div style="text-align:right; direction:rtl; font-size:28px; color:#FF0000; font-weight:bold;">Arabic: {arabic}</div>', unsafe_allow_html=True)
                        st.write(f"What is the {answer_type} translation?")
                
                # Store correct answer for this question
                st.session_state[f"correct_answer_{current_index}"] = correct_answer
                st.session_state[f"question_direction_{current_index}"] = question_direction
                st.session_state[f"translit_{current_index}"] = translit
                
                # Check if answer already submitted for this question
                if current_index in st.session_state.quiz_answers:
                    # Show feedback for already answered question
                    selected_answer = st.session_state.quiz_answers[current_index]
                    
                    # Show only the correct answer
                    st.info(f"**Correct answer:** {correct_answer}")
                    
                    # Show transliteration if available for Arabic answers
                    if question_direction == "English to Arabic" and translit:
                        st.write(f"*Transliteration: {translit}*")
                    
                    # Next Question button
                    col1, col2 = st.columns([1, 2])
                    with col1:
                        if st.button("➡️ Next Question", key=f"next_{current_index}", type="primary"):
                            if current_index + 1 < len(quiz_flashcards):
                                st.session_state.current_question_index = current_index + 1
                            else:
                                st.session_state.quiz_completed = True
                            st.rerun()
                    
                    with col2:
                        if st.button("⏭️ Skip to Results", key=f"skip_results_{current_index}"):
                            st.session_state.quiz_completed = True
                            st.rerun()
                
                else:
                    # Not answered yet - show options for selection
                    options = [correct_answer]
                    other_flashcards = [f for f in flashcards if f != (english, arabic, translit)]
                    
                    if len(other_flashcards) >= 3:
                        if question_direction == "English to Arabic":
                            other_options = random.sample(other_flashcards, 3)
                            options.extend([opt[1] for opt in other_options])
                        else:
                            other_options = random.sample(other_flashcards, 3)
                            options.extend([opt[0] for opt in other_options])
                    else:
                        if question_direction == "English to Arabic":
                            options.extend(["نَعَم", "لا", "شُكْرًا"])
                        else:
                            options.extend(["Yes", "No", "Thank you"])
                    
                    random.shuffle(options)
                    
                    # Use a unique key for the radio button
                    radio_key = f"quiz_radio_{current_index}"
                    selected_answer = st.radio(
                        f"Select your answer:",
                        options,
                        key=radio_key,
                        index=None  # No default selection
                    )
                    
                    # Show hint for correct answer
                    if st.checkbox("🔍 Click here for Correct Answer", key=f"hint_{current_index}"):
                        st.info(f"**Correct answer:** {correct_answer}")
                        if translit and question_direction == "English to Arabic":
                            st.write(f"*Transliteration: {translit}*")
                    
                    # Auto-submit when an answer is selected
                    if selected_answer:
                        # Store the answer
                        st.session_state.quiz_answers[current_index] = selected_answer
                        
                        # Show the correct answer immediately
                        st.info(f"**Correct answer:** {correct_answer}")
                        
                        # Show transliteration if available for Arabic answers
                        if question_direction == "English to Arabic" and translit:
                            st.write(f"*Transliteration: {translit}*")
                        
                        # Show Next Question button
                        if st.button("➡️ Next Question", key=f"next_{current_index}", type="primary"):
                            if current_index + 1 < len(quiz_flashcards):
                                st.session_state.current_question_index = current_index + 1
                            else:
                                st.session_state.quiz_completed = True
                            st.rerun()
                    
                    # Skip button
                    if st.button("⏭️ Skip Question", key=f"skip_{current_index}", type="secondary"):
                        # Mark as skipped
                        st.session_state.quiz_answers[current_index] = "SKIPPED"
                        # Move to next question
                        if current_index + 1 < len(quiz_flashcards):
                            st.session_state.current_question_index = current_index + 1
                        else:
                            st.session_state.quiz_completed = True
                        st.rerun()
            
            else:
                # All questions answered
                st.session_state.quiz_completed = True
                st.rerun()
        
        else:
            # Quiz completed - show simple summary
            st.success("🎉 Quiz Completed!")
            
            # Display completion message
            st.markdown("---")
            st.info("You have completed all questions!")
            
            # Review answers expander
            with st.expander("📋 Review Your Answers", expanded=False):
                for i, (english, arabic, translit) in enumerate(quiz_flashcards):
                    if i in st.session_state.quiz_answers:
                        user_answer = st.session_state.quiz_answers.get(i, "No answer")
                        
                        # Get question direction for this question
                        question_direction = "English to Arabic"  # Default
                        if i in st.session_state.quiz_feedback:
                            question_direction = st.session_state.quiz_feedback[i].get("question_direction", "English to Arabic")
                        
                        st.markdown(f"**Q{i+1}:**")
                        
                        if question_direction == "English to Arabic":
                            st.write(f"**English:** {english}")
                            st.write(f"**Correct Arabic:** {arabic}")
                            if translit:
                                st.write(f"*Transliteration: {translit}*")
                        else:
                            st.markdown(f"<div style='text-align:right; direction:rtl;'>**Arabic:** {arabic}</div>", unsafe_allow_html=True)
                            st.write(f"**Correct English:** {english}")
                        
                        st.markdown("---")
            
            # Restart options
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Retry Same Quiz", use_container_width=True):
                    # Reset for same quiz
                    st.session_state.quiz_started = True
                    st.session_state.quiz_completed = False
                    st.session_state.quiz_answers = {}
                    st.session_state.quiz_feedback = {}
                    st.session_state.current_question_index = 0
                    st.rerun()
            with col2:
                if st.button("📝 Start New Quiz", use_container_width=True, type="primary"):
                    # Go back to start
                    st.session_state.quiz_started = False
                    st.session_state.quiz_completed = False
                    st.session_state.current_question_index = 0
                    st.rerun()

# 📥 Bulk download functionality
def show_bulk_download(flashcards):
    st.title("📥 Bulk Audio Download")
    st.write("Download all flashcards as audio files")
    
    col1, col2 = st.columns(2)
    with col1:
        download_type = st.selectbox(
            "Select download type:",
            ["English only", "Arabic only", "English then Arabic", "Arabic then English"]
        )
    
    with col2:
        file_format = st.selectbox(
            "File naming format:",
            ["With numbers (flashcard_01.mp3)", "With text (hello_مرحبا.mp3)"]
        )
    
    if st.button("🛠️ Generate Download Package", type="primary"):
        with st.spinner("Generating audio files..."):
            import zipfile
            import tempfile
            import os
            
            # Create temporary directory for files
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_filename = f"flashcards_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
                zip_path = os.path.join(tmpdir, zip_filename)
                
                with zipfile.ZipFile(zip_path, 'w') as zipf:
                    for i, (english, arabic, translit) in enumerate(flashcards):
                        # Clean text for filename
                        clean_english = re.sub(r'[^\w\s-]', '', english)[:30]
                        clean_arabic = re.sub(r'[^\w\s-]', '', arabic)[:30]
                        
                        # Generate audio based on type
                        if download_type == "English only":
                            audio_bytes = text_to_speech(english, lang="en")
                            if audio_bytes:
                                if file_format == "With numbers (flashcard_01.mp3)":
                                    filename = f"flashcard_{i+1:02d}_english.mp3"
                                else:
                                    filename = f"{clean_english}_english.mp3"
                                zipf.writestr(filename, audio_bytes)
                        
                        elif download_type == "Arabic only":
                            audio_bytes = text_to_speech(arabic, lang="ar")
                            if audio_bytes:
                                if file_format == "With numbers (flashcard_01.mp3)":
                                    filename = f"flashcard_{i+1:02d}_arabic.mp3"
                                else:
                                    filename = f"{clean_arabic}_arabic.mp3"
                                zipf.writestr(filename, audio_bytes)
                        
                        elif download_type == "English then Arabic":
                            audio_bytes = generate_combined_audio(english, arabic)
                            if audio_bytes:
                                if file_format == "With numbers (flashcard_01.mp3)":
                                    filename = f"flashcard_{i+1:02d}_english_arabic.mp3"
                                else:
                                    filename = f"{clean_english}_{clean_arabic}.mp3"
                                zipf.writestr(filename, audio_bytes)
                        
                        elif download_type == "Arabic then English":
                            # Generate Arabic then English
                            arabic_audio = text_to_speech(arabic, lang="ar")
                            english_audio = text_to_speech(english, lang="en")
                            if arabic_audio and english_audio:
                                combined_bytes = arabic_audio + english_audio
                                if file_format == "With numbers (flashcard_01.mp3)":
                                    filename = f"flashcard_{i+1:02d}_arabic_english.mp3"
                                else:
                                    filename = f"{clean_arabic}_{clean_english}.mp3"
                                zipf.writestr(filename, combined_bytes)
                
                # Read the zip file
                with open(zip_path, 'rb') as f:
                    zip_data = f.read()
                
                # Provide download link
                b64_zip = base64.b64encode(zip_data).decode()
                href = f'<a href="data:application/zip;base64,{b64_zip}" download="{zip_filename}" style="text-decoration:none;">'
                st.markdown(f'{href}<button style="background-color:#2196F3; color:white; padding:10px 20px; border:none; border-radius:5px; font-size:16px; cursor:pointer;">⬇️ Download All Audio Files ({len(flashcards)} files)</button></a>', unsafe_allow_html=True)
                
                st.success(f"✅ Generated {len(flashcards)} audio files!")
                st.info("The zip file contains all audio files in MP3 format.")

# 🚀 Run the app
if __name__ == "__main__":
    try:
        flashcards = load_flashcards(doc_path)
        
        if not flashcards:
            st.warning("⚠️ No flashcards loaded. Check document format.")
        else:
            st.success(f"✅ Loaded {len(flashcards)} flashcards with voiceover!")
            
            # Create tabs for different functionalities
            tab1, tab2, tab3, tab4 = st.tabs(["🎴 Flashcards", "📝 Quiz", "📥 Bulk Download", "⚙️ Settings"])
            
            with tab1:
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
                    
                    col1, col2, col3 = st.columns([1, 1, 1])
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
                    
                    with col3:
                        # Download preview audio
                        combined_audio = generate_combined_audio(en, ar)
                        if combined_audio:
                            filename = f"preview_english_arabic.mp3"
                            b64 = base64.b64encode(combined_audio).decode()
                            href = f'<a href="data:audio/mp3;base64,{b64}" download="{filename}" style="text-decoration:none;">'
                            st.markdown(f'{href}<button style="background-color:#4CAF50; color:white; padding:5px 10px; border:none; border-radius:5px; cursor:pointer;">⬇️ Preview Audio</button></a>', unsafe_allow_html=True)
                    
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
            
            with tab2:
                show_quiz(flashcards)
            
            with tab3:
                show_bulk_download(flashcards)
            
            with tab4:
                st.subheader("⚙️ Application Settings")
                st.info("Flashcards loaded successfully!")
                st.metric("Total Flashcards", len(flashcards))
                
                # Display first few flashcards as sample
                with st.expander("📋 Sample Flashcards"):
                    for i, (en, ar, tr) in enumerate(flashcards[:5]):
                        st.write(f"**Card {i+1}:**")
                        st.write(f"English: {en}")
                        st.write(f"Arabic: {ar}")
                        st.write(f"Transliteration: {tr}")
                        st.write("---")
                
                # Reset button
                if st.button("🔄 Reset Application State"):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
        
    except FileNotFoundError:
        st.error(f"❌ File not found: `{doc_path}`")
        st.info("Update the `doc_path` variable with the correct path.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
