"""
Ultra Humanizer v2
The most comprehensive human behavior simulation system.
Every single action looks like it came from a real person.
"""

import random
import asyncio
import math
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class PersonalityType(Enum):
    """Different human personality archetypes that affect behavior."""
    FAST_TYPER = "fast_typer"         # Types fast, shorter breaks
    SLOW_CAREFUL = "slow_careful"     # Types slow, reads everything
    DISTRACTED = "distracted"        # Gets distracted often, long random pauses
    METHODICAL = "methodical"        # Consistent pace, thorough
    IMPATIENT = "impatient"          # Rushes, makes typos
    CASUAL = "casual"                # Average everything


class MoodState(Enum):
    """Human mood changes throughout the day, affects behavior."""
    ENERGETIC = "energetic"      # Morning, fast actions
    FOCUSED = "focused"          # Mid-morning, efficient
    SLUGGISH = "sluggish"        # After lunch, slow
    PRODUCTIVE = "productive"    # Afternoon, moderate
    TIRED = "tired"              # Evening, slow and error-prone
    DROWSY = "drowsy"            # Late night, very slow


@dataclass
class HumanProfile:
    """A simulated human profile with consistent personality traits."""
    personality: PersonalityType
    base_typing_wpm: float          # Words per minute
    base_reading_wpm: float         # Reading speed
    attention_span: float           # 0-1 how easily distracted
    error_rate: float               # 0-1 how many mistakes
    break_tendency: float           # 0-1 how often they take breaks
    punctuation_habit: float        # 0-1 how consistent with punctuation
    capitalization_style: str       # "proper", "lowercase", "mixed"
    emoji_usage: float              # 0-1 how often they add emojis
    verbosity: float                # 0-1 how long their messages are
    
    # Behavioral quirks
    double_space_rate: float = 0.03
    missing_period_rate: float = 0.1
    autocorrect_artifact_rate: float = 0.02
    
    @classmethod
    def generate_random(cls) -> 'HumanProfile':
        """Generate a random but consistent human profile."""
        personality = random.choice(list(PersonalityType))
        
        profiles = {
            PersonalityType.FAST_TYPER: {
                "base_typing_wpm": random.uniform(55, 80),
                "base_reading_wpm": random.uniform(280, 400),
                "attention_span": random.uniform(0.6, 0.8),
                "error_rate": random.uniform(0.08, 0.15),
                "break_tendency": random.uniform(0.02, 0.05),
                "punctuation_habit": random.uniform(0.5, 0.7),
                "capitalization_style": random.choice(["proper", "mixed"]),
                "emoji_usage": random.uniform(0.0, 0.15),
                "verbosity": random.uniform(0.3, 0.6),
            },
            PersonalityType.SLOW_CAREFUL: {
                "base_typing_wpm": random.uniform(20, 35),
                "base_reading_wpm": random.uniform(180, 250),
                "attention_span": random.uniform(0.85, 0.95),
                "error_rate": random.uniform(0.01, 0.04),
                "break_tendency": random.uniform(0.05, 0.1),
                "punctuation_habit": random.uniform(0.85, 0.98),
                "capitalization_style": "proper",
                "emoji_usage": random.uniform(0.0, 0.05),
                "verbosity": random.uniform(0.6, 0.9),
            },
            PersonalityType.DISTRACTED: {
                "base_typing_wpm": random.uniform(30, 50),
                "base_reading_wpm": random.uniform(200, 300),
                "attention_span": random.uniform(0.2, 0.45),
                "error_rate": random.uniform(0.05, 0.1),
                "break_tendency": random.uniform(0.1, 0.2),
                "punctuation_habit": random.uniform(0.4, 0.7),
                "capitalization_style": random.choice(["mixed", "lowercase"]),
                "emoji_usage": random.uniform(0.05, 0.2),
                "verbosity": random.uniform(0.3, 0.7),
            },
            PersonalityType.METHODICAL: {
                "base_typing_wpm": random.uniform(35, 50),
                "base_reading_wpm": random.uniform(220, 300),
                "attention_span": random.uniform(0.8, 0.95),
                "error_rate": random.uniform(0.02, 0.05),
                "break_tendency": random.uniform(0.04, 0.08),
                "punctuation_habit": random.uniform(0.9, 1.0),
                "capitalization_style": "proper",
                "emoji_usage": random.uniform(0.0, 0.03),
                "verbosity": random.uniform(0.7, 1.0),
            },
            PersonalityType.IMPATIENT: {
                "base_typing_wpm": random.uniform(50, 70),
                "base_reading_wpm": random.uniform(300, 450),
                "attention_span": random.uniform(0.4, 0.6),
                "error_rate": random.uniform(0.1, 0.2),
                "break_tendency": random.uniform(0.01, 0.04),
                "punctuation_habit": random.uniform(0.3, 0.5),
                "capitalization_style": random.choice(["lowercase", "mixed"]),
                "emoji_usage": random.uniform(0.0, 0.1),
                "verbosity": random.uniform(0.2, 0.4),
            },
            PersonalityType.CASUAL: {
                "base_typing_wpm": random.uniform(35, 55),
                "base_reading_wpm": random.uniform(230, 320),
                "attention_span": random.uniform(0.5, 0.7),
                "error_rate": random.uniform(0.03, 0.08),
                "break_tendency": random.uniform(0.04, 0.08),
                "punctuation_habit": random.uniform(0.6, 0.85),
                "capitalization_style": random.choice(["proper", "mixed", "lowercase"]),
                "emoji_usage": random.uniform(0.02, 0.12),
                "verbosity": random.uniform(0.4, 0.7),
            },
        }
        
        traits = profiles[personality]
        return cls(personality=personality, **traits)


