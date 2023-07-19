import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
from tkinter import messagebox
from ttkthemes import ThemedStyle
import json
import tempfile
import win32api


current_version = "1.2.3"
file_path = ""
changes_made = False
category_entries = []
amount_entries = []
num_expenses = 0
remove_buttons = []
ascending_order = True


def calculate_expenses():
    global changes_made

    income = income_entry.get().strip()

    if not income:
        return

    try:
        income = float(income)
    except ValueError:
        return

    expenses = {}
    for i in range(num_expenses):
        if i >= len(category_entries):
            continue

        category = category_entries[i].get()
        amount = amount_entries[i].get().strip()

        if amount:
            try:
                amount = float(amount)
            except ValueError:
                continue

            expenses[category] = amount

    percentages, remaining_amount = calculate_percentages(income, expenses)

    remaining_amount_label.config(text=f"Remaining amount: {remaining_amount:.2f}")

    sorted_percentages = sorted(
        percentages.items(), key=lambda item: item[1], reverse=not ascending_order
    )  # Sort percentages based on ascending/descending order

    percentages_text.configure(state="normal")
    percentages_text.delete(1.0, tk.END)
    for category, percentage in sorted_percentages:
        percentages_text.insert(tk.END, f"{category}: {percentage:.2f}%\n")
    percentages_text.configure(state="disabled")

    changes_made = True


def add_expense_line():
    global num_expenses, changes_made

    # Create StringVar variables to track changes in the entry fields
    category_var = tk.StringVar()
    amount_var = tk.StringVar()

    category_entry = ttk.Entry(expense_lines_frame, textvariable=category_var)
    category_entry.grid(row=num_expenses, column=0, padx=10, pady=5, sticky=tk.W)
    category_entries.append(category_entry)

    amount_entry = ttk.Entry(expense_lines_frame, textvariable=amount_var)
    amount_entry.grid(row=num_expenses, column=1, padx=10, pady=5, sticky=tk.W)
    amount_entries.append(amount_entry)

    remove_button = ttk.Button(
        expense_lines_frame, text="-",
        command=lambda index=num_expenses: remove_expense_line(index),
        width=5
    )
    remove_button.grid(row=num_expenses, column=2, padx=10, pady=5, sticky=tk.W)
    remove_buttons.append(remove_button)

    num_expenses += 1

    calculate_expenses()
    changes_made = True

    # Bind the calculate_expenses function to the <<Modified>> event of the StringVar variables
    category_var.trace_add("write", lambda *_: calculate_expenses())
    amount_var.trace_add("write", lambda *_: calculate_expenses())

    # Bind the calculate_expenses function to the <<Modified>> event of the entry fields
    category_entry.bind("<<Modified>>", lambda event: calculate_expenses())
    amount_entry.bind("<<Modified>>", lambda event: calculate_expenses())

    # Set the background color of the expense_lines_frame
    style.configure("TFrame", background=center_frame["background"])


def remove_expense_line(index):
    global num_expenses, changes_made

    category_entries[index].destroy()
    amount_entries[index].destroy()
    remove_buttons[index].destroy()

    category_entries.pop(index)
    amount_entries.pop(index)
    remove_buttons.pop(index)

    num_expenses -= 1

    # Reconfigure the grid for remaining expense lines
    for i in range(num_expenses):
        category_entries[i].grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
        amount_entries[i].grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
        remove_buttons[i].config(command=lambda idx=i: remove_expense_line(idx))
        remove_buttons[i].grid(row=i, column=2, padx=10, pady=5, sticky=tk.W)

    calculate_expenses()
    changes_made = True

    # Bind the calculate_expenses function to the <<Modified>> event of the entry fields
    for entry in category_entries + amount_entries:
        entry.bind("<<Modified>>", lambda event: calculate_expenses())

    print("Expense line removed.")


def calculate_percentages(income, expenses):
    percentages = {}
    total_expenses = sum(expenses.values())

    for category, amount in expenses.items():
        percentage = (amount / income) * 100
        percentages[category] = percentage

    remaining_amount = income - total_expenses

    return percentages, remaining_amount


def exit_application():
    global num_expenses, changes_made

    if num_expenses > 0 and changes_made:
        response = messagebox.askyesnocancel(
            "Save Changes", "Do you want to save changes before exiting?"
        )

        if response is None:
            return

        if response:
            save_file()

    window.destroy()


def save_file():
    global file_path, changes_made

    if not file_path:
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )

    if file_path:
        data = {
            "income": income_entry.get().strip(),
            "expenses": []
        }

        for i in range(num_expenses):
            category = category_entries[i].get()
            amount = amount_entries[i].get().strip()
            data["expenses"].append({"category": category, "amount": amount})

        with open(file_path, "w") as file:
            json.dump(data, file)

        print(f"Data saved to: {file_path}")
        changes_made = False


def save_as_file():
    global file_path, changes_made

    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if file_path:
        save_file()


