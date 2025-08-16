
import os
import io
import re
import pandas as pd
import streamlit as st
from utils import count_tokens, estimate_tokens_per_tc
from bedrock_client import call_bedrock_model
from file_utils import read_uploaded_file
from prompts import ESTIMATE_PROMPT, GENERATE_PROMPT, FORMAT_INSTRUCTIONS


def parse_test_cases_to_rows(ai_output: str):
    """
    Parse AI output into structured test cases with steps as separate rows.
    """
    test_cases = []
    current_id = None
    current_title = None
    current_preconditions = None
    current_expected = None
    current_priority = None
    current_tags = None

    for block in ai_output.strip().split("\n\n"):
        lines = block.strip().split("\n")
        steps = []
        for line in lines:
            if line.lower().startswith("tc-") or line.lower().startswith("id:"):  # Match TC-001 or just a number
                ##current_id = line.split(":", 1)[1].strip()
                current_id = line.strip().removeprefix("ID:").strip()
            elif line.lower().startswith("title:"):
                current_title = line.split(":", 1)[1].strip()
            elif line.lower().startswith("preconditions:"):
                current_preconditions = line.split(":", 1)[1].strip()
            elif line.lower().startswith("expected result:"):
                current_expected = line.split(":", 1)[1].strip()
            elif line.lower().startswith("priority:"):
                current_priority = line.split(":", 1)[1].strip()
            elif line.lower().startswith("tags:"):
                current_tags = line.split(":", 1)[1].strip()
            elif re.match(r"^\d+[\).]", line.strip()):  # e.g., "1. " or "2) "
                steps.append(line.strip())

        for idx, step in enumerate(steps, start=1):
            test_cases.append({
                "ID": current_id,
                "Title": current_title,
                "Preconditions": current_preconditions,
                "Step": f"{idx}. {step.split('.', 1)[1].strip()}" if '.' in step else step,
                "Expected Result": current_expected,
                "Priority": current_priority,
                "Tags": current_tags
            })

    return pd.DataFrame(test_cases)


def export_test_cases_excel(df: pd.DataFrame, filename="test_cases.xlsx"):
    df.to_excel(filename, index=False)
    return filename

######Sidebar Style#######
st.markdown(
    """
    <style>
    /* Styling for general sidebar text (if using st.write or st.markdown) */
    .sidebar-text {
        font-size: 14px; /* Adjust as needed */
        font-family: sans-serif; /* Consistent font */
    }

    /* Styling for widget labels in the sidebar (checkboxes, select boxes, etc.) */
    .stSidebar [data-testid="stWidgetLabel"] p {
        font-size: 14px; /* Adjust as needed */
        font-family: sans-serif; /* Consistent font */
    }   
        
    /* Styling for selectbox options in the sidebar */
    .stSidebar [data-testid="stSelectbox"] div[role="listbox"] {
        font-size: 14px; /* Adjust as needed */
        font-family: sans-serif; /* Consistent font */
    }

    /* Styling for the displayed value in the selectbox */
    .stidebar [data-testid="stSelectbox"] .st-bs { 
        font-size: 14px; /* Adjust as needed */
        font-family: sans-serif; /* Consistent font */
    }
    </style>
    """,
    unsafe_allow_html=True,
)

##########################

