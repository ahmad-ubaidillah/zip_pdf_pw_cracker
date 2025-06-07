import itertools
import string
import time
import zipfile
import os
import sys
import json
from multiprocessing import Pool, Manager, cpu_count
from datetime import datetime
import zlib

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
    from rich.text import Text
except ImportError:
    print("Error: The 'rich' library is not found. Please run the install script again: ./install.sh")
    sys.exit(1)

# Other core library
try:
    import pikepdf
except ImportError:
    print("Error: The 'pikepdf' library is not found. Please run the install script again: ./install.sh")
    sys.exit(1)

# --- Global Configuration ---
console = Console()
SESSION_FILE = "session.json"

# --- Global Worker Variables ---
worker_file_path = None
worker_stop_event = None
worker_file_type = None

# (Fungsi-fungsi lain tidak berubah)
def get_char_set(shortcuts):
    """Translates charset shortcuts into a character string."""
    char_map = {
        'l': string.ascii_lowercase,
        'u': string.ascii_uppercase,
        'd': string.digits,
        's': string.punctuation + ' ',
        'h': string.hexdigits.lower(),
        'H': string.hexdigits.upper(),
    }
    return ''.join(sorted(list(set(''.join(char_map.get(c, '') for c in shortcuts)))))

def check_zip_password(password):
    """Tries to open a ZIP file with a password, handling corrupted data errors."""
    try:
        with zipfile.ZipFile(worker_file_path, 'r') as zf:
            zf.extractall(pwd=password.encode())
        return True
    except (RuntimeError, zipfile.BadZipFile, zlib.error):
        return False

def check_pdf_password(password):
    """Tries to open a PDF file with a password."""
    try:
        with pikepdf.open(worker_file_path, password=password):
            pass
        return True
    except pikepdf.PasswordError:
        return False

def init_worker(file_path, file_type, stop_event):
    """Initializes global variables for each worker process."""
    global worker_file_path, worker_file_type, worker_stop_event
    worker_file_path = file_path
    worker_file_type = file_type
    worker_stop_event = stop_event

def try_password(password):
    """The function executed by each worker. Tries a single password."""
    if worker_stop_event.is_set():
        return None
    checker_func = check_zip_password if worker_file_type == 'zip' else check_pdf_password
    if checker_func(password):
        worker_stop_event.set()
        return password
    return None

def save_session(session_data):
    """Saves the attack session data to a JSON file."""
    with open(SESSION_FILE, "w") as f:
        json.dump(session_data, f, indent=4)

