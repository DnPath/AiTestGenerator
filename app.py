import streamlit as st
import pandas as pd
import io
from bedrock_client import call_bedrock_model
from file_utils import read_uploaded_file
from prompts import ESTIMATE_PROMPT, GENERATE_PROMPT, FORMAT_INSTRUCTIONS

def main():
    st.title('Manual Test Case Generator — AWS Bedrock')

    # Input section
    source = st.radio('Provide requirements by:', ['Paste text', 'Upload file'])
    requirements_text = ''
    if source == 'Paste text':
        requirements_text = st.text_area('Paste requirements here', height=300)
    else:
        uploaded = st.file_uploader('Upload (txt, pdf, docx)', type=['txt', 'pdf', 'docx'])
        if uploaded:
            requirements_text = read_uploaded_file(uploaded)
            st.text_area('Preview', value=requirements_text, height=200)

    test_type = st.selectbox('Test case format', ['Traditional', 'BDD'])
    model_estimate = st.text_input('Estimation model id', value='anthropic.claude-instant-v1')
    model_generate = st.text_input('Generation model id', value='anthropic.claude-3-sonnet-20240229-v1:0')
    max_tokens = st.slider('Max tokens', 256, 8000, 1500, 128)
    temperature = st.slider('Temperature', 0.0, 1.0, 0.0, 0.05)
    use_two_step = st.checkbox('Use estimation step', value=True)

    # Initialize session state to persist results
    if "generated_cases" not in st.session_state:
        st.session_state.generated_cases = None
    if "estimation" not in st.session_state:
        st.session_state.estimation = None

    generate_button = st.button('Generate Test Cases')
    reset_button = st.button('Reset')

    if reset_button:
        st.session_state.generated_cases = None
        st.session_state.estimation = None

    if generate_button:
        if not requirements_text.strip():
            st.error('Please provide requirements.')
            return
        try:
            if use_two_step:
                est_prompt = ESTIMATE_PROMPT.format(requirements=requirements_text)
                est_resp = call_bedrock_model(est_prompt, model_estimate, max_tokens=300, temperature=0.0)
                st.session_state.estimation = est_resp

                import re
                m = re.search(r'number\s*[:=]?\s*(\d+)', est_resp, re.IGNORECASE)
                count = int(m.group(1)) if m else 10
            else:
                count = 10

            fmt_inst = FORMAT_INSTRUCTIONS['traditional'] if test_type == 'Traditional' else FORMAT_INSTRUCTIONS['bdd']
            gen_prompt = GENERATE_PROMPT.format(count=count, format=test_type.upper(), requirements=requirements_text, format_instructions=fmt_inst)
            gen_resp = call_bedrock_model(gen_prompt, model_generate, max_tokens=max_tokens, temperature=temperature)
            st.session_state.generated_cases = gen_resp

        except Exception as e:
            st.error(f'Error during generation: {e}')

    # Show estimation output if available
    if st.session_state.estimation:
        st.subheader('Estimation Output')
        st.code(st.session_state.estimation)

    # Show generated test cases if available
    if st.session_state.generated_cases:
        st.subheader('Generated Test Cases')
        st.text_area('Raw', value=st.session_state.generated_cases, height=400)

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
                    if '**scenario:**' in line_stripped.lower():
                        # Extract scenario name after '**Scenario:**'
                        scenario = line_stripped.split('**Scenario:**', 1)[1].strip()
                        found_scenario = True
                    # Match both "**Preconditions:**" and "Preconditions:"
                    import re
                    precond_match = re.search(r"(?:- )?\*\*precondition[s]?:\*\*|precondition[s]?:", line_lower)
                    if precond_match:
                        preconditions = line_stripped.split(":", 1)[1].strip()
                    elif found_scenario:
                        # Only add lines that are NOT preconditions
                        if line_stripped and not re.search(r"(?:- )?\*\*precondition[s]?:\*\*|precondition[s]?:", line_lower):
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

        st.dataframe(df)

        csv_bytes = df.to_csv(index=False).encode('utf-8')
        excel_buf = io.BytesIO()

        with pd.ExcelWriter(excel_buf, engine='openpyxl') as writer:
            df.to_excel(writer, index=False)
        excel_buf.seek(0)  # Reset buffer position
        st.download_button('Download CSV', csv_bytes, 'testcases.csv')
        st.download_button('Download Excel', excel_buf.getvalue(), 'testcases.xlsx')
        st.download_button('Download TXT', st.session_state.generated_cases.encode('utf-8'), 'testcases.txt')

if __name__ == '__main__':
    main()
