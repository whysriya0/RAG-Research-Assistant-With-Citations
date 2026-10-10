# make_corpus.py
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
RAW = BASE / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
(BASE / "eval").mkdir(exist_ok=True)

DOCS = {}

DOCS["marlow_bridge"] = """
# The Marlow Bridge

## Overview

The Marlow Bridge crosses the Tessen River in the town of Orrin Vale. It was completed in 1923 and is 412 meters long. It is a steel arch bridge and carries a single railway line along with a pedestrian walkway.

## History

Construction began in 1917 under the engineer Halvard Pike. Work stopped for two years during the Great Flood of 1919, which swept away the first set of temporary supports. After the flood, Pike redesigned the foundations so that each pier rested on bedrock instead of river gravel. The redesign added eleven months to the schedule and raised the total cost to 3.2 million crowns.

## Restoration

In 1987 the bridge was closed for repairs after inspectors found corrosion in the lower arch. The restoration took four years and replaced about a third of the original steel. The bridge reopened in 1991 with a new coat of green paint. Green was chosen because it matched the color of the surrounding pine forest.

## Visiting

The pedestrian walkway is open daily from sunrise to sunset. Guided tours run on Saturdays and start at the Orrin Vale station. Tickets cost 6 crowns for adults, and children under twelve enter free.
"""

DOCS["brindle_cheese"] = """
# Brindle Cheese

## What it is

Brindle is a semi-hard cheese made in the Halden valley. It has a pale orange rind and a slightly sweet, nutty taste. Most wheels weigh about 9 kilograms.

## How it is made

Brindle is made from raw cow's milk collected within 15 kilometers of the dairy. The curds are cut to the size of rice grains and heated to 41 degrees Celsius. After pressing, the wheels are soaked in brine for two days.

## Aging

Wheels are aged in limestone caves for a minimum of eight months. During aging, each wheel is turned by hand every week and brushed with a mixture of salt water and annatto. Wheels aged for more than eighteen months are sold as Brindle Reserve and cost roughly double the standard price.

## Protected status

Since 2004 the name Brindle has been protected, meaning only cheese made in the Halden valley may use it. The rule was introduced after imitation cheeses began appearing in foreign markets. Producers must pass an annual inspection to keep the right to use the name.
"""

DOCS["quill_language"] = """
# The Quill Programming Language

## Overview

Quill is a small scripting language designed for teaching. It was created by Ines Marchetti and first released in 2011. The language uses indentation to mark blocks and has only fourteen keywords.

## Design goals

Marchetti wanted beginners to read code almost like plain English. For that reason, Quill uses the word "say" to print output and "ask" to read input. Variables are declared with the keyword "hold". Error messages are written as full sentences that suggest a fix.

## Types and memory

Quill has four built-in types: number, text, list and flag. All values are checked when the program runs, not before. Memory is managed by reference counting, so a value is freed as soon as nothing uses it.

## Tooling

The standard interpreter is called quillrun. A web playground lets students run code without installing anything. Version 3.0, released in 2019, added a debugger that lets learners step through a program one line at a time.

## Limitations

Quill is slow compared with most languages because it has no compiler. For this reason it is rarely used outside classrooms.
"""

DOCS["skerryball"] = """
# Skerryball

## Overview

Skerryball is a team sport played on small rocky islands off the northern coast. It was first played in 1923, the same year the Marlow Bridge opened, although the two have no connection. Each team has seven players and a match lasts three periods of twenty minutes.

## Rules

Players score by throwing a leather ball into a net fixed to a wooden post. The ball may not be carried for more than three steps. A player who touches the ball with a foot is penalized with a two-minute suspension. The post stands 2.4 meters high.

## The Gull Cup

The national championship is called the Gull Cup. It is held every August on the island of Brae. The team from Fenwick has won the cup nine times, more than any other club. The most recent winner was the team from Dunmore in 2024.

## Equipment

The ball is made of sealed leather and weighs 380 grams. Players wear rubber-soled shoes because the playing surface is often wet rock. Helmets are not required but are recommended for beginners.
"""

DOCS["aurelia_probe"] = """
# The Aurelia Probe

## Mission

Aurelia was an uncrewed probe launched in March 2014 to study the ice moons of the planet Veth. It carried six instruments and was designed to operate for five years. The mission was led by the Calder Space Agency.

## Spacecraft

The probe weighed 1,850 kilograms at launch. Power came from two solar wings that together produced 900 watts near Veth. A xenon ion engine handled course corrections during the long cruise.

## Discoveries

Aurelia's radar showed that the moon Osk has a liquid ocean beneath about 14 kilometers of ice. The probe also detected faint plumes of water vapor rising from cracks near the south pole of the moon Teb. These plumes were the first evidence that Teb is geologically active.

## End of mission

Contact with Aurelia was lost in November 2018 after a radiation storm damaged its main computer. The team had already received nearly all planned data. The probe was left in orbit around Veth and is expected to remain there for several centuries.
"""

