# All-in-One Password Recovery Utility

A powerful, user-friendly, command-line password recovery tool for ZIP and PDF files, written in Python. This project leverages multiprocessing to maximize performance by utilizing all available CPU cores.

## Features

- **Multi-File Support**: Works with both `.zip` and `.pdf` files.
- **Multiple Attack Modes**:
  - **Dictionary Attack**: Tests passwords from a given wordlist.
  - **Hybrid Attack**: Mutates words from a wordlist with common rules (capitalization, numbers, symbols).
  - **Brute-Force Attack**: Tries all possible character combinations within a specific length range and character set.
- **High Performance**: Uses Python's `multiprocessing` to run attacks in parallel across all CPU cores.
- **User-Friendly Interface**: A clean, interactive menu built with the `rich` library.
- **Robust & Resilient**:
  - Automatically saves progress for Dictionary/Hybrid attacks and allows resuming an interrupted session.
  - Handles corrupted files gracefully without crashing.
  - Includes sanity checks to prevent impossibly large brute-force attacks.
- **Flexible Brute-Force**: Allows you to specify custom character sets (`lowercase`, `uppercase`, `digits`, `symbols`) for targeted attacks.

## ⚠️ Ethical Use Disclaimer

This tool is intended for educational purposes and for use in professional security auditing environments (penetration testing). **Only use this tool on files that you own or have explicit, legal permission to test.** Unauthorized use of this tool on files you do not own is illegal. The author is not responsible for any misuse of this software.

## Installation & Usage

This script is designed for a Linux or macOS environment.

**1. Clone the Repository**
```bash
git clone https://github.com/ahmad-ubaidillah/zip_pdf_pw_cracker/upload
```

**2. Navigate to the Directory**
```bash
cd zip_pdf_pw_cracker
````

**3. Run the Installation Script**
```bash
bash install.sh
````

**4. Run the Application**
```bash
bash run.sh
````

The application will start, presenting you with an interactive menu. Follow the on-screen prompts to begin an attack.

## Understanding the Attack Modes
- **Dictionary Attack**:
    The fastest method if you have a good idea of what the password might be. Use it with a targeted wordlist.
- **Hybrid Attack**:
    Use this when you know a keyword (e.g., a name, a company, a pet) but suspect it's been modified with numbers or symbols (e.g., company123 or !Password!).`
- **Brute-Force Attack**:
    The "last resort" method. Use this only for short passwords when you have no idea what the password could be. For best results, provide a specific character set if you have any clues (e.g., use d for digits if you know the password is a PIN).
