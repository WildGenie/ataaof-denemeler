import base64
import json
import re

def extract_course_data(html_content):
    match = re.search(r'window\.courseData\s*=\s*"([^"]+)"', html_content)
    if match:
        encoded_data = match.group(1)
        try:
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            return json.loads(decoded_data)
        except Exception as e:
            print(f"Error decoding data: {e}")
            return None
    return None

def extract_questions(course_data):
    questions = []
    if not course_data or 'course' not in course_data or 'lessons' not in course_data['course']:
        return questions

    for lesson in course_data['course']['lessons']:
        if 'items' not in lesson:
            continue

        for item in lesson['items']:
            # Check for knowledge check or quiz components
            if item.get('type') == 'knowledgeCheck' or item.get('family') == 'knowledgeCheck':
                if 'items' in item:
                    for q_item in item['items']:
                         questions.append(process_question_item(q_item))
            # Check for other types that might contain questions
            elif 'items' in item:
                 for sub_item in item['items']:
                     if sub_item.get('type') == 'knowledgeCheck' or sub_item.get('family') == 'knowledgeCheck':
                         if 'items' in sub_item:
                             for q_item in sub_item['items']:
                                 questions.append(process_question_item(q_item))

    return questions

def process_question_item(item):
    q = {
        "title": item.get("title", ""),
        "type": item.get("type", ""),
        "answers": []
    }

    # Clean up HTML from title
    q["title"] = re.sub(r'<[^>]+>', '', q["title"]).strip()

    if "answers" in item:
        for ans in item["answers"]:
            a_text = re.sub(r'<[^>]+>', '', ans.get("title", "")).strip()
            q["answers"].append({
                "text": a_text,
                "correct": ans.get("correct", False)
            })

    return q

if __name__ == "__main__":
    with open("interactive_index.html", "r", encoding="utf-8") as f:
        html_content = f.read()

    data = extract_course_data(html_content)
    if data:
        print("Successfully extracted course data.")
        # Save raw JSON
        with open("interactive_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        questions = extract_questions(data)
        print(f"Found {len(questions)} questions.")

        # Save processed questions
        with open("interactive_questions.json", "w", encoding="utf-8") as f:
            json.dump(questions, f, indent=4, ensure_ascii=False)

        # Print preview
        for i, q in enumerate(questions[:3]):
            print(f"Q{i+1}: {q['title']}")
            for ans in q['answers']:
                print(f"  - [{'x' if ans['correct'] else ' '}] {ans['text']}")
    else:
        print("Failed to extract course data.")
