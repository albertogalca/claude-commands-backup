#!/usr/bin/env node
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

interface HookInput {
    session_id: string;
    transcript_path: string;
    cwd: string;
    permission_mode: string;
    prompt: string;
}

interface PromptTriggers {
    keywords?: string[];
    intentPatterns?: string[];
}

interface SkillRule {
    type: 'guardrail' | 'domain';
    enforcement: 'block' | 'suggest' | 'warn';
    priority: 'critical' | 'high' | 'medium' | 'low';
    promptTriggers?: PromptTriggers;
}

interface SkillRules {
    version: string;
    skills: Record<string, SkillRule>;
}

interface MatchedSkill {
    name: string;
    matchType: 'keyword' | 'intent';
    config: SkillRule;
}

async function main() {
    try {
        // Read input from stdin
        const input = readFileSync(0, 'utf-8');
        const data: HookInput = JSON.parse(input);
        const prompt = data.prompt.toLowerCase();

        // Load skill rules
        // Try project-specific first, fallback to global ~/.claude
        const homeDir = process.env.HOME || process.env.USERPROFILE || '';
        const globalRulesPath = join(homeDir, '.claude', 'skills', 'skill-rules.json');

        let rulesPath = globalRulesPath;

        // Check for project-specific rules if CLAUDE_PROJECT_DIR is set
        if (process.env.CLAUDE_PROJECT_DIR) {
            const projectRulesPath = join(process.env.CLAUDE_PROJECT_DIR, '.claude', 'skills', 'skill-rules.json');
            if (existsSync(projectRulesPath)) {
                rulesPath = projectRulesPath;
            }
        }

        const rules: SkillRules = JSON.parse(readFileSync(rulesPath, 'utf-8'));

        const matchedSkills: MatchedSkill[] = [];

        // Check each skill for matches
        for (const [skillName, config] of Object.entries(rules.skills)) {
            const triggers = config.promptTriggers;
            if (!triggers) {
                continue;
            }

            // Keyword matching
            if (triggers.keywords) {
                const keywordMatch = triggers.keywords.some(kw =>
                    prompt.includes(kw.toLowerCase())
                );
                if (keywordMatch) {
                    matchedSkills.push({ name: skillName, matchType: 'keyword', config });
                    continue;
                }
            }

            // Intent pattern matching
            if (triggers.intentPatterns) {
                const intentMatch = triggers.intentPatterns.some(pattern => {
                    const regex = new RegExp(pattern, 'i');
                    return regex.test(prompt);
                });
                if (intentMatch) {
                    matchedSkills.push({ name: skillName, matchType: 'intent', config });
                }
            }
        }

        // Only output for blocking skills - suggestions should be silent
        // Claude Code shows hook output as interruptions, so we only notify for critical issues
        const blockingSkills = matchedSkills.filter(s => s.config.enforcement === 'block');

        if (blockingSkills.length > 0) {
            let output = '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';
            output += '🎯 SKILL ACTIVATION REQUIRED\n';
            output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n';

            output += '⚠️ REQUIRED SKILLS (must use before proceeding):\n';
            blockingSkills.forEach(s => output += `  → ${s.name}\n`);
            output += '\n';

            output += 'ACTION: Use Skill tool with the above skill(s) BEFORE responding\n';
            output += '━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n';

            console.log(output);
        }

        // For non-blocking skills, log silently to stderr for debugging (won't interrupt user)
        const suggestedSkills = matchedSkills.filter(s => s.config.enforcement !== 'block');
        if (suggestedSkills.length > 0) {
            const skillNames = suggestedSkills.map(s => s.name).join(', ');
            console.error(`[DEBUG] Suggested skills: ${skillNames}`);
        }

        process.exit(0);
    } catch (err) {
        console.error('Error in skill-activation-prompt hook:', err);
        process.exit(1);
    }
}

main().catch(err => {
    console.error('Uncaught error:', err);
    process.exit(1);
});
