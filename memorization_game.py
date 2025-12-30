import tkinter as tk
from tkinter import messagebox, filedialog
import random

# Read words from file and split into word-definition pairs
def load_words(file_path):
    words = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if '--' in line:
                    word, definition = line.split('--', 1)
                    words.append((word.strip(), definition.strip()))
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load words: {e}")
    return words

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

        # Main menu
        self.menu_frame = tk.Frame(root)
        self.menu_frame.pack(pady=20)

        tk.Label(self.menu_frame, text="Memorization Game", font=("Arial", 24)).pack()
        tk.Button(self.menu_frame, text="Load Words", command=self.load_words).pack(pady=10)
        tk.Button(self.menu_frame, text="Guessing Game", command=self.start_guessing_game).pack(pady=5)
        tk.Button(self.menu_frame, text="Blank Filling", command=self.start_blank_filling).pack(pady=5)
        tk.Button(self.menu_frame, text="Sentence Making", command=self.start_sentence_making).pack(pady=5)
        tk.Button(self.menu_frame, text="Article Writing", command=self.start_article_writing).pack(pady=5)

        # Game frame
        self.game_frame = tk.Frame(root)
        self.words = load_words("/Volumes/evo2T/src/english/words.txt")


    def load_words(self):
        file_path = filedialog.askopenfilename(title="Select Words File", filetypes=[("Text Files", "*.txt")])
        if file_path:
            self.words = load_words(file_path)
            if self.words:
                messagebox.showinfo("Success", f"Loaded {len(self.words)} words.")
            else:
                messagebox.showwarning("Warning", "No valid words found in the file.")

    def start_guessing_game(self):
        if not self.words:
            messagebox.showwarning("Warning", "Please load words first.")
            return

        self.menu_frame.pack_forget()
        self.game_frame.pack()

        # Select 20 unique words for the round
        self.guessing_round_words = random.sample(self.words, min(400, len(self.words)))
        self.current_word_index = 0
        self.show_next_guessing_word()

    def show_next_guessing_word(self):
        if self.current_word_index >= len(self.guessing_round_words):
            messagebox.showinfo("Round Complete", f"You have completed this round!\nYour score: {self.score}/{len(self.guessing_round_words)}\nTotal tries: {self.total_tries}\nPerfect score: {len(self.guessing_round_words)}")
            self.back_to_menu()
            return

        self.current_word = self.guessing_round_words[self.current_word_index]
        self.current_word_index += 1
       #print(f"next word: {self.current_word}")
        
        # Clear previous game frame
        for widget in self.game_frame.winfo_children():
           # print(f"Destroying widget: {widget}")
            widget.destroy()

        question = self.current_word[1]  # Definition

        tk.Label(self.game_frame, text="Guess the Word", font=("Arial", 18)).pack(pady=10)
        tk.Label(self.game_frame, text=f"Progress: {self.current_word_index}/{len(self.guessing_round_words)}", font=("Arial", 14)).pack(pady=5)
        tk.Label(self.game_frame, text=question, wraplength=400, font=("Arial", 14)).pack(pady=10)

        self.guess_entry = tk.Entry(self.game_frame, font=("Arial", 14))
        self.guess_entry.pack(pady=10)

        tk.Button(self.game_frame, text="Submit", command=self.check_guess).pack(pady=5)
        tk.Button(self.game_frame, text="Back to Menu", command=self.back_to_menu).pack(pady=5)

    def check_guess(self):
        guess = self.guess_entry.get().strip()
        self.total_tries += 1  # Increment total tries
        if guess.lower() == self.current_word[0].lower():
            if self.current_word[0] not in self.guessed_words:
                self.score += 1  # Increment score only if correct on the first attempt
                self.guessed_words.add(self.current_word[0])
            messagebox.showinfo("Correct!", "You guessed the word correctly!")
            self.show_next_guessing_word()
        else:
            messagebox.showerror("Incorrect", f"The correct word was: {self.current_word[0]}")
      
        

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