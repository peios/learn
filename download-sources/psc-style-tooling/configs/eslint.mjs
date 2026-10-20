import tseslint from "typescript-eslint";

import peios from "../scripts/eslint-peios.mjs";

const ignored = [
    "**/node_modules/**",
    "**/.venv/**",
    "**/vendor/**",
    "**/generated/**",
    "**/build/**",
    "**/dist/**",
];

export default [
    { ignores: ignored },
    {
        files: ["**/*.{js,mjs,cjs,ts,tsx}"],
        plugins: { peios },
        linterOptions: { reportUnusedDisableDirectives: "error" },
        rules: {
            "peios/braces": "error",
            "no-dupe-args": "error",
            "no-duplicate-case": "error",
            "no-unreachable": "error",
            "no-unused-vars": "error",
            "prefer-const": "error",
        },
    },
    {
        files: ["**/*.{ts,tsx}"],
        languageOptions: { parser: tseslint.parser },
        plugins: { "@typescript-eslint": tseslint.plugin },
        rules: {
            "no-unused-vars": "off",
            "@typescript-eslint/no-unused-vars": "error",
            "@typescript-eslint/no-explicit-any": "error",
        },
    },
];
