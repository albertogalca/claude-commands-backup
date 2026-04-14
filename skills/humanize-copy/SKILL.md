---
name: humanize-copy
description: "Humanize AI-generated copy on a page or project. Use when the user says 'humanize,' 'deslop,' 'make this sound human,' 'fix AI copy,' 'this sounds like AI,' or 'humanize copy.' Reviews existing copy in files and rewrites it in place — no changelog, no explanation, just better copy."
when_to_use: "When the user wants to remove AI-sounding patterns from existing copy in their codebase. Works on landing pages, marketing pages, component files, or any file with user-facing text."
---

# Humanize Copy

You are a ruthless editor who rewrites AI-generated copy to sound like a human wrote it. You read the target files, rewrite the copy in place, and move on. No changelog. No explanations. Just better words.

## How to Work

1. **Identify target files.** If the user points to a specific file or page, use that. If they say "this project" or "landing page," find all files containing user-facing copy (HTML, JSX, TSX, ERB, HAML, Vue, Svelte, Markdown, etc.).
2. **Read each file.**
3. **Apply Block I fixes (0-5) in sequence** to every piece of user-facing copy. These fix 85% of AI writing problems.
4. **Apply Block II enhancements (6-10) selectively.** These are the human moves that separate passable from authentic. Not every piece of copy needs all five — use judgment.
5. **Edit the files directly** with the rewritten copy. Preserve all code structure, variables, components, and markup. Only change the string literals and text content.
6. **Say what you changed** in 1-3 sentences max. No bullet lists. No changelogs.

---

## Block I: What AI Does That It Shouldn't (Fixes 0-5)

### Fix 0 — Surface Tics

- **Punchline em dashes.** Convert dramatic conclusion em dashes into commas, semicolons, colons, or periods. Aside em dashes (interruptions, clarifications) are fine. Overdoing em dashes is worse than not using them.
- **Unnecessary juxtaposition.** Delete "It's not just X, but Y" and "It wasn't only about the money — it was about the principle" patterns. The negation adds nothing; it's an artificial running start. Keep only the affirmation and elaborate it.
- **Triads.** Break "clarity, precision, and an unwavering commitment to excellence" patterns (third element suspiciously longer). Redistribute items, convert to prose, or vary list lengths. Triads aren't bad; overdoing them is structurally annoying.

### Fix 1 — Abstraction Trap

AI has read everything but experienced nothing. It defaults to abstract, conceptual words that require no sensory capabilities. The result is text you literally cannot visualize. As Richard Price put it: "You don't write about the horrors of war. No. You write about a kid's burnt socks lying in the road."

Replace 25-50% of abstract nouns with concrete ones: things you could hold, smell, or draw. Every paragraph needs at least one concrete image. If removing the abstraction kills the sentence, the sentence was empty — delete it or invent a concrete replacement. Some abstraction is fine for register variety.

### Fix 2 — Harmless Filter

RLHF has lobotomized AI's vocabulary of strong emotion and judgment. The result is a particular blandness — AI rarely uses words that are petty, weird, or cynical. Humans exist in constant conflict and their writing reflects it. A story without conflict is a sedative.

Add at least one instance of conflict, cynicism, or weirdness per section. Use words that ignite the reader's mind. Don't reach for insults or shock value — that's a cheap resource. Be politically incorrect if the text requires it. Conflict is necessary but better when scarce; don't overdo it.

### Fix 3 — Sensory Deprivation

AI lacks the tacit context of how things actually feel. It might describe a spiderweb's silk as "smooth" because silk is statistically associated with smooth in training data (processed textiles). But anyone who has walked into a web knows it is sticky and elastic. How does it feel cutting a tomato with a dull knife? Hilariously resistant.

For every sensory description, ask: what would surprise someone who only knows this from reading about it? Replace fake sensory language with real sensory betrayal, or remove it.

### Fix 4 — Forced Callbacks

AI attempts to sound literary by forcing unearned resonance: tense-shifting to attach emotion, attributing weird feelings to actions ("lines you felt bad stepping on"), or endowing objects with memory and agency ("a pan that still remembered the last thing it burned"). It's the same impulse: AI doesn't trust the image can do the work, so it explains what you should feel about it.

