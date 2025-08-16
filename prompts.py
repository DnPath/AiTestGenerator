ESTIMATE_PROMPT = (
    "You are an experienced QA test engineer.\n"
    "Given the following requirements (delimited by triple backticks), suggest an optimal number of manual test cases to thoroughly test the described functionality, and briefly justify your choice (2-4 short bullet points).\n\n"
    "Requirements:\n```{requirements}```\n\n"
    "Answer format:\n- number: <integer>\n- rationale:\n  - <point1>\n  - <point2>\n"
)

GENERATE_PROMPT = (
    "You are an expert QA test engineer. Generate {count} manual test cases in the {format} format for the following requirements.\n\n"
    "Requirements:\n```{requirements}```\n\n"
    "Format instructions:\n{format_instructions}\n\n"
    "Each test case should include a unique id, title, preconditions (if any), steps, expected result, and tags (optional). Keep cases concise but actionable."
)



NEW_TRADITIONAL_FORMAT_INST ="""You are a test case generator.  
Generate detailed functional test cases in the following strict format.  
Do NOT include any extra commentary, notes, or formatting outside the specified structure.

For each test case, use this exact template:

ID: TC-<number>
Title: <Short descriptive title>
Preconditions: <Any setup or assumptions>
Steps:
1. <Step 1 description>
2. <Step 2 description>
3. <Step 3 description>
Expected Result: <Single sentence expected outcome>
Priority: <High/Medium/Low>
Tags: <Comma separated tags>

Rules:
- Number steps exactly "1.", "2.", "3." etc.
- No blank lines inside steps list
- Each test case must have at least 3 steps
- Keep wording concise but precise
- Separate each test case with a blank line
- Do not add extra sections or commentary"""

FORMAT_INSTRUCTIONS = {
    'traditional':  (NEW_TRADITIONAL_FORMAT_INST)
        ###"ID: TC-001\nTitle: Verify login with valid credentials\nPreconditions: User account exists\nSteps:\n  1. Go to login page\n  2. Enter valid username and password\n  3. Click 'Login'\nExpected Result:\n  - User is logged in and dashboard is shown"
    ,
    'bdd': (
        "Scenario: Successful login with valid credentials\nGiven the user has a valid account\nWhen the user enters valid username and password and clicks Login\nThen the user should see the dashboard"
    )
}

BASE_PROMPT = """
You are an expert QA engineer. Based on the given requirements, generate comprehensive test cases.

Each test case should be in JSON format:
{
  "test_case_id": "TC-001",
  "title": "Test case title",
  "description": "Brief description",
  "steps": [
    {
      "step_number": 1,
      "action": "Step action",
      "expected_result": "Expected outcome"
    }
  ],
  "requirement_ref": "REQ-001"
}

Ensure:
- Clear step-by-step actions
- Each step has an expected result
- Test coverage spans all requirement points
- Test case IDs are unique
"""
