import requests
import json

URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
APP_NAME = "asvab"

flashcards = [
    {"Topic": "1", "Subtopic": "4", "Front": "Addition", "Back": "The mathematical process of putting two or more numbers together to find their sum."},
    {"Topic": "1", "Subtopic": "4", "Front": "Subtraction", "Back": "The process of taking one quantity away from another to find the difference."},
    {"Topic": "1", "Subtopic": "4", "Front": "Multiplication", "Back": "The process of repeated addition of a number to itself a certain number of times."},
    {"Topic": "1", "Subtopic": "4", "Front": "Division", "Back": "The process of splitting a large group into smaller equal groups or finding how many times one number is contained within another."},
    {"Topic": "1", "Subtopic": "4", "Front": "Sum", "Back": "The total amount resulting from the addition of two or more numbers."},
    {"Topic": "1", "Subtopic": "4", "Front": "Difference", "Back": "The result of subtracting one number from another."},
    {"Topic": "1", "Subtopic": "4", "Front": "Product", "Back": "The result of multiplying two or more numbers together."},
    {"Topic": "1", "Subtopic": "4", "Front": "Quotient", "Back": "The result obtained by dividing one quantity by another."},
    {"Topic": "1", "Subtopic": "4", "Front": "Remainder", "Back": "The amount 'left over' after performing a division calculation."},
    {"Topic": "1", "Subtopic": "4", "Front": "PEMDAS", "Back": "An acronym for the order of operations: Parentheses, Exponents, Multiplication and Division, and Addition and Subtraction."},
    {"Topic": "1", "Subtopic": "4", "Front": "Parentheses", "Back": "Grouping symbols used in mathematics to indicate that the operations inside should be performed first."},
    {"Topic": "1", "Subtopic": "4", "Front": "Exponents", "Back": "A quantity representing the power to which a given number or expression is to be raised."},
    {"Topic": "1", "Subtopic": "4", "Front": "Order of Operations", "Back": "A collection of rules that reflect conventions about which procedures to perform first in order to evaluate a given mathematical expression."},
    {"Topic": "1", "Subtopic": "4", "Front": "Inverse Operations", "Back": "Operations that undo each other, such as addition and subtraction, or multiplication and division."},
    {"Topic": "1", "Subtopic": "4", "Front": "Commutative Property", "Back": "The rule that says the order in which we add or multiply numbers does not change the result ($a + b = b + a$)."},
    {"Topic": "1", "Subtopic": "4", "Front": "Associative Property", "Back": "The rule that says the way in which numbers are grouped in addition or multiplication does not change the result ($(a + b) + c = a + (b + c)$)."},
    {"Topic": "1", "Subtopic": "4", "Front": "Distributive Property", "Back": "The rule stating that multiplying a sum by a number is the same as multiplying each addend by the number and then adding the products ($a(b + c) = ab + ac$)."},
    {"Topic": "1", "Subtopic": "4", "Front": "Identity Property of Addition", "Back": "The rule stating that adding zero to any number results in that same number ($a + 0 = a$)."},
    {"Topic": "1", "Subtopic": "4", "Front": "Identity Property of Multiplication", "Back": "The rule stating that multiplying any number by one results in that same number ($a \\times 1 = a$)."},
    {"Topic": "1", "Subtopic": "4", "Front": "Decimal Point", "Back": "A dot used to separate the whole number part from the fractional part of a number."},
    {"Topic": "1", "Subtopic": "4", "Front": "Place Value", "Back": "The numerical value that a digit has by virtue of its position in a number (e.g., units, tens, hundreds)."},
    {"Topic": "1", "Subtopic": "4", "Front": "Rounding", "Back": "The process of making a number simpler but keeping its value close to what it was."},
    {"Topic": "1", "Subtopic": "4", "Front": "Estimating", "Back": "Finding a value that is close enough to the right answer, usually with some thought or calculation involved."},
    {"Topic": "1", "Subtopic": "4", "Front": "Integers", "Back": "A whole number that can be positive, negative, or zero."},
    {"Topic": "1", "Subtopic": "4", "Front": "Absolute Value", "Back": "The distance of a number from zero on a number line, regardless of direction."},
    {"Topic": "1", "Subtopic": "4", "Front": "Factor", "Back": "A number that divides into another number exactly and without leaving a remainder."},
    {"Topic": "1", "Subtopic": "4", "Front": "Multiple", "Back": "The product of a given number and any other whole number."},
    {"Topic": "1", "Subtopic": "4", "Front": "Prime Number", "Back": "A whole number greater than 1 that cannot be formed by multiplying two smaller whole numbers."},
    {"Topic": "1", "Subtopic": "4", "Front": "Composite Number", "Back": "A positive integer greater than 1 that has at least one divisor other than 1 and itself."},
    {"Topic": "1", "Subtopic": "4", "Front": "Square Root", "Back": "A value that, when multiplied by itself, gives the original number ($\sqrt{x}$)."},
]

payload = {
    "app_name": APP_NAME,
    "flashcards": flashcards
}

response = requests.post(URL, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
