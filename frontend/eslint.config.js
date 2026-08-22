import tseslint from 'typescript-eslint'
import reactHooks from 'eslint-plugin-react-hooks'

/*
 * Deliberately minimal: the project's two style rules plus the react hooks
 * rules. Formatting itself is Prettier's job (see .prettierrc); both run
 * from the pre-commit hook (tools/git-hooks/pre-commit) via lint-staged.
 */
export default tseslint.config({
  files: ['src/**/*.{ts,tsx}'],
  languageOptions: {
    parser: tseslint.parser,
  },
  plugins: {
    'react-hooks': reactHooks,
  },
  rules: {
    /* every if/else/loop body gets braces (auto-fixed; Prettier then
     * expands the block onto its own lines) */
    curly: ['error', 'all'],
    /* a ternary inside a ternary cannot be auto-fixed — the commit is
     * blocked and the condition has to be rewritten by hand */
    'no-nested-ternary': 'error',
    /* a conditional hook call is always a bug */
    'react-hooks/rules-of-hooks': 'error',
    /* a warning, not an error: several effects here are deliberately
     * mount-only (boot, url-derived credentials) and carry an explicit
     * eslint-disable with the reason. Erroring would block every commit
     * touching those files instead of flagging new omissions. */
    'react-hooks/exhaustive-deps': 'warn',
  },
})