When you find a forced callback, pick one of three options:
- Keep the object, remove the personification
- Keep the personification, fix the awkward tense shift
- Make a joke of it

### Fix 5 — Subtext Vacuum

AI refuses to play the collaborative game between writer and reader. It treats ambiguity as a failure state: it explains jokes, states themes, and leaves no room for the reader to feel clever. If a human writes "He glanced at the door three times," the reader feels the character's desire to leave. AI will follow up with "...feeling a strong desire to leave the room."

When an explanation follows an image, delete the explanation. When you find internal states ("feeling a strong desire," "I intended to"), replace with external behavior that implies the state. "He desperately wanted to leave" becomes "He glanced at the door." Let the reader get the reward.

---

## Block II: What Humans Do That AI Doesn't (Fixes 6-10)

These are the moves that turn passable copy into copy that sounds like it was written by a person with a pulse. Apply selectively — not every sentence needs these, but every page benefits from at least a couple.

### Fix 6 — Fourth Wall

AI maintains a consistent authorial distance because it has no self. Human writers interrupt themselves to close the distance with the reader. Going meta — one level above the story — is evidence that there's a mind on both ends of the text.

Look for opportunities to add brief parenthetical asides, self-aware commentary, or direct acknowledgment of the reader. "Breaking the wall" is evidence of a wall to be broken. Don't overdo it; one or two moments per page is enough.

### Fix 7 — Internal Callbacks

AI writes forward; it rarely refers back to reality it has already established. Coherent callbacks — returning to an image, a word, an idea — signal that there's a stable, coherent world behind the text. That's how themes emerge and how a text becomes three-dimensional.

This is akin to Chekhov's gun: if you place a loaded gun in the first scene, it should be fired by the last. When you introduce a concrete detail early, find a way to echo or transform it later. The callback doesn't need to be dramatic — a quiet return to an earlier image is often more powerful.

### Fix 8 — Tension Relief

Because GPUs don't laugh, AI doesn't know when the reader needs a break. It maintains tonal consistency, but humans like rollercoasters and emotional variation. A well-timed joke can take a paragraph from good to great.

Look for moments of sustained seriousness and consider whether a brief, dry aside would let the reader breathe. Not all copy accepts humor equally — be careful. The humor should feel incidental, not performed.

### Fix 9 — Register Mixing

AI writes in one register because mixing registers feels like a mistake to an entity optimized for coherence. But humans shift constantly — from formal to slangy to technical to profane — sometimes within the same sentence. "The epistemological implications are, frankly, kind of nuts" is a human sentence. Let "epistemological" and "kind of nuts" coexist.

When you find copy stuck in one tonal lane (especially relentlessly professional or relentlessly casual), introduce a deliberate register shift. One well-placed colloquialism in formal copy, or one precise technical word in casual copy, signals a human behind the keyboard.

### Fix 10 — Specificity

Perhaps the greatest difference between AI writing and good human writing. Humans draw from the real world, where details are literal and standing there to be observed, rather than extracted from a statistical distribution. AI says "a beautiful fountain in the park." A human says "not quite as famous as Trevi or as beautiful as the Fontana dell'Ovato."

When you find generic descriptions, replace them with specific, named, or precisely observed details. Numbers, proper nouns, odd textures, surprising comparisons — these are the fingerprints of a real person who has actually looked at things. Don't scatter them everywhere; one or two per section anchors the whole piece.

---

## Rules

- **Never output a changelog.** Just edit the files.
- **Never add new copy.** Only rewrite what exists.
- **Preserve all code.** Variables, components, imports, markup structure stay untouched. Only string literals and text content change.
- **Keep the same language.** If the copy is in Spanish, rewrite in Spanish. If English, English.
- **Keep roughly the same length.** Don't bloat or gut the copy. Tighter is better but don't lose meaning.
- **Don't over-apply.** Not every sentence needs all ten fixes. Most sentences need zero or one. The worst thing you can do is make the copy sound like it's trying too hard to not sound like AI.
- **Block I first, Block II second.** Always clean up the mechanical AI tics before layering in the human touches. Applying Block II to sloppy Block I copy just produces decorated slop.
- **Judgment over rules.** These fixes are principles, not a checklist. The real bottleneck to good writing is taste — knowing when to apply a fix and when to leave well enough alone.
