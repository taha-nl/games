from database import SessionLocal
from models import Card, CardType, Challenge, QuizQuestion, Team, TestCase, TutorAccount, TutorRole
from auth import hash_password


def seed_if_empty():
    db = SessionLocal()
    try:
        if db.query(Team).count() > 0:
            if db.query(QuizQuestion).count() == 0:
                _seed_quiz(db)
            if db.query(Challenge).filter(Challenge.challenge_type == "riddle").count() == 0:
                _seed_riddles(db)
            return
        _seed(db)
    finally:
        db.close()


def _seed(db):
    # Admin + Tutor accounts
    db.add(TutorAccount(
        username="admin",
        password_hash=hash_password("admin123"),
        role=TutorRole.admin,
    ))
    db.add(TutorAccount(
        username="tutor",
        password_hash=hash_password("tutor123"),
        role=TutorRole.tutor,
    ))

    # Demo teams
    for name in ["Alpha", "Beta", "Gamma", "Delta"]:
        db.add(Team(
            name=f"Team {name}",
            password_hash=hash_password("password123"),
            score=0,
            coins=100,
        ))

    # Challenges
    challenges = [
        Challenge(
            title="Cosmic Sum",
            planet_name="Planet Novara",
            difficulty="easy",
            points=100,
            coins_reward=10,
            order_index=0,
            description=(
                "Write a Python function called `cosmic_sum` that takes a list of integers "
                "and returns their sum.\n\n"
                "Example:\n  cosmic_sum([1, 2, 3]) → 6\n  cosmic_sum([10, -5, 0]) → 5\n\n"
                "Your function must handle empty lists (return 0) and negative numbers."
            ),
            examples="cosmic_sum([1, 2, 3])  # → 6\ncosmic_sum([])         # → 0\ncosmic_sum([-1, 1])    # → 0",
            starter_code="def cosmic_sum(numbers):\n    # Your code here\n    pass\n",
        ),
        Challenge(
            title="Star Counter",
            planet_name="Planet Lyra",
            difficulty="easy",
            points=120,
            coins_reward=10,
            order_index=1,
            description=(
                "Write a function `count_stars` that receives a string and counts "
                "how many times the character `*` appears in it.\n\n"
                "Bonus: also handle the case where the input is None (return 0)."
            ),
            examples='count_stars("**hello*")  # → 3\ncount_stars("")         # → 0\ncount_stars(None)       # → 0',
            starter_code="def count_stars(s):\n    pass\n",
        ),
        Challenge(
            title="Asteroid Reversal",
            planet_name="Planet Zephyr",
            difficulty="medium",
            points=200,
            coins_reward=20,
            order_index=2,
            description=(
                "Write a function `reverse_words` that takes a sentence string and "
                "returns the sentence with each word reversed, but keeping the word order.\n\n"
                "Example: 'hello world' → 'olleh dlrow'\n\n"
                "Words are separated by single spaces. Preserve original spacing."
            ),
            examples="reverse_words('hello world')      # → 'olleh dlrow'\nreverse_words('Space Mission')  # → 'ecapS noissiM'",
            starter_code="def reverse_words(sentence):\n    pass\n",
        ),
        Challenge(
            title="Nebula Fibonacci",
            planet_name="Planet Cassian",
            difficulty="medium",
            points=250,
            coins_reward=20,
            order_index=3,
            description=(
                "Write a function `fibonacci(n)` that returns the nth Fibonacci number.\n\n"
                "Fibonacci sequence: 0, 1, 1, 2, 3, 5, 8, 13, 21...\n"
                "fibonacci(0) = 0, fibonacci(1) = 1, fibonacci(7) = 13\n\n"
                "Optimize for n up to 50 (don't use naive recursion)."
            ),
            examples="fibonacci(0)   # → 0\nfibonacci(1)   # → 1\nfibonacci(7)   # → 13\nfibonacci(10)  # → 55",
            starter_code="def fibonacci(n):\n    pass\n",
        ),
        Challenge(
            title="Black Hole Detector",
            planet_name="Planet Vanthar",
            difficulty="hard",
            points=350,
            coins_reward=35,
            order_index=4,
            description=(
                "A 'black hole' number is one where if you repeatedly apply the following "
                "operation, you eventually reach 495 (for 3-digit numbers):\n\n"
                "1. Take any 3-digit number with at least two different digits\n"
                "2. Arrange digits in descending order → subtract ascending order\n"
                "3. Repeat until you reach 495\n\n"
                "Write `kaprekar_steps(n)` that returns how many steps it takes to reach 495. "
                "If n is already 495, return 0."
            ),
            examples="kaprekar_steps(495) # → 0\nkaprekar_steps(123) # → 3\nkaprekar_steps(100) # → 5",
            starter_code="def kaprekar_steps(n):\n    pass\n",
        ),
        Challenge(
            title="Wormhole Palindrome",
            planet_name="Planet Mirova",
            difficulty="hard",
            points=300,
            coins_reward=30,
            order_index=5,
            description=(
                "Write a function `longest_palindrome(s)` that finds the longest palindromic "
                "substring in a given string.\n\n"
                "A palindrome reads the same forward and backward.\n"
                "If multiple palindromes of the same max length exist, return the first one found.\n\n"
                "Must handle strings of length 1 (the string itself is a palindrome)."
            ),
            examples='longest_palindrome("babad")  # → "bab"\nlongest_palindrome("cbbd")   # → "bb"\nlongest_palindrome("a")      # → "a"',
            starter_code="def longest_palindrome(s):\n    pass\n",
        ),
        # --- New challenges ---
        Challenge(
            title="Space Roll Call",
            planet_name="Planet Vega",
            difficulty="easy",
            points=100,
            coins_reward=10,
            order_index=6,
            description=(
                "The mission commander calls out astronaut names. Write a function `roll_call(names)` "
                "that takes a list of names and returns only the ones that start with a vowel (A, E, I, O, U — "
                "case insensitive).\n\n"
                "Keep the original order. Return an empty list if none qualify."
            ),
            examples='roll_call(["Alice", "Bob", "Omar"])  # → [\'Alice\', \'Omar\']\nroll_call([])                        # → []',
            starter_code="def roll_call(names):\n    # Your code here\n    pass\n",
        ),
        Challenge(
            title="Fuel Gauge",
            planet_name="Planet Draco",
            difficulty="easy",
            points=120,
            coins_reward=10,
            order_index=7,
            description=(
                "A rocket needs exactly 100 units of fuel. You have several tanks, each with a different amount.\n\n"
                "Write a function `fuel_gauge(tanks)` that returns `True` if any two tanks "
                "add up to exactly 100, and `False` otherwise.\n\n"
                "You cannot combine a tank with itself."
            ),
            examples="fuel_gauge([30, 70, 50, 20])  # → True  (30 + 70)\nfuel_gauge([10, 20, 30])      # → False",
            starter_code="def fuel_gauge(tanks):\n    # Your code here\n    pass\n",
        ),
        Challenge(
            title="Alien Decoder",
            planet_name="Planet Xenon",
            difficulty="easy",
            points=150,
            coins_reward=15,
            order_index=8,
            description=(
                "Aliens encrypt messages using a Caesar cipher: each letter is shifted forward by 3 "
                "in the alphabet. Write a function `alien_decode(msg)` that reverses this — "
                "shift each letter back by 3.\n\n"
                "Only shift letters (a-z, A-Z). Leave spaces and other characters unchanged.\n\n"
                "Examples: 'khoor' → 'hello', 'zruog' → 'world'"
            ),
            examples="alien_decode('khoor')    # → 'hello'\nalien_decode('zruog')    # → 'world'\nalien_decode('vsdfh')    # → 'space'",
            starter_code="def alien_decode(msg):\n    # Your code here\n    pass\n",
        ),
        Challenge(
            title="Asteroid Divisors",
            planet_name="Planet Kronos",
            difficulty="medium",
            points=200,
            coins_reward=20,
            order_index=9,
            description=(
                "Write a function `asteroid_divisors(n)` that returns a tuple `(total, is_perfect)` where:\n\n"
                "- `total` is the sum of all divisors of `n` excluding `n` itself\n"
                "- `is_perfect` is `True` if that sum equals `n` (called a perfect number)\n\n"
                "Examples: 28 is perfect because 1+2+4+7+14 = 28\n"
                "12 is not perfect because 1+2+3+4+6 = 16 ≠ 12"
            ),
            examples="asteroid_divisors(28)   # → (28, True)\nasteroid_divisors(12)   # → (16, False)\nasteroid_divisors(6)    # → (6, True)",
            starter_code="def asteroid_divisors(n):\n    # Your code here\n    pass\n",
        ),
        Challenge(
            title="Orbit Calculator",
            planet_name="Planet Elliptica",
            difficulty="medium",
            points=200,
            coins_reward=20,
            order_index=10,
            description=(
                "A planet's orbit is shaped like an ellipse. The area of an ellipse is:\n\n"
                "    area = π × a × b\n\n"
                "where `a` is the semi-major axis and `b` is the semi-minor axis.\n\n"
                "Write a function `orbit_area(a, b)` that returns the area rounded to 2 decimal places.\n\n"
                "Use `import math` and `math.pi` for precision."
            ),
            examples="orbit_area(5, 3)   # → 47.12\norbit_area(7, 2)   # → 43.98\norbit_area(1, 1)   # → 3.14",
            starter_code="import math\n\ndef orbit_area(a, b):\n    # Your code here\n    pass\n",
        ),
        Challenge(
            title="Binary Star",
            planet_name="Planet Bitara",
            difficulty="medium",
            points=220,
            coins_reward=20,
            order_index=11,
            description=(
                "Write a function `binary_ones(n)` that converts a decimal number to binary "
                "WITHOUT using Python's built-in `bin()` function, then counts and returns "
                "how many 1s appear in the binary representation.\n\n"
                "This count is called the Hamming weight or population count.\n\n"
                "Hint: repeatedly divide by 2 and collect remainders."
            ),
            examples="binary_ones(13)   # → 3   (13 = 1101 in binary)\nbinary_ones(255)  # → 8   (255 = 11111111)\nbinary_ones(0)    # → 0",
            starter_code="def binary_ones(n):\n    # Your code here\n    pass\n",
        ),
    ]
    for c in challenges:
        db.add(c)
    db.flush()  # get IDs before adding test cases

    # Test cases — students must print() the result
    test_cases = [
        # Cosmic Sum
        TestCase(challenge_id=challenges[0].id, order_index=0, stdin="", expected_output="6",
                 is_hidden=False),   # cosmic_sum([1,2,3])
        TestCase(challenge_id=challenges[0].id, order_index=1, stdin="", expected_output="0",
                 is_hidden=False),   # cosmic_sum([])
        TestCase(challenge_id=challenges[0].id, order_index=2, stdin="", expected_output="5",
                 is_hidden=True),    # cosmic_sum([10,-5,0])

        # Star Counter
        TestCase(challenge_id=challenges[1].id, order_index=0, stdin="", expected_output="3",
                 is_hidden=False),
        TestCase(challenge_id=challenges[1].id, order_index=1, stdin="", expected_output="0",
                 is_hidden=False),
        TestCase(challenge_id=challenges[1].id, order_index=2, stdin="", expected_output="0",
                 is_hidden=True),

        # Asteroid Reversal
        TestCase(challenge_id=challenges[2].id, order_index=0, stdin="", expected_output="olleh dlrow",
                 is_hidden=False),
        TestCase(challenge_id=challenges[2].id, order_index=1, stdin="", expected_output="ecapS noissiM",
                 is_hidden=False),
        TestCase(challenge_id=challenges[2].id, order_index=2, stdin="", expected_output="a",
                 is_hidden=True),

        # Nebula Fibonacci
        TestCase(challenge_id=challenges[3].id, order_index=0, stdin="", expected_output="0",
                 is_hidden=False),
        TestCase(challenge_id=challenges[3].id, order_index=1, stdin="", expected_output="13",
                 is_hidden=False),
        TestCase(challenge_id=challenges[3].id, order_index=2, stdin="", expected_output="55",
                 is_hidden=True),

        # Black Hole Detector
        TestCase(challenge_id=challenges[4].id, order_index=0, stdin="", expected_output="0",
                 is_hidden=False),
        TestCase(challenge_id=challenges[4].id, order_index=1, stdin="", expected_output="3",
                 is_hidden=False),
        TestCase(challenge_id=challenges[4].id, order_index=2, stdin="", expected_output="5",
                 is_hidden=True),

        # Wormhole Palindrome
        TestCase(challenge_id=challenges[5].id, order_index=0, stdin="", expected_output="bab",
                 is_hidden=False),
        TestCase(challenge_id=challenges[5].id, order_index=1, stdin="", expected_output="bb",
                 is_hidden=False),
        TestCase(challenge_id=challenges[5].id, order_index=2, stdin="", expected_output="a",
                 is_hidden=True),

        # Space Roll Call
        TestCase(challenge_id=challenges[6].id, order_index=0, stdin="", expected_output="['Alice', 'Omar']",     is_hidden=False),
        TestCase(challenge_id=challenges[6].id, order_index=1, stdin="", expected_output="[]",                    is_hidden=False),
        TestCase(challenge_id=challenges[6].id, order_index=2, stdin="", expected_output="['eve', 'ian']",        is_hidden=False),
        TestCase(challenge_id=challenges[6].id, order_index=3, stdin="", expected_output="[]",                    is_hidden=False),
        TestCase(challenge_id=challenges[6].id, order_index=4, stdin="", expected_output="['Alice', 'Eve', 'Iris']", is_hidden=False),
        TestCase(challenge_id=challenges[6].id, order_index=5, stdin="", expected_output="['Uma', 'Eli']",        is_hidden=True),

        # Fuel Gauge
        TestCase(challenge_id=challenges[7].id, order_index=0, stdin="", expected_output="True",  is_hidden=False),
        TestCase(challenge_id=challenges[7].id, order_index=1, stdin="", expected_output="False", is_hidden=False),
        TestCase(challenge_id=challenges[7].id, order_index=2, stdin="", expected_output="True",  is_hidden=False),
        TestCase(challenge_id=challenges[7].id, order_index=3, stdin="", expected_output="False", is_hidden=False),
        TestCase(challenge_id=challenges[7].id, order_index=4, stdin="", expected_output="True",  is_hidden=False),
        TestCase(challenge_id=challenges[7].id, order_index=5, stdin="", expected_output="True",  is_hidden=True),

        # Alien Decoder
        TestCase(challenge_id=challenges[8].id, order_index=0, stdin="", expected_output="hello",   is_hidden=False),
        TestCase(challenge_id=challenges[8].id, order_index=1, stdin="", expected_output="world",   is_hidden=False),
        TestCase(challenge_id=challenges[8].id, order_index=2, stdin="", expected_output="space",   is_hidden=False),
        TestCase(challenge_id=challenges[8].id, order_index=3, stdin="", expected_output="mission", is_hidden=False),
        TestCase(challenge_id=challenges[8].id, order_index=4, stdin="", expected_output="",        is_hidden=False),
        TestCase(challenge_id=challenges[8].id, order_index=5, stdin="", expected_output="comet",  is_hidden=True),

        # Asteroid Divisors
        TestCase(challenge_id=challenges[9].id, order_index=0, stdin="", expected_output="(28, True)",  is_hidden=False),
        TestCase(challenge_id=challenges[9].id, order_index=1, stdin="", expected_output="(16, False)", is_hidden=False),
        TestCase(challenge_id=challenges[9].id, order_index=2, stdin="", expected_output="(6, True)",   is_hidden=False),
        TestCase(challenge_id=challenges[9].id, order_index=3, stdin="", expected_output="(0, False)",  is_hidden=False),
        TestCase(challenge_id=challenges[9].id, order_index=4, stdin="", expected_output="(9, False)",  is_hidden=False),
        TestCase(challenge_id=challenges[9].id, order_index=5, stdin="", expected_output="(496, True)", is_hidden=True),

        # Orbit Calculator
        TestCase(challenge_id=challenges[10].id, order_index=0, stdin="", expected_output="47.12",  is_hidden=False),
        TestCase(challenge_id=challenges[10].id, order_index=1, stdin="", expected_output="43.98",  is_hidden=False),
        TestCase(challenge_id=challenges[10].id, order_index=2, stdin="", expected_output="3.14",   is_hidden=False),
        TestCase(challenge_id=challenges[10].id, order_index=3, stdin="", expected_output="157.08", is_hidden=False),
        TestCase(challenge_id=challenges[10].id, order_index=4, stdin="", expected_output="28.27",  is_hidden=False),
        TestCase(challenge_id=challenges[10].id, order_index=5, stdin="", expected_output="75.4",  is_hidden=True),

        # Binary Star
        TestCase(challenge_id=challenges[11].id, order_index=0, stdin="", expected_output="3", is_hidden=False),
        TestCase(challenge_id=challenges[11].id, order_index=1, stdin="", expected_output="8", is_hidden=False),
        TestCase(challenge_id=challenges[11].id, order_index=2, stdin="", expected_output="0", is_hidden=False),
        TestCase(challenge_id=challenges[11].id, order_index=3, stdin="", expected_output="1", is_hidden=False),
        TestCase(challenge_id=challenges[11].id, order_index=4, stdin="", expected_output="1", is_hidden=False),
        TestCase(challenge_id=challenges[11].id, order_index=5, stdin="", expected_output="4", is_hidden=True),
    ]

    # Patch starter_code to include print() calls matching the test cases
    call_map = {
        0: [
            "print(cosmic_sum([1, 2, 3]))",
            "print(cosmic_sum([]))",
            "print(cosmic_sum([10, -5, 0]))",
        ],
        1: [
            'print(count_stars("**hello*"))',
            'print(count_stars(""))',
            'print(count_stars(None))',
        ],
        2: [
            "print(reverse_words('hello world'))",
            "print(reverse_words('Space Mission'))",
            "print(reverse_words('a'))",
        ],
        3: [
            "print(fibonacci(0))",
            "print(fibonacci(7))",
            "print(fibonacci(10))",
        ],
        4: [
            "print(kaprekar_steps(495))",
            "print(kaprekar_steps(123))",
            "print(kaprekar_steps(100))",
        ],
        5: [
            'print(longest_palindrome("babad"))',
            'print(longest_palindrome("cbbd"))',
            'print(longest_palindrome("a"))',
        ],
        6: [
            'print(roll_call(["Alice", "Bob", "Omar"]))',
            'print(roll_call([]))',
            'print(roll_call(["eve", "sam", "ian"]))',
            'print(roll_call(["Bob", "Sam", "Tom"]))',
            'print(roll_call(["Alice", "Eve", "Iris"]))',
            'print(roll_call(["Uma", "Zara", "Eli"]))',
        ],
        7: [
            'print(fuel_gauge([30, 70, 50, 20]))',
            'print(fuel_gauge([10, 20, 30]))',
            'print(fuel_gauge([50, 50]))',
            'print(fuel_gauge([]))',
            'print(fuel_gauge([100, 0]))',
            'print(fuel_gauge([99, 1, 5, 95]))',
        ],
        8: [
            'print(alien_decode("khoor"))',
            'print(alien_decode("zruog"))',
            'print(alien_decode("vsdfh"))',
            'print(alien_decode("plvvlrq"))',
            'print(alien_decode(""))',
            'print(alien_decode("frphw"))',
        ],
        9: [
            'print(asteroid_divisors(28))',
            'print(asteroid_divisors(12))',
            'print(asteroid_divisors(6))',
            'print(asteroid_divisors(1))',
            'print(asteroid_divisors(15))',
            'print(asteroid_divisors(496))',
        ],
        10: [
            'print(orbit_area(5, 3))',
            'print(orbit_area(7, 2))',
            'print(orbit_area(1, 1))',
            'print(orbit_area(10, 5))',
            'print(orbit_area(3, 3))',
            'print(orbit_area(6, 4))',
        ],
        11: [
            'print(binary_ones(13))',
            'print(binary_ones(255))',
            'print(binary_ones(0))',
            'print(binary_ones(1))',
            'print(binary_ones(64))',
            'print(binary_ones(170))',
        ],
    }

    for i, tc in enumerate(test_cases):
        # find which challenge index and case index this belongs to
        for ci, c in enumerate(challenges):
            if tc.challenge_id == c.id:
                tc.stdin = call_map[ci][tc.order_index]
                break
        db.add(tc)

    for c in challenges:
        db.commit()

    # Cards
    cards = [
        Card(name="Hint Card", card_type=CardType.hint, cost_coins=50, icon="💡",
             description="Request a hint from a tutor for the current challenge."),
        Card(name="Bug Detector", card_type=CardType.bug_detector, cost_coins=75, icon="🐛",
             description="Ask a tutor to point out where a bug is hiding in your code."),
        Card(name="Double Points", card_type=CardType.double_points, cost_coins=100, icon="⚡",
             description="Your next approved submission earns double the points!"),
        Card(name="Extra Time", card_type=CardType.extra_time, cost_coins=60, icon="⏰",
             description="Ask for extra time or a deadline extension from the tutor."),
        Card(name="Freeze Opponent", card_type=CardType.freeze_opponent, cost_coins=120, icon="🥶",
             description="Freeze another team's submissions for 5 minutes!"),
        Card(name="Skip Challenge", card_type=CardType.skip_challenge, cost_coins=80, icon="⏭️",
             description="Signal you want to skip a challenge for partial credit."),
    ]
    for card in cards:
        db.add(card)

    db.commit()
    _seed_quiz(db)
    _seed_riddles(db)
    print("✅ Database seeded with demo teams, challenges, cards, quiz questions, and riddles.")


