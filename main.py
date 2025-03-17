import customtkinter as ctk
from ui.app import PriceComparisonApp

def main():
    print("Starting price comparison application...")
    root = ctk.CTk()
    app = PriceComparisonApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 