def load_session():
    """Loads an attack session data from a JSON file."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

def clear_session():
    """Deletes the session file if it exists."""
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def generate_hybrid_mutations(word):
    """Generates various mutations from a base word, with rule combination."""
    base_mutations = set()
    base_mutations.add(word)
    base_mutations.add(word.lower())
    base_mutations.add(word.upper())
    base_mutations.add(word.capitalize())
    
    leet_map = {'a': '@', 'o': '0', 'e': '3', 'i': '1', 's': '$'}
    leet_word = "".join(leet_map.get(c.lower(), c) for c in word)
    if leet_word != word:
        base_mutations.add(leet_word)
        base_mutations.add(leet_word.capitalize())

    final_mutations = set(base_mutations)
    
    suffixes = [str(datetime.now().year), str(datetime.now().year-1), '123', '1', '12345']
    symbols = ['!', '@', '#', '_', '$']

    for base_word in base_mutations:
        for sym in symbols:
            final_mutations.add(f"{base_word}{sym}")
            final_mutations.add(f"{sym}{base_word}")

        for suf in suffixes:
            final_mutations.add(f"{base_word}{suf}")
        
        for sym in symbols:
            word_with_sym = f"{base_word}{sym}"
            for suf in suffixes:
                final_mutations.add(f"{word_with_sym}{suf}")

    return list(final_mutations)


def launch_attack(attack_params):
    """Configures and starts the password cracking process."""
    passwords_to_try = []
    total_passwords = 0
    mode = attack_params['mode']
    
    console.print("\n[bold cyan]🚀 Preparing attack...[/bold cyan]")

    if mode in ['dictionary', 'hybrid']:
        try:
            with open(attack_params['wordlist'], 'r', encoding='utf-8', errors='ignore') as f:
                base_words = [line.strip() for line in f if line.strip()]
            
            if attack_params.get('resume_from'):
                last_word = attack_params['resume_from']
                try:
                    resume_index = base_words.index(last_word)
                    console.print(f"✅ [bold]Resuming session.[/bold] Skipping first {resume_index + 1} words.")
                    base_words = base_words[resume_index + 1:]
                except ValueError:
                    console.print(f"⚠️ [yellow]Warning:[/yellow] Last password '{last_word}' not found in wordlist. Starting from the beginning.")

            if mode == 'hybrid':
                all_mutations = []
                for word in base_words:
                    all_mutations.extend(generate_hybrid_mutations(word))
                passwords_to_try = list(dict.fromkeys(all_mutations))
            else:
                passwords_to_try = base_words
                
            total_passwords = len(passwords_to_try)

        except FileNotFoundError:
            console.print(f"❌ [bold red]Error:[/bold red] Wordlist file not found at '{attack_params['wordlist']}'")
            return
            
    elif mode == 'bruteforce':
        char_set = get_char_set(attack_params['charset'])
        console.print(f"ℹ️  [bold]Brute-force[/bold] using charset: '[green]{char_set}[/green]'")
        passwords_to_try = (
            ''.join(p) for length in range(attack_params['min_len'], attack_params['max_len'] + 1) 
            for p in itertools.product(char_set, repeat=length)
        )
        total_passwords = sum(len(char_set) ** i for i in range(attack_params['min_len'], attack_params['max_len'] + 1))
        
        PRACTICAL_LIMIT = 100_000_000_000
        if total_passwords > PRACTICAL_LIMIT:
            console.print(Panel(f"❌ [bold red]ERROR: Combination Count Too Large[/bold red]\n\nThe total number of passwords ({total_passwords:,}) is too large to be processed.\n\nPlease choose a smaller length range ([bold]min/max[/bold]).", title="[red]Warning[/red]", border_style="red"))
            Prompt.ask("\nPress Enter to return to the main menu")
            return

    if total_passwords == 0:
        console.print("🤷 [yellow]Warning:[/yellow] No passwords to try. Aborting attack.")
        return
    
    summary_table = Table(title="Attack Summary", show_header=False, border_style="cyan")
    summary_table.add_row("Attack Mode", f"[bold]{mode.capitalize()}[/bold]")
    summary_table.add_row("Target File", f"[yellow]{attack_params['file_path']}[/yellow]")
    summary_table.add_row("Total Passwords", f"{total_passwords:,}")
    summary_table.add_row("Worker Processes", str(attack_params['workers']))
    console.print(summary_table)

    start_time = time.time()
    found_password = None
    
    with Manager() as manager, Pool(processes=attack_params['workers'], initializer=init_worker, initargs=(attack_params['file_path'], attack_params['file_type'], manager.Event())) as pool:
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            "[progress.percentage]{task.percentage:>3.0f}%", "•",
            TextColumn("{task.completed} of {task.total}"), "•",
            TimeRemainingColumn(),
            console=console
        ) as progress:
            
            task = progress.add_task("[green]Cracking Passwords...", total=total_passwords)

            if mode == 'bruteforce':
                chunk_size = 10000 
            else:
                chunk_size = max(1, total_passwords // (attack_params['workers'] * 10)) if total_passwords > 1000 else 1

            results = pool.imap_unordered(try_password, passwords_to_try, chunksize=chunk_size)
            
            passwords_checked_since_save = 0
            for i, result in enumerate(results):
                progress.update(task, advance=1)
                
                if mode in ['dictionary', 'hybrid']:
                    passwords_checked_since_save += 1
                    if passwords_checked_since_save >= 1000:
                        pass
                
                if result:
                    found_password = result
                    pool.terminate()
                    progress.stop()
                    break
    
    end_time = time.time()
    duration = end_time - start_time

    console.print("\n" + "="*60)
    if found_password:
        console.print(Panel(f"[bold green]✅ SUCCESS! Password Found![/bold green]\n\n🔑 Password: [bold magenta]{found_password}[/bold magenta]", border_style="green"))
        clear_session()
    else:
        console.print(Panel("❌ [bold red]FAILED.[/bold red] Password not found.", border_style="red"))
    
    results_table = Table(title="Execution Summary", border_style="blue")
    results_table.add_column("Metric", style="cyan")
    results_table.add_column("Value", style="bold")
    results_table.add_row("Total Time", f"{duration:.2f} seconds")

    if duration > 0 and progress.tasks:
        speed = progress.tasks[0].completed / duration
        results_table.add_row("Average Speed", f"{speed:,.2f} passwords/sec")

    console.print(results_table)
    
    Prompt.ask("\nPress Enter to return to the main menu")

def main():
    """Main function to run the interactive menu UI."""
    attack_params = {}
    
    session = load_session()
    if session:
        if Confirm.ask(f"[bold yellow]⚠️ Found an unfinished session for '{os.path.basename(session['file_path'])}'. Resume?[/bold yellow]"):
            launch_attack(session)
        else:
            clear_session()

    while True:
        console.clear()
        console.print(Panel("[bold]All-in-One Password Recovery Utility[/bold]", title="[blue]Welcome!", border_style="blue"))
        
        console.print("\n[bold]Select File Type:[/bold]")
        console.print("1. Crack ZIP file")
        console.print("2. Crack PDF file")
        console.print("3. Exit")
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3"], default="3")

        if choice == '3':
            console.print("[bold cyan]Goodbye![/bold cyan]")
            break
        elif choice in ['1', '2']:
            attack_params['file_type'] = 'zip' if choice == '1' else 'pdf'
            
            file_path = Prompt.ask(f"Enter the path to the [bold].{attack_params['file_type']}[/bold] file")
            
            if len(file_path) > 1 and file_path.startswith("'") and file_path.endswith("'"):
                file_path = file_path[1:-1]
            elif len(file_path) > 1 and file_path.startswith('"') and file_path.endswith('"'):
                file_path = file_path[1:-1]

            if not (os.path.exists(file_path) and file_path.lower().endswith(attack_params['file_type'])):
                console.print(f"❌ [bold red]Error:[/bold red] File not found or incorrect type.")
                time.sleep(2)
                continue
            attack_params['file_path'] = file_path

            console.print(f"\n[bold]Select Attack Mode for [yellow]{os.path.basename(file_path)}[/yellow]:[/bold]")
            console.print("1. Dictionary Attack")
            console.print("2. Brute-Force Attack")
            console.print("3. Hybrid Attack")
            console.print("4. Back to Main Menu")

            mode_choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="4")

            if mode_choice == '4':
                continue

            if mode_choice in ['1', '3']:
                attack_params['mode'] = 'dictionary' if mode_choice == '1' else 'hybrid'
                wl_path = Prompt.ask("Enter the path to your wordlist file")

                if len(wl_path) > 1 and wl_path.startswith("'") and wl_path.endswith("'"):
                    wl_path = wl_path[1:-1]
                elif len(wl_path) > 1 and wl_path.startswith('"') and wl_path.endswith('"'):
                    wl_path = wl_path[1:-1]

                if os.path.exists(wl_path):
                    attack_params['wordlist'] = wl_path
                else:
                    console.print("❌ [bold red]Error:[/bold red] Wordlist file not found.")
                    time.sleep(2)
                    continue

            elif mode_choice == '2':
                attack_params['mode'] = 'bruteforce'

                # --- [PERBAIKAN] --- Panel penjelasan yang lebih informatif ---
                help_text = Text.from_markup("""