def _seed_quiz(db):
    questions = [
        # ── Origins ─────────────────────────────────────────────────────────
        QuizQuestion(
            category="Origins",
            order_index=0,
            points=10,
            question="The word 'algorithm' comes from the name of a famous scholar. Who is he?",
            joke_hint="Hint: his name also gave us the word 'algebra' — he really liked naming things after himself! 😄",
            option_a="Euclid of Alexandria",
            option_b="Muhammad ibn Musa al-Khwarizmi",
            option_c="Alan Turing",
            option_d="Albert Einstein",
            correct="b",
            explanation="Al-Khwarizmi was a 9th-century mathematician at the House of Wisdom in Baghdad. The Latin form of his name — 'Algoritmi' — became our word 'algorithm'. Every time you say the word, you say his name!",
        ),
        QuizQuestion(
            category="Origins",
            order_index=1,
            points=10,
            question="Al-Khwarizmi's book also gave us which other math word we use every day?",
            joke_hint="Think of balancing both sides of an equation… like balancing your breakfast plate! 🍳",
            option_a="Calculus",
            option_b="Geometry",
            option_c="Algebra",
            option_d="Trigonometry",
            correct="c",
            explanation="His book 'al-Kitāb al-mukhtaṣar fī ḥisāb al-jabr' (The Compendious Book on Calculation by Completion and Balancing) gave us the word 'algebra' from 'al-jabr'.",
        ),

        # ── What is an Algorithm ────────────────────────────────────────────
        QuizQuestion(
            category="What is an Algorithm",
            order_index=2,
            points=10,
            question="Which of these is the BEST definition of an algorithm?",
            joke_hint="It's not a dance move — though some algorithms are surprisingly rhythmic! 🕺",
            option_a="A type of computer programming language",
            option_b="A finite, ordered set of unambiguous steps that solves a problem",
            option_c="A math formula used only in calculators",
            option_d="Any piece of code written by a programmer",
            correct="b",
            explanation="An algorithm must be FINITE (it ends), ORDERED (steps in the right sequence), and UNAMBIGUOUS (no guessing — every step is clear). 'Put on socks before shoes' is a simple algorithm!",
        ),
        QuizQuestion(
            category="What is an Algorithm",
            order_index=3,
            points=10,
            question="Which of these is NOT a valid property of an algorithm?",
            joke_hint="One of these would make a computer say 'ERROR: I cannot improvise!' 🤖",
            option_a="It must eventually stop (finite)",
            option_b="Steps must be in the correct order",
            option_c="It can include vague instructions like 'add a pinch of salt'",
            option_d="Each step must be clear and exact",
            correct="c",
            explanation="Algorithms must be UNAMBIGUOUS — 'a pinch of salt' means nothing to a computer! Every instruction must be precise enough that a machine can execute it without guessing.",
        ),
        QuizQuestion(
            category="What is an Algorithm",
            order_index=4,
            points=15,
            question="You're making a sandwich. Which version is a proper algorithm?",
            joke_hint="One of these might result in bread soup… 🍞🌊",
            option_a="Make a sandwich however you like.",
            option_b="1. Get bread. 2. Add filling. 3. Close sandwich. 4. Eat.",
            option_c="Put filling somewhere between bread-ish things.",
            option_d="Think about a sandwich really hard.",
            correct="b",
            explanation="Option B has all the properties: it's finite (ends at step 4), ordered (can't eat before assembling!), and unambiguous (each step is clear). The others are vague or endless!",
        ),

        # ── Real World Applications ──────────────────────────────────────────
        QuizQuestion(
            category="Real World",
            order_index=5,
            points=10,
            question="Which algorithm type does your GPS use to find the fastest route home?",
            joke_hint="Without this, GPS would just spin around yelling 'ARE WE THERE YET?' 🗺️",
            option_a="Bubble Sort",
            option_b="Shortest-path algorithm",
            option_c="Binary Search",
            option_d="Stack algorithm",
            correct="b",
            explanation="GPS uses shortest-path algorithms (like Dijkstra's or A*) to check millions of possible routes in milliseconds — including live traffic data — to find the fastest way home.",
        ),
        QuizQuestion(
            category="Real World",
            order_index=6,
            points=15,
            question="When YouTube suggests a video you'd probably like, what kind of algorithm is doing that?",
            joke_hint="It's why you meant to watch ONE video and ended up watching 47... 📺",
            option_a="Sorting algorithm",
            option_b="Shortest-path algorithm",
            option_c="Recommendation engine",
            option_d="Binary search",
            correct="c",
            explanation="Recommendation engines learn your taste from patterns across millions of users. They use machine learning algorithms to predict what you'll enjoy next — which is why YouTube always has 'just one more' video for you!",
        ),

        # ── Big O Complexity ────────────────────────────────────────────────
        QuizQuestion(
            category="Big O Complexity",
            order_index=7,
            points=20,
            question="What does O(1) mean in algorithm complexity?",
            joke_hint="This is the dream — like finding your keys immediately because they're always in the same pocket. 🗝️",
            option_a="The algorithm takes 1 second to run",
            option_b="The algorithm uses 1 unit of memory",
            option_c="The algorithm runs in constant time regardless of input size",
            option_d="The algorithm has only 1 step",
            correct="c",
            explanation="O(1) means CONSTANT time — no matter how big the input is, the operation takes the same amount of time. Example: looking up a value at a known index in an array is always instant!",
        ),
        QuizQuestion(
            category="Big O Complexity",
            order_index=8,
            points=20,
            question="You compare every student to every other student in a class. As the class doubles in size, how much slower does this get?",
            joke_hint="If comparing 10 kids takes 1 minute, comparing 20 kids won't just take 2 minutes… 😬",
            option_a="Twice as slow — O(n)",
            option_b="Four times as slow — O(n²)",
            option_c="The same speed — O(1)",
            option_d="Eight times as slow — O(n³)",
            correct="b",
            explanation="Comparing everyone to everyone is O(n²) — quadratic. If you have 10 students that's 100 comparisons. Double to 20 students: 400 comparisons. 4× slower! This is why O(n²) algorithms struggle with big data.",
        ),
        QuizQuestion(
            category="Big O Complexity",
            order_index=9,
            points=25,
            question="For n = 1,000,000 inputs, roughly how many steps does an O(n²) algorithm need?",
            joke_hint="Grab a calculator… actually, grab a VERY big calculator. 🧮",
            option_a="1,000,000 steps",
            option_b="2,000,000 steps",
            option_c="1,000,000,000,000 steps",
            option_d="20 steps",
            correct="c",
            explanation="O(n²) means n × n steps. For n = 1,000,000: that's 1,000,000 × 1,000,000 = 1 trillion steps! An O(n) algorithm would finish in a blink; the O(n²) one would finish… after you graduate. 🎓",
        ),
        QuizQuestion(
            category="Big O Complexity",
            order_index=10,
            points=20,
            question="Which complexity 'barely slows down' even as data grows massively?",
            joke_hint="This is like looking for a word in a dictionary by opening it in the middle first — genius! 📖",
            option_a="O(n²)",
            option_b="O(n)",
            option_c="O(log n)",
            option_d="O(1)",
            correct="c",
            explanation="O(log n) is logarithmic — it barely slows down even with huge inputs. Binary search is a classic example: searching a sorted list of 1 billion items only takes about 30 steps!",
        ),

        # ── Data Structures ─────────────────────────────────────────────────
        QuizQuestion(
            category="Data Structures",
            order_index=11,
            points=15,
            question="Which data structure works like a stack of plates — the last one you put on is the first one you take off?",
            joke_hint="Think about washing dishes — you always grab the top plate first (not the bottom one, unless you're brave 🍽️)",
            option_a="Queue",
            option_b="Array",
            option_c="Stack",
            option_d="Dictionary",
            correct="c",
            explanation="A Stack is LIFO — Last In, First Out. Just like a stack of plates! In programming, Ctrl+Z (undo) uses a stack: the last action you did is the first one undone. Your browser's Back button works the same way.",
        ),
        QuizQuestion(
            category="Data Structures",
            order_index=12,
            points=15,
            question="A Queue data structure works like a line at a café. What rule does it follow?",
            joke_hint="The person who arrived FIRST gets served first — cutting in line is NOT allowed in data structures! ☕",
            option_a="LIFO — Last In, First Out",
            option_b="FIFO — First In, First Out",
            option_c="Random order",
            option_d="Sorted by priority",
            correct="b",
            explanation="A Queue is FIFO — First In, First Out. The first item added is the first one removed. Real examples: printer job queues (first document sent = first printed) and video buffering!",
        ),
        QuizQuestion(
            category="Data Structures",
            order_index=13,
            points=15,
            question="You need to instantly jump to item #3 in a collection without scanning items #1 and #2. Which data structure lets you do this?",
            joke_hint="Think of numbered lockers — you don't need to open #1 and #2 to get to #3! 🔐",
            option_a="Stack",
            option_b="Queue",
            option_c="Array",
            option_d="Linked List",
            correct="c",
            explanation="An Array stores items in numbered slots (indices). You can jump straight to any position — array[3] is instant! This is called O(1) random access, and it's one of the main advantages of arrays.",
        ),

        # ── Sorting ─────────────────────────────────────────────────────────
        QuizQuestion(
            category="Sorting",
            order_index=14,
            points=20,
            question="In Bubble Sort, what happens during each 'pass' through the list?",
            joke_hint="Imagine the biggest number floating to the top like a bubble — hence the name! 🫧",
            option_a="All elements are sorted at once",
            option_b="Neighbours are compared and swapped if in wrong order, moving the largest to the end",
            option_c="The list is split in half and merged back",
            option_d="Elements are inserted into their correct position one by one",
            correct="b",
            explanation="Bubble Sort compares each pair of neighbours and swaps them if they're in the wrong order. After each pass, the largest unsorted element 'bubbles up' to its correct position at the end. Simple but slow — O(n²)!",
        ),
        QuizQuestion(
            category="Sorting",
            order_index=15,
            points=20,
            question="What is the time complexity of Bubble Sort?",
            joke_hint="Spoiler: it's the 'painful one' from the complexity chart! 😬",
            option_a="O(1)",
            option_b="O(log n)",
            option_c="O(n)",
            option_d="O(n²)",
            correct="d",
            explanation="Bubble Sort is O(n²) — in the worst case, you need to compare every element with every other element. This makes it very slow for large lists. Faster algorithms like Merge Sort and Quick Sort use O(n log n).",
        ),
        QuizQuestion(
            category="Sorting",
            order_index=16,
            points=25,
            question="You want to sort 1 BILLION items. Bubble Sort is O(n²). A better algorithm is O(n log n). Roughly how many times faster is the better algorithm?",
            joke_hint="The difference is so big it'll make your head spin. Grab a calculator! 🤯",
            option_a="About 2× faster",
            option_b="About 100× faster",
            option_c="About 33 MILLION times faster",
            option_d="Same speed, different style",
            correct="c",
            explanation="For n=1 billion: Bubble Sort needs n²=10¹⁸ steps. O(n log n) needs about 30 billion steps (30×10⁹). That's 10¹⁸ / 3×10¹⁰ ≈ 33 million times faster! Great algorithm choice = a HUGE real-world difference.",
        ),
    ]

    for q in questions:
        db.add(q)
    db.commit()
    print(f"✅ Seeded {len(questions)} quiz questions.")


