import requests
import json

URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
APP_NAME = "asvab"

flashcards = [
    # TOPIC 8.1: MAIN IDEA (30 cards)
    {"Topic": "8", "Subtopic": "1", "Front": "Main Idea", "Back": "The central point or most important message that an author wants to convey in a paragraph."},
    {"Topic": "8", "Subtopic": "1", "Front": "Active Reading", "Back": "A strategy of engaging with the text by asking, 'What is the author's overall point?' during reading."},
    {"Topic": "8", "Subtopic": "1", "Front": "Topic Sentence", "Back": "A sentence that summarizes the entire paragraph's content, typically found at the beginning or end."},
    {"Topic": "8", "Subtopic": "1", "Front": "Supporting Details", "Back": "Specific facts, examples, or evidence that provide more information about the main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Implicit Main Idea", "Back": "A main idea that is not directly stated in a single sentence but must be inferred from the details."},
    {"Topic": "8", "Subtopic": "1", "Front": "Explicit Main Idea", "Back": "A main idea that is clearly stated in the text, usually in the topic sentence."},
    {"Topic": "8", "Subtopic": "1", "Front": "Summarization", "Back": "The process of briefly stating the main points of a paragraph in your own words."},
    {"Topic": "8", "Subtopic": "1", "Front": "Overly General Choice", "Back": "An incorrect answer choice that covers a broader topic than what is actually discussed in the paragraph."},
    {"Topic": "8", "Subtopic": "1", "Front": "Overly Specific Choice", "Back": "An incorrect answer choice that only focuses on one small detail rather than the central point."},
    {"Topic": "8", "Subtopic": "1", "Front": "Contradictory Choice", "Back": "An incorrect answer choice that states the opposite of what is presented in the text."},
    {"Topic": "8", "Subtopic": "1", "Front": "Paragraph Scope", "Back": "The specific boundaries of the topic being discussed, which helps identify the most accurate main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Author's Purpose", "Back": "The reason why the author wrote the paragraph, which often leads directly to the main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Key Themes", "Back": "Recurring ideas or concepts that appear throughout the paragraph to support the central message."},
    {"Topic": "8", "Subtopic": "1", "Front": "Introductory Paragraph", "Back": "The first paragraph of a longer text, which often introduces the main idea of the entire piece."},
    {"Topic": "8", "Subtopic": "1", "Front": "Concluding Sentence", "Back": "The final sentence of a paragraph that often restates or summarizes the main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Transition Words", "Back": "Words like 'however' or 'furthermore' that help signal how details relate to the main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Word Repetition", "Back": "A signal that a specific subject is central to the paragraph's main idea based on how often it is mentioned."},
    {"Topic": "8", "Subtopic": "1", "Front": "Distractor Identification", "Back": "Recognizing answer choices that are true facts from the text but do not represent the main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Main Idea Location", "Back": "Focusing your search for the central point on the first and last sentences of the paragraph."},
    {"Topic": "8", "Subtopic": "1", "Front": "Detail Synthesis", "Back": "The process of combining all supporting details to form a single, coherent main idea."},
    {"Topic": "8", "Subtopic": "1", "Front": "Central Message", "Back": "The underlying lesson or point that the author intends for the reader to understand."},
    {"Topic": "8", "Subtopic": "1", "Front": "Primary Subject", "Back": "The main person, thing, or concept that the entire paragraph is built around."},
    {"Topic": "8", "Subtopic": "1", "Front": "Focus Filtering", "Back": "Filtering out minor details to see the big picture of what the paragraph is about."},
    {"Topic": "8", "Subtopic": "1", "Front": "Heading Check", "Back": "Using the title or heading as a clue to identify the main idea of the following paragraph."},
    {"Topic": "8", "Subtopic": "1", "Front": "Unsupported Choice", "Back": "An answer choice that makes a claim not found anywhere in the provided paragraph."},
    {"Topic": "8", "Subtopic": "1", "Front": "Fact vs. Main Idea", "Back": "Understanding that a specific fact supports the main idea but is not the main idea itself."},
    {"Topic": "8", "Subtopic": "1", "Front": "Evaluation Strategy", "Back": "Comparing each answer choice to the entire paragraph to see which one best fits as a summary."},
    {"Topic": "8", "Subtopic": "1", "Front": "Main Point Consistency", "Back": "Ensuring the chosen main idea is supported by every sentence in the paragraph."},
    {"Topic": "8", "Subtopic": "1", "Front": "Summary Accuracy", "Back": "Selecting the choice that includes all essential parts of the paragraph without adding outside information."},
    {"Topic": "8", "Subtopic": "1", "Front": "Paragraph Analysis", "Back": "The systematic breakdown of a text to find its core components and central message."},

    # TOPIC 8.2: WIDER IMPLICATIONS (30 cards)
    {"Topic": "8", "Subtopic": "2", "Front": "Wider Implications", "Back": "The logical conclusions or consequences that can be drawn from a text but are not explicitly stated."},
    {"Topic": "8", "Subtopic": "2", "Front": "Inference", "Back": "A conclusion reached on the basis of evidence and reasoning from the information provided."},
    {"Topic": "8", "Subtopic": "2", "Front": "Drawing Conclusions", "Back": "The process of using details in the text to arrive at a logical and supported final thought."},
    {"Topic": "8", "Subtopic": "2", "Front": "Textual Evidence", "Back": "Specific information from the passage that supports a conclusion or inference."},
    {"Topic": "8", "Subtopic": "2", "Front": "Avoiding Assumptions", "Back": "A critical strategy of basing all conclusions strictly on the text rather than personal opinions or outside knowledge."},
    {"Topic": "8", "Subtopic": "2", "Front": "Logical Deduction", "Back": "The act of using facts to reach a certain conclusion that must be true based on those facts."},
    {"Topic": "8", "Subtopic": "2", "Front": "Reading Between the Lines", "Back": "Understanding the hidden or unstated meaning that the author implies through their choice of words."},
    {"Topic": "8", "Subtopic": "2", "Front": "Author's Tone", "Back": "The author's attitude toward the subject, which often hints at wider implications of the text."},
    {"Topic": "8", "Subtopic": "2", "Front": "Cause and Effect Inference", "Back": "Concluding that one event led to another based on the relationship described in the passage."},
    {"Topic": "8", "Subtopic": "2", "Front": "Implied Meaning", "Back": "A meaning that is suggested by the author but not expressed in direct, literal language."},
    {"Topic": "8", "Subtopic": "2", "Front": "Contextual Inference", "Back": "Using the surrounding circumstances described in the text to understand a broader implication."},
    {"Topic": "8", "Subtopic": "2", "Front": "Predicting Outcomes", "Back": "A type of inference where the reader determines what is likely to happen next based on current evidence."},
    {"Topic": "8", "Subtopic": "2", "Front": "Generalization", "Back": "A broad statement or conclusion that applies to a group of things based on specific examples in the text."},
    {"Topic": "8", "Subtopic": "2", "Front": "Reasoning from Details", "Back": "Using small pieces of information to build toward a larger, unstated conclusion."},
    {"Topic": "8", "Subtopic": "2", "Front": "Author's Bias", "Back": "An author's preference for one side of an issue, which can influence the wider implications of their writing."},
    {"Topic": "8", "Subtopic": "2", "Front": "Character Inference", "Back": "Drawing conclusions about a person's traits or motivations based on their actions or words in the text."},
    {"Topic": "8", "Subtopic": "2", "Front": "Logical Flow", "Back": "The sequence of ideas that leads a reader from stated facts to a supported conclusion."},
    {"Topic": "8", "Subtopic": "2", "Front": "Implicit Conclusion", "Back": "A final thought that the author wants the reader to reach without stating it directly."},
    {"Topic": "8", "Subtopic": "2", "Front": "Constraint Awareness", "Back": "Recognizing the limits of the information provided to avoid making unsupported inferences."},
    {"Topic": "8", "Subtopic": "2", "Front": "Supporting Evidence", "Back": "The facts or details that prove a specific inference is logical and valid."},
    {"Topic": "8", "Subtopic": "2", "Front": "Critical Thinking", "Back": "The disciplined process of evaluating information to draw accurate and supported conclusions."},
    {"Topic": "8", "Subtopic": "2", "Front": "Contextual Clues", "Back": "Hints within the text that help a reader understand wider implications or unstated meanings."},
    {"Topic": "8", "Subtopic": "2", "Front": "Inductive Reasoning", "Back": "Making a broad conclusion based on several specific observations found in the paragraph."},
    {"Topic": "8", "Subtopic": "2", "Front": "Deductive Reasoning", "Back": "Applying a general rule or fact found in the text to a specific situation to draw a conclusion."},
    {"Topic": "8", "Subtopic": "2", "Front": "Relationship Analysis", "Back": "Examining how ideas in the text connect to determine what those connections imply."},
    {"Topic": "8", "Subtopic": "2", "Front": "Synthesizing Information", "Back": "Combining multiple pieces of information from the text to form a new, unstated conclusion."},
    {"Topic": "8", "Subtopic": "2", "Front": "Valid Inference", "Back": "A conclusion that is logically sound and directly supported by the evidence in the passage."},
    {"Topic": "8", "Subtopic": "2", "Front": "Invalid Inference", "Back": "A conclusion that may seem plausible but is not actually supported by the information in the text."},
    {"Topic": "8", "Subtopic": "2", "Front": "Significance Analysis", "Back": "Determining why the information in the paragraph is important and what its impact might be."},
    {"Topic": "8", "Subtopic": "2", "Front": "Conclusion Verification", "Back": "Checking a drawn conclusion against all parts of the text to ensure it remains supported."},
]

payload = {
    "app_name": APP_NAME,
    "flashcards": flashcards
}

response = requests.post(URL, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
