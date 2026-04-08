import enchant
import os
import re
from pathlib import Path
from docx import Document
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

sfx = {
    "achoo", "bam", "bang", "bark", "beep", "buzz", "chirp", "clank",
    "click", "cluck", "crack", "crackk", "crash", "crunch", "crunchh",
    "drip", "giggle", "gurgle", "hiccup", "hiss", "knock", "meow",
    "mumble", "oh", "ping", "pop", "roar", "rustle", "screech",
    "slam", "slap", "slurp", "snore", "splash", "squelch", "thud",
    "tick tock", "tick-tock", "tweet", "wheeze", "whir", "zip", "zoom"
}

blacklist = {
    "PAGE", "PANEL", "CONTINUED", "TRANSITION", "VFX", "SOUND",
    "INT.", "EXT.", "CUT TO", "FADE IN", "CLOSE UP",
    "GUION", "TESTEO", "TITLE", "FIN", "END"
}


class Script:
    def __init__(self, name):
        self.name = name
        self.pages = 0
        self.dialogue_count = 0
        self.characters = {}
        self.symbols = (":", "-", "--")


def is_name(name):
    # Here we check if it is not a forbidden word, in case it is, it returns false
    if name in blacklist or any(word in blacklist for word in name.split()):
        return False
    # Here we check if the word is too long and has weird signs, IT IS NOT A NAME, FALSE IS RETURNED
    if len(name) > 20 or any(c in name for c in "!?¿¡"):
        return False

    # If it does not meet the above conditions, it is a name and everything is fine :)
    return True


def is_sfx(full_line, dictionary):
    # Here I can read the complete line and if the line has more than 4 elements, 4 words, then I return 0, because it means it is a dialogue and not an SFX

    words = full_line.split()

    if len(words) > 3 or ":" in full_line:
        return 0  # Returns 0 because it means we are facing a dialogue line, i.e., IT IS NOT AN SFX

    # These are the symbols that an SFX is very likely to have
    symbols = ("!", "?", "*", "-", ".", ",")
    sfx_probability = 0  # This is the probability that a word is an SFX

    # We are going to iterate through the word list
    for word in words:
        # Here I am validating if the word has one of the symbols that makes me suspect it is an SFX
        if any(l in symbols for l in word):
            sfx_probability += 0.3

        # Here we are going to check if the word has many repeated letters, for this we are going to clean it
        clean_word = word.lower().strip('.,!?;:()-\"')

        # Here, although there are words that repeat two letters, we are going to give it a slight suspicion that it is an SFX
        if any(clean_word.count(l) > 2 for l in clean_word):
            sfx_probability += 0.5

        # The fact that the word is not in the dictionary gives me a minimal suspicion that it is an SFX
        if clean_word:
            if not dictionary.check(clean_word):
                sfx_probability += 0.2

        if clean_word in sfx:
            sfx_probability += 1

    # Here I am going to validate if the word is repeated
    lowercase_words = [p.lower().strip('.,!?;:()-\"') for p in words]
    if any(lowercase_words.count(p) > 1 for p in lowercase_words):
        sfx_probability += 0.3

    return min(sfx_probability, 1.0)


def dialogue_search(line, user_script, dictionary):
    score = 0
    words = line.split()

    # Here I am validating if the line starts with page or panel or if there are no words to validate
    if line.upper().startswith(("PAGE", "PANEL")) or not words:
        return None, 0

    if len(words) == 1:
        word = words[0].strip('.,!?;:()-\"')
        if word:
            if dictionary.check(word.lower()) and not (word.istitle() or word.isupper()):
                score -= 0.5

    is_name_flag = all(p[0].isupper() for p in words if p and p[0].isalpha())
    is_upper = line.isupper()

    # Here we are going to verify if it is an SFX
    sfx_probability = is_sfx(line, dictionary)

    if is_name_flag or is_upper:
        sfx_probability /= 2

    if sfx_probability > 0.5:
        return None, 0
    else:
        score -= sfx_probability  # This is to start from a suspicion of an SFX

    if 0 < len(words) <= 2 and is_name_flag:
        score += 0.7

    if any(p.endswith(user_script.symbols) for p in words) and all(p.istitle() for p in words):
        score += 0.8

    pattern = r"^[0-9]?[0-9]?[A-Z0-9 \-]+:?|^[0-9]?[0-9]?[A-Z0-9 \-]+-?"

    if re.search(pattern, line, re.IGNORECASE):
        score += 0.3

    if len(words) == 1:
        return words[0], score
    elif len(words) > 1:
        return " ".join(words[:3]), score


