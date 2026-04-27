import streamlit as st
import requests

st.set_page_config(page_title="MedResearchGPT", layout="wide")

st.title("🩺 MedResearchGPT")
st.caption("Upload PDF • Summarize • Ask Questions")

if "summary" not in st.session_state:
    st.session_state.summary = ""

uploaded_file = st.file_uploader(
    "Upload Medical Research PDF",
    type=["pdf"]
)

if uploaded_file is not None:
    if st.button("Generate Summary"):
        files = {
            "file": (
                uploaded_file.name,
                uploaded_file.getvalue(),
                "application/pdf"
            )
        }

        with st.spinner("Reading paper..."):
            try:
                response = requests.post(
                    "http://127.0.0.1:8000/upload-pdf/",
                    files=files
                )

                data = response.json()

                if response.status_code == 200:
                    st.session_state.summary = data.get(
                        "summary",
                        "No summary generated."
                    )
                else:
                    st.error("Backend error")
                    st.write(data)

            except Exception as e:
                st.error("Cannot connect to backend")
                st.write(str(e))

if st.session_state.summary:
    st.subheader("AI Summary")
    st.write(st.session_state.summary)

st.divider()

question = st.text_input(
    "Ask a question about the uploaded paper"
)

if st.button("Ask"):
    if question.strip():
        try:
            with st.spinner("Thinking..."):
                res = requests.get(
                    "http://127.0.0.1:8000/ask/",
                    params={"q": question}
                )

            data = res.json()

            if res.status_code == 200:
                st.subheader("Answer")
                st.write(data.get("answer", "No answer found"))
            else:
                st.error("Question API error")
                st.write(data)

        except Exception as e:
            st.error("Cannot connect to backend")
            st.write(str(e))

