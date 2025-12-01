
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from libs.anadolu_lib import map_to_old_format

def test_title_logic():
    # Test Case 1: Title and Explanation are distinct
    print("\n--- Test Case 1: Distinct Title and Explanation ---")
    q1 = {
        "Title": "This is a title.",
        "AnswerExplanation": "This is an explanation.",
        "QuestionId": 1, "Text": "Q1", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "CorrectAnswer": "A"
    }
    mapped_q1 = map_to_old_format(q1, "Course", "Unit", 1)
    print(f"Title: {q1['Title']}")
    print(f"Explanation: {q1['AnswerExplanation']}")
    print(f"Result: {mapped_q1['Aciklama']}")
    assert mapped_q1['Aciklama'] == "This is a title.<br>This is an explanation."

    # Test Case 2: Title contains Explanation
    print("\n--- Test Case 2: Title contains Explanation ---")
    q2 = {
        "Title": "This is a long title that contains the explanation.",
        "AnswerExplanation": "contains the explanation",
        "QuestionId": 2, "Text": "Q2", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "CorrectAnswer": "A"
    }
    mapped_q2 = map_to_old_format(q2, "Course", "Unit", 1)
    print(f"Title: {q2['Title']}")
    print(f"Explanation: {q2['AnswerExplanation']}")
    print(f"Result: {mapped_q2['Aciklama']}")
    assert mapped_q2['Aciklama'] == "This is a long title that contains the explanation."

    # Test Case 3: Explanation contains Title
    print("\n--- Test Case 3: Explanation contains Title ---")
    q3 = {
        "Title": "Short Title",
        "AnswerExplanation": "This is a long explanation that includes the Short Title inside it.",
        "QuestionId": 3, "Text": "Q3", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "CorrectAnswer": "A"
    }
    mapped_q3 = map_to_old_format(q3, "Course", "Unit", 1)
    print(f"Title: {q3['Title']}")
    print(f"Explanation: {q3['AnswerExplanation']}")
    print(f"Result: {mapped_q3['Aciklama']}")
    assert mapped_q3['Aciklama'] == "This is a long explanation that includes the Short Title inside it."

    # Test Case 4: Identical Title and Explanation
    print("\n--- Test Case 4: Identical Title and Explanation ---")
    q4 = {
        "Title": "Identical Content",
        "AnswerExplanation": "Identical Content",
        "QuestionId": 4, "Text": "Q4", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "CorrectAnswer": "A"
    }
    mapped_q4 = map_to_old_format(q4, "Course", "Unit", 1)
    print(f"Title: {q4['Title']}")
    print(f"Explanation: {q4['AnswerExplanation']}")
    print(f"Result: {mapped_q4['Aciklama']}")
    assert mapped_q4['Aciklama'] == "Identical Content"

    # Test Case 6: HTML Tag Differences (should be deduped)
    print("\n--- Test Case 6: HTML Tag Differences ---")
    q6 = {
        "Title": "<p>Content with <b>bold</b> text.</p>",
        "AnswerExplanation": "Content with bold text.",
        "QuestionId": 6, "Text": "Q6", "A": "A", "B": "B", "C": "C", "D": "D", "E": "E", "CorrectAnswer": "A"
    }
    mapped_q6 = map_to_old_format(q6, "Course", "Unit", 1)
    print(f"Title: {q6['Title']}")
    print(f"Explanation: {q6['AnswerExplanation']}")
    print(f"Result: {mapped_q6['Aciklama']}")
    # clean_html strips tags, so both become "Content with bold text."
    # Deduplication should kick in.
    assert "Content with bold text." in mapped_q6['Aciklama']
    assert "<br>" not in mapped_q6['Aciklama']

if __name__ == "__main__":
    try:
        test_title_logic()
        print("\nAll tests passed!")
    except AssertionError as e:
        print("\nTest failed!")
        raise e
