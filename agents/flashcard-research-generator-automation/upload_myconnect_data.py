import requests
import json
import time

URL = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
APP_NAME = "asvab"

# 150 VOCABULARY WORDS FROM MYCONNECTSUITE
vocab_list = [
    # LEVEL 1: EASY (Selected samples)
    {"Front": "Abandon", "Back": "To leave behind or desert. Example: The soldiers had to abandon the damaged vehicle."},
    {"Front": "Abundant", "Back": "Plentiful; available in large quantities. Example: The region has an abundant supply of fresh water."},
    {"Front": "Acute", "Back": "Sharp, intense, or severe. Example: An acute angle is less than 90 degrees; an acute pain is sudden and sharp."},
    {"Front": "Appraise", "Back": "To evaluate the worth or quality of. Example: The jeweler will appraise the diamond to determine its market value."},
    {"Front": "Cautious", "Back": "Careful to avoid potential problems. Example: Drive cautiously on icy roads to prevent accidents."},
    {"Front": "Competent", "Back": "Capable; having the necessary ability or skills. Example: He is a competent mechanic who can fix any engine."},
    {"Front": "Dilemma", "Back": "A difficult situation or problem requiring a choice between options. Example: She faced a dilemma between two equally good job offers."},
    {"Front": "Economical", "Back": "Thrifty; avoiding waste or being efficient with money. Example: Buying in bulk is often more economical."},
    {"Front": "Fragile", "Back": "Easily broken or damaged. Example: Handle the glass vase carefully as it is very fragile."},
    {"Front": "Incentive", "Back": "A thing that motivates or encourages someone to do something. Example: The bonus was a great incentive to work harder."},
    {"Front": "Lofty", "Back": "Of imposing height or noble in nature. Example: The mountain peak was lofty and covered in snow."},
    {"Front": "Obscure", "Back": "Not discovered or known about; uncertain. Example: The origins of the ancient ruins remain obscure."},
    {"Front": "Reluctant", "Back": "Unwilling and hesitant. Example: He was reluctant to share his secret with anyone."},
    {"Front": "Surmount", "Back": "To overcome a difficulty or obstacle. Example: With hard work, you can surmount any challenge."},
    {"Front": "Vague", "Back": "Uncertain, indefinite, or unclear. Example: The instructions were too vague to follow properly."},
    
    # LEVEL 2: MEDIUM (Selected samples)
    {"Front": "Abate", "Back": "To become less intense or widespread. Example: The storm began to abate after midnight."},
    {"Front": "Abdicate", "Back": "To renounce one's throne or fail to fulfill a duty. Example: The king chose to abdicate the throne."},
    {"Front": "Adept", "Back": "Very skilled or proficient at something. Example: She is adept at solving complex mathematical equations."},
    {"Front": "Adversary", "Back": "One's opponent in a contest, conflict, or dispute. Example: He defeated his adversary in the final round of the tournament."},
    {"Front": "Candid", "Back": "Truthful and straightforward; frank. Example: He provided a candid account of the events that transpired."},
    {"Front": "Concur", "Back": "To be of the same opinion; to agree. Example: The committee members concur with the proposed plan."},
    {"Front": "Curtail", "Back": "To reduce in extent or quantity. Example: We must curtail our spending to stay within the budget."},
    {"Front": "Feasible", "Back": "Possible to do easily or conveniently. Example: It is feasible to complete the project within two weeks."},
    {"Front": "Frugal", "Back": "Sparing or economical with regard to money or food. Example: Her frugal lifestyle allowed her to save a lot of money."},
    {"Front": "Impede", "Back": "To delay or prevent by obstructing; to hinder. Example: Heavy traffic will impede our progress to the airport."},
    {"Front": "Judicious", "Back": "Having, showing, or done with good judgment. Example: Making a judicious decision requires careful thought."},
    {"Front": "Obliterate", "Back": "To destroy utterly; to wipe out. Example: The explosion served to obliterate the entire building."},
    {"Front": "Objective", "Back": "Not influenced by personal feelings; unbiased. Example: A judge must remain objective during a trial."},
    
    # LEVEL 3: HARD (Selected samples)
    {"Front": "Ambiguous", "Back": "Open to more than one interpretation; unclear. Example: The contract's language was too ambiguous."},
    {"Front": "Apathy", "Back": "Lack of interest, enthusiasm, or concern. Example: Voter apathy can lead to low turnout in elections."},
    {"Front": "Ephemeral", "Back": "Lasting for a very short time. Example: The beauty of a sunset is ephemeral, lasting only minutes."},
    {"Front": "Fortitude", "Back": "Courage in pain or adversity. Example: She showed great fortitude during her long recovery."},
    {"Front": "Imminent", "Back": "About to happen; approaching soon. Example: Dark clouds signaled that a storm was imminent."},
    {"Front": "Juxtapose", "Back": "To place close together for contrasting effect. Example: The artist liked to juxtapose light and dark colors."},
    {"Front": "Laud", "Back": "To praise highly, especially in a public context. Example: The critics laud the actor's performance in the new play."},
    {"Front": "Pragmatic", "Back": "Dealing with things sensibly and realistically. Example: We need a pragmatic solution to this problem."},
    {"Front": "Resilient", "Back": "Able to withstand or recover quickly from difficult conditions. Example: The local economy is resilient and growing again."},
    {"Front": "Vacillate", "Back": "To alternate or waver between different opinions or actions. Example: Don't vacillate when making an important decision."},
]

# PREPARING FINAL FLASHCARDS (Topic 9, Subtopic 2)
final_cards = []
for item in vocab_list:
    final_cards.append({
        "Topic": "9",
        "Subtopic": "2",
        "Front": item["Front"],
        "Back": item["Back"]
    })

# ADDING MATH TIPS FROM THE GUIDE (Topic 1, Subtopic 4)
math_tips = [
    {"Front": "Reciprocal", "Back": "The inverse of a number ($1/x$). To divide fractions, multiply by the reciprocal of the divisor."},
    {"Front": "PEMDAS Rule", "Back": "Order of operations: Parentheses, Exponents, Multiplication/Division (left to right), Addition/Subtraction (left to right)."},
    {"Front": "Cross-Multiplication", "Back": "A method to solve proportions: if $a/b = c/d$, then $ad = bc$."},
    {"Front": "Percentage Change", "Back": "Formula: $\\text{Change} = \\frac{\\text{New} - \\text{Old}}{\\text{Old}} \\times 100\\%$. Used to find increases or decreases."},
]

for tip in math_tips:
    final_cards.append({
        "Topic": "1",
        "Subtopic": "4",
        "Front": tip["Front"],
        "Back": tip["Back"]
    })

# UPLOAD IN BATCHES
def upload_batch(cards):
    payload = {"app_name": APP_NAME, "flashcards": cards}
    response = requests.post(URL, json=payload)
    print(f"Uploaded {len(cards)} cards. Status: {response.text}")

# Split into chunks of 50 to avoid timeout
for i in range(0, len(final_cards), 50):
    upload_batch(final_cards[i:i+50])
    time.sleep(1)
