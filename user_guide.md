
# 🧪 AI Test Case Generator

An AI-powered test case generator that takes software requirements (plain text or file) and produces structured test cases in traditional or BDD format. Supports token estimation, configurable model settings, Excel export, and AWS deployment.

---

## ✨ Features

- **Requirement Upload:** Upload text or paste directly into the input box.
- **AI Token Estimation:** Estimate the optimal number of test cases before generation.
- **Configurable Settings:** Choose model, temperature, token limit, and batch generation.
- **Multiple Formats:** Generate in Traditional or BDD style.
- **Excel Export:** Download results in multi-column Excel format (with step numbers and expected results).
- **Persistent Session:** Keeps generated test cases until reset.
- **Sidebar Controls:** All configuration options in one place.

---

## 📊 Using the App

1. Upload or paste requirements in the main page.
2. Configure Model, Temperature, Max Tokens, Batch Mode, and Format in the sidebar.
3. Optionally enable **Estimate Optimal Test Cases** — the AI will suggest how many to generate.
4. Click **Generate Test Cases**.
5. View results in the table (Traditional format) or download as .txt (BDD format).
6. Export to Excel for sharing or reporting.
8. Reset session anytime to start fresh.

---
## 📦 Local Setup

### 1️⃣ Prerequisites

- Python 3.9 or later
- AWS account (for Bedrock API access)
- AWS CLI configured locally (`aws configure`)

### 2️⃣ Clone the repository

```bash
git clone https://github.com/yourusername/AWSTestSageAI.git
cd AWSTestSageAI
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Set environment variables

Create a `.env` file in the project root:

```env
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
AWS_DEFAULT_REGION=us-east-1
```

### 5️⃣ Run locally

```bash
streamlit run Test_Case_Generator_V3.py.py
```

Access the app at: [http://localhost:8501](http://localhost:8501)

---

## ☁️ AWS Elastic Beanstalk Setup

### 1️⃣ Install EB CLI

```bash
pip install awsebcli
```

### 2️⃣ Initialize Elastic Beanstalk

```bash
eb init
# Select your AWS region
# Select Python platform (Python 3.9)
```

### 3️⃣ Create environment

```bash
eb create my-testcase-env --single
```

### 4️⃣ Deploy

```bash
eb deploy
```

### 5️⃣ Set environment variables in EB

```bash
eb setenv AWS_ACCESS_KEY_ID=your_aws_key AWS_SECRET_ACCESS_KEY=your_aws_secret AWS_DEFAULT_REGION=us-east-1
```

---

## 📊 Using the App

1. Upload or paste requirements in the main page.
2. Configure Model, Temperature, Max Tokens, Batch Mode, and Format in the sidebar.
3. Optionally enable **Estimate Optimal Test Cases** — the AI will suggest how many to generate.
4. Click **Generate Test Cases**.
5. View results in the table (Traditional format) or download as .txt (BDD format).
6. Export to Excel for sharing or reporting.
8. Reset session anytime to start fresh.

---

