import requests
import json

URL = "https://script.google.com/macros/s/AKfycbzX9ZvLEAZ0D2FRtMnH-97Fahbph6ZXHJFQ4gSj9eTtKIWaMki9USV7URD5w3UmQKfFPg/exec"
APP_NAME = "asvab"

flashcards = [
    # PREFIXES (Table 4-2)
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: bi-", "Back": "Meaning 'two'. Example: Bilateral (having or relating to two sides)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: con- / contra-", "Back": "Meaning 'against'. Example: Contradict (to speak against or deny the truth of a statement)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: de-", "Back": "Meaning 'away from'. Example: Deny (to state that one has no connection with or responsibility for)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: dec-", "Back": "Meaning 'ten'. Example: Decade (a period of ten years)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: extra-", "Back": "Meaning 'outside' or 'beyond'. Example: Extracurricular (activity pursued in addition to the normal course of study)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: fore-", "Back": "Meaning 'in front of'. Example: Foreman (a worker who supervises and directs other workers)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: geo-", "Back": "Meaning 'earth'. Example: Geology (the science that deals with the earth's physical structure and substance)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: hyper-", "Back": "Meaning 'excess' or 'over'. Example: Hyperactive (abnormally or extremely active)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: il-", "Back": "Meaning 'not'. Example: Illogical (lacking sense or clear, sound reasoning)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: mal- / male-", "Back": "Meaning 'wrong' or 'bad'. Example: Malediction (a magical word or phrase uttered with the intention of bringing about evil)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: multi-", "Back": "Meaning 'many'. Example: Multiply (increase or cause to increase greatly in number or quantity)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: nom-", "Back": "Meaning 'name'. Example: Nominate (propose or formally enter as a candidate for election or an award)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: omni-", "Back": "Meaning 'all'. Example: Omnibus (a volume containing several novels or other items previously published separately)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: ped-", "Back": "Meaning 'foot'. Example: Pedestrian (a person walking along a road or in a developed area)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: que- / quer- / ques-", "Back": "Meaning 'ask'. Example: Question (a sentence worded or expressed so as to elicit information)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: re-", "Back": "Meaning 'back'. Example: Return (come or go back to a place or person)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: semi-", "Back": "Meaning 'half'. Example: Semisweet (slightly sweetened)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: super-", "Back": "Meaning 'over' or 'more'. Example: Superior (higher in station, rank, or degree)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: tele-", "Back": "Meaning 'far'. Example: Telephone (a system for transmitting voices over a distance)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: trans-", "Back": "Meaning 'across'. Example: Translate (express the sense of words or text in another language)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Prefix: un-", "Back": "Meaning 'not'. Example: Uninformed (not having or showing awareness or understanding of the facts)."},

    # SUFFIXES (Table 4-3)
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -able / -ible", "Back": "Meaning 'capable of'. Example: Agreeable (willing to agree to something)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -age", "Back": "Meaning 'action' or 'result'. Example: Breakage (the action of breaking or the fact of being broken)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -al", "Back": "Meaning 'characterized by'. Example: Functional (designed to be practical and useful, rather than attractive)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ance", "Back": "Meaning 'instance of an action'. Example: Performance (an act of staging or presenting a play, concert, or other form of entertainment)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ation", "Back": "Meaning 'action' or 'process'. Example: Liberation (the action of setting someone free from imprisonment or oppression)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -en", "Back": "Meaning 'made of'. Example: Silken (made of silk)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ful", "Back": "Meaning 'full of'. Example: Helpful (giving or ready to give help)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ic", "Back": "Meaning 'consisting of'. Example: Alcoholic (containing or relating to alcohol)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ical", "Back": "Meaning 'possessing a quality of'. Example: Statistical (relating to the use of statistics)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ion", "Back": "Meaning 'result of act or process'. Example: Legislation (laws, considered collectively)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ish", "Back": "Meaning 'relating to'. Example: Childish (of, like, or appropriate to a child)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ism", "Back": "Meaning 'act' or 'practice'. Example: Buddhism (a widespread Asian religion or philosophy)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ist", "Back": "Meaning 'characteristic of'. Example: Elitist (demonstrating the belief that a society should be led by an elite)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ity", "Back": "Meaning 'quality of'. Example: Specificity (the quality of being specific)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -less", "Back": "Meaning 'not having'. Example: Childless (not having any children)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -let", "Back": "Meaning 'small one'. Example: Booklet (a small book consisting of a few sheets, typically with paper covers)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -man", "Back": "Meaning 'relating to humans'. Example: Gentleman (a chivalrous, courteous, or honorable man)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ment", "Back": "Meaning 'action' or 'process'. Example: Establishment (the action of establishing something)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ness", "Back": "Meaning 'possessing a quality'. Example: Goodness (the quality of being good)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -or", "Back": "Meaning 'one who does a thing'. Example: Orator (a public speaker, especially one who is eloquent or skilled)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -ous", "Back": "Meaning 'having'. Example: Dangerous (able or likely to cause harm or injury)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Suffix: -y", "Back": "Meaning 'quality of'. Example: Tasty (having a pleasant, distinct flavor)."},

    # ROOTS (Table 4-4)
    {"Topic": "9", "Subtopic": "2", "Front": "Root: anthro / anthrop", "Back": "Meaning 'relating to humans'. Example: Anthropology (the study of human societies and cultures)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: bibli / biblio", "Back": "Meaning 'relating to books'. Example: Bibliography (a list of the books referred to in a scholarly work)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: brev", "Back": "Meaning 'short'. Example: Abbreviate (shorten a word, phrase, or text)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: cede / ceed", "Back": "Meaning 'go' or 'yield'. Example: Recede (go or move back or further away from a previous position)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: circum", "Back": "Meaning 'around'. Example: Circumnavigate (sail or otherwise travel all the way around something)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: chrom", "Back": "Meaning 'color'. Example: Monochrome (a photograph or picture developed or executed in black and white or in varying tones of only one color)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: cogn / cogno", "Back": "Meaning 'know'. Example: Cognizant (having knowledge or being aware of)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: corp", "Back": "Meaning 'body'. Example: Corporate (relating to a large company or group)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: dic / dict", "Back": "Meaning 'speak'. Example: Diction (the choice and use of words and phrases in speech or writing)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: domin", "Back": "Meaning 'rule'. Example: Dominate (have a commanding influence on; exercise control over)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: flu / flux", "Back": "Meaning 'flow'. Example: Influx (an arrival or entry of large numbers of people or things)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: form", "Back": "Meaning 'shape'. Example: Formulate (create or devise methodically a strategy or a proposal)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: frac / frag", "Back": "Meaning 'break'. Example: Fragment (a small part broken or separated off something)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: graph", "Back": "Meaning 'writing'. Example: Biography (an account of someone's life written by someone else)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: junct", "Back": "Meaning 'join'. Example: Juncture (a particular point in events or time)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: liber", "Back": "Meaning 'free'. Example: Liberate (set someone free from a situation)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: lum", "Back": "Meaning 'light'. Example: Illuminate (make something visible or bright by shining light on it)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: oper", "Back": "Meaning 'work'. Example: Co-operate (work jointly towards the same end)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: pat / path", "Back": "Meaning 'suffer'. Example: Pathology (the science of the causes and effects of diseases)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: port", "Back": "Meaning 'carry'. Example: Portable (able to be easily carried or moved)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: press", "Back": "Meaning 'squeeze'. Example: Repress (subdue someone or something by force)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: sens / sent", "Back": "Meaning 'think' or 'feel'. Example: Sentient (able to perceive or feel things)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: scrib / script", "Back": "Meaning 'write'. Example: Describe (give an account in words of someone or something)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: tract", "Back": "Meaning 'pull'. Example: Traction (the action of drawing or pulling a thing over a surface)."},
    {"Topic": "9", "Subtopic": "2", "Front": "Root: voc / vok", "Back": "Meaning 'call'. Example: Revoke (officially cancel a decree, decision, or promise)."},
]

payload = {
    "app_name": APP_NAME,
    "flashcards": flashcards
}

response = requests.post(URL, json=payload)
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
