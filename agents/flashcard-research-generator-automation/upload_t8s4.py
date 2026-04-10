import requests
import json

URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
APP_NAME = "asvab"

flashcards = [
    {"Topic": "8", "Subtopic": "4", "Front": "Finding Information", "Back": "The skill of locating specific facts, details, or data within a text to answer direct questions."},
    {"Topic": "8", "Subtopic": "4", "Front": "Scanning", "Back": "Quickly reading through a text to find a specific word, number, or piece of information without reading every sentence."},
    {"Topic": "8", "Subtopic": "4", "Front": "Scientific Search", "Back": "A strategy of identifying keywords (nouns, verbs, or numbers) in a question and then looking for those exact terms in the passage."},
    {"Topic": "8", "Subtopic": "4", "Front": "Fact Traps", "Back": "Answer choices that are factually true according to the text but do not actually answer the specific question asked."},
    {"Topic": "8", "Subtopic": "4", "Front": "Key Word Identification", "Back": "Selecting unique or specific terms from the question to use as anchors when scanning the paragraph for the answer."},
    {"Topic": "8", "Subtopic": "4", "Front": "Factual Questions", "Back": "Questions that require identifying specific information explicitly stated in the text, such as dates, names, or locations."},
    {"Topic": "8", "Subtopic": "4", "Front": "Explicit Information", "Back": "Information that is clearly and directly stated in the text, leaving no room for interpretation."},
    {"Topic": "8", "Subtopic": "4", "Front": "Detail-Oriented Reading", "Back": "A reading approach focused on noticing small, specific pieces of information rather than the overall theme."},
    {"Topic": "8", "Subtopic": "4", "Front": "Who, What, Where, When", "Back": "The four primary types of specific detail questions found in Paragraph Comprehension."},
    {"Topic": "8", "Subtopic": "4", "Front": "Distractor Identification", "Back": "The process of spotting answer choices that are included only to lead the reader away from the specific detail requested."},
    {"Topic": "8", "Subtopic": "4", "Front": "Paragraph Reference", "Back": "Always returning to the text to verify a specific detail rather than relying on memory after reading."},
    {"Topic": "8", "Subtopic": "4", "Front": "Scanning for Numbers", "Back": "Looking specifically for digits or dates in a paragraph to quickly answer questions about time or quantity."},
    {"Topic": "8", "Subtopic": "4", "Front": "Synonym Matching", "Back": "Recognizing that the answer choice may use a synonym for the information found in the text rather than the exact word."},
    {"Topic": "8", "Subtopic": "4", "Front": "Sentence Context", "Back": "Reading the sentence immediately before and after a key word to fully understand the specific information found."},
    {"Topic": "8", "Subtopic": "4", "Front": "Irrelevant Data", "Back": "Information provided in the paragraph that does not relate to the question being asked and should be ignored during scanning."},
    {"Topic": "8", "Subtopic": "4", "Front": "Targeted Reading", "Back": "Only reading the portions of the paragraph that are likely to contain the answer based on keyword locations."},
    {"Topic": "8", "Subtopic": "4", "Front": "Qualifiers", "Back": "Words like 'always,' 'never,' or 'only' that can significantly change the meaning of the information being sought."},
    {"Topic": "8", "Subtopic": "4", "Front": "Direct Evidence", "Back": "A specific quote or statement from the text that proves an answer choice is correct for a detail-based question."},
    {"Topic": "8", "Subtopic": "4", "Front": "Location Strategy", "Back": "Identifying where in the paragraph (beginning, middle, or end) specific types of information are typically located."},
    {"Topic": "8", "Subtopic": "4", "Front": "Literal Meaning", "Back": "Focusing on exactly what the words say for finding information, rather than inferring what they might mean."},
    {"Topic": "8", "Subtopic": "4", "Front": "Chronological Search", "Back": "Searching for information in the order it appears in the text, which often follows the order of the questions."},
    {"Topic": "8", "Subtopic": "4", "Front": "Data Verification", "Back": "Double-checking names, dates, and figures against the text before finalizing an answer choice."},
    {"Topic": "8", "Subtopic": "4", "Front": "Narrow Focus", "Back": "Focusing only on the small aspect of the paragraph that the question addresses, rather than the 'larger picture.'"},
    {"Topic": "8", "Subtopic": "4", "Front": "Search Anchor", "Back": "A specific, easily identifiable word from the question used to locate the relevant sentence in the text."},
    {"Topic": "8", "Subtopic": "4", "Front": "Negative Detail Questions", "Back": "Questions asking what is NOT included in the text, requiring a scan for all other mentioned details."},
    {"Topic": "8", "Subtopic": "4", "Front": "Topic Sentence Link", "Back": "Recognizing how specific details support the main idea presented in the topic sentence."},
    {"Topic": "8", "Subtopic": "4", "Front": "Skimming vs. Scanning", "Back": "Skimming is for the general idea; scanning is specifically for finding a particular piece of information."},
    {"Topic": "8", "Subtopic": "4", "Front": "Comparison Questions", "Back": "Questions that require finding two different pieces of information and identifying the relationship between them."},
    {"Topic": "8", "Subtopic": "4", "Front": "Text Structure Awareness", "Back": "Using the way a paragraph is organized (e.g., cause/effect, sequence) to predict where information is located."},
    {"Topic": "8", "Subtopic": "4", "Front": "Precision Reading", "Back": "Reading a specific sentence slowly once it has been located to ensure all details are correctly understood."},
]

payload = {
    "app_name": APP_NAME,
    "flashcards": flashcards
}

response = requests.post(URL, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
