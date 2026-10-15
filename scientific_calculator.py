import tkinter as tk
from tkinter import messagebox
import math
import ast
import operator

HISTORY_FILE = "history.txt"
angle_mode = "DEG"

# -------------------- Scientific Functions --------------------
def sin_value(x):
    return math.sin(math.radians(x)) if angle_mode == "DEG" else math.sin(x)

def cos_value(x):
    return math.cos(math.radians(x)) if angle_mode == "DEG" else math.cos(x)

def tan_value(x):
    if angle_mode == "DEG" and math.isclose(x % 180, 90, abs_tol=1e-10):
        raise ValueError("tan is undefined at 90° + 180° × n")
    return math.tan(math.radians(x)) if angle_mode == "DEG" else math.tan(x)

def factorial_value(x):
    if x < 0 or not float(x).is_integer():
        raise ValueError("Factorial requires a non-negative integer")
    if x > 170:
        raise ValueError("Please use a number from 0 to 170 for factorial")
    return math.factorial(int(x))

# -------------------- Safe Expression Evaluator --------------------
def safe_eval(expression):
    expression = expression.replace("^", "**")
    tree = ast.parse(expression, mode="eval")

    binary_ops = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
    }
    unary_ops = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    functions = {
        "sin": sin_value, "cos": cos_value, "tan": tan_value,
        "sqrt": math.sqrt, "log": math.log10, "ln": math.log,
        "exp": math.exp, "abs": abs, "factorial": factorial_value,
    }
    constants = {"pi": math.pi, "e": math.e}

    def evaluate(node):
        if isinstance(node, ast.Expression):
            return evaluate(node.body)
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            return node.value
        if isinstance(node, ast.Name):
            if node.id in constants:
                return constants[node.id]
            raise ValueError(f"Unknown name: {node.id}")
        if isinstance(node, ast.BinOp) and type(node.op) in binary_ops:
            left, right = evaluate(node.left), evaluate(node.right)
            # Limit extreme powers to reduce accidental resource exhaustion.
            if isinstance(node.op, ast.Pow) and abs(right) > 1000:
                raise ValueError("Exponent is too large")
            return binary_ops[type(node.op)](left, right)
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary_ops:
            return unary_ops[type(node.op)](evaluate(node.operand))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            func = functions.get(node.func.id)
            if func is None or node.keywords or len(node.args) != 1:
                raise ValueError("Invalid function or arguments")
            return func(evaluate(node.args[0]))
        raise ValueError("Invalid expression")

    result = evaluate(tree)
    if isinstance(result, complex):
        raise ValueError("Complex results are not supported")
    if isinstance(result, float) and not math.isfinite(result):
        raise ValueError("Result is not finite")
    return result

# -------------------- History --------------------
def save_history(entry):
    with open(HISTORY_FILE, "a", encoding="utf-8") as file:
        file.write(entry + "\n")

def view_history():
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as file:
            data = file.read().strip() or "No History Found"
    except FileNotFoundError:
        data = "No History Found"
    messagebox.showinfo("Calculation History", data)

# -------------------- Calculator Actions --------------------
def insert_text(value):
    display.insert(tk.INSERT, value)
    display.focus_set()

def clear():
    display.delete(0, tk.END)
    display.focus_set()

def backspace():
    pos = display.index(tk.INSERT)
    if pos > 0:
        display.delete(pos - 1, pos)
    display.focus_set()

def format_result(result):
    if isinstance(result, float):
        if result.is_integer() and abs(result) < 1e16:
            return str(int(result))
        return f"{result:.12g}"
    return str(result)

def calculate():
    expression = display.get().strip()
    if not expression:
        return
    try:
        result_text = format_result(safe_eval(expression))
        save_history(f"{expression} = {result_text}")
        display.delete(0, tk.END)
        display.insert(0, result_text)
        display.icursor(tk.END)
    except (ValueError, TypeError, SyntaxError, ZeroDivisionError,
            OverflowError, ArithmeticError, MemoryError, RecursionError) as error:
        messagebox.showerror("Calculation Error", str(error) or "Invalid expression")

def apply_square():
    expression = display.get().strip()
    if not expression:
        messagebox.showinfo("Square", "Enter a number or expression first.")
        return
    display.delete(0, tk.END)
    display.insert(0, f"({expression})**2")
    display.icursor(tk.END)
    display.focus_set()

def apply_power():
    if not display.get().strip():
        messagebox.showinfo("Power", "Enter the base first, then press xʸ and enter the exponent.")
        return
    insert_text("**")

def toggle_angle():
    global angle_mode
    angle_mode = "RAD" if angle_mode == "DEG" else "DEG"
    angle_button.config(text=angle_mode)
    mode_label.config(text=f"Angle: {angle_mode}")

