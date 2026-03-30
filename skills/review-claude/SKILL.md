---
name: review-claude
description: "Instead of manually reading through every file in your setup line by line (which nobody actually does), just tell Claude to audit itself."
---

Read my entire setup before responding. Check my CLAUDE.md, every skill in my skills folder, every file in my context folder, and any other instruction files you can find.
Then go through every rule, instruction, and preference you found. For each one, tell me:

1. Is this something you already do by default without being told?
2. Does this contradict or conflict with another rule somewhere else in my setup?
3. Does this repeat something that's already covered by a different rule or file?
4. Does this read like it was added to fix one specific bad output rather than improve outputs overall?
5. Is this so vague that you'd interpret it differently every time? (ex: "be more natural" or "use a good tone")

   Then give me:

- A list of everything you'd cut, with a one-line reason for each
- A list of any conflicts you found between files
- A cleaned-up version of my CLAUDE.md with the dead weight removed