# ==================== MESSAGE TEMPLATES ====================

REPORT_TEMPLATES = {
    "spam": {
        "openers": [
            "This account is sending unsolicited spam messages to multiple users.",
            "Receiving unwanted promotional content from this user repeatedly.",
            "This user is spamming my inbox with promotional messages.",
            "Account sending mass spam messages, please review.",
            "Continuous spam from this account, disrupting my experience.",
            "This account keeps sending spam advertisements.",
            "Unwanted bulk messages from this user.",
            "Spamming users with promotional content without consent.",
            "This is a spam account sending mass messages.",
            "Receiving repeated spam from this account, very annoying.",
            "I keep getting spam from this account every day.",
            "This user sends nothing but spam links.",
            "Mass messaging spam bot account.",
            "This account is part of a spam ring.",
            "Non-stop promotional spam from this user.",
        ],
        "context": [
            "They have sent me messages multiple times this week.",
            "I've seen other people complain about this account too.",
            "The messages contain suspicious links.",
            "They promote fake products and services.",
            "I keep blocking them but they find new ways to message.",
            "The spam contains misleading information.",
            "Many users in my group have reported the same issue.",
        ],
    },
    "scam": {
        "openers": [
            "This account is running a scam operation.",
            "Fraudulent account trying to scam users.",
            "This user is attempting to defraud people.",
            "Scam account asking for money/crypto.",
            "This is a fraud account running scams.",
            "Account engaging in fraudulent activities.",
            "This user tried to scam me out of money.",
            "Running fake investment/giveaway scams.",
            "Fraudulent scheme being promoted by this account.",
            "This account is part of a scam network.",
            "Fake crypto investment scam from this user.",
            "They tried to trick me into sending them money.",
            "This is a phishing account pretending to be legit.",
            "Romance scam operator targeting vulnerable people.",
            "Advance fee fraud attempt by this account.",
        ],
        "context": [
            "They promised guaranteed returns on investment.",
            "They asked me to send cryptocurrency to a wallet.",
            "They impersonated a well-known company.",
            "Multiple people in my contacts have been targeted.",
            "They use fake testimonials to build trust.",
            "The payment links lead to phishing sites.",
            "They pressure victims to act quickly before thinking.",
        ],
    },
    "fake": {
        "openers": [
            "This account is impersonating someone else.",
            "Fake account pretending to be a real person/organization.",
            "This is a fake profile using stolen photos.",
            "Account is impersonating a public figure.",
            "Fraudulent account using false identity.",
            "This user is pretending to be someone they're not.",
            "Fake account created for deception.",
            "Identity theft - using someone else's photos and name.",
            "This account is a fake impersonation.",
            "Impersonator account deceiving users.",
            "Stolen identity being used by this account.",
            "This is not the real person they claim to be.",
            "Catfish account using someone else's identity.",
            "Fake brand account mimicking a real business.",
            "This account falsely claims to be official.",
        ],
        "context": [
            "The real person has confirmed this is not their account.",
            "The profile photos are taken from another social media.",
            "They are using this fake identity to scam people.",
            "The name and photos don't match any real person.",
            "This account was created recently and looks suspicious.",
            "They copy content from the real account to seem legitimate.",
        ],
    },
    "violence": {
        "openers": [
            "This account is sharing violent and dangerous content.",
            "Posting content that promotes violence.",
            "Sharing threatening and violent material.",
            "This user is posting dangerous violent content.",
            "Account promoting violence and harmful behavior.",
            "Violent content being shared by this account.",
            "This account posts content inciting violence.",
            "Sharing material that threatens safety.",
            "Dangerous content promoting harm to others.",
            "This user shares violent and threatening posts.",
            "Graphic violence being distributed by this account.",
            "Threats of physical harm from this user.",
            "This account glorifies and promotes violence.",
            "Disturbing violent content being shared publicly.",
        ],
        "context": [
            "The content is extremely graphic and disturbing.",
            "They have been sending threats to other users.",
            "This type of content can inspire real-world harm.",
            "Children could potentially see this content.",
            "The threats seem specific and credible.",
            "Multiple users have expressed concern about safety.",
        ],
    },
    "pornography": {
        "openers": [
            "This account is sharing inappropriate adult content.",
            "Posting pornographic material publicly.",
            "Adult content being shared without proper restrictions.",
            "This user is distributing NSFW content.",
            "Inappropriate sexual content from this account.",
            "Account sharing explicit material in public groups.",
            "Pornographic content being posted openly.",
            "This account posts adult material to minors.",
            "NSFW content shared without any warning.",
            "Explicit content from this user in public channels.",
        ],
        "context": [
            "This content is visible to underage users.",
            "The material is being shared in family-friendly groups.",
            "No age verification or content warning is provided.",
            "The content was sent unsolicited to my account.",
        ],
    },
    "child_abuse": {
        "openers": [
            "This account contains content that exploits minors.",
            "CSAM content detected on this account.",
            "This account is sharing content involving minors.",
            "Urgent: child exploitation material found.",
            "This account must be investigated immediately for child safety.",
        ],
        "context": [
            "This needs immediate action to protect children.",
            "Please escalate this to the relevant authorities.",
            "The content clearly involves underage individuals.",
        ],
    },
    "illegal_drugs": {
        "openers": [
            "This account is promoting illegal drugs.",
            "Selling illegal substances through this platform.",
            "Drug-related content being openly shared.",
            "This user is advertising drugs for sale.",
            "Account involved in drug promotion and sales.",
            "Illegal drug marketplace being operated.",
            "Promoting controlled substances illegally.",
            "This account is a drug dealer operating openly.",
        ],
        "context": [
            "They are openly listing prices and quantities.",
            "The account provides delivery services for drugs.",
            "Multiple drug types are being advertised.",
            "They use code words but it's clearly drug sales.",
        ],
    },
    "copyright": {
        "openers": [
            "This account is sharing copyrighted content without permission.",
            "Copyright infringement by this account.",
            "Unauthorized distribution of copyrighted material.",
            "This user is pirating copyrighted content.",
            "Intellectual property theft by this account.",
        ],
        "context": [
            "The content belongs to a known creator/company.",
            "No permission or license has been obtained.",
            "The original creator has not authorized this distribution.",
        ],
    },
    "personal_details": {
        "openers": [
            "This account is sharing private personal information.",
            "Doxxing - sharing someone's personal details without consent.",
            "Private information being posted publicly.",
            "This user is leaking personal data.",
            "Unauthorized sharing of private information.",
        ],
        "context": [
            "Home addresses and phone numbers are being shared.",
            "The person did not consent to this information being public.",
            "This puts real people in danger.",
        ],
    },
    "other": {
        "openers": [
            "This account is violating community guidelines.",
            "Please review this account for policy violations.",
            "This user's behavior violates the terms of service.",
            "Account engaging in inappropriate behavior.",
            "Multiple violations from this account.",
            "This account needs to be reviewed for violations.",
            "Violating platform policies repeatedly.",
            "This user is breaking the rules consistently.",
        ],
        "context": [
            "I've reported this before but the behavior continues.",
            "Other users have also noticed the violations.",
            "The behavior is getting worse over time.",
        ],
    },
}

