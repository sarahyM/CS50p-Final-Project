# The Script Analyzer

#### Video Demo: https://youtu.be/BPTVuGBs5H4

#### Description:

This project is an automated script analyzer specifically designed for the comic lettering industry. Its primary objective is to analyze Word documents and extract precise metrics regarding dialogue. The system is capable of detecting and classifying text into various categories, including standard dialogue, caption dialogue (text boxes), and sound effects (SFX).

To ensure extraction accuracy, a blacklist system has been implemented. If there are specific parameters or keywords that should not be counted as dialogue—such as camera directions or transitions—they can be added to this list to be ignored by the algorithm.

## File Architecture

The development is structured into the following fundamental files:

- **project.py**: The core of the project. It contains the main Script class and all logic functions responsible for document reading, basic natural language processing (NLP), heuristic line evaluation, and metric counting.

- **test_project.py**: The unit testing file. It is responsible for validating the correct functionality of individual functions within project.py (such as the accurate detection of a name or an SFX) to ensure code stability during future modifications.

- **requirements.txt**: A document specifying the external dependencies required to execute the program, such as python-docx (for Word document manipulation) and pyenchant (for spell-checking and dictionary validation).

## Algorithm Functionality and Detection Logic

The central algorithm operates by reading the Word document paragraph by paragraph and line by line. Lines consisting primarily of punctuation marks are omitted. The analysis focuses on short lines, upon which a set of algorithmic and heuristic rules are applied to determine their nature.

### Name Detection (is_name)

To determine if a text string corresponds to a character's name, the function evaluates multiple exclusive conditions:

- It verifies that the potential name is not within the predefined blacklist.
- It evaluates length and composition: if the word exceeds 20 characters or contains specific punctuation marks (!?¿¡), it is automatically discarded as a name.
- If the string passes these filters, it is temporarily classified as a valid character identifier.

### Sound Effect Detection (isSFX)

There is a high probability of confusing an SFX line (e.g., "SFX: CRASH") with a character's dialogue. To mitigate this, a scoring-based heuristic model was designed to calculate the probability (sfx_probability) of a line being a sound effect.

- **Initial Filter**: If the line, when split into words, contains more than 3 elements or includes the ":" character, it is assigned a probability of 0, assuming it is a line of dialogue.
- **Probability Accumulation**: The system iterates over the words in the line, assigning weighted values. The presence of specific symbols (!, ?, *, -, ., ,) adds 0.3 points.
- **Morphological Analysis**: Words are normalized. If they feature unusually sequential repeated letters (e.g., "CRAAASH"), the probability increases by 0.5. If the word does not exist in the selected dictionary, 0.2 is added. Finally, if it matches the predefined set of SFX words, 1.0 is added. The final value is normalized to a maximum of 1.0.

## Additional Function Documentation

In addition to the previously mentioned functions, the system is composed of the following modules:

- **Script (Class)**: A data structure that encapsulates the state of the analyzed script. It stores the filename, page count, total dialogue count, a character dictionary with their respective interventions, and expected symbol formats.

- **dialogues_search(line, user_script, dictionary)**: Evaluates a line of text using a scoring system to determine if it contains a dialogue attribution. It subtracts points if words are common (found in the dictionary without initial capitalization) or if they have a high probability of being an SFX. It adds points based on regular expression (regex) patterns and the use of uppercase letters.

- **dialogue_validation(user_script, lines, d)**: The orchestrator function for text processing. It divides lines using common delimiters (:, --, -), cleans the text of special characters (like brackets or parentheses), and calls dialogues_search. It also manages character storage logic, ensuring variations like "JOSH" and "JOSH (CONT)" are counted under a single entity by processing the first element of the string.

- **page_count(lines)**: Scans the document for pagination patterns (e.g., "PAGE 1") using regex to establish the total length of the document.

- **read_file(doc)**: Utilizes the docx library to extract plain text from the Word file, separating paragraphs into a sequential list of lines.

- **average(dialogues, pages)**: Calculates dialogue density, returning the average number of interventions per page.

- **dictionary_setup()**: Initial configuration interface that allows the user to select the analysis language (English or Spanish) to load the corresponding pyenchant dictionary.

- **main()**: The entry point of the program. It requests the file path, initializes classes, executes validation, and presents the final metrics in the console.

## Design Decisions

Natural Language Processing (NLP) presents inherent challenges due to the complexity and infinite combinations of human language. The most significant design decision was to avoid strict binary rules in favor of a heuristic scoring and probability system.

Grouping rules into a probabilistic evaluation proved to be the most appropriate methodological approach, as there is no single grammatical rule that unifies all script formats.

## Overcoming Technical Challenges

### Differentiating SFX vs. Characters

Onomatopoeic words or prolonged sound effects share structural similarities with proper names in uppercase. Implementing a count for consecutive repeated characters solved this ambiguity (e.g., differentiating "CRAAASH" from a real name).

### Unifying Character Entities

Character accounting required additional logic to prevent duplicate records. A tiered search rule was established: the system first checks for the existence of the full string in the character dictionary; if not found, it searches for the first element of the string (to group cases like identifiers followed by a continuity tag). If neither condition is met, a new record is created.

## Installation and Usage

### Prerequisites

- Python 3.x
- A functional installation of C libraries for pyenchant (varies by OS, e.g., `brew install enchant` on macOS or `apt-get install enchant-2` on Linux).

### Installation

1. Clone or download this repository to your local machine.
2. Navigate to the project root directory.
3. Install the required Python dependencies using pip:

```bash
pip install -r requirements.txt
```

### Running the Project

1. Execute the main script:

```bash
python project.py
```

2. When prompted, enter the full path to your .docx script file.
3. Select your script's language (1 for English, 2 for Spanish) to load the appropriate dictionary.
4. Review the generated metrics (Total dialogues, Total pages, and Average dialogue per page) displayed in the terminal.
#
