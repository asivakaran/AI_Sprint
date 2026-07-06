import os
import requests
from dotenv import load_dotenv
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, HTMLResponse

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

app = FastAPI(title="AI Fitness Coach")


def call_groq(system_msg: str, user_msg: str, max_tokens: int = 200) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": max_tokens,
    }
    response = requests.post(GROQ_URL, headers=headers, json=payload, timeout=30)
    if response.status_code != 200:
        raise RuntimeError(f"Groq API error ({response.status_code}): {response.text}")

    data = response.json()
    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )


@app.get("/motivate")
async def motivate(name: str = Query(..., description="Name of the person to motivate")):
    if not GROQ_API_KEY:
        return JSONResponse(status_code=500, content={"error": "GROQ_API_KEY not set in environment."})

    try:
        quote = call_groq(
            system_msg="You are a motivational fitness coach.",
            user_msg=(
                f"Write exactly one short, punchy motivational sentence addressed "
                f"directly to {name}, encouraging them to crush their workout today. "
                f"Return ONLY the sentence — no quotes, no preamble."
            ),
            max_tokens=60,
        )
    except RuntimeError as e:
        return JSONResponse(status_code=502, content={"error": str(e)})

    return {"name": name, "quote": quote}


@app.get("/get-plan")
async def get_plan(goal: str = Query(..., description="Describe the fitness goal for a custom 3-point plan")):
    if not GROQ_API_KEY:
        return JSONResponse(status_code=500, content={"error": "GROQ_API_KEY not set in environment."})

    try:
        plan = call_groq(
            system_msg="You are a helpful fitness coach.",
            user_msg=(
                f"Create a 3-point fitness plan to help someone achieve the following goal:\n"
                f"Goal: {goal}\n"
                f"List the plan as 1., 2., 3."
            ),
            max_tokens=512,
        )
    except RuntimeError as e:
        return JSONResponse(status_code=502, content={"error": str(e)})

    return {"plan": plan}


@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Fitness Coach</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            background: #18181b;
            color: #f8fafc;
            font-family: 'Segoe UI', 'Roboto', Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            justify-content: center;
            margin: 0;
        }
        .container {
            background: #242432;
            border-radius: 18px;
            box-shadow: 0 6px 25px 0 #0005;
            padding: 36px 40px 30px 40px;
            max-width: 390px;
            width: 95vw;
            margin: 25px 0;
            display: flex;
            flex-direction: column;
            align-items: stretch;
        }
        h1 {
            margin-bottom: 18px;
            text-align: center;
            letter-spacing: 1.3px;
            font-size: 2.2rem;
            font-weight: 700;
        }
        label {
            margin-bottom: 8px;
            margin-top: 12px;
            font-size: 1rem;
            font-weight: 500;
        }
        input[type="text"] {
            background: #2c2f39;
            color: #f5f5fa;
            border: none;
            border-radius: 8px;
            padding: 12px 14px;
            font-size: 1rem;
            margin-bottom: 16px;
            outline: none;
            transition: box-shadow 0.2s;
            box-shadow: 0 1px 5px 0 #0002;
        }
        input[type="text"]:focus {
            box-shadow: 0 2px 8px 0 #3b82f630;
        }
        button {
            background: linear-gradient(90deg, #0ea5e9, #6366f1);
            color: #fff;
            border: none;
            border-radius: 8px;
            padding: 12px;
            font-size: 1.08rem;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 18px;
            box-shadow: 0 2px 8px 0 #0003;
            transition: background 0.2s, transform 0.1s;
        }
        button:active {
            transform: scale(0.97);
        }
        #result {
            background: #232338;
            min-height: 100px;
            border-radius: 8px;
            padding: 16px;
            font-size: 1.02rem;
            margin-top: 4px;
            white-space: pre-line;
            color: #b8c2fc;
        }
        @media (max-width: 560px) {
            .container {
                padding: 18px 8vw 18px 8vw;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>AI Fitness Coach</h1>
        <label for="goal-input">Your fitness goal</label>
        <input type="text" id="goal-input" placeholder="e.g. Lose 5kg in 2 months">
        <button id="generate-btn">Generate Plan</button>
        <div id="result"></div>
    </div>
    <script>
        document.getElementById('generate-btn').addEventListener('click', async function() {
            const goalInput = document.getElementById('goal-input');
            const resultDiv = document.getElementById('result');
            const goal = goalInput.value.trim();
            resultDiv.textContent = '';
            if (!goal) {
                resultDiv.textContent = "Please enter a fitness goal.";
                resultDiv.style.color = "#fb7185";
                return;
            }
            resultDiv.textContent = "Generating your plan...";
            resultDiv.style.color = "#b8c2fc";
            try {
                const response = await fetch('/get-plan?goal=' + encodeURIComponent(goal));
                if (!response.ok) {
                    const err = await response.json();
                    resultDiv.textContent = err.error || "Error generating plan.";
                    resultDiv.style.color = "#fb7185";
                    return;
                }
                const data = await response.json();
                resultDiv.textContent = data.plan || "No plan generated.";
                resultDiv.style.color = "#b8c2fc";
            } catch (e) {
                resultDiv.textContent = "Failed to generate plan. Please try again.";
                resultDiv.style.color = "#fb7185";
            }
        });
        document.getElementById('goal-input').addEventListener('keyup', function(e) {
            if (e.key === 'Enter') {
                document.getElementById('generate-btn').click();
            }
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)