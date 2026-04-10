import requests
import json

URL = "https://script.google.com/macros/s/AKfycbzzNrqiWiV3kTbwaAN1f94X6gcaxxuy7b_NmC1mlKTyBlpjYRZ4JQKcQXVP04qQUfCioQ/exec"
APP_NAME = "asvab"

flashcards = [
    # CONTEXT CLUE STRATEGIES (50 cards total for Topic 9.1)
    {"Topic": "9", "Subtopic": "1", "Front": "Definition Clue", "Back": "A context clue where the word's meaning is explicitly stated in the sentence. Example: 'The arachnid, a creature with eight legs, crawled across the ceiling.'"},
    {"Topic": "9", "Subtopic": "1", "Front": "Synonym Clue", "Back": "A context clue where a word with a similar meaning is used nearby. Example: 'The speaker was loquacious, often rambling on for hours with his talkative nature.'"},
    {"Topic": "9", "Subtopic": "1", "Front": "Antonym Clue (Contrast)", "Back": "A context clue where a word with an opposite meaning is used to provide contrast. Example: 'Unlike her gregarious brother, who loved parties, she preferred quiet evenings alone.'"},
    {"Topic": "9", "Subtopic": "1", "Front": "Example Clue", "Back": "A context clue where specific examples illustrate the word's meaning. Example: 'Many plants, such as orchids, thrive in humid environments.'"},
    {"Topic": "9", "Subtopic": "1", "Front": "Cause-and-Effect Clue", "Back": "A context clue where the word's meaning can be inferred from a relationship. Example: 'His obstinate refusal to listen to advice eventually led to his downfall.'"},
    {"Topic": "9", "Subtopic": "1", "Front": "Inference Clue", "Back": "A context clue where the meaning must be deduced from the overall context. Example: 'Sandra’s demure nature made her popular with parents and teachers.'"},
    
    # PRACTICE CONTEXTUALIZED CARDS
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The candidate's *loquacious* nature made it hard for others to speak during the debate.'", "Back": "Word: Loquacious. Meaning: Very talkative or tending to talk a lot."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'Despite the cold weather, the *resilient* plants continued to bloom.'", "Back": "Word: Resilient. Meaning: Able to withstand or recover quickly from difficult conditions."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'His *frugal* lifestyle allowed him to save enough money for a new house.'", "Back": "Word: Frugal. Meaning: Sparing or economical with regard to money; thrifty."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *obscure* instructions were difficult for the students to follow.'", "Back": "Word: Obscure. Meaning: Not discovered or known about; uncertain or unclear."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'She was *reluctant* to join the team until she knew more about the goals.'", "Back": "Word: Reluctant. Meaning: Unwilling and hesitant; disinclined."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *abundant* harvest provided enough food for the entire village for the winter.'", "Back": "Word: Abundant. Meaning: Existing or available in large quantities; plentiful."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'His *acute* hearing allowed him to hear the smallest sound from across the room.'", "Back": "Word: Acute. Meaning: Present or experienced to a severe or intense degree; sharp."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *pragmatic* approach to solving the problem was more effective than the theoretical one.'", "Back": "Word: Pragmatic. Meaning: Dealing with things sensibly and realistically in a practical way."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *ambiguous* ending of the movie left many viewers confused.'", "Back": "Word: Ambiguous. Meaning: Open to more than one interpretation; having a double meaning."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *imminent* storm forced the hikers to find shelter immediately.'", "Back": "Word: Imminent. Meaning: About to happen; fast approaching."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'Her *gregarious* personality made her the center of attention at every party.'", "Back": "Word: Gregarious. Meaning: Fond of company; sociable."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *diligent* student studied for hours every night to prepare for the exam.'", "Back": "Word: Diligent. Meaning: Having or showing care and conscientiousness in one's work or duties."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *superfluous* information in the report made it longer than necessary.'", "Back": "Word: Superfluous. Meaning: Unnecessary, especially through being more than enough."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *meticulous* planning of the event ensured that everything went smoothly.'", "Back": "Word: Meticulous. Meaning: Showing great attention to detail; very careful and precise."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'His *ephemeral* interest in the hobby lasted only a few weeks.'", "Back": "Word: Ephemeral. Meaning: Lasting for a very short time; fleeting."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *candid* interview revealed many surprising facts about the celebrity.'", "Back": "Word: Candid. Meaning: Truthful and straightforward; frank."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *vivid* description of the landscape made me feel like I was actually there.'", "Back": "Word: Vivid. Meaning: Producing powerful feelings or strong, clear images in the mind."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *adversary* proved to be a formidable opponent on the battlefield.'", "Back": "Word: Adversary. Meaning: One's opponent in a contest, conflict, or dispute."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *prolific* writer produced three novels in just one year.'", "Back": "Word: Prolific. Meaning: Producing much fruit or offspring, or many works of art or literature."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *versatile* athlete competed in five different sports during high school.'", "Back": "Word: Versatile. Meaning: Able to adapt or be adapted to many different functions or activities."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'His *stoic* response to the bad news surprised everyone.'", "Back": "Word: Stoic. Meaning: Enduring pain or hardship without showing feelings or complaining."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *tangible* evidence proved that the suspect was at the crime scene.'", "Back": "Word: Tangible. Meaning: Perceptible by touch; clear and definite; real."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *unprecedented* growth of the company led to many new job openings.'", "Back": "Word: Unprecedented. Meaning: Never done or known before."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *volatile* situation required careful handling by the authorities.'", "Back": "Word: Volatile. Meaning: Liable to change rapidly and unpredictably, especially for the worse."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'His *zealous* support for the cause inspired others to join as well.'", "Back": "Word: Zealous. Meaning: Having or showing great energy or enthusiasm in pursuit of a cause or an objective."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *arbitrary* decision was made without any clear reasoning or evidence.'", "Back": "Word: Arbitrary. Meaning: Based on random choice or personal whim, rather than any reason or system."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *belligerent* attitude of the driver led to a heated argument.'", "Back": "Word: Belligerent. Meaning: Hostile and aggressive."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *complacent* attitude of the team led to their defeat in the final game.'", "Back": "Word: Complacent. Meaning: Showing smug or uncritical satisfaction with oneself or one's achievements."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *disparate* groups were unable to reach an agreement on the new policy.'", "Back": "Word: Disparate. Meaning: Essentially different in kind; not allowing comparison."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *eloquent* speaker moved the audience with her powerful words.'", "Back": "Word: Eloquent. Meaning: Fluent or persuasive in speaking or writing."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *fastidious* chef insisted on only using the freshest ingredients.'", "Back": "Word: Fastidious. Meaning: Very attentive to and concerned about accuracy and detail; picky."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *gullible* person believed everything he was told without question.'", "Back": "Word: Gullible. Meaning: Easily persuaded to believe something; credulous."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *hypothetical* situation was used to illustrate a complex theory.'", "Back": "Word: Hypothetical. Meaning: Based on or serving as a hypothesis; supposed but not necessarily true."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *innocuous* comment was misunderstood and caused a lot of trouble.'", "Back": "Word: Innocuous. Meaning: Not harmful or offensive."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *judicious* use of resources ensured that the project was completed on time.'", "Back": "Word: Judicious. Meaning: Having, showing, or done with good judgment or sense."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *lucid* explanation made the complex topic easy to understand.'", "Back": "Word: Lucid. Meaning: Expressed clearly; easy to understand."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *mundane* tasks of everyday life can sometimes be very boring.'", "Back": "Word: Mundane. Meaning: Lacking interest or excitement; dull; earthly."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *nefarious* plot to take over the city was discovered by the police.'", "Back": "Word: Nefarious. Meaning: Wicked or criminal (typically of an action or activity)."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *objective* view of the situation allowed for a fair decision to be made.'", "Back": "Word: Objective. Meaning: Not influenced by personal feelings or opinions in considering and representing facts."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *pensive* look on his face suggested that he was deep in thought.'", "Back": "Word: Pensive. Meaning: Engaged in, involving, or reflecting deep or serious thought."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *quaint* village was filled with charming old houses and narrow streets.'", "Back": "Word: Quaint. Meaning: Attractively unusual or old-fashioned."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *revered* leader was loved and respected by all of his followers.'", "Back": "Word: Revered. Meaning: Feel deep respect or admiration for (something or someone)."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *scrupulous* attention to detail ensured that the final product was perfect.'", "Back": "Word: Scrupulous. Meaning: Diligent, thorough, and extremely attentive to details; very moral."},
    {"Topic": "9", "Subtopic": "1", "Front": "Sentence: 'The *ubiquitous* presence of cell phones has changed the way we communicate.'", "Back": "Word: Ubiquitous. Meaning: Present, appearing, or found everywhere."},
]

payload = {
    "app_name": APP_NAME,
    "flashcards": flashcards
}

response = requests.post(URL, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
