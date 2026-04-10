import os
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

topics = [
    "Arithmetic Reasoning: Fraction, Statistics, Distance, Rate & Time, Math Operations, Percentage, Ratio & Proportion, Geometry, Unit Conversion, Number Properties, Equations",
    "Assembling Objects: Connection Items, Puzzle Items",
    "Auto & Shop Information: Mechanical Systems, Metal Shop, Woodworking, Automotive Knowledge",
    "Electronics Information: Electricity, Electrical Systems",
    "General Science: Earth Science, Ecology, Nutrition & Health, Cellular Biology, Human Body Systems, Physical Science",
    "Mathematics Knowledge: Algebra, Geometry",
    "Mechanical Comprehension: Machines, Fundamentals of Mechanics",
    "Paragraph Comprehension: Main Idea, Wider Implications, Word Meaning in Context, Finding Information",
    "Word Knowledge: Contextualised Questions, Synonym-based Questions"
]

with open("asvab_full_reference.txt", "w") as f:
    for topic in topics:
        print(f"Generating for {topic}")
        prompt = f"Write a comprehensive, highly detailed study guide section for the ASVAB exam covering the following topic and subtopics: {topic}. Include definitions, key formulas, concepts, and factual details."
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        f.write(f"=== {topic} ===\n\n")
        f.write(response.text)
        f.write("\n\n")

print("Generated asvab_full_reference.txt")
