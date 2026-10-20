import assert from "node:assert/strict";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { ESLint } from "eslint";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const eslint = new ESLint({ cwd: root, overrideConfigFile: path.join(root, "configs/eslint.mjs") });
const cases = [
    ["short guard", "export function f(x) { if (x) return 1; return 0; }", false],
    ["optional braces", "export function f(x) { if (x) { return 1; } else return 0; }", false],
    ["body on next line", "export function f(x) { if (x)\nreturn 1; return 0; }", true],
    ["multiline condition", "export function f(x) { if (\nx\n) return 1; return 0; }", true],
    [
        "long clause",
        'export function f(x) { if (x) return "' + "x".repeat(110) + '"; return 0; }',
        true,
    ],
    ["mixed chain", "export function f(x) { if (x) { x++; return x; } else return 0; }", true],
    [
        "chain with wrapped condition",
        "export function f(x) { if (x) return 1; else if (\nx > 1\n) return 2; else return 0; }",
        true,
    ],
    ["all braced chain", "export function f(x) { if (x) { return 1; } else { return 0; } }", false],
    ["short loop", "export function f(x) { while (x > 0) x--; return x; }", false],
    ["wrapped loop", "export function f(x) { while (\nx > 0\n) x--; return x; }", true],
    ["short do loop", "export function f(x) { do x--; while (x > 0); return x; }", false],
    ["wrapped do tail", "export function f(x) { do x--; while (\nx > 0\n); return x; }", true],
    [
        "braced long literal",
        'export function f(x) { if (x) { return "' + "x".repeat(110) + '"; } return 0; }',
        false,
    ],
];
const results = [];
for (const [name, code, rejected] of cases) {
    const [result] = await eslint.lintText(code, { filePath: "fixtures/case.js" });
    assert.equal(result.fatalErrorCount, 0, name);
    const messages = result.messages.filter((message) => message.ruleId === "peios/braces");
    assert.equal(messages.length > 0, rejected, name + ": " + JSON.stringify(result.messages));
    results.push({ name, passed: true });
}

for (const [name, code, rule, rejected] of [
    [
        "explicit any",
        "export function f(x: any): unknown { return x; }",
        "@typescript-eslint/no-explicit-any",
        true,
    ],
    [
        "narrow explained suppression",
        "// eslint-disable-next-line @typescript-eslint/no-explicit-any -- adapter to untyped input\nexport function f(x: any): unknown { return x; }",
        "@typescript-eslint/no-explicit-any",
        false,
    ],
    [
        "unused suppression",
        "// eslint-disable-next-line @typescript-eslint/no-explicit-any -- obsolete exception\nexport function f(x: number): number { return x; }",
        null,
        true,
    ],
]) {
    const [result] = await eslint.lintText(code, { filePath: "fixtures/case.ts" });
    const messages = result.messages.filter((message) => message.ruleId === rule);
    assert.equal(messages.length > 0, rejected, name + ": " + JSON.stringify(result.messages));
    results.push({ name, passed: true });
}

for (const folder of ["vendor", "generated"]) {
    assert.equal(await eslint.isPathIgnored(path.join(root, folder, "bad.ts")), true);
    results.push({ name: folder + " excluded", passed: true });
}

const largeFunction =
    "export function count(x) {\nlet total = 0;\n" +
    "total += 1;\n".repeat(55) +
    "if (x) { if (x > 1) { if (x > 2) { if (x > 3) { total += x; } } } }\nreturn total;\n}";
const [largeResult] = await eslint.lintText(largeFunction, { filePath: "fixtures/large.js" });
assert.equal(largeResult.errorCount, 0, JSON.stringify(largeResult.messages));
results.push({ name: "size and nesting thresholds remain review prompts", passed: true });
process.stdout.write(JSON.stringify(results, null, 4) + "\n");
