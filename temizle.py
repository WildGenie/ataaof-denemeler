import re


def process_questions(input_file, output_file):
    """Processes questions from the input file and writes to the output file."""

    with open(input_file, "r", encoding="utf-8") as infile, open(
        output_file, "w", encoding="utf-8"
    ) as outfile:
        # Updated regex pattern
        question_pattern = re.compile(
            r"##### \d+-\)\W((?:.|\n)*?)(?:\n-\W*\*\*(?:A|B|C|D|E)-\)\*\*\W*(.*?)){5}\n-\W*\*\*Boş\*\*\n-.*\n.*\n.*Doğru Cevap : (.)"
            #  r"(### \d+-\)\W(.*?))\n(?:\n- \*\*(?:A|B|C|D|E)\-\)\*\*\W(.*?)){5}\n- \*\*Boş\*\*\n- .*Doğru Cevap : (.)\*\*"
        )

        seen_questions = set()
        question_number = 1

        file_content = infile.read()  # Read the entire file content

        for match in question_pattern.finditer(file_content):
            question_text = match.group(1).strip()

            # Skip duplicate questions
            if question_text in seen_questions:
                continue

            seen_questions.add(question_text)

            question_text = '\\\n'.join(re.sub("^((?:I|V)+)\.",r"\1\\.",s) for s in question_text.split('\n'))

            # Extract options (with text) - Corrected regex
            options = re.findall(
                r"-\W*\*\*(?:A|B|C|D|E)\-\)\*\*\W(.*?)\n", match.group(0)
            )

            # Extract correct answer
            correct_answer = match.group(3)

            # Write to output file
            outfile.write(f"{question_number}.  {question_text}\n\n")
            for i, option in enumerate(options):
                isanswer = chr(65 + i) == correct_answer
                outfile.write(
                    #f"    - {'**Cevap ' if isanswer else ''}{chr(65 + i)}-) {option.strip()}{'**' if isanswer else ''}\n"
                    f"    - {'Cevap ' if isanswer else ''}{chr(65 + i)}-) {option.strip()}{'' if isanswer else ''}\n"
                )  # Format options

            outfile.write("\n\n    ***\n\n")



# Process questions and write to the specified file
input_file = "ATA - Yayın Grafiği - Ham.md"
output_file = "ATA - Yayın Grafiği - Final.md"
process_questions(input_file, output_file)

print(f"Processed questions and answers written to '{output_file}'")
