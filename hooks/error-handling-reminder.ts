#!/usr/bin/env node
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

interface HookInput {
    session_id: string;
    transcript_path: string;
    cwd: string;
    permission_mode: string;
    hook_event_name: string;
}

interface EditedFile {
    path: string;
    tool: string;
    timestamp: string;
}

interface SessionTracking {
    edited_files: EditedFile[];
}

function getFileCategory(filePath: string): 'backend' | 'frontend' | 'database' | 'other' {
    // Frontend detection (React/Inertia components)
    if (filePath.includes('/frontend/') ||
        filePath.includes('/client/') ||
        filePath.includes('/src/components/') ||
        filePath.includes('/src/features/') ||
        filePath.includes('/resources/js/') ||
        filePath.includes('/resources/ts/')) return 'frontend';

    // Backend detection - Laravel specific
    if (filePath.includes('/app/Http/Controllers/') ||
        filePath.includes('/app/Services/') ||
        filePath.includes('/app/Actions/') ||
        filePath.includes('/app/Models/') ||
        filePath.includes('/routes/')) return 'backend';

    // Backend detection - Node/general
    if (filePath.includes('/src/controllers/') ||
        filePath.includes('/src/services/') ||
        filePath.includes('/src/routes/') ||
        filePath.includes('/src/api/') ||
        filePath.includes('/server/')) return 'backend';

    // Database detection
    if (filePath.includes('/database/') ||
        filePath.includes('/prisma/') ||
        filePath.includes('/migrations/')) return 'database';

    return 'other';
}

function shouldCheckErrorHandling(filePath: string): boolean {
    // Skip test files, config files, and type definitions
    if (filePath.match(/\.(test|spec)\.(ts|tsx|php)$/)) return false;
    if (filePath.match(/Test\.php$/)) return false;
    if (filePath.match(/\.(config|d)\.(ts|tsx)$/)) return false;
    if (filePath.includes('types/')) return false;
    if (filePath.includes('.styles.ts')) return false;

    // Skip Laravel config and blade views
    if (filePath.includes('/config/') && filePath.endsWith('.php')) return false;
    if (filePath.match(/\.blade\.php$/)) return false;

    // Check for code files (JS/TS and PHP)
    return filePath.match(/\.(ts|tsx|js|jsx|php)$/) !== null;
}