st.set_page_config(
    page_title="AI Test Case Generator",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Hide Streamlit default menu/footer (cosmetic)
HIDE_DEFAULT_CSS = """
    <style>
    MainMenu {visibility: visible;}
    footer {visibility: hidden;}
    header {visibility: visible;}
    </style>
"""
st.markdown(HIDE_DEFAULT_CSS, unsafe_allow_html=True)

st.title("AI Test Case Generator")

# ---- Session State ----
if "generated_cases" not in st.session_state:
    st.session_state.generated_cases = None
if "estimation" not in st.session_state:
    st.session_state.estimation = None
if "req_token_count" not in st.session_state:
    st.session_state.req_token_count = 0    
# if "count_override" not in st.session_state:
#     st.session_state.count_override = 10

# Sidebar config
st.sidebar.header("Model Configuration")

st.session_state.selected_model = st.sidebar.selectbox(
    "**Select Model**",
    ["anthropic.claude-3-sonnet-20240229-v1:0"]  ## "anthropic.claude-instant-v1", "amazon.titan"
)
##temperature = st.sidebar.slider("Temperature", 0.0, 1.0, 0.0, 0.05)
temperature = st.sidebar.slider("**Temperature**", 0.0, 1.0, 0.0, 0.05, help="Controls randomness: low=precise, high=creative")
##num_test_cases = st.sidebar.number_input("Estimated Number of Test Cases", min_value=1, max_value=50, value=10)



# ---- Main Layout ----
# left, right = st.columns([2, 1])

# with left:
st.subheader("Requirements Input")
source = st.radio("Provide requirements by:", ["Paste text", "Upload file"], horizontal=True)
requirements_text = ""
if source == "Paste text":
    requirements_text = st.text_area("Paste requirements here", height=240, placeholder="Paste product/feature requirements...")
else:
    up = st.file_uploader("Upload (txt, pdf, docx)", type=["txt", "pdf", "docx"])
    if up:
        try:
            requirements_text = read_uploaded_file(up)
            st.session_state.req_token_count = count_tokens(requirements_text)
        except Exception as e:
            st.error(f"Failed to read file: {e}")
        st.text_area("Preview", value=requirements_text, height=200)

st.markdown("---")
# st.subheader("Generate")
# colX, colY, colZ = st.columns(3)

########
# Custom CSS for multiple button colors
st.markdown("""
    <style>
    /* Change Generate Test Cases button color to #008000 */
    div[data-testid="generate-btn"] button {
        background-color: #008000 !important;
        color: white !important;
        font-weight: bold !important;
    }

    /* Reset button - red */
    div[data-testid="reset-btn"] button {
        background-color: lightcoral;
        color: white;
        font-weight: bold;
    }

    /* Download button - blue */
    div[data-testid="download-btn"] button {
        background-color: lightblue;
        color: black;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)
######



colB, colC = st.columns(2)
# with colA:
#     test_type = st.selectbox("Test case format", ["Traditional", "BDD"])
with colB:
    go = st.button("🚀 Generate Test Cases", use_container_width=True, type="primary")
    
with colC:
    reset = st.button("♻️ Reset", use_container_width=True, type="secondary")


### Side Bar Config
test_type = st.sidebar.selectbox("**Test Case Format**", ["Traditional", "BDD"])

# use_two_step = st.sidebar.checkbox("$\\textsf{\\scriptsize Let AI Estimate the TC Count}$", value=True,
#                                 help="First estimate the optimal number of cases, then generate.")

use_two_step = st.sidebar.checkbox("Let AI Estimate the TC Count", value=True,
                                help="First estimate the optimal number of cases, then generate.")

st.sidebar.number_input("Required Test Case Count",help="Manual count (if not using estimate or to override)", disabled=use_two_step,
                min_value=1, max_value=500, value=10, key="count_override") ###"Manual count (if not using estimate or to override)",

# Display token info dynamically
req_tokens = st.session_state.req_token_count ###count_tokens(st.session_state.get("requirement_text", ""), selected_model)
output_tokens_est = estimate_tokens_per_tc(st.session_state.selected_model) * st.session_state.get("count_override")
total_tokens_est = req_tokens + output_tokens_est + 200  # buffer
# st.sidebar.write(f"$\\textsf{{\\scriptsize Requirement Tokens: {req_tokens}}}$")
# st.sidebar.write(f"$\\textsf{{\\scriptsize Estimated Output Tokens: {output_tokens_est}}}$")
# st.sidebar.write(f"$\\textsf{{\\scriptsize Total Estimated Tokens: {total_tokens_est}}}$")
st.sidebar.write(f"Requirement Tokens: {req_tokens}")
st.sidebar.write(f"Estimated Output Tokens: {output_tokens_est}")
st.sidebar.write(f"Total Estimated Tokens: {total_tokens_est}")

# go = st.button("🚀 Generate Test Cases", use_container_width=True)
# reset = st.button("♻️ Reset", use_container_width=True)

# with right:
#     st.subheader("Notes")
#     st.markdown("- Configure **model, tokens, temperature** on the *Config* page in the sidebar.\n"
#                 "- Supports Claude Instant (legacy prompt) and Claude 3 Sonnet (messages API).")
#     st.info(f"AWS Region (effective): {os.getenv('AWS_REGION') or os.getenv('AWS_DEFAULT_REGION') or 'not set'}")

if reset:
    st.session_state.generated_cases = None
    st.session_state.estimation = None

# ---- Action ----
if go:
    if not requirements_text.strip():
        st.error("Please provide requirements text or upload a document.")
    else:
        try:
            # Step 1: estimate count
            max_tokens_total = min(total_tokens_est, 8000)
            st.session_state.max_tokens = max_tokens_total
            if use_two_step:
                est_prompt = ESTIMATE_PROMPT.format(requirements=requirements_text)

                est = call_bedrock_model(
                    prompt=est_prompt,
                    model_id=st.session_state.get("selected_model", os.getenv("BEDROCK_MODEL_ID_INSTANT", "anthropic.claude-3-sonnet-20240229-v1:0")),
                    max_tokens=max_tokens_total,
                    temperature=0.0
                )
                st.session_state.estimation = est
                m = re.search(r'number:\s*(\d+)', est, re.IGNORECASE)
                count = int(m.group(1)) if m else st.session_state.get("count_override")
            else:
                count = st.session_state.get("count_override")

            # Step 2: generate
            fmt_inst = FORMAT_INSTRUCTIONS["traditional"] if test_type == "Traditional" else FORMAT_INSTRUCTIONS["bdd"]
            gen_prompt = GENERATE_PROMPT.format(
                count=count,
                format=test_type.upper(),
                requirements=requirements_text,
                format_instructions=fmt_inst
            )
            gen = call_bedrock_model(
                prompt=gen_prompt,
                model_id=st.session_state.get("selected_model", os.getenv("BEDROCK_MODEL_ID_SONNET", "anthropic.claude-3-sonnet-20240229-v1:0")),
                max_tokens=st.session_state.get("max_tokens", 8000),
                temperature=st.session_state.get("temperature", 0.0)
            )
            print(f'-------------max_tokens {st.session_state.max_tokens}--------------------------')
            print(gen)
            print('---------------------------------------')
            st.session_state.generated_cases = gen
            st.session_state.generated_cases_df = parse_test_cases_to_rows(gen)
        except Exception as e:
            st.error(f"Error during generation: {e}")

st.markdown("---")

# ---- Results ----
if st.session_state.estimation:
    st.subheader("Estimation Output")
    st.code(st.session_state.estimation)

if st.session_state.generated_cases:
    st.subheader("Generated Test Cases (Raw)")
    st.text_area("Output", value=st.session_state.generated_cases, height=360)

    # # Simple parsing to table (best-effort)
    # parts = [p.strip() for p in st.session_state.generated_cases.split("\n\n") if p.strip()]
    # rows = []
    # for i, p in enumerate(parts, 1):
    #     title = p.splitlines()[0][:120] if p.splitlines() else f"Case {i}"
    #     rows.append({"ID": f"TC-{i:03d}", "Title": title, "Details": p})
    # df = pd.DataFrame(rows) if rows else pd.DataFrame([{"ID":"TC-001","Title":"Generated Test Case","Details": st.session_state.generated_cases}])
################
    rows = []
    parts = [p.strip() for p in st.session_state.generated_cases.split('\n\n')]
    parts = [p for p in parts if p]
    tc_counter = 1  # Initialize test case counter
    for i, p in enumerate(parts, 1):
        if test_type == 'Traditional':
            # Parse traditional test case format
            title = ""
            preconditions = ""
            steps = []
            expected = ""
            collecting_steps = False
            collecting_expected = False
            for line in p.split('\n'):
                line_lower = line.lower().strip()
                if line_lower.startswith("title:"):
                    title = line.split(":", 1)[1].strip()
                    collecting_steps = False
                    collecting_expected = False
                elif line_lower.startswith("preconditions:"):
                    preconditions = line.split(":", 1)[1].strip()
                    collecting_steps = False
                    collecting_expected = False
                elif line_lower.startswith("steps:"):
                    collecting_steps = True
                    collecting_expected = False
                elif line_lower.startswith("expected result:"):
                    collecting_steps = False
                    collecting_expected = True
                    expected = line.split(":", 1)[1].strip()
                elif collecting_steps:
                    if line.strip():
                        steps.append(line.strip())
                elif collecting_expected:
                    if line.strip():  # skip empty lines
                        expected += "\n" + line.strip()
            # Only add non-empty test cases
            if title or steps or expected:    
                rows.append({
                    'ID': f'TC-{tc_counter:03d}', 
                    'Title': title,
                    'Preconditions': preconditions,
                    'Steps': "\n".join(steps),
                    'Expected Results': expected
                })
                tc_counter += 1  # Increment counter for each test case
            
        else: #BDD
            # Parse title, scenario
            scenario = ""
            preconditions = ""
            description = []
            found_scenario = False
            for line in p.split('\n'):
                line_stripped = line.strip()
                line_lower = line_stripped.lower()  # <-- Add this line

                # Find the scenario line
                if 'scenario:' in line_stripped.lower():
                    # Extract scenario name after '**Scenario:**'
                    scenario = line_stripped.split('Scenario:', 1)[1].strip()
                    found_scenario = True
                # Match both "**Preconditions:**" and "Preconditions:"
                precond_match = re.search(r"(?:- )?\*\*precondition[s]?:\*\*|precondition[s]?:", line_lower)
                if precond_match:
                    preconditions = line_stripped.split(":", 1)[1].strip()
                elif found_scenario:
                    # Only add lines that are NOT preconditions
                    if line_stripped and not re.search(r"(?:- )?\*\*precondition[s]?:\*\*|precondition[s]?", line_lower):
                        description.append(line_stripped)
            # Only add non-empty BDD test cases
            if scenario or description:
                rows.append({
                    'ID': f'TC-{tc_counter:03d}',
                    'Scenario': scenario,
                    'Preconditions': preconditions,
                    'Description': "\n".join(description)  # Use space to keep all in one line
                })
                tc_counter += 1  # Increment counter for each test case
            
    # Create DataFrame after processing all cases
    if test_type == 'Traditional':
        df = pd.DataFrame(rows, columns=['ID', 'Title', 'Preconditions','Steps', 'Expected Results'])
    else:
        df = pd.DataFrame(rows, columns=['ID', 'Scenario', 'Preconditions','Description'])

################

    # st.subheader("Test Cases Parsed with Steps as Rows")
    # if "generated_cases_df" in st.session_state and st.session_state.generated_cases_df is not None:
    #     st.dataframe(st.session_state.generated_cases_df)

    st.subheader("Test Cases")
    st.dataframe(df, use_container_width=True)

    # Downloads
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="TestCases")


    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button("⬇️ Download CSV", data=csv_bytes, file_name="testcases.csv", mime="text/csv", use_container_width=True)
    with c2:
        st.download_button("⬇️ Download Excel", data=excel_buf.getvalue(), file_name="testcases.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        # excel_file = export_test_cases_excel(st.session_state.generated_cases_df)
        # with open(excel_file, "rb") as f:
        #     st.download_button("Download ExcelX1", f, file_name="test_cases.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    with c3:
        st.download_button("⬇️ Download TXT", data=st.session_state.generated_cases, file_name="testcases.txt",
                        mime="text/plain", use_container_width=True)
    
    
###########
    if test_type != 'BDD':
        st.subheader("Test Cases with Steps as Rows")
        if "generated_cases_df" in st.session_state and st.session_state.generated_cases_df is not None:
            st.dataframe(st.session_state.generated_cases_df)

            excel_file = export_test_cases_excel(st.session_state.generated_cases_df)
            with open(excel_file, "rb") as f:
                st.download_button("Download as Excel", f, file_name="test_case_steps.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

