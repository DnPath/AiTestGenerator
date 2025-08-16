import pdfplumber
from docx import Document
import streamlit as st
import pandas as pd
import io
import re
import pandas as pd


def save_test_cases(text, format):
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    df = pd.DataFrame({"Test Cases": lines})

    if format == "csv":
        buffer = io.StringIO()
        df.to_csv(buffer, index=False)
        st.download_button("Download CSV", buffer.getvalue(), "test_cases.csv", "text/csv")

    elif format == "txt":
        st.download_button("Download TXT", "\n".join(lines), "test_cases.txt", "text/plain")

    elif format == "xlsx":
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="TestCases")
        st.download_button("Download Excel", buffer.getvalue(), "test_cases.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")



def extract_text_from_pdf(file_stream) -> str:
    text = []
    with pdfplumber.open(file_stream) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n\n".join(text)

def extract_text_from_docx(file_stream) -> str:
    doc = Document(file_stream)
    return "\n\n".join([p.text for p in doc.paragraphs if p.text])

def read_uploaded_file(uploaded) -> str:
    if not uploaded:
        return ""
    fname = uploaded.name.lower()
    if fname.endswith('.pdf'):
        return extract_text_from_pdf(uploaded)
    elif fname.endswith('.docx'):
        return extract_text_from_docx(uploaded)
    else:
        return uploaded.getvalue().decode('utf-8', errors='ignore')

# def parse_test_cases_to_rows(ai_output: str):
#     """
#     Parse AI output into structured test cases with steps as separate rows.
#     """
#     test_cases = []
#     current_id = None
#     current_title = None
#     current_preconditions = None
#     current_expected = None
#     current_priority = None
#     current_tags = None

#     for block in ai_output.strip().split("\n\n"):
#         lines = block.strip().split("\n")
#         steps = []
#         for line in lines:
#             if line.lower().startswith("id:"):
#                 current_id = line.split(":", 1)[1].strip()
#             elif line.lower().startswith("title:"):
#                 current_title = line.split(":", 1)[1].strip()
#             elif line.lower().startswith("preconditions:"):
#                 current_preconditions = line.split(":", 1)[1].strip()
#             elif line.lower().startswith("expected result:"):
#                 current_expected = line.split(":", 1)[1].strip()
#             elif line.lower().startswith("priority:"):
#                 current_priority = line.split(":", 1)[1].strip()
#             elif line.lower().startswith("tags:"):
#                 current_tags = line.split(":", 1)[1].strip()
#             elif re.match(r"^\d+[\).]", line.strip()):  # e.g., "1. " or "2) "
#                 steps.append(line.strip())

#         for idx, step in enumerate(steps, start=1):
#             test_cases.append({
#                 "ID": current_id,
#                 "Title": current_title,
#                 "Preconditions": current_preconditions,
#                 "Step": f"{idx}. {step.split('.', 1)[1].strip()}" if '.' in step else step,
#                 "Expected Result": current_expected,
#                 "Priority": current_priority,
#                 "Tags": current_tags
#             })

#     return pd.DataFrame(test_cases)


# def export_test_cases_excel(df: pd.DataFrame, filename="test_cases.xlsx"):
#     df.to_excel(filename, index=False)
#     return filename    
