import os
import requests
import json
import re
import time

# Load API key from environment variable
api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY environment variable is not set.")

# API config
url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-site.com",
    "X-Title": "Story Generator"
}

# Outline for the story
outline_points = [
    "Protagonist receives a mysterious letter with no return address.",
    "The letter warns of a danger that will strike in 24 hours.",
    "Protagonist initially ignores it but strange events start happening.",
    "Protagonist decides to investigate the letter further.",
    "An unexpected ally appears to help the protagonist.",
    "Danger escalates forcing protagonist to flee.",
    "Secrets about protagonist’s past are revealed.",
    "Climax confrontation with antagonist.",
    "Protagonist overcomes the threat but at a cost.",
    "Resolution and new beginning for protagonist."
]

# Function to clean unwanted content from the AI response
def clean_story_output(raw_text):
    lines = raw_text.splitlines()
    cleaned_lines = []
    skip_patterns = [
        r'^\s*(\*+|---+|###*|Point \d+.*|End of.*|Preparation for.*|Continuity Notes.*|Please Provide.*|Generating story.*|Context.*|Tone:.*|Events:.*|Character Development:.*|NOTE:.*)',
        r'.*outline.*'
    ]
    for line in lines:
        if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):
            continue
        if "NOTE:" in line or line.strip().endswith(":"):
            continue
        cleaned_lines.append(line)
    return '\n'.join(cleaned_lines).strip()

# Function to generate story for a given point with context
def generate_story_part(point, context, index):
    prompt = (
        f"You are a professional storyteller.\n"
        f"Your task is to write a long, engaging, and coherent story that follows a 10-point outline.\n"
        f"Focus: Write at least 500 words for the current outline point.\n"
        f"Instructions: Emphasize consistency in characters, tone, and events throughout the story.\n\n"
        f"{'This is the beginning of the story.' if index == 1 else ''}"
        f"{'This is the ending of the story.' if index == 10 else ''}\n"
        f"Outline Point {index}: {point}\n\n"
        f"Previous Story Context:\n{context}\n\n"
        f"Please ONLY provide the story narrative in plain text.\n"
        f"Do NOT include any titles, section headers, explanations, or any text outside of the story.\n"
        f"Write naturally and engagingly as if for a novel or screenplay.\n"
    )
    data = {
        "model": "nvidia/llama-3.3-nemotron-super-49b-v1:free",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        result = response.json()
        raw_story = result['choices'][0]['message']['content']
        return clean_story_output(raw_story)
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def main():
    full_story = ""  # Accumulate the story here

    for idx, point in enumerate(outline_points, start=1):
        print(f"--- Generating story part {idx} ---")
        story_part = generate_story_part(point, full_story, idx)
        if story_part:
            print(story_part)
            print("\n")
            full_story += "\n" + story_part  # Append new part to context for next call
            time.sleep(1)
        else:
            print(f"Failed to generate part {idx}. Stopping.")
            break

    print("--- FULL STORY GENERATED ---")

if __name__ == "__main__":
    main()
