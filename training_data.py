# Sample complaints with their correct category label
# Add more examples of your own later to improve accuracy

training_data = [
    # Road
    ("There is a huge pothole on the main road", "Road"),
    ("The road near my house is badly damaged", "Road"),
    ("Street is full of cracks and broken pavement", "Road"),
    ("Highway has deep potholes causing accidents", "Road"),
    ("The road surface has collapsed after rain", "Road"),

    # Water
    ("There is a water leak near the main road", "Water"),
    ("Pipeline burst and water is flooding the street", "Water"),
    ("No water supply in our area for three days", "Water"),
    ("Water is leaking from underground pipes", "Water"),
    ("Drinking water supply line is broken", "Water"),

    # Drainage
    ("The drainage system is blocked and overflowing", "Drainage"),
    ("Sewage water is flowing on the street", "Drainage"),
    ("Drain near my house is clogged with garbage", "Drainage"),
    ("Gutter is overflowing after every rain", "Drainage"),
    ("Sewer line is broken and smells terrible", "Drainage"),

    # Waste
    ("Garbage bin is overflowing and not collected", "Waste"),
    ("Trash has not been picked up for a week", "Waste"),
    ("Waste is piling up on the street corner", "Waste"),
    ("Garbage truck never comes to our area", "Waste"),
    ("Litter is scattered all over the park", "Waste"),

    # Electricity
    ("Streetlight has been broken for a month", "Electricity"),
    ("Power outage in our area since morning", "Electricity"),
    ("Electric pole is leaning and looks dangerous", "Electricity"),
    ("Streetlights are not working at night", "Electricity"),
    ("Frequent electricity cuts in our neighborhood", "Electricity"),

    # Safety
    ("This area is unsafe at night with no lighting", "Safety"),
    ("Open manhole is a danger to pedestrians", "Safety"),
    ("Stray dogs are attacking people in the park", "Safety"),
    ("Broken fence near the school is a safety hazard", "Safety"),
    ("Construction site has no warning signs", "Safety"),
]