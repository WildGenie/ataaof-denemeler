import os
import json
import glob

def find_missing_explanations(base_dir):
    json_files = glob.glob(os.path.join(base_dir, '**', '*.json'), recursive=True)

    missing_count = 0
    total_questions = 0
    files_with_missing = {}

    print(f"Scanning {len(json_files)} files in {base_dir}...\n")

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if 'questions' not in data:
                continue

            current_file_missing = []

            for q in data['questions']:
                total_questions += 1
                # Check for explanation field
                explanation = q.get('explanation')

                # Also check for AnswerExplanation just in case, though file shows 'explanation'
                if not explanation:
                    explanation = q.get('AnswerExplanation')

                if not explanation or not isinstance(explanation, str) or not explanation.strip():
                    current_file_missing.append({
                        'id': q.get('id'),
                        'exam_question_number': q.get('exam_question_number'),
                        'question_text': q.get('question', '')[:50] + "..." if q.get('question') else "No text",
                        'material_id': q.get('material_id')
                    })
                    missing_count += 1

            if current_file_missing:
                files_with_missing[file_path] = current_file_missing

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    # Report results
    print("-" * 80)
    print(f"Total Questions Scanned: {total_questions}")
    print(f"Total Missing Explanations: {missing_count}")
    print("-" * 80)

    if missing_count > 0:
        print("\nDetails by File:")
        for file_path, questions in files_with_missing.items():
            rel_path = os.path.relpath(file_path, base_dir)
            print(f"\nFile: {rel_path} ({len(questions)} missing)")
            for q in questions:
                print(f"  - QID: {q['id']} (Exam Q#{q['exam_question_number']}) [MatID: {q['material_id']}]: {q['question_text']}")
    else:
        print("No missing explanations found!")

if __name__ == "__main__":
    base_dir = "/Users/wildgenie/Projects/ataaof-denemeler/output/anadolu/json"
    find_missing_explanations(base_dir)
