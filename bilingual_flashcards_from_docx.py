# bilingual_flashcards_from_docx.py
import streamlit as st
from docx import Document
import re

# 📂 Path to your text document
doc_path = "Flash Card Text.docx"
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
            
            # Extract Arabic text from [text]{dir="rtl"} format
            arabic_raw = parts[1].strip()
            arabic_match = re.search(r'\[(.*?)\]', arabic_raw)
            arabic = arabic_match.group(1) if arabic_match else arabic_raw
            
            # Get transliteration
            translit = parts[2].strip()
            
            flashcards.append((english, arabic, translit))
    
    return flashcards

# 🎴 Display flashcards
def show_flashcards(flashcards, reverse=False):
    st.title("📚 Bilingual Flashcards")
    st.write("🔹 Check the box below each card to reveal the translation.")
    
    for i, (english, arabic, translit) in enumerate(flashcards):
        with st.container():
            # Card container
            st.markdown('<div style="border:1px solid #ddd; padding:15px; border-radius:8px; margin-bottom:15px;">', unsafe_allow_html=True)
            
            if not reverse:
                # English → Arabic mode
                st.markdown(f"### 🔹 **{english}**")
                
                if st.checkbox("Show Arabic & Transliteration", key=f"en_ar_{i}"):
                    st.markdown(
                        f"""
                        <div style='text-align:right; direction:rtl; font-size:32px; color:#008000; font-weight:bold; margin-top:15px;'>{arabic}</div>
                        <div style='text-align:left; font-size:18px; font-style:italic; color:#555; margin-top:10px;'>Transliteration: {translit}</div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                # Arabic → English mode
                st.markdown(
                    f"<div style='text-align:right; direction:rtl; font-size:32px; color:#000080; font-weight:bold;'>{arabic}</div>",
                    unsafe_allow_html=True
                )
                
                if st.checkbox("Show English & Transliteration", key=f"ar_en_{i}"):
                    st.markdown(
                        f"""
                        <div style='text-align:left; font-size:28px; color:#008000; font-weight:bold; margin-top:15px;'>{english}</div>
                        <div style='text-align:left; font-size:18px; font-style:italic; color:#555; margin-top:10px;'>Transliteration: {translit}</div>
                        """,
                        unsafe_allow_html=True
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)

# 🚀 Run the app
if __name__ == "__main__":
    try:
        flashcards = load_flashcards(doc_path)
        
        if not flashcards:
            st.warning("⚠️ No flashcards loaded. Check document format.")
        else:
            st.success(f"✅ Loaded {len(flashcards)} flashcards!")
            
            # Preview first parsed card
            with st.expander("🔍 Preview first card"):
                en, ar, tr = flashcards[0]
                st.text(f"English: {en}")
                st.text(f"Arabic: {ar}")
                st.text(f"Transliteration: {tr}")
        
        mode = st.radio("Choose mode:", ["English → Arabic", "Arabic → English"])
        reverse = mode == "Arabic → English"
        show_flashcards(flashcards, reverse=reverse)
        
    except FileNotFoundError:
        st.error(f"❌ File not found: `{doc_path}`")
        st.info("Update the `doc_path` variable with the correct path.")
    except Exception as e:
        st.error(f"❌ Error: {e}")
        