def key_press(event):
    if event.keysym == "Return":
        calculate()
        return "break"
    if event.keysym == "Escape":
        clear()
        return "break"
    if event.keysym == "BackSpace":
        backspace()
        return "break"
    if event.char and event.char in "0123456789+-*/().%^":
        insert_text(event.char)
        return "break"

# -------------------- Window --------------------
root = tk.Tk()
root.title("Scientific Calculator")
root.geometry("470x700")
root.resizable(False, False)
root.configure(bg="#1e1e1e")

display = tk.Entry(
    root, font=("Segoe UI", 24), bg="#2d2d2d", fg="white",
    insertbackground="white", justify="right", relief="flat", bd=10
)
display.pack(fill="x", padx=12, pady=(14, 6))
display.focus_set()

mode_label = tk.Label(
    root, text="Angle: DEG", bg="#1e1e1e", fg="#bbbbbb",
    font=("Segoe UI", 10)
)
mode_label.pack(anchor="e", padx=16, pady=(0, 8))

BG, OP_BG, SCI_BG, ACCENT = "#3c3f41", "#55585a", "#34495e", "#168aad"

def make_button(parent, label, command, row, col, bg=BG, colspan=1):
    button = tk.Button(
        parent, text=label, command=command, bg=bg, fg="white",
        activebackground="#6b7073", activeforeground="white",
        font=("Segoe UI", 11, "bold"), relief="flat",
        width=7, height=2, bd=0, cursor="hand2"
    )
    button.grid(row=row, column=col, columnspan=colspan,
                padx=3, pady=3, sticky="nsew")
    return button

# -------------------- Scientific Buttons --------------------
science = tk.Frame(root, bg="#1e1e1e")
science.pack(padx=8, fill="x")

science_buttons = [
    ("sin(", lambda: insert_text("sin("), 0, 0),
    ("cos(", lambda: insert_text("cos("), 0, 1),
    ("tan(", lambda: insert_text("tan("), 0, 2),
    ("√(", lambda: insert_text("sqrt("), 0, 3),
    ("log(", lambda: insert_text("log("), 1, 0),
    ("ln(", lambda: insert_text("ln("), 1, 1),
    ("x²", apply_square, 1, 2),
    ("xʸ", apply_power, 1, 3),
    ("10ˣ", lambda: insert_text("10**"), 2, 0),
    ("eˣ", lambda: insert_text("exp("), 2, 1),
    ("n!", lambda: insert_text("factorial("), 2, 2),
    ("|x|", lambda: insert_text("abs("), 2, 3),
    ("π", lambda: insert_text("pi"), 3, 0),
    ("e", lambda: insert_text("e"), 3, 1),
    ("(", lambda: insert_text("("), 3, 2),
    (")", lambda: insert_text(")"), 3, 3),
]

for label, command, row, col in science_buttons:
    make_button(science, label, command, row, col, SCI_BG)
for col in range(4):
    science.grid_columnconfigure(col, weight=1)

# -------------------- Main Buttons --------------------
main = tk.Frame(root, bg="#1e1e1e")
main.pack(padx=8, pady=(8, 0), fill="x")
main_buttons = [
    ("7", 0, 0), ("8", 0, 1), ("9", 0, 2), ("/", 0, 3),
    ("4", 1, 0), ("5", 1, 1), ("6", 1, 2), ("*", 1, 3),
    ("1", 2, 0), ("2", 2, 1), ("3", 2, 2), ("-", 2, 3),
    ("0", 3, 0), (".", 3, 1), ("%", 3, 2), ("+", 3, 3),
]
for label, row, col in main_buttons:
    make_button(main, label, lambda v=label: insert_text(v),
                row, col, OP_BG if label in "+-*/" else BG)
for col in range(4):
    main.grid_columnconfigure(col, weight=1)

# -------------------- Utility Buttons --------------------
utility = tk.Frame(root, bg="#1e1e1e")
utility.pack(padx=8, pady=8, fill="x")
make_button(utility, "C", clear, 0, 0, "#9b2226")
make_button(utility, "⌫", backspace, 0, 1, OP_BG)
angle_button = make_button(utility, angle_mode, toggle_angle, 0, 2, SCI_BG)
make_button(utility, "History", view_history, 0, 3, SCI_BG)
for col in range(4):
    utility.grid_columnconfigure(col, weight=1)

# -------------------- Equals Button --------------------
equals = tk.Frame(root, bg="#1e1e1e")
equals.pack(padx=8, pady=(0, 10), fill="x")
make_button(equals, "=", calculate, 0, 0, ACCENT, colspan=4)
equals.grid_columnconfigure(0, weight=1)

root.bind("<Key>", key_press)
root.mainloop()