for name, text in DOCS.items():
    (RAW / f"{name}.md").write_text(text.strip() + "\n", encoding="utf-8")

# (id, type, question, doc, evidence)   evidence=None -> unanswerable
Q = [
 ("q01", "factual", "How long is the Marlow Bridge?", "marlow_bridge", "is 412 meters long"),
 ("q02", "factual", "Who was the engineer behind the Marlow Bridge?", "marlow_bridge", "under the engineer Halvard Pike"),
 ("q03", "exact_term", "Which river does the Marlow Bridge cross?", "marlow_bridge", "crosses the Tessen River"),
 ("q04", "vague", "Why was the bridge so late getting finished?", "marlow_bridge", "Work stopped for two years during the Great Flood of 1919"),
 ("q05", "multi_part", "When did the Marlow Bridge reopen after repairs, and what color was it painted?", "marlow_bridge", "reopened in 1991 with a new coat of green paint"),
 ("q06", "factual", "How much does a wheel of Brindle usually weigh?", "brindle_cheese", "Most wheels weigh about 9 kilograms"),
 ("q07", "exact_term", "At what temperature are Brindle curds heated?", "brindle_cheese", "heated to 41 degrees Celsius"),
 ("q08", "factual", "What is the minimum aging time for Brindle?", "brindle_cheese", "minimum of eight months"),
 ("q09", "vague", "Is there a fancier, pricier version of that cheese?", "brindle_cheese", "sold as Brindle Reserve and cost roughly double the standard price"),
 ("q10", "multi_part", "Since when is the Brindle name protected, and what must producers do to keep using it?", "brindle_cheese", "Since 2004 the name Brindle has been protected"),
 ("q11", "factual", "Who created the Quill language?", "quill_language", "created by Ines Marchetti"),
 ("q12", "exact_term", "Which keyword declares a variable in Quill?", "quill_language", "declared with the keyword hold"),
 ("q13", "exact_term", "What is the standard Quill interpreter called?", "quill_language", "called quillrun"),
 ("q14", "vague", "Why do real projects rarely use that teaching language?", "quill_language", "Quill is slow compared with most languages because it has no compiler"),
 ("q15", "multi_part", "What did Quill 3.0 add, and in which year did it come out?", "quill_language", "Version 3.0, released in 2019, added a debugger"),
 ("q16", "factual", "How many players does a Skerryball team have?", "skerryball", "Each team has seven players"),
 ("q17", "exact_term", "What is the Skerryball national championship called?", "skerryball", "called the Gull Cup"),
 ("q18", "factual", "Which club has won the Gull Cup the most times?", "skerryball", "has won the cup nine times"),
 ("q19", "vague", "What happens if a player kicks the ball?", "skerryball", "touches the ball with a foot is penalized with a two-minute suspension"),
 ("q20", "multi_part", "Where and when is the Gull Cup held?", "skerryball", "held every August on the island of Brae"),
 ("q21", "factual", "How heavy was the Aurelia probe at launch?", "aurelia_probe", "weighed 1,850 kilograms"),
 ("q22", "exact_term", "What kind of engine handled Aurelia's course corrections?", "aurelia_probe", "xenon ion engine handled course corrections"),
 ("q23", "vague", "Did the probe find any sign of water under the ice on one of the moons?", "aurelia_probe", "liquid ocean beneath about 14 kilometers of ice"),
 ("q24", "multi_part", "When did Aurelia stop communicating, and what caused it?", "aurelia_probe", "lost in November 2018 after a radiation storm damaged its main computer"),
 ("q25", "unanswerable", "How much did the 1991 restoration of the Marlow Bridge cost?", None, None),
 ("q26", "unanswerable", "Who designed the xenon engine used on the Aurelia probe?", None, None),
 ("q27", "unanswerable", "Which team won the very first Gull Cup?", None, None),
 ("q28", "unanswerable", "Does Quill support object-oriented classes?", None, None),
 ("q29", "unanswerable", "What does a wheel of Brindle cost in dollars?", None, None),
]

with (BASE / "eval" / "questions.jsonl").open("w", encoding="utf-8") as f:
    for qid, typ, question, doc, ev in Q:
        f.write(json.dumps({"id": qid, "type": typ, "question": question, "doc": doc,
                            "evidence": ev, "answerable": ev is not None}) + "\n")

print(f"Wrote {len(DOCS)} docs to {RAW} and {len(Q)} questions to eval/questions.jsonl")