function analyzeFileContent(filePath: string): {
    hasTryCatch: boolean;
    hasAsync: boolean;
    hasPrisma: boolean;
    hasController: boolean;
    hasApiCall: boolean;
    hasEloquent: boolean;
    hasLaravelController: boolean;
    hasInertiaResponse: boolean;
} {
    if (!existsSync(filePath)) {
        return {
            hasTryCatch: false,
            hasAsync: false,
            hasPrisma: false,
            hasController: false,
            hasApiCall: false,
            hasEloquent: false,
            hasLaravelController: false,
            hasInertiaResponse: false
        };
    }

    const content = readFileSync(filePath, 'utf-8');
    const isPHP = filePath.endsWith('.php');

    return {
        // JS/TS patterns
        hasTryCatch: isPHP ? /try\s*\{/.test(content) : /try\s*\{/.test(content),
        hasAsync: /async\s+/.test(content),
        hasPrisma: /prisma\.|PrismaService|findMany|findUnique|create\(|update\(|delete\(/i.test(content),
        hasController: /export class.*Controller|router\.|app\.(get|post|put|delete|patch)/.test(content),
        hasApiCall: /fetch\(|axios\.|apiClient\.|router\.(get|post|put|delete|patch)/i.test(content),

        // PHP/Laravel patterns
        hasEloquent: isPHP && /::find|::create|::update|::delete|->save\(\)|->delete\(\)|DB::|Model::/i.test(content),
        hasLaravelController: isPHP && /extends Controller|public function (index|show|store|update|destroy)/.test(content),
        hasInertiaResponse: isPHP && /Inertia::render|inertia\(/i.test(content),
    };
}

async function main() {
    try {
        // Read input from stdin
        const input = readFileSync(0, 'utf-8');
        const data: HookInput = JSON.parse(input);

        const { session_id } = data;
        const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();

        // Check for edited files tracking
        const cacheDir = join(process.env.HOME || '/root', '.claude', 'tsc-cache', session_id);
        const trackingFile = join(cacheDir, 'edited-files.log');

        if (!existsSync(trackingFile)) {
            // No files edited this session, no reminder needed
            process.exit(0);
        }

        // Read tracking data
        const trackingContent = readFileSync(trackingFile, 'utf-8');
        const editedFiles = trackingContent
            .trim()
            .split('\n')
            .filter(line => line.length > 0)
            .map(line => {
                const [timestamp, tool, path] = line.split('\t');
                return { timestamp, tool, path };
            });

        if (editedFiles.length === 0) {
            process.exit(0);
        }

        // Categorize files
        const categories = {
            backend: [] as string[],
            frontend: [] as string[],
            database: [] as string[],
            other: [] as string[],
        };

        const analysisResults: Array<{
            path: string;
            category: string;
            analysis: ReturnType<typeof analyzeFileContent>;
        }> = [];

        for (const file of editedFiles) {
            if (!shouldCheckErrorHandling(file.path)) continue;

            const category = getFileCategory(file.path);
            categories[category].push(file.path);

            const analysis = analyzeFileContent(file.path);
            analysisResults.push({ path: file.path, category, analysis });
        }

        // Check if any code that needs error handling was written
        const needsAttention = analysisResults.some(
            ({ analysis }) =>
                analysis.hasTryCatch ||
                analysis.hasAsync ||
                analysis.hasPrisma ||
                analysis.hasController ||
                analysis.hasApiCall ||
                analysis.hasEloquent ||
                analysis.hasLaravelController ||
                analysis.hasInertiaResponse
        );

        if (!needsAttention) {
            // No risky code patterns detected, skip reminder
            process.exit(0);
        }

        // Display reminder
        console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('📋 ERROR HANDLING SELF-CHECK');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

        // Backend reminders
        if (categories.backend.length > 0) {
            const backendFiles = analysisResults.filter(f => f.category === 'backend');
            const hasTryCatch = backendFiles.some(f => f.analysis.hasTryCatch);
            const hasPrisma = backendFiles.some(f => f.analysis.hasPrisma);
            const hasController = backendFiles.some(f => f.analysis.hasController);
            const hasEloquent = backendFiles.some(f => f.analysis.hasEloquent);
            const hasLaravelController = backendFiles.some(f => f.analysis.hasLaravelController);
            const hasInertiaResponse = backendFiles.some(f => f.analysis.hasInertiaResponse);

            console.log('⚠️  Backend Changes Detected');
            console.log(`   ${categories.backend.length} file(s) edited\n`);

            // Laravel-specific reminders
            if (hasEloquent) {
                console.log('   ❓ Are Eloquent operations wrapped in try-catch?');
                console.log('   ❓ Are database errors handled gracefully?');
            }
            if (hasLaravelController) {
                console.log('   ❓ Do controllers return proper error responses?');
                console.log('   ❓ Are validation errors handled?');
            }
            if (hasInertiaResponse) {
                console.log('   ❓ Do Inertia responses handle errors properly?');
                console.log('   ❓ Are error messages passed to the frontend?');
            }

            // Node/TypeScript reminders
            if (hasTryCatch && !hasEloquent) {
                console.log('   ❓ Did you add Sentry.captureException() in catch blocks?');
            }
            if (hasPrisma) {
                console.log('   ❓ Are Prisma operations wrapped in error handling?');
            }
            if (hasController && !hasLaravelController) {
                console.log('   ❓ Do controllers use BaseController.handleError()?');
            }

            console.log('\n   💡 Backend Best Practice:');
            if (hasEloquent || hasLaravelController) {
                console.log('      - Use try-catch for database operations');
                console.log('      - Return proper HTTP status codes (422, 500, etc.)');
                console.log('      - Use Laravel\'s exception handler for logging');
                console.log('      - Pass validation errors to Inertia responses\n');
            } else {
                console.log('      - All errors should be captured to Sentry');
                console.log('      - Use appropriate error helpers for context');
                console.log('      - Controllers should extend BaseController\n');
            }
        }

        // Frontend reminders
        if (categories.frontend.length > 0) {
            const frontendFiles = analysisResults.filter(f => f.category === 'frontend');
            const hasApiCall = frontendFiles.some(f => f.analysis.hasApiCall);
            const hasTryCatch = frontendFiles.some(f => f.analysis.hasTryCatch);

            console.log('💡 Frontend Changes Detected');
            console.log(`   ${categories.frontend.length} file(s) edited\n`);

            if (hasApiCall) {
                console.log('   ❓ Do API calls show user-friendly error messages?');
                console.log('   ❓ Are Inertia form errors displayed properly?');
            }
            if (hasTryCatch) {
                console.log('   ❓ Are errors displayed to the user?');
            }

            console.log('\n   💡 Frontend Best Practice (React + Inertia):');
            console.log('      - Use Inertia\'s error prop for form validation errors');
            console.log('      - Display toast/notifications for user feedback');
            console.log('      - Error boundaries for component errors');
            console.log('      - Handle async errors from router.get/post/put\n');
        }

        // Database reminders
        if (categories.database.length > 0) {
            console.log('🗄️  Database Changes Detected');
            console.log(`   ${categories.database.length} file(s) edited\n`);
            console.log('   ❓ Did you verify column names against schema?');
            console.log('   ❓ Are migrations tested?\n');
        }

        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        console.log('💡 TIP: Disable with SKIP_ERROR_REMINDER=1');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');

        process.exit(0);
    } catch (err) {
        // Silently fail - this is just a reminder, not critical
        process.exit(0);
    }
}

main().catch(() => process.exit(0));