[bold]l[/bold]: [green]lowercase[/green]   (a, b, c, ...)
[bold]u[/bold]: [green]uppercase[/green]   (A, B, C, ...)
[bold]d[/bold]: [green]digits[/green]      (0, 1, 2, ...)
[bold]s[/bold]: [green]symbols[/green]     (e.g., !@#$ and space)

[dim]-- Special Use Cases --[/dim]
[bold]h[/bold]: [yellow]hex (lower)[/yellow]   (0-9, a-f, for network keys, etc.)
[bold]H[/bold]: [yellow]hex (upper)[/yellow]   (0-9, A-F)
""")
                console.print(Panel(help_text, title="[bold cyan]Select Charset for Brute-Force[/bold cyan]", border_style="cyan"))
                # --- [AKHIR PERBAIKAN] ---

                attack_params['charset'] = Prompt.ask("Enter charset combination (e.g., 'luds' for all)", default='luds')
                
                attack_params['min_len'] = int(Prompt.ask("Enter minimum length", default="4"))
                attack_params['max_len'] = int(Prompt.ask("Enter maximum length", default="8"))

            attack_params['workers'] = int(Prompt.ask("Enter number of worker processes", default=str(cpu_count())))
            
            save_session(attack_params)
            launch_attack(attack_params)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n[bold yellow]Process interrupted by user. Goodbye![/bold yellow]")
        sys.exit(0)