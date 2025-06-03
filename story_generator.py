
        import os  
        import json  
        import time  
        import requests  
        import re  
  
        outline_text = os.getenv("INPUT_OUTLINE_TEXT", "")  
        outline_points = [line.strip() for line in outline_text.strip().split("\\n") if line.strip()]  
  
        url = "https://openrouter.ai/api/v1/chat/completions"  
        headers = {  
            "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",  
            "Content-Type": "application/json",  
            "HTTP-Referer": "https://your-site.com",  
            "X-Title": "Story Generator"  
        }  
  
        def clean_story_output(raw_text):  
            lines = raw_text.splitlines()  
            cleaned_lines = []  
            skip_patterns = [  
                r'^\\s*(\\*+|---+|###*|Point \\d+.*|End of.*|Preparation for.*|Continuity Notes.*|Please Provide.*|Generating story.*|Context.*|Tone:.*|Events:.*|Character Development:.*|NOTE:.*)',  
                r'.*outline.*'  
            ]  
            for line in lines:  
                if any(re.match(pattern, line, re.IGNORECASE) for pattern in skip_patterns):  
                    continue  
                if "NOTE:" in line or line.strip().endswith(":"):  
                    continue  
                cleaned_lines.append(line)  
            return '\\n'.join(cleaned_lines).strip()  
  
        def generate_story_part(point, context, index, total):  
            is_first = index == 1  
            is_last = index == total  
  
            # Enhanced prompt with voiceover-ready specifications    
            voiceover_ready_prompt = (    
                "CRITICAL: This script must be 100% VOICEOVER-READY. Write ONLY speakable content that flows naturally when read aloud.\\n\\n"    
                "VOICEOVER REQUIREMENTS:\\n"    
                "- Write in PURE CONVERSATIONAL PROSE only - no bullet points, headers, or formatting\\n"    
                "- NO stage directions, parenthetical notes, or character labels\\n"    
                "- NO meta-commentary about the script itself\\n"    
                "- NO incomplete sections or 'to be continued' references\\n"    
                "- Every sentence must be complete and speakable\\n"    
                "- Use natural speech rhythm with varied sentence lengths\\n"    
                "- Write as if speaking directly to one person in a friendly conversation\\n"    
                "- NO artificial dialogue between characters - tell the story as a narrator\\n"    
                "- NO formatting symbols (* ** - • # [ ] | etc.)\\n"    
                "- NO section breaks or headers within the content\\n\\n"    
            )    
  
            # Conversational YouTube tone prompt    
            conversational_tone_prompt = (    
                "YOUTUBE CONVERSATIONAL TONE REQUIREMENTS:\\n"    
                "- Write like you're talking to a friend over coffee, not writing a novel\\n"    
                "- Use simple, everyday language that anyone can understand\\n"    
                "- Keep sentences SHORT and punchy - average 10-15 words per sentence\\n"    
                "- NO literary descriptions or purple prose - be direct and clear\\n"    
                "- Replace fancy words with simple ones (utilize = use, facilitate = help)\\n"    
                "- Use contractions naturally (don't, can't, won't, here's, that's)\\n"    
                "- Start sentences with simple words (So, Now, But, And, This, Here's)\\n"    
                "- NO overly dramatic language or theatrical descriptions\\n"    
                "- Sound like a real person talking, not a professional narrator\\n"    
                "- Use 'you' to directly address the viewer frequently\\n\\n"    
            )    
  
            # Natural integration prompt    
            natural_integration_prompt = (    
                "NATURAL CONTENT INTEGRATION:\\n"    
                "- Integrate statistics conversationally: 'Here's something crazy...' or 'Get this...'\\n"    
                "- NO formal introductions to data - weave it into the story naturally\\n"    
                "- Replace 'According to experts' with 'Turns out' or 'Here's the thing'\\n"    
                "- Make rhetorical questions sound natural, not forced\\n"    
                "- Use transition phrases that people actually say: 'So here's what happened', 'But wait', 'Now this is where it gets interesting'\\n"    
                "- NO academic or formal language - keep it casual and relatable\\n"    
                "- Make every fact feel like you're sharing a secret with a friend\\n\\n"    
            )    
  
            # Simplification enforcement prompt    
            simplification_prompt = (    
                "MANDATORY SIMPLIFICATION RULES:\\n"    
                "- Maximum sentence length: 20 words\\n"    
                "- NO complex metaphors or elaborate descriptions\\n"    
                "- Replace ALL flowery language with simple, direct statements\\n"    
                "- NO phrases like 'storm brewing in her eyes' - just say 'she looked determined'\\n"    
                "- Cut ALL unnecessary adjectives and adverbs\\n"    
                "- Use active voice, not passive voice\\n"    
                "- Every sentence must pass the 'would I say this to a friend?' test\\n"    
                "- NO poetic language - be practical and straightforward\\n"    
                "- Sound like a regular person telling an interesting story\\n\\n"    
            )    
  
            youtube_script_prompt = (    
                "Write a YouTube script for the given topic that must be started with a powerful Trailer level hook to grab immediate attention. Add a top level hook in the first 30 sec that maintains viewers to watch video from start to end, and then maintain that hook in all over script till end. The script should immediately grab attention and keep viewers hooked. The intro should start by directly proving the video's title claim with a bold and exciting statement. It should make the topic feel important, exclusive, or shocking so that viewers instantly trust that they will get valuable and relevant content. Use simple yet powerful language that builds curiosity and makes them want to keep watching. If possible, include a surprising fact, statistic, or statement that supports the claim. To keep the audience engaged, introduce an element of suspense, danger, mystery, or controversy related to the topic. The goal is to make them feel like they are about to learn something they can't afford to miss. End the intro by teasing what's coming next, making sure the transition into the main content feels natural and exciting. Keep it clear, concise, and full of energy so that viewers stay invested in the video. The tone should match the topic-whether it's thrilling, dramatic, or informative-so that the intro feels like the perfect setup for what's coming next\\n\\n"    
                "Structure the script into clear sections, including an introduction, main content and a conclusion with a specific call to action. I do not want a local plz subscribe type call to action, I want a genius call to action, Use engagement techniques like open loops, delayed reveals, Curiosity, fear, and emotional variety to keep viewers interested in video.\\n\\n"    
                "Apply a storytelling approach with a beginning, middle, and end, using relatable scenarios and transformations. Maintain a conversational and natural tone, avoiding overly complex language or Al-sounding phrases. Ensure that the script aligns with the expectations set by the title or hint provided, and make the CTA at the end engaging and relevant to the topic.\\n\\n"    
                "If there are any relevant, include Well Researched (data, statistics, expert quotes, comparisons etc) Include engaging elements like Rhetorical questions, Contrasts, Humor Cliffhangers before key revelations.\\n\\n"    
                "Use easy wording, Write in paragraphs. Do not suggest scenes and clips. Add engaging sentence starters like 'this was shocking, Let me explain how, This is how' and other suitable engaging starters (these are just examples to understand the concept, apply accordingly)\\n\\n"    
                "NOTE: I want a genius script. Well researched script with a humorous tone. Also please don't include these words: like, we delve into, Unlock the secrets, Join us on a journey, deep, delve, dive, Embark, journey, Discover, explore, Picture this, unravel, embrace, Picture, Get ready, realm, unravel the secrets, In this realm, Let's dive in, Imagine (because these words sound like AI generated content)\\n\\n"    
                "If Duration is above 10 Minutes expand points with more storytelling, examples, and in-depth explanations.\\n\\n"    
                "Clearly introduce the video topic, Add emotional or relatable elements that directly hit viewers mind, to keep them engaged\\n\\n"    
                "Voice & Tone Must be Friendly, engaging, and conversational. Written as if you're speaking directly to the viewer. No robotic or overly formal tone. Use natural pauses and variation in sentence lengths for a human feel\\n\\n"    
                "The most important thing is that I want 5000 Words script, So Write 5000 words script, Don't compromise with me I will count if you write less than given number, so be sure script must be 5000 Words\\n\\n"    
                "CRITICAL QUALITY IMPROVEMENTS - Fix these common weaknesses:\\n"    
                "- START WITH ACTION/CONFLICT immediately, not lengthy scene descriptions\\n"    
                "- Use NATURAL DIALOGUE that sounds like real people talking, avoid formal/artificial speech\\n"    
                "- Create FLAWED, REALISTIC CHARACTERS with authentic reactions and vulnerabilities\\n"    
                "- SHOW through action rather than TELL through excessive description\\n"    
                "- Maintain CONSISTENT PACING - don't drag scenes or rush through important moments\\n"    
                "- Give each character DISTINCT VOICE and speech patterns\\n"    
                "- Build tension GRADUALLY and naturally, avoid forced dramatic moments\\n"    
                "- Make stakes CRYSTAL CLEAR early - what exactly is at risk?\\n"    
                "- Use varied sentence lengths and structures to avoid monotony\\n"    
                "- Cut purple prose - be concise and impactful, not overwritten\\n"    
                "- Ensure smooth scene transitions and logical flow\\n"    
                "- Add unexpected character moments that break stereotypes\\n"    
                "- Balance exposition with action - don't info-dump through dialogue\\n\\n"    
            )    
  
            narrative_flow_prompt = (    
                "NARRATIVE STRUCTURE REQUIREMENTS:\\n"    
                "- Tell the story as a YouTube narrator speaking directly to the audience\\n"    
                "- NO character dialogue scenes - describe what happened instead\\n"    
                "- Use 'Elena did this' or 'Elena said that' rather than writing dialogue\\n"    
                "- Maintain single narrator voice throughout\\n"    
                "- Create smooth transitions between all topics\\n"    
                "- Each paragraph should flow naturally to the next\\n"    
                "- Complete all thoughts and stories - no cliff-hangers mid-section\\n"    
                "- Write in present tense for immediacy\\n\\n"    
            )    
  
            completion_prompt = (    
                "COMPLETION REQUIREMENTS:\\n"    
                "- Every section must be 100% complete with no placeholders\\n"    
                "- NO references to 'coming up next' or 'stay tuned' within sections\\n"    
                "- NO bullet points or lists - convert everything to flowing sentences\\n"    
                "- NO technical formatting or markup\\n"    
                "- Write complete stories and explanations, not outlines\\n"    
                "- End each section with smooth transition to maintain flow\\n\\n"    
            )    
  
            if is_first:    
                prompt = (    
                    f"{voiceover_ready_prompt}"    
                    f"{conversational_tone_prompt}"    
                    f"{natural_integration_prompt}"    
                    f"{simplification_prompt}"    
                    f"You are a master YouTube script writer creating an engaging 5000-word video script.\\n\\n"    
                    f"{youtube_script_prompt}"    
                    f"This is the opening section of the script. Write like you're talking to a friend, not writing literature.\\n"    
                    f"Keep sentences SHORT and punchy. NO flowery descriptions or dramatic language.\\n"    
                    f"Tell Elena's story conversationally - like you're sharing gossip with a friend.\\n\\n"    
                    f"Topic/Outline Point to develop: {point}\\n\\n"    
                    f"OPENING SECTION REQUIREMENTS:\\n"    
                    f"- Write 1200-1500 words in simple, conversational language\\n"    
                    f"- Start with immediate hook - no fancy scene setting\\n"    
                    f"- Use short sentences (10-15 words max)\\n"    
                    f"- Sound like a regular person telling an interesting story\\n"    
                    f"- NO theatrical language or purple prose\\n"    
                    f"- Integrate facts naturally like sharing secrets\\n"    
                    f"- Use contractions and casual language throughout\\n"    
                    f"- Write ONLY speakable script content\\n"    
                    f"Please ONLY provide the story narrative in plain text.\\n"    
                    f"Do NOT include any titles, section headers, explanations, or any text outside of the story.\\n"    
                    f"Write naturally and engagingly as if for a novel or screenplay.\\n\\n"    
                    f"Begin the YouTube script with conversational storytelling:"    
                )    
            elif is_last:    
                prompt = (    
                    f"{voiceover_ready_prompt}"    
                    f"{conversational_tone_prompt}"    
                    f"{natural_integration_prompt}"    
                    f"{simplification_prompt}"    
                    f"You are a master YouTube script writer crafting the conclusion section.\\n\\n"    
                    f"{youtube_script_prompt}"    
                    f"This is the final section. Keep the same casual, friendly tone from previous sections.\\n"    
                    f"Wrap up Elena's story like you're finishing a conversation with a friend.\\n\\n"    
                    f"Topic/Outline Point to develop: {point}\\n\\n"    
                    f"Previous Story Context:\\n{context}\\n\\n"    
                    f"CONCLUSION REQUIREMENTS:\\n"    
                    f"- Write 1200-1500 words in simple, conversational language\\n"    
                    f"- Wrap up Elena's story naturally and casually\\n"    
                    f"- Include genius call-to-action that feels natural\\n"    
                    f"- Keep same friendly, casual tone throughout\\n"    
                    f"- NO fancy conclusions - just wrap it up like a friend would\\n"    
                    f"- Use short, punchy sentences\\n"    
                    f"- Write ONLY speakable script content\\n"    
                    f"Ensure consistency in characters, tone, and events.\\n"    
                    f"Do NOT introduce new subplots or major characters.\\n"    
                    f"Please ONLY provide the story narrative in plain text.\\n"    
                    f"Do NOT include any titles, section headers, explanations, or any text outside of the story.\\n"    
                    f"Write naturally and engagingly as if for a novel or screenplay.\\n\\n"    
                    f"Continue and conclude the YouTube script naturally:"    
                )    
            else:    
                prompt = (    
                    f"{voiceover_ready_prompt}"    
                    f"{conversational_tone_prompt}"    
                    f"{natural_integration_prompt}"    
                    f"{simplification_prompt}"    
                    f"You are a master YouTube script writer developing the middle section.\\n\\n"    
                    f"{youtube_script_prompt}"    
                    f"Continue Elena's story with the same casual, friendly tone.\\n"    
                    f"Keep sentences short and conversational throughout.\\n\\n"    
                    f"Topic/Outline Point to develop: {point}\\n\\n"    
                    f"Previous Story Context:\\n{context}\\n\\n"    
                    f"MIDDLE SECTION REQUIREMENTS:\\n"    
                    f"- Write 1200-1500 words in simple, conversational language\\n"    
                    f"- Continue Elena's story like you're chatting with a friend\\n"    
                    f"- Integrate research and facts naturally, not formally\\n"    
                    f"- Use casual transitions: 'So here's what happened', 'But wait'\\n"    
                    f"- Keep sentences short and punchy (10-15 words)\\n"    
                    f"- NO literary descriptions - just tell the story simply\\n"    
                    f"- Write ONLY speakable script content\\n"    
                    f"Focus: Write at least 500 words for the current outline point.\\n"    
                    f"Instructions: Emphasize consistency in characters, tone, and events.\\n"    
                    f"Please ONLY provide the story narrative in plain text.\\n"    
                    f"Do NOT include any titles, section headers, explanations, or any text outside of the story.\\n"    
                    f"Write naturally and engagingly as if for a novel or screenplay.\\n\\n"    
                    f"Continue the YouTube script conversationally:"    
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
            full_story = ""    
            total_points = len(outline_points)    
            for idx, point in enumerate(outline_points, start=1):    
                print(f"--- Generating story part {idx} ---")    
                story_part = generate_story_part(point, full_story, idx, total_points)    
                if story_part:    
                    print(story_part)    
                    print("\\n")    
                    full_story += "\\n" + story_part    
                    time.sleep(2)    
                else:    
                    print(f"Failed to generate part {idx}. Stopping.")    
                    break    
  
            with open("generated_story.txt", "w") as f:    
                f.write(full_story.strip())    
  
        if __name__ == "__main__":    
            main()  