# Filler phrases
PREFIXES = [
    "", "", "",  # Most common: no prefix
    "Hello, ",
    "Hi, ",
    "Please help, ",
    "I need to report that ",
    "I'm reporting because ",
    "This is urgent: ",
    "Please review: ",
    "Reporting this account - ",
    "I'd like to report: ",
    "Attention needed: ",
]

SUFFIXES = [
    "", "", "", "",  # Most common: no suffix
    " Thank you for reviewing.",
    " Please take action.",
    " This needs attention.",
    " I appreciate your help.",
    " Please investigate.",
    " Thank you.",
    " Looking forward to action being taken.",
    " I hope this gets resolved quickly.",
    " Thanks for keeping the platform safe.",
    " Please handle this as soon as possible.",
]

CONNECTORS = [
    " ", " Also, ", " Additionally, ", " Furthermore, ",
    " Moreover, ", " On top of that, ", " To add, ",
    "\n\n", "\n", " — ",
]


class Humanizer:
    """
    Ultra Humanizer v2 - Makes every action indistinguishable from a real human.
    
    Features:
    - Personality-based behavior (each session gets a unique "person")
    - Mood changes throughout the day
    - Reading time calculation based on content length
    - Typing speed variation with micro-pauses
    - Distraction events (random long pauses)
    - Natural error injection (typos, missing punctuation)
    - Message construction with personality influence
    - Time-of-day behavioral adaptation
    """
    
    def __init__(self):
        self._last_action_time: Optional[float] = None
        self._action_count: int = 0
        self._profile: Optional[HumanProfile] = None
        self._mood: MoodState = MoodState.FOCUSED
        self._session_start: Optional[float] = None
        self._distraction_history: List[float] = []
    
    def reset(self):
        """Reset state and generate a new personality for the session."""
        self._action_count = 0
        self._last_action_time = None
        self._profile = HumanProfile.generate_random()
        self._session_start = datetime.now().timestamp()
        self._distraction_history = []
        self._update_mood()
        
        print(f"🧠 Humanizer v2 initialized:")
        print(f"   Personality: {self._profile.personality.value}")
        print(f"   Typing: {self._profile.base_typing_wpm:.0f} WPM")
        print(f"   Attention: {self._profile.attention_span:.0%}")
        print(f"   Error rate: {self._profile.error_rate:.1%}")
        print(f"   Mood: {self._mood.value}")
    
    def _ensure_profile(self):
        """Ensure a profile exists."""
        if not self._profile:
            self.reset()
    
    def _update_mood(self):
        """Update mood based on time of day."""
        hour = datetime.now().hour
        
        if 6 <= hour < 9:
            self._mood = MoodState.ENERGETIC
        elif 9 <= hour < 12:
            self._mood = MoodState.FOCUSED
        elif 12 <= hour < 14:
            self._mood = MoodState.SLUGGISH
        elif 14 <= hour < 17:
            self._mood = MoodState.PRODUCTIVE
        elif 17 <= hour < 22:
            self._mood = MoodState.TIRED
        else:
            self._mood = MoodState.DROWSY
    
    def _get_mood_multiplier(self) -> float:
        """Get speed multiplier based on current mood."""
        multipliers = {
            MoodState.ENERGETIC: random.uniform(0.7, 0.9),
            MoodState.FOCUSED: random.uniform(0.8, 1.0),
            MoodState.SLUGGISH: random.uniform(1.2, 1.6),
            MoodState.PRODUCTIVE: random.uniform(0.9, 1.1),
            MoodState.TIRED: random.uniform(1.3, 1.8),
            MoodState.DROWSY: random.uniform(1.5, 2.5),
        }
        return multipliers.get(self._mood, 1.0)
    
    # ==================== MESSAGE GENERATION ====================
    
    def get_message_for_reason(self, reason: str, custom_message: str = "") -> str:
        """
        Generate a uniquely human report message.
        Combines templates with custom text, personality influence, and natural errors.
        """
        self._ensure_profile()
        profile = self._profile
        
        templates = REPORT_TEMPLATES.get(reason, REPORT_TEMPLATES["other"])
        
        parts = []
        
        # Prefix (personality-dependent probability)
        prefix_chance = 0.3 if profile.verbosity > 0.5 else 0.15
        if random.random() < prefix_chance:
            prefix = random.choice(PREFIXES)
            if prefix:
                parts.append(prefix)
        
        # Main opener
        opener = random.choice(templates["openers"])
        parts.append(opener)
        
        # Custom message integration
        if custom_message and custom_message.strip():
            connector = random.choice(CONNECTORS)
            custom = custom_message.strip()
            
            # Apply personality-based modifications to custom text
            if profile.capitalization_style == "lowercase" and random.random() < 0.5:
                custom = custom.lower()
            
            if not custom.endswith(('.', '!', '?')) and random.random() < profile.punctuation_habit:
                custom += '.'
            
            parts.append(connector)
            parts.append(custom)
        
        # Context (based on verbosity)
        context_chance = 0.2 + profile.verbosity * 0.4
        if random.random() < context_chance and templates.get("context"):
            connector = random.choice(CONNECTORS[:5])
            context = random.choice(templates["context"])
            parts.append(connector)
            parts.append(context)
        
        # Sometimes add a second context (verbose people)
        if profile.verbosity > 0.7 and random.random() < 0.2 and templates.get("context"):
            remaining = [c for c in templates["context"] if c not in parts]
            if remaining:
                parts.append(" ")
                parts.append(random.choice(remaining))
        
        # Suffix
        suffix_chance = 0.25 + profile.verbosity * 0.2
        if random.random() < suffix_chance:
            suffix = random.choice(SUFFIXES)
            if suffix:
                parts.append(suffix)
        
        message = "".join(parts)
        
        # Apply human imperfections
        message = self._apply_human_errors(message)
        
        # Ensure under 4000 chars
        if len(message) > 4000:
            message = message[:3997] + "..."
        
        return message
    
    def _apply_human_errors(self, text: str) -> str:
        """Apply realistic human typing errors to text."""
        self._ensure_profile()
        profile = self._profile
        
        # Double space (common mobile typo)
        if random.random() < profile.double_space_rate:
            words = text.split(' ')
            if len(words) > 3:
                idx = random.randint(1, len(words) - 2)
                words[idx] = words[idx] + ' '
                text = ' '.join(words)
        
        # Missing final period
        if random.random() < profile.missing_period_rate and text.endswith('.'):
            text = text[:-1]
        
        # Capitalize first letter inconsistently
        if profile.capitalization_style == "lowercase" and random.random() < 0.3:
            text = text[0].lower() + text[1:] if text else text
        elif profile.capitalization_style == "mixed" and random.random() < 0.2:
            text = text[0].lower() + text[1:] if text else text
        
        # Autocorrect artifacts (common on mobile)
        if random.random() < profile.autocorrect_artifact_rate:
            # Simulate autocorrect changing a word slightly
            autocorrect_pairs = [
                ("the", "thr"), ("and", "abd"), ("with", "wuth"),
                ("this", "thus"), ("that", "thst"), ("from", "form"),
                ("have", "gave"), ("they", "then"), ("been", "bean"),
            ]
            pair = random.choice(autocorrect_pairs)
            if pair[0] in text.lower():
                # Sometimes the autocorrect error stays, sometimes it gets fixed
                if random.random() < 0.4:
                    text = text.replace(pair[0], pair[1], 1)
        
        # Extra comma or period (fat finger)
        if random.random() < 0.02:
            words = text.split()
            if len(words) > 4:
                idx = random.randint(2, len(words) - 2)
                words[idx] = words[idx] + ","
                text = " ".join(words)
        
        return text
    
    # ==================== TIMING SIMULATION ====================
    
    async def simulate_typing(self, text_length: int) -> float:
        """
        Simulate realistic typing with micro-pauses.
        Accounts for personality, mood, and text complexity.
        """
        self._ensure_profile()
        profile = self._profile
        
        # Base typing speed (chars per second)
        wpm = profile.base_typing_wpm * (1.0 / self._get_mood_multiplier())
        cps = (wpm * 5) / 60  # chars per second
        
        # Add variation per "burst" (humans type in bursts)
        total_time = 0.0
        remaining = text_length
        
        while remaining > 0:
            # Burst length (5-20 chars)
            burst = min(remaining, random.randint(5, 20))
            burst_time = burst / cps
            
            # Burst speed variation
            burst_time *= random.uniform(0.7, 1.3)
            
            total_time += burst_time
            remaining -= burst
            
            # Micro-pause between bursts (thinking, reading what they typed)
            if remaining > 0:
                pause = random.uniform(0.1, 0.8)
                
                # Sometimes longer pause (thinking about next word)
                if random.random() < 0.15:
                    pause += random.uniform(0.5, 2.0)
                
                total_time += pause
        
        # Add correction time (backspace + retype)
        corrections = int(text_length * profile.error_rate * random.uniform(0.5, 1.5))
        correction_time = corrections * random.uniform(0.3, 0.7)
        total_time += correction_time
        
        # Mood adjustment
        total_time *= self._get_mood_multiplier()
        
        # Don't actually wait the full typing time (simulate background typing)
        actual_wait = total_time * random.uniform(0.3, 0.5)
        actual_wait = min(actual_wait, 30.0)  # Cap at 30 seconds
        
        await asyncio.sleep(actual_wait)
        return actual_wait
    
    async def simulate_reading(self, content_length: int) -> float:
        """
        Simulate reading content with comprehension pauses.
        """
        self._ensure_profile()
        profile = self._profile
        
        word_count = content_length / 5
        wpm = profile.base_reading_wpm * (1.0 / self._get_mood_multiplier())
        
        reading_time = (word_count / wpm) * 60
        
        # Add comprehension pauses
        pause_count = max(1, int(word_count / random.randint(30, 80)))
        for _ in range(pause_count):
            reading_time += random.uniform(0.3, 1.5)
        
        # Sometimes re-read (humans do this)
        if random.random() < 0.1:
            reading_time *= random.uniform(1.2, 1.5)
        
        # Mood and attention adjustment
        reading_time *= self._get_mood_multiplier()
        
        # Distracted people read slower
        if profile.attention_span < 0.5:
            reading_time *= random.uniform(1.1, 1.4)
        
        reading_time = max(0.5, min(reading_time, 20.0))
        
        await asyncio.sleep(reading_time)
        return reading_time
    
    # ==================== DELAY SIMULATION ====================
    
    async def human_delay(
        self,
        min_seconds: float = 2.0,
        max_seconds: float = 8.0,
        action_type: str = "report",
    ) -> float:
        """
        Generate and wait for a personality-and-mood-aware delay.
        """
        self._ensure_profile()
        self._update_mood()
        profile = self._profile
        
        # Base delay
        base = random.uniform(min_seconds, max_seconds)
        
        # Mood modifier
        base *= self._get_mood_multiplier()
        
        # Fatigue
        self._action_count += 1
        if self._action_count > 10:
            fatigue = min(self._action_count / 40, 0.6)
            base *= (1 + fatigue)
        
        # Personality modifier
        if profile.personality == PersonalityType.IMPATIENT:
            base *= random.uniform(0.6, 0.85)
        elif profile.personality == PersonalityType.SLOW_CAREFUL:
            base *= random.uniform(1.2, 1.5)
        elif profile.personality == PersonalityType.DISTRACTED:
            base *= random.uniform(0.8, 1.3)
        
        # Distraction event (random long pause)
        if random.random() < (1 - profile.attention_span) * 0.15:
            distraction = random.uniform(5, 25)
            base += distraction
            self._distraction_history.append(distraction)
            print(f"   💭 Got distracted for {distraction:.1f}s")
        
        # Jitter
        jitter = random.uniform(-base * 0.2, base * 0.3)
        base += jitter
        
        # Floor
        base = max(1.0, base)
        
        self._last_action_time = datetime.now().timestamp()
        
        await asyncio.sleep(base)
        return base
    
    # ==================== BREAK SIMULATION ====================
    
    def should_take_break(self) -> bool:
        """Determine if the human would take a break now."""
        self._ensure_profile()
        
        # Base probability from personality
        base_prob = self._profile.break_tendency
        
        # Increase with fatigue
        if self._action_count > 15:
            base_prob += 0.1
        if self._action_count > 25:
            base_prob += 0.15
        
        # Mood-based
        if self._mood in [MoodState.SLUGGISH, MoodState.TIRED, MoodState.DROWSY]:
            base_prob += 0.05
        
        return random.random() < base_prob
    
    async def take_break(self):
        """Simulate a human break."""
        self._ensure_profile()
        
        # Break types
        break_type = random.choices(
            ["micro", "short", "medium", "long"],
            weights=[40, 30, 20, 10],
        )[0]
        
        durations = {
            "micro": (3, 10),
            "short": (10, 30),
            "medium": (30, 90),
            "long": (60, 180),
        }
        
        duration = random.uniform(*durations[break_type])
        
        # Mood affects break length
        duration *= self._get_mood_multiplier()
        
        emoji = {"micro": "💨", "short": "☕", "medium": "🚶", "long": "😴"}
        print(f"   {emoji[break_type]} {break_type.capitalize()} break: {duration:.0f}s")
        
        await asyncio.sleep(duration)
        
        # Break reduces fatigue
        reduction = {"micro": 2, "short": 5, "medium": 10, "long": 20}
        self._action_count = max(0, self._action_count - reduction[break_type])
        
        return duration
    
    def should_skip_action(self, base_probability: float = 0.02) -> bool:
        """Human-like skip decision."""
        self._ensure_profile()
        
        # Distracted people skip more
        prob = base_probability
        if self._profile.attention_span < 0.5:
            prob *= 1.5
        if self._mood in [MoodState.TIRED, MoodState.DROWSY]:
            prob *= 1.3
        
        return random.random() < prob
    
    # ==================== UTILITY ====================
    
    def shuffle_with_bias(self, items: List, keep_some_order: bool = True) -> List:
        """Shuffle items but maintain some original order (human-like)."""
        if len(items) <= 2:
            return items.copy()
        
        items = items.copy()
        
        if keep_some_order:
            n = len(items)
            chunk_size = max(2, n // 3)
            
            for i in range(0, n, chunk_size):
                chunk = items[i:i + chunk_size]
                random.shuffle(chunk)
                items[i:i + chunk_size] = chunk
        else:
            random.shuffle(items)
        
        return items
    
    def get_session_config(self) -> dict:
        """Get randomized session config influenced by personality."""
        self._ensure_profile()
        
        base = {
            "delay_min": random.uniform(2.5, 4.5),
            "delay_max": random.uniform(6.0, 12.0),
            "batch_size": random.randint(3, 8),
            "break_after": random.randint(8, 20),
            "skip_probability": random.uniform(0.01, 0.04),
        }
        
        # Personality adjustments
        if self._profile.personality == PersonalityType.IMPATIENT:
            base["delay_min"] *= 0.7
            base["delay_max"] *= 0.7
        elif self._profile.personality == PersonalityType.SLOW_CAREFUL:
            base["delay_min"] *= 1.3
            base["delay_max"] *= 1.4
        
        return base
    
    def get_profile_info(self) -> Dict[str, Any]:
        """Get current personality info."""
        self._ensure_profile()
        return {
            "personality": self._profile.personality.value,
            "typing_wpm": round(self._profile.base_typing_wpm),
            "reading_wpm": round(self._profile.base_reading_wpm),
            "attention_span": round(self._profile.attention_span, 2),
            "error_rate": round(self._profile.error_rate, 3),
            "mood": self._mood.value,
            "actions_done": self._action_count,
            "distractions": len(self._distraction_history),
        }


# Global instance
humanizer = Humanizer()