def _seed_riddles(db):
    riddles = [
        Challenge(
            title="The Three Switches",
            planet_name="Logic Station Alpha",
            challenge_type="riddle",
            difficulty="medium",
            points=200,
            coins_reward=20,
            order_index=100,
            description=(
                "You are outside a closed room. Outside the room are three switches. "
                "Inside the room is one light bulb.\n\n"
                "Only one switch controls the bulb. You may turn the switches on or off as much as you want, "
                "but you may enter the room only once.\n\n"
                "How can you identify the correct switch?"
            ),
            examples="",
            starter_code=(
                "Turn on switch 1 for several minutes, then turn it off. "
                "Turn on switch 2. Enter the room.\n"
                "- If the bulb is ON → switch 2.\n"
                "- If the bulb is OFF but WARM → switch 1.\n"
                "- If the bulb is OFF and COLD → switch 3."
            ),
        ),
        Challenge(
            title="The Two Doors",
            planet_name="Planet Paradox",
            challenge_type="riddle",
            difficulty="medium",
            points=175,
            coins_reward=18,
            order_index=101,
            description=(
                "You stand before two doors. One leads to safety, the other to danger.\n\n"
                "A guard stands beside each door. One guard always tells the truth; "
                "the other always lies.\n\n"
                "You may ask only ONE question to ONE guard.\n\n"
                "What do you ask to find the safe door?"
            ),
            examples="",
            starter_code=(
                'Ask either guard: "Which door would the OTHER guard say leads to safety?"\n\n'
                "Then choose the OPPOSITE door.\n\n"
                "Why it works: the truth-teller tells you what the liar would say (wrong door). "
                "The liar lies about what the truth-teller would say (also the wrong door). "
                "Both always point to the wrong door, so you pick the opposite."
            ),
        ),
        Challenge(
            title="The Farmer's Problem",
            planet_name="Crossroads Nebula",
            challenge_type="riddle",
            difficulty="hard",
            points=300,
            coins_reward=30,
            order_index=102,
            description=(
                "A farmer must cross a river with a wolf, a goat, and a basket of cabbage. "
                "The boat can carry only the farmer and ONE item.\n\n"
                "Rules:\n"
                "- The wolf cannot be left alone with the goat.\n"
                "- The goat cannot be left alone with the cabbage.\n\n"
                "How can the farmer get everything safely across?"
            ),
            examples="",
            starter_code=(
                "1. Take the GOAT across → return alone.\n"
                "2. Take the WOLF across → bring the GOAT back.\n"
                "3. Take the CABBAGE across → return alone.\n"
                "4. Take the GOAT across.\n\n"
                "Done! Wolf and cabbage are never alone with the goat."
            ),
        ),
        Challenge(
            title="The Heavy Ball",
            planet_name="Gravity Core",
            challenge_type="riddle",
            difficulty="medium",
            points=200,
            coins_reward=20,
            order_index=103,
            description=(
                "You have 9 identical-looking balls. One ball is heavier than the others.\n\n"
                "You have a balance scale and may use it only TWICE.\n\n"
                "How do you find the heavier ball?"
            ),
            examples="",
            starter_code=(
                "Weigh 1: Put 3 balls on each side.\n"
                "- If one side is heavier → the heavy ball is in that group.\n"
                "- If balanced → the heavy ball is in the remaining group of 3.\n\n"
                "Weigh 2: From the identified group of 3, put 1 on each side, leave 1 off.\n"
                "- One side heavier → that's the heavy ball.\n"
                "- Balanced → the ball left off the scale is the heavy one."
            ),
        ),
        Challenge(
            title="The Wrong Labels",
            planet_name="Mislabel Moon",
            challenge_type="riddle",
            difficulty="medium",
            points=225,
            coins_reward=23,
            order_index=104,
            description=(
                "There are three boxes:\n"
                "- One contains only apples.\n"
                "- One contains only oranges.\n"
                "- One contains both apples and oranges.\n\n"
                "ALL THREE labels are wrong.\n\n"
                "You may take ONE fruit from ONE box (without looking inside first).\n\n"
                "How can you correctly label all three boxes?"
            ),
            examples="",
            starter_code=(
                "Take a fruit from the box labelled 'Apples & Oranges'.\n\n"
                "Since every label is wrong, this box CANNOT be mixed.\n"
                "- If you draw an apple → this box is Apples only.\n"
                "- If you draw an orange → this box is Oranges only.\n\n"
                "Now the remaining two labels are also wrong, so you can deduce the rest by elimination."
            ),
        ),
        Challenge(
            title="The Missing Dollar",
            planet_name="Planet Illusia",
            challenge_type="riddle",
            difficulty="easy",
            points=125,
            coins_reward=13,
            order_index=105,
            description=(
                "Three friends pay $30 for a hotel room ($10 each).\n"
                "The hotel realizes the room costs only $25. An employee returns $5 but keeps $2, "
                "giving each friend $1 back.\n\n"
                "Each friend now paid $9 → together $27. The employee kept $2.\n\n"
                "$27 + $2 = $29.\n\n"
                "Where is the missing dollar?"
            ),
            examples="",
            starter_code=(
                "There is NO missing dollar. The puzzle uses misleading arithmetic.\n\n"
                "The friends paid $27 total:\n"
                "  $25 went to the hotel + $2 kept by the employee = $27. ✓\n\n"
                "You should NOT add the employee's $2 to the $27 — the $2 is already included in $27. "
                "Adding them together is the trick that creates the illusion of a missing dollar."
            ),
        ),
        Challenge(
            title="The Family",
            planet_name="Family Cluster",
            challenge_type="riddle",
            difficulty="easy",
            points=100,
            coins_reward=10,
            order_index=106,
            description=(
                "A family has two parents and six sons.\n"
                "Each son has one sister.\n\n"
                "How many people are in the family?"
            ),
            examples="",
            starter_code=(
                "9 people.\n\n"
                "2 parents + 6 sons + 1 sister = 9.\n\n"
                "The key: 'each son has ONE sister' — they all share the SAME sister, "
                "not one sister each."
            ),
        ),
        Challenge(
            title="The Clock",
            planet_name="Timekeepers World",
            challenge_type="riddle",
            difficulty="easy",
            points=125,
            coins_reward=13,
            order_index=107,
            description=(
                "A clock strikes 6 times in 5 seconds.\n\n"
                "How long will it take to strike 12 times?"
            ),
            examples="",
            starter_code=(
                "11 seconds.\n\n"
                "6 strikes = 5 intervals between them → each interval = 1 second.\n"
                "12 strikes = 11 intervals → 11 seconds.\n\n"
                "The common wrong answer is 10 seconds (just doubling 5), "
                "which forgets that you count the GAPS between strikes, not the strikes themselves."
            ),
        ),
        Challenge(
            title="The Water Jugs",
            planet_name="Measurement Rift",
            challenge_type="riddle",
            difficulty="medium",
            points=200,
            coins_reward=20,
            order_index=108,
            description=(
                "You have:\n"
                "- A 5-litre jug\n"
                "- A 3-litre jug\n\n"
                "Neither jug has measurement markings.\n\n"
                "How can you measure exactly 4 litres of water?"
            ),
            examples="",
            starter_code=(
                "1. Fill the 5L jug.\n"
                "2. Pour from 5L into 3L until 3L is full → 2L remain in 5L jug.\n"
                "3. Empty the 3L jug.\n"
                "4. Pour the 2L into the 3L jug.\n"
                "5. Fill the 5L jug again.\n"
                "6. Pour from 5L into 3L until 3L is full (needs 1L more).\n"
                "7. Exactly 4L remain in the 5L jug. ✓"
            ),
        ),
        Challenge(
            title="The Bridge at Night",
            planet_name="Dark Bridge Sector",
            challenge_type="riddle",
            difficulty="hard",
            points=300,
            coins_reward=30,
            order_index=109,
            description=(
                "Four people must cross a bridge at night. They have ONE flashlight. "
                "Only TWO people can cross at once.\n\n"
                "Crossing times:\n"
                "- Person A: 1 minute\n"
                "- Person B: 2 minutes\n"
                "- Person C: 7 minutes\n"
                "- Person D: 10 minutes\n\n"
                "When two people cross together, they move at the slower person's speed.\n\n"
                "Can everyone cross in exactly 17 minutes? If so, how?"
            ),
            examples="",
            starter_code=(
                "Yes! Total: 17 minutes.\n\n"
                "1. A + B cross → 2 min. (A returns with flashlight → 1 min)\n"
                "2. C + D cross → 10 min. (B returns with flashlight → 2 min)\n"
                "3. A + B cross → 2 min.\n\n"
                "Total: 2 + 1 + 10 + 2 + 2 = 17 minutes ✓"
            ),
        ),
        Challenge(
            title="The Prisoner's Hats",
            planet_name="Logic Nebula Prime",
            challenge_type="riddle",
            difficulty="hard",
            points=350,
            coins_reward=35,
            order_index=110,
            description=(
                "Three people stand in a line. Each wears a black or white hat.\n\n"
                "- The person at the BACK sees the two ahead.\n"
                "- The person in the MIDDLE sees the person in front.\n"
                "- The person in FRONT sees nobody.\n\n"
                "They know at least one hat is white.\n\n"
                "The person at the back says: 'I don't know my hat colour.'\n"
                "The person in the middle says: 'I don't know either.'\n"
                "The person in front says: 'I know my hat colour.'\n\n"
                "What colour is the front person's hat — and how do they know?"
            ),
            examples="",
            starter_code=(
                "The front person's hat is WHITE.\n\n"
                "Reasoning:\n"
                "- Back person sees two hats. They say 'I don't know' → they do NOT see two black hats "
                "(that would mean theirs is white). So at least one of the front two is white.\n"
                "- Middle person hears this and sees the front person's hat. They still say 'I don't know' "
                "→ the front person's hat is NOT black (if it were, the middle person would know theirs is white). "
                "So the front person's hat must be white.\n"
                "- The front person follows this logic and concludes: WHITE."
            ),
        ),
        Challenge(
            title="The Burning Ropes",
            planet_name="Time Warp Zone",
            challenge_type="riddle",
            difficulty="hard",
            points=325,
            coins_reward=33,
            order_index=111,
            description=(
                "You have two ropes. Each rope takes exactly ONE HOUR to burn completely.\n\n"
                "They burn UNEVENLY — half a rope does not necessarily take 30 minutes.\n\n"
                "Using only the ropes and a lighter, how can you measure exactly 45 minutes?"
            ),
            examples="",
            starter_code=(
                "1. At time 0: Light BOTH ends of rope 1, and ONE end of rope 2.\n"
                "2. Rope 1 burns from both ends → it finishes in exactly 30 minutes.\n"
                "3. At the 30-minute mark: Light the OTHER end of rope 2.\n"
                "4. Rope 2 had 30 minutes of burn left. Burning from both ends halves the time → 15 more minutes.\n"
                "5. Rope 2 finishes at the 45-minute mark. ✓"
            ),
        ),
        Challenge(
            title="The Elevator",
            planet_name="Common Sense Station",
            challenge_type="riddle",
            difficulty="easy",
            points=125,
            coins_reward=13,
            order_index=112,
            description=(
                "A short man lives on the 10th floor of a building.\n\n"
                "Every morning, he takes the elevator DOWN to the ground floor.\n\n"
                "When he returns, he takes the elevator to the 7th floor and walks up three floors.\n\n"
                "However, on rainy days, he takes the elevator directly to the 10th floor.\n\n"
                "Why?"
            ),
            examples="",
            starter_code=(
                "He is too short to reach the button for floor 10.\n\n"
                "He can only reach up to the button for floor 7.\n\n"
                "On rainy days, he uses his UMBRELLA to press the floor 10 button."
            ),
        ),
        Challenge(
            title="The Portrait",
            planet_name="Family Tree Rim",
            challenge_type="riddle",
            difficulty="easy",
            points=100,
            coins_reward=10,
            order_index=113,
            description=(
                "A man looks at a portrait and says:\n\n"
                '"Brothers and sisters, I have none. '
                'But this man\'s father is my father\'s son."\n\n'
                "Who is in the portrait?"
            ),
            examples="",
            starter_code=(
                "His SON.\n\n"
                "'My father's son' = the man himself (he has no brothers).\n"
                "So 'this man's father is ME'.\n"
                "Therefore, the person in the portrait is HIS SON."
            ),
        ),
        Challenge(
            title="The Sequence",
            planet_name="Number Sequence Realm",
            challenge_type="riddle",
            difficulty="medium",
            points=175,
            coins_reward=18,
            order_index=114,
            description=(
                "What number comes next in this sequence?\n\n"
                "1, 11, 21, 1211, 111221, ___\n\n"
                "Explain your reasoning."
            ),
            examples="",
            starter_code=(
                "312211\n\n"
                "This is the 'Look and Say' sequence — each number describes the previous one:\n"
                "1        → one 1              → '11'\n"
                "11       → two 1s             → '21'\n"
                "21       → one 2, one 1       → '1211'\n"
                "1211     → one 1, one 2, two 1s → '111221'\n"
                "111221   → three 1s, two 2s, one 1 → '312211'"
            ),
        ),
    ]
    for r in riddles:
        db.add(r)
    db.commit()
    print(f"✅ Seeded {len(riddles)} logic riddles.")


if __name__ == "__main__":
    from database import engine, Base
    import models  # noqa
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    _seed(db)