def dialogue_validation(user_script, lines, dictionary_obj):
    for line_item in lines:
        pattern = r":|--| - "
        parts = re.split(pattern, line_item, maxsplit=1)

        possible_name = parts[0] if len(parts) > 1 else line_item

        clean_name = possible_name.strip("[]").split("(")[0].strip()

        if not clean_name or len(clean_name) < 2:
            continue

        if clean_name.endswith(("?", "!", ".")):
            continue

        if len(parts) > 1:
            given_name, score = dialogue_search(
                clean_name, user_script, dictionary_obj)
        else:
            given_name, score = dialogue_search(
                line_item, user_script, dictionary_obj)

        if given_name:
            name = given_name.upper().strip(
                ".,!?;:()-[]").replace("(", "").replace(")", "").strip()
            if is_name(name) and score > 0.7:
                if user_script.characters.get(name):
                    user_script.characters[name] += 1
                # IF WE DON'T FIND THAT NAME, WE PROCESS IT TO SEE IF WE SAVE IT USING ONLY ITS POSITION [0]
                elif not user_script.characters.get(name):
                    processed_name_list = name.split()
                    if user_script.characters.get(processed_name_list[0]):
                        user_script.characters[processed_name_list[0]] += 1
                    else:
                        # IF IT DOESN'T APPEAR IN ANY CASE, WE CREATE IT
                        user_script.characters[name] = user_script.characters.get(
                            name, 0) + 1

                user_script.dialogue_count += 1


def page_count(lines):
    pattern = "^page[0-9]?[0-9]?[0-9]?|^pagina[0-9]?[0-9]?[0-9]?|^página[0-9]?[0-9]?[0-9]?"
    page_count_total = 0

    for line in lines:
        if re.search(pattern, line, re.IGNORECASE):
            page_count_total += 1

    return page_count_total


def read_file(doc):
    lines = []
    for paragraph in doc.paragraphs:
        internal_lines = paragraph.text.split("\n")
        for line in internal_lines:
            lines.append(line)
    return lines


def average(dialogues: int, pages: int):
    if pages == 0:
        return 0
    return round((dialogues / pages), 2)


# This is to configure the dictionary
def dictionary_setup():
    console = Console()
    console.print("\n[bold cyan]Configuración de idioma[/bold cyan]")
    console.print("1. Inglés (en_US)")
    console.print("2. Español (es_ES)")

    option = int(input("\nSelecciona el idioma (1 o 2): ").strip())

    try:
        if option == 1:
            return enchant.Dict("en_US")
        elif option == 2:
            return enchant.Dict("es_ES")
        else:
            print("Opcion no valida, cargando diccionario ingles por defecto.")
            return enchant.Dict("en_US")
    except enchant.errors.DictNotFoundError:
        print("Error: El diccionario solicitado no está instalado en tu sistema.")
        return None


# This function is to display the table:
def display_results(user_script, avg_dialogues):
    console = Console()

    # We create the table
    table = Table(
        title=f"Resultados del Análisis:\n[bold]{user_script.name}[/bold]", show_header=True, header_style="bold magenta")
    table.add_column("Personaje", style="cyan")
    table.add_column("Intervenciones", justify="right", style="green")

    # We sort the characters by who speaks the most
    sorted_chars = sorted(user_script.characters.items(),
                          key=lambda x: x[1], reverse=True)

    for char, count in sorted_chars:
        table.add_row(char, str(count))

    # We print the table
    console.print(table)

    # Final summary panel
    summary = (
        f"Total de Diálogos: [bold]{user_script.dialogue_count}[/bold]\n"
        f"Total de Páginas: [bold]{user_script.pages}[/bold]\n"
        f"Promedio: [bold yellow]{avg_dialogues}[/bold yellow] diálogos por página"
    )
    console.print(Panel(summary, title="Resumen Métrico", border_style="blue"))


def main():
    console = Console()
    file_route = input("What's the route to your file? ").strip().replace(
        "'", "").replace('"', "")

    if not os.path.exists(file_route):
        print("El archivo no existe")
        return
    file_name = Path(file_route).stem

    document = Document(file_route)
    lines = read_file(document)

    user_script = Script(file_name)

    dictionary = dictionary_setup()

    with console.status("[bold green]Analizando guion..."):
        dialogue_validation(user_script, lines, dictionary)
        user_script.pages = page_count(lines)
        if user_script.pages > 0:
            avg = average(user_script.dialogue_count, user_script.pages)
        else:
            avg = 0

    # Call to the pretty table
    display_results(user_script, avg)


if __name__ == "__main__":
    main()