def open_file():
    global file_path, changes_made, num_expenses, category_entries, amount_entries, remove_buttons

    file_path = filedialog.askopenfilename(
        filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
    )
    if file_path:
        with open(file_path, "r") as file:
            data = json.load(file)

            income = data.get("income", "")
            income_entry.delete(0, tk.END)
            income_entry.insert(0, income)

            expenses = data.get("expenses", [])
            num_expenses = len(expenses)

            # Clear the grid cell of the expense lines frame
            for widget in expense_lines_frame.winfo_children():
                widget.grid_forget()

            category_entries = []
            amount_entries = []
            remove_buttons = []

            for i, expense in enumerate(expenses):
                category = expense.get("category", "")
                amount = expense.get("amount", "")

                category_entry = ttk.Entry(expense_lines_frame)
                category_entry.grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
                category_entry.insert(0, category)
                category_entries.append(category_entry)

                amount_entry = ttk.Entry(expense_lines_frame)
                amount_entry.grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
                amount_entry.insert(0, amount)
                amount_entries.append(amount_entry)

                remove_button = ttk.Button(
                    expense_lines_frame, text="-",
                    command=lambda idx=i: remove_expense_line(idx),
                    width=5
                )
                remove_button.grid(row=i, column=2, padx=10, pady=5, sticky=tk.W)
                remove_buttons.append(remove_button)

            calculate_expenses()

    print(f"Data loaded from: {file_path}")
    changes_made = False


def new_file():
    global file_path, num_expenses, changes_made

    if num_expenses > 0 or changes_made:
        response = messagebox.askyesnocancel(
            "Save Changes", "Do you want to save changes before starting a new file?"
        )

        if response is None:
            return

        if response:
            save_file()

    # Reset the file_path and clear the expense lines
    file_path = ""
    num_expenses = 0

    # Clear the grid cell of the expense lines frame
    for widget in expense_lines_frame.winfo_children():
        widget.grid_forget()

    # Redraw the remaining expense lines (in case there were any)
    for i in range(num_expenses):
        category_entries[i].grid(row=i, column=0, padx=10, pady=5, sticky=tk.W)
        amount_entries[i].grid(row=i, column=1, padx=10, pady=5, sticky=tk.W)
        remove_buttons[i].grid(row=i, column=2, padx=10, pady=5, sticky=tk.W)

    # Reset other GUI elements as needed
    income_entry.delete(0, tk.END)
    remaining_amount_label.config(text="Remaining amount: ")
    percentages_text.configure(state="normal")
    percentages_text.delete(1.0, tk.END)
    percentages_text.configure(state="disabled")

    print("Started a new file.")
    changes_made = False


def show_info():
    info_message = f"   Expense Calculator Alpha{current_version}\n\n   @NeonWaa\n"
    messagebox.showinfo("Expense Calculator - Info", info_message)


def toggle_dark_mode():
    if dark_mode_enabled.get():
        window.configure(bg="black")  # Set root window background to black
        style.configure(".", foreground="white")  # Set text color to white
        set_widget_colors("white", "black")  # Set widget text color to white and background color to black
        for entry in category_entries + amount_entries:
            entry.configure(foreground="black")  # Set the font color of category_entry and amount_entry to black
    else:
        window.configure(bg="white")  # Set root window background to white
        style.configure(".", foreground="black")  # Set text color to black
        set_widget_colors("black", "white")  # Set widget text color to black and background color to white


def set_widget_colors(text_color, bg_color):
    center_frame.configure(bg=bg_color)  # Set main widget background color

    for widget in [income_label, category_label, amount_label, remaining_amount_label, percentages_label]:
        widget.configure(foreground=text_color)
        widget.configure(background=bg_color)

    percentages_text.configure(foreground=text_color)
    percentages_text.configure(background=bg_color)

    # Set text color to black for income_entry, category_entry, and amount_entry
    income_entry.configure(foreground="black")
    for entry in category_entries:
        entry.configure(foreground="black")
    for entry in amount_entries:
        entry.configure(foreground="black")

    # Set the background color of category_entry and amount_entry to white
    for entry in category_entries + amount_entries:
        entry.configure(background="white")

    style.configure("TEntry", foreground="black")  # Set font color of TEntry widgets to black
    style.configure("TButton", foreground="black")  # Set font color of buttons to black

    window.update()  # Update the window to immediately apply the changes


def set_text_color(color):
    for widget in [income_label, category_label, amount_label, remaining_amount_label, percentages_label]:
        widget.configure(foreground=color)

    percentages_text.configure(foreground=color)


def set_widget_background_color(color):
    global style
    for widget in window.winfo_children():
        widget_class = widget.winfo_class()
        style.configure(widget_class, background=color)


def apply_default_theme():
    window.configure(bg="white")  # Set root window background to white
    style.set_theme("clam")  # Apply the default theme


def apply_dark_mode_theme():
    window.configure(bg="black")  # Set root window background to black
    style.set_theme("equilux")  # Apply the dark mode theme


