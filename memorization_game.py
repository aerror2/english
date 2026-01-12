import tkinter as tk
from tkinter import messagebox, filedialog
import random
import re
from pathlib import Path
from datetime import datetime

# Read words from file and split into word-definition pairs
def load_words(file_path):
    words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '\t' in line:
                    # If line ends with: <TAB>something<TAB>something<TAB>YYYY-MM-DD HH:MM:SS
                    # then treat it as extra metadata and keep only the head.
                    m = re.match(r"^(.*?)(?:\t[^\t]*\t[^\t]*\t\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})$", line)
                    if m:
                        line = m.group(1).strip()
                if '--' in line:
                    word, definition = line.split('--', 1)
                    words.append((word.strip(), definition.strip()))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load words: {e}")
    return words


def load_words_from_files(file_paths):
    """
    Load word-definition pairs from one or more files.
    Deduplicate by (word.lower(), definition).
    """
    combined = []
    seen = set()
    for fp in file_paths:
        for word, definition in load_words(fp):
            if not word or not definition:
                continue
            key = (word.lower(), definition)
            if key in seen:
                continue
            seen.add(key)
            combined.append((word, definition))
    return combined

# Initialize the main application
class MemorizationGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Memorization Game")
        self.words = []
        self.current_word = None
        self.score = 0  # Initialize score
        self.guessed_words = set()  # Track guessed words
        self.total_tries = 0  # Track total number of tries
        self.selected_files = []
        self.review_log_path = (Path(__file__).resolve().parent / "db_words_to_review.txt")
        self.logged_this_round = set()
        self.current_word_first_try = True
        self.exclude_reviewed_var = tk.BooleanVar(value=True)
        self._reviewed_words_cache = None  # set of lowercased words already in db_words_to_review.txt

        # Main menu
        self.menu_frame = tk.Frame(root)
        self.menu_frame.pack(pady=20)

        tk.Label(self.menu_frame, text="Memorization Game", font=("Arial", 24)).pack()
        tk.Button(self.menu_frame, text="Select Word Files (word*.txt)", command=self.select_word_files).pack(pady=10)
        tk.Checkbutton(
            self.menu_frame,
            text="Exclude words in words_to_review.txt (resume progress)",
            variable=self.exclude_reviewed_var,
            command=self._update_source_label,
        ).pack(pady=4)
        tk.Button(self.menu_frame, text="Meaning → Guess Word", command=self.start_guessing_game).pack(pady=5)
        tk.Button(self.menu_frame, text="Word → Do You Know?", command=self.start_know_game).pack(pady=5)

        # Game frame
        self.game_frame = tk.Frame(root)
        self.source_label = tk.Label(self.menu_frame, text="No word files selected.", font=("Arial", 11), fg="#444")
        self.source_label.pack(pady=10)


    def _append_review_log(self, word, definition, mode, reason):
        """
        Append one line to words_to_review.txt
        Format: word--definition<TAB>mode<TAB>reason<TAB>timestamp
        """
        reviewed = self._get_reviewed_words_cache()
        wl = word.lower()
        # Ensure uniqueness: if word already exists in db_*.txt, don't add again.
        if wl in reviewed:
            return

        key = (word.lower(), definition, mode, reason)
        if key in self.logged_this_round:
            return
        self.logged_this_round.add(key)

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        line = f"{word}--{definition}\t{mode}\t{reason}\t{timestamp}\n"
        try:
            with open(self.review_log_path, "a", encoding="utf-8") as f:
                f.write(line)
            reviewed.add(wl)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to write review log: {e}")


    def _get_reviewed_words_cache(self, force_reload=False):
        """
        Cache reviewed words from review_log_path. This is used for:
        - excluding reviewed words during gameplay
        - ensuring db_*.txt has unique words (checking before append)
        """
        if self._reviewed_words_cache is not None and not force_reload:
            return self._reviewed_words_cache

        reviewed = set()
        try:
            if self.review_log_path.exists():
                with open(self.review_log_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        left = line.split("\t", 1)[0].strip()
                        if "--" in left:
                            w = left.split("--", 1)[0].strip()
                        else:
                            w = left.strip()
                        if w:
                            reviewed.add(w.lower())
        except Exception as e:
            messagebox.showerror("Error", f"Failed to read review log: {e}")

        self._reviewed_words_cache = reviewed
        return self._reviewed_words_cache


    def _load_reviewed_words_set(self):
        """
        Read words_to_review.txt and return a set of reviewed words (lowercased).
        Expected line format:
          word--definition<TAB>mode<TAB>reason<TAB>timestamp
        """
        return set(self._get_reviewed_words_cache())


    def _effective_words(self):
        """Apply 'exclude reviewed' filter if enabled."""
        if not self.exclude_reviewed_var.get():
            return list(self.words)
        reviewed = self._load_reviewed_words_set()
        return [wd for wd in self.words if wd[0].lower() not in reviewed]


    def _update_source_label(self):
        if not self.selected_files:
            self.source_label.config(text="No word files selected.")
            return

        total = len(self.words)
        shown = ", ".join([Path(p).name for p in self.selected_files[:5]])
        more = "" if len(self.selected_files) <= 5 else f" ... (+{len(self.selected_files) - 5})"

        if self.exclude_reviewed_var.get():
            effective = len(self._effective_words())
            excluded = total - effective
            self.source_label.config(
                text=f"Loaded {total} words ({excluded} excluded) from: {shown}{more}"
            )
        else:
            self.source_label.config(text=f"Loaded {total} words from: {shown}{more}")


    def select_word_files(self):
        file_paths = filedialog.askopenfilenames(
            title="Select word*.txt files",
            filetypes=[("Text Files", "*.txt")],
        )
        if not file_paths:
            return

        self.selected_files = list(file_paths)
        self.words = load_words_from_files(self.selected_files)

        if self.words:
            self._update_source_label()
            messagebox.showinfo("Success", f"Loaded {len(self.words)} words from {len(self.selected_files)} file(s).")
        else:
            self.source_label.config(text="No valid words found in selected files.")
            messagebox.showwarning("Warning", "No valid words found in the selected file(s).")

    def start_guessing_game(self):
        if not self.words:
            messagebox.showwarning("Warning", "Please load words first.")
            return
        effective_words = self._effective_words()
        if not effective_words:
            messagebox.showwarning("Warning", "No words available (all excluded by words_to_review.txt).")
            return

        # Reset round stats
        self.score = 0
        self.total_tries = 0
        self.guessed_words = set()
        self.logged_this_round = set()

        self.menu_frame.pack_forget()
        self.game_frame.pack()

        # Select 20 unique words for the round
        self.guessing_round_words = random.sample(effective_words, min(400, len(effective_words)))
        self.current_word_index = 0
        self.show_next_guessing_word()

    def start_know_game(self):
        if not self.words:
            messagebox.showwarning("Warning", "Please load words first.")
            return
        effective_words = self._effective_words()
        if not effective_words:
            messagebox.showwarning("Warning", "No words available (all excluded by words_to_review.txt).")
            return

        self.total_tries = 0
        self.logged_this_round = set()

        self.menu_frame.pack_forget()
        self.game_frame.pack()

        self.know_round_words = random.sample(effective_words, min(1000000, len(effective_words)))
        self.current_word_index = 0
        self.show_next_know_word()

    def show_next_guessing_word(self):
        if self.current_word_index >= len(self.guessing_round_words):
            messagebox.showinfo("Round Complete", f"You have completed this round!\nYour score: {self.score}/{len(self.guessing_round_words)}\nTotal tries: {self.total_tries}\nPerfect score: {len(self.guessing_round_words)}")
            self.back_to_menu()
            return

        self.current_word = self.guessing_round_words[self.current_word_index]
        self.current_word_index += 1
        self.current_word_first_try = True
        
        # Clear previous game frame
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        question = self.current_word[1]  # Definition

        tk.Label(self.game_frame, text="Guess the Word", font=("Arial", 18)).pack(pady=10)
        tk.Label(self.game_frame, text=f"Progress: {self.current_word_index}/{len(self.guessing_round_words)}", font=("Arial", 14)).pack(pady=5)
        tk.Label(self.game_frame, text=question, wraplength=400, font=("Arial", 14)).pack(pady=10)

        self.guess_entry = tk.Entry(self.game_frame, font=("Arial", 14))
        self.guess_entry.pack(pady=10)
        self.guess_entry.focus_set()

        tk.Button(self.game_frame, text="Submit", command=self.check_guess).pack(pady=5)
        tk.Button(self.game_frame, text="Skip (Show Answer & Next)", command=self.skip_guessing_word).pack(pady=5)
        tk.Button(self.game_frame, text="Back to Menu", command=self.back_to_menu).pack(pady=5)

    def check_guess(self):
        guess = self.guess_entry.get().strip()
        self.total_tries += 1  # Increment total tries
        if guess.lower() == self.current_word[0].lower():
            if self.current_word_first_try:
                self.score += 1  # Increment score only if correct on the first attempt
            messagebox.showinfo("Correct!", "You guessed the word correctly!")
            self.show_next_guessing_word()
        else:
            if self.current_word_first_try:
                self._append_review_log(
                    self.current_word[0],
                    self.current_word[1],
                    mode="meaning_to_word",
                    reason="missed_first_try",
                )
                self.current_word_first_try = False
            hint = self.current_word[0][0] if self.current_word[0] else ""
            messagebox.showerror("Incorrect", f"Incorrect. Try again.\nHint: starts with '{hint}'")


    def skip_guessing_word(self):
        self._append_review_log(
            self.current_word[0],
            self.current_word[1],
            mode="meaning_to_word",
            reason="skipped",
        )
        messagebox.showinfo("Answer", f"{self.current_word[0]}\n\nMeaning:\n{self.current_word[1]}")
        self.show_next_guessing_word()


    def show_next_know_word(self):
        if self.current_word_index >= len(self.know_round_words):
            messagebox.showinfo(
                "Round Complete",
                f"You have completed this round!\nTotal shown: {len(self.know_round_words)}\nTotal clicks: {self.total_tries}",
            )
            self.back_to_menu()
            return

        self.current_word = self.know_round_words[self.current_word_index]
        self.current_word_index += 1

        for widget in self.game_frame.winfo_children():
            widget.destroy()

        word = self.current_word[0]
        tk.Label(self.game_frame, text="Do You Know This Word?", font=("Arial", 18)).pack(pady=10)
        tk.Label(self.game_frame, text=f"Progress: {self.current_word_index}/{len(self.know_round_words)}", font=("Arial", 14)).pack(pady=5)
        tk.Label(self.game_frame, text=word, wraplength=400, font=("Arial", 20), fg="#1a1a1a").pack(pady=15)

        btn_frame = tk.Frame(self.game_frame)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="I Know", width=12, command=self.know_yes).grid(row=0, column=0, padx=6, pady=4)
        tk.Button(btn_frame, text="I Don't Know", width=12, command=self.know_no).grid(row=0, column=1, padx=6, pady=4)
        tk.Button(btn_frame, text="Show Meaning", width=12, command=self.show_current_meaning).grid(row=0, column=2, padx=6, pady=4)

        tk.Button(self.game_frame, text="Back to Menu", command=self.back_to_menu).pack(pady=8)


    def show_current_meaning(self):
        messagebox.showinfo("Meaning", f"{self.current_word[0]}\n\n{self.current_word[1]}")


    def know_yes(self):
        self.total_tries += 1
        self.show_next_know_word()


    def know_no(self):
        self.total_tries += 1
        self._append_review_log(
            self.current_word[0],
            self.current_word[1],
            mode="word_to_know",
            reason="dont_know",
        )
        messagebox.showinfo("Meaning", f"{self.current_word[0]}\n\n{self.current_word[1]}")
        self.show_next_know_word()
      
        

    def start_blank_filling(self):
        messagebox.showinfo("Info", "Blank Filling mode is under construction.")

    def start_sentence_making(self):
        messagebox.showinfo("Info", "Sentence Making mode is under construction.")

    def start_article_writing(self):
        messagebox.showinfo("Info", "Article Writing mode is under construction.")

    def back_to_menu(self):
        self.game_frame.pack_forget()
        self.menu_frame.pack()

if __name__ == "__main__":
    root = tk.Tk()
    app = MemorizationGame(root)
    root.mainloop()