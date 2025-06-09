import os
import json
import time
import requests
import re
import traceback

# --- Configuration ---
API_URL = "https://openrouter.ai/api/v1/chat/completions"
API_KEY = "Bearer " + os.getenv("OPENROUTER_API_KEY")
API_MODEL = "nvidia/llama-3.3-nemotron-super-49b-v1:free"
HTTP_REFERER = "https://your-site.com"
X_TITLE = "Story Generator"

# Output file
OUTPUT_FILENAME = "generated_story.txt"
WORDS_PER_POINT = 500  # Approximate target per sub-point
NUM_CONTEXT_SENTENCES = 2  # How many sentences to include from previous segment

# --- Helper Functions ---
def get_last_sentences(text, num_sentences):
    """Extracts the last N sentences from a block of text."""
    if not text:
        return ""
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s for s in sentences if s]
    last_n = sentences[-num_sentences:] if len(sentences) >= num_sentences else sentences
    return " ".join(last_n).strip()

def parse_hierarchical_outline(outline_text):
    """Parses the hierarchical outline text into a flat list of segments."""
    segments = []
    current_section = "Unknown Section"
    
    # Split the outline text into lines
    lines = outline_text.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check for section header (### Section Title)
        if line.startswith("###"):
            # Extract section title, remove potential word count info
            match = re.match(r"###\s*(.*?)(?:\s*\(\d+,\d+\s+words\))?$", line)
            if match:
                current_section = match.group(1).strip()
            else:
                current_section = line.lstrip("### ").strip()  # Fallback
                
        # Check for sub-point (starts with -)
        elif line.startswith("-"):
            sub_point_text = line.lstrip("- ").strip()
            segments.append({
                "section": current_section,
                "instruction": sub_point_text
            })
            
    if not segments:
        print("Warning: No segments parsed from outline. Ensure it uses '### Section' and '- Sub-point' format.")
        return None
        
    return segments

# --- Main Script Logic ---
def generate_story_script_hierarchical(outline_text):
    """Generates the story script using a hierarchical outline."""
    
    # Parse the outline from the input text
    parsed_outline = parse_hierarchical_outline(outline_text)
    if not parsed_outline:
        print("Stopping script due to outline parsing error.")
        return None

    full_script = ""
    headers = {
        "Authorization": API_KEY,
        "Content-Type": "application/json",
        "HTTP-Referer": HTTP_REFERER,
        "X-Title": X_TITLE
    }

    print(f"Starting script generation using parsed outline with {len(parsed_outline)} segments")

    for i, segment_data in enumerate(parsed_outline):
        section_context = segment_data["section"]
        point_instruction = segment_data["instruction"]
        
        print(f"\n--- Generating segment {i+1}/{len(parsed_outline)} ---")
        print(f"    Section: {section_context}")
        print(f"    Instruction: {point_instruction[:80]}..." if len(point_instruction) > 80 else f"    Instruction: {point_instruction}")

        # Get context from the previous segment (if not the first point)
        previous_context = ""
        if i > 0 and full_script:
            previous_context = get_last_sentences(full_script, NUM_CONTEXT_SENTENCES)

        # Construct the prompt
        prompt_content = "You are writing a continuous story script for a YouTube voiceover. "
        prompt_content += "The overall story involves a young woman named Elena challenging a corrupt CEO in a tech company.\n\n"
        prompt_content += "Current Section Context: \"" + section_context + "\"\n\n"
        
        if previous_context:
            prompt_content += "The previous part ended exactly like this: \"" + previous_context + "\"\n\n"
            prompt_content += "Now, continue the story *immediately* from that ending, focusing on this specific point within the current section: \"" + point_instruction + "\".\n"
        else:
            # First point prompt
            prompt_content += "Start the story focusing on this first point: \"" + point_instruction + "\".\n"

        prompt_content += f"Write approximately {WORDS_PER_POINT} words for this part.\n\n"
        prompt_content += "Follow these strict rules:\n"
        prompt_content += "- Write ONLY speakable, conversational text for a single narrator.\n"
        prompt_content += "- **IMPORTANT: Balance internal thoughts with descriptions of the character's physical actions, gestures, and interactions with their environment. Show, don't just tell feelings through actions.**\n"
        prompt_content += "- Use simple, everyday language (8th-grade level). Keep sentences short (10-15 words avg).\n"
        prompt_content += "- Sound like talking to a friend. Use contractions (don't, it's). Start sentences casually (So, Now, But).\n"
        prompt_content += "- NO bullet points, headers, formatting (*, **, -, •, #, []), stage directions, character labels, meta-commentary, placeholders.\n"
        prompt_content += "- NO literary descriptions, metaphors, poetic language, theatrical tone. Be direct.\n"
        prompt_content += "- DO NOT use these words: like, we delve into, unlock the secrets, join us on a journey, deep, dive, embark, journey, discover, explore, picture this, unravel, embrace, get ready, realm, let's dive in, imagine, unravel the secrets, in this realm.\n"
        
        if previous_context:
            prompt_content += "- Ensure this part flows *directly* and naturally from the previous ending sentence provided above.\n"
        else:
            prompt_content += "- Make this an attention-grabbing start to the story.\n"
            
        # Add specific instructions for cliffhangers if needed based on outline structure
        if "Cliffhanger:" in point_instruction:
            prompt_content += "- End this segment with the specified cliffhanger moment.\n"

        # Prepare API request data
        data = {
            "model": API_MODEL,
            "messages": [{"role": "user", "content": prompt_content}]
        }

        response = None
        try:
            print("Sending request to API...")
            response = requests.post(API_URL, headers=headers, data=json.dumps(data), timeout=180)
            print(f"API Response Status Code: {response.status_code}")
            response.raise_for_status()

            result = response.json()
            print("API Response JSON received.")
            if not result.get('choices') or not result['choices'][0].get('message') or 'content' not in result['choices'][0]['message']:
                print(f"Error: Unexpected API response format for segment {i+1}.")
                print(f"Response Content: {result}")
                print("Stopping script generation.")
                return None

            segment_text = result['choices'][0]['message']['content'].strip()
            print(f"Segment {i+1} content received from API.")

            # Basic cleaning
            prohibited = ["like", "we delve into", "unlock the secrets", "join us on a journey", "deep", "dive", "embark", "journey", "discover", "explore", "picture this", "unravel", "embrace", "get ready", "realm", "let's dive in", "imagine", "unravel the secrets", "in this realm"]
            for phrase in prohibited:
                pattern = r'\b' + re.escape(phrase) + r'\b'
                if re.search(pattern, segment_text, re.IGNORECASE):
                    print(f"Warning: Prohibited phrase '{phrase}' detected in segment {i+1}. Attempting removal.")
                    segment_text = re.sub(pattern, '', segment_text, flags=re.IGNORECASE)
                    segment_text = re.sub(r'\s{2,}', ' ', segment_text).strip()

            # --- Print the generated segment --- 
            print(f"\n--- Generated Text for Segment {i+1} ---")
            print(segment_text[:200] + "..." if len(segment_text) > 200 else segment_text)
            print("-------------------------------------")
            # -------------------------------------

            if full_script:
                full_script += "\n\n"
            full_script += segment_text
            print(f"Segment {i+1} processed and appended successfully.")

        except requests.exceptions.Timeout:
            print(f"Error: API call timed out for segment {i+1} after 180 seconds.")
            print("Stopping script generation.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error during API call for segment {i+1}: {e}")
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                try: print(f"Response Text: {response.json()}")
                except json.JSONDecodeError: print(f"Response Text (non-JSON): {response.text}")
            else: print("No response object received before exception.")
            print("Stopping script generation.")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during segment {i+1} generation: {e}")
            traceback.print_exc()
            print("Stopping script generation.")
            return None
            
        # Add a small delay between API calls to avoid rate limiting
        time.sleep(2)

    # Save the final script
    print(f"\nScript generation loop completed. Full script length: {len(full_script)} characters.")
    if not full_script:
        print("Warning: The generated script content is empty. File will not be written.")
        return None

    print(f"Attempting to write script to {OUTPUT_FILENAME}...")
    try:
        with open(OUTPUT_FILENAME, 'w', encoding='utf-8') as f:
            f.write(full_script)
        print(f"Full script generated and saved to {OUTPUT_FILENAME}")
        return OUTPUT_FILENAME
    except IOError as e:
        print(f"Error writing final script to file: {e}")
        print(f"Current working directory: {os.getcwd()}")
        print("Please ensure you have write permissions in this directory.")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    print("Executing generate_story_script_hierarchical function...")
    outline_text = os.getenv("INPUT_OUTLINE_TEXT", "")
    
    if not outline_text:
        print("Error: No outline text provided in the workflow input.")
        exit(1)
        
    print(f"Received outline text ({len(outline_text)} characters)")
    result_file = generate_story_script_hierarchical(outline_text)
    
    if result_file:
        print(f"Script execution successful. Output: {result_file}")
    else:
        print("Script execution failed or produced no output file.")
        exit(1)
        
    print("Python script finished.")