def print_expense_details():
    income = income_entry.get().strip()
    expenses = []

    for i in range(num_expenses):
        category = category_entries[i].get()
        amount = amount_entries[i].get().strip()
        expenses.append({"category": category, "amount": amount})

    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
            # Write the expense details to the temporary file
            temp_file.write(f"Income: {income}\n\n".encode())
            total_expenses = 0
            temp_file.write("Category\tAmount\n".encode())
            temp_file.write("------------------\n".encode())
            for expense in expenses:
                category = expense["category"]
                amount = expense["amount"]
                formatted_amount = f"{float(amount):.2f}"
                temp_file.write(f"{category}\t\t{formatted_amount}\n".encode())
                total_expenses += float(amount)

            remaining_income = float(income) - total_expenses
            formatted_remaining_income = f"{remaining_income:.2f}"
            temp_file.write("------------------\n".encode())
            temp_file.write(f"Remaining Income:\t{formatted_remaining_income}\n\n".encode())

            temp_file.write("Category\tPercentage\n".encode())
            temp_file.write("----------------------\n".encode())
            percentages = percentages_text.get("1.0", tk.END).strip()
            temp_file.write(f"{percentages}\n\n".encode())

            # Close the file to ensure changes are flushed to disk
            temp_file.close()

            # Launch the default print command for the temporary file
            win32api.ShellExecute(
                0,  # Handle to parent window (0 = desktop)
                "print",  # Verb
                temp_file.name,  # File path of the document to print
                None,  # Parameters (None for default)
                ".",  # Working directory
                0  # Show window flag (0 = Hide the window)
            )

    except Exception as e:
        messagebox.showerror("Error", str(e))


def toggle_sort_order():
    global ascending_order
    ascending_order = not ascending_order
    sort_button.config(text="Sort (High -> Low)" if ascending_order else "Sort (Low -> High)")
    calculate_expenses()  # Re-calculate and update the percentages display


window = tk.Tk()
window.title("Expense Calculator")

style = ThemedStyle(window)
style.set_theme("clam")

# Center the window on the screen
window_width = 400
window_height = 400
screen_width = window.winfo_screenwidth()
screen_height = window.winfo_screenheight()
x = int((screen_width / 2) - (window_width / 2))
y = int((screen_height / 2) - (window_height / 2))
window.geometry(f"{window_width}x{window_height}+{x}+{y}")

# Create a frame for center alignment
center_frame = tk.Frame(window)
center_frame.pack(expand=True)

# Create a menu bar
menu_bar = tk.Menu(window)

# Create a File menu
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="New", command=new_file)
file_menu.add_command(label="Open", command=open_file)
file_menu.add_command(label="Print", command=print_expense_details)
file_menu.add_command(label="Save", command=save_file)
file_menu.add_command(label="Save As", command=save_as_file)
file_menu.add_command(label="Exit", command=exit_application)
menu_bar.add_cascade(label="File", menu=file_menu)

# Create a View menu
view_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="View", menu=view_menu)

# Create a Help menu
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=show_info)
menu_bar.add_cascade(label="Help", menu=help_menu)

# Configure the window's menu
window.config(menu=menu_bar)

income_label = ttk.Label(center_frame, text="Income:", anchor=tk.W)
income_label.grid(row=0, column=0, padx=10, pady=5, sticky=tk.W)

income_entry = ttk.Entry(center_frame)
income_entry.grid(row=0, column=1, padx=0, pady=5, sticky=tk.W)

category_label = ttk.Label(center_frame, text="Expense: ")
category_label.grid(row=1, column=0, padx=50, pady=5, sticky=tk.W)

amount_label = ttk.Label(center_frame, text="Amount $:")
amount_label.grid(row=1, column=1, padx=0, pady=5, sticky=tk.W)

expense_lines_frame = ttk.Frame(center_frame)
expense_lines_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky=tk.W)

sort_button = ttk.Button(center_frame, text="Sort (High -> Low)", command=toggle_sort_order)
sort_button.grid(row=8, column=0, columnspan=2, padx=10, pady=5)

add_button = ttk.Button(
    center_frame, text="Add Expense Line", command=add_expense_line
)
add_button.grid(row=3, column=0, columnspan=2, padx=10, pady=5)

calculate_button = ttk.Button(
    center_frame, text="Calculate", command=calculate_expenses
)
calculate_button.grid(row=4, column=0, columnspan=2, padx=10, pady=10)

remaining_amount_label = ttk.Label(
    center_frame, text="Remaining amount: "
)
remaining_amount_label.grid(row=5, column=0, padx=10, pady=5, sticky=tk.W)

percentages_label = ttk.Label(
    center_frame, text="Expense Percentages:"
)
percentages_label.grid(row=6, column=0, padx=10, pady=5, sticky=tk.W)

percentages_text = tk.Text(
    center_frame, height=5, width=30, state="disabled"
)
percentages_text.grid(row=7, column=0, padx=10, pady=5, columnspan=2, sticky=tk.W)

# Add a dark mode option to the View menu
dark_mode_enabled = tk.BooleanVar(value=False)
view_menu.add_checkbutton(
    label="Dark Mode",
    variable=dark_mode_enabled,
    command=toggle_dark_mode
)

# Bind the exit_application function to the WM_DELETE_WINDOW event
window.protocol("WM_DELETE_WINDOW", exit_application)

window.mainloop()
