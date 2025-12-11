# Semantic Theming - Reference

## Detection Script

Run this to check if a project uses semantic theming:

```bash
#!/bin/bash
# Check for semantic theming indicators

THEMING_DOC="docs/THEMING.md"
ESLINT_RULE="eslint-rules/no-raw-colors.js"
CSS_VARS=$(grep -r "var(--color-" src/ 2>/dev/null | head -1)
ESLINT_CONFIG=$(grep -l "no-raw-colors" eslint.config.* .eslintrc* 2>/dev/null | head -1)

if [[ -f "$THEMING_DOC" || -f "$ESLINT_RULE" || -n "$CSS_VARS" || -n "$ESLINT_CONFIG" ]]; then
  echo "SEMANTIC_THEMING=true"
  [[ -f "$THEMING_DOC" ]] && echo "  - Found: $THEMING_DOC"
  [[ -f "$ESLINT_RULE" ]] && echo "  - Found: $ESLINT_RULE"
  [[ -n "$CSS_VARS" ]] && echo "  - Found: CSS variables"
  [[ -n "$ESLINT_CONFIG" ]] && echo "  - Found: ESLint theming rule"
else
  echo "SEMANTIC_THEMING=false"
  echo "  This project does not appear to use semantic theming."
fi
```

## How Semantic Theming Works

### Layer 1: CSS Custom Properties

Defined in `src/index.css` or similar:

```css
:root {
  /* Semantic color tokens */
  --color-primary: theme('colors.gray.900');
  --color-secondary: theme('colors.gray.500');
  --color-surface: theme('colors.white');
  --color-surface-secondary: theme('colors.gray.100');
  --color-error: theme('colors.red.500');
  --color-success: theme('colors.green.500');
  --color-accent: theme('colors.blue.500');
}

.dark {
  --color-primary: theme('colors.white');
  --color-secondary: theme('colors.gray.400');
  --color-surface: theme('colors.gray.900');
  --color-surface-secondary: theme('colors.gray.800');
}
```

### Layer 2: Tailwind Extension

Defined in `tailwind.config.js`:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: 'var(--color-primary)',
        secondary: 'var(--color-secondary)',
        surface: 'var(--color-surface)',
        'surface-secondary': 'var(--color-surface-secondary)',
        error: 'var(--color-error)',
        success: 'var(--color-success)',
        accent: 'var(--color-accent)',
      }
    }
  }
}
```

### Layer 3: ESLint Enforcement

The `no-raw-colors` rule blocks:

1. **Raw color literals**: `#hex`, `rgb()`, `hsl()`
2. **Non-semantic Tailwind**: `bg-red-500`, `text-white`, etc.

```javascript
// Forbidden color names (Tailwind defaults)
const FORBIDDEN_COLOR_NAMES = [
  'red', 'blue', 'green', 'yellow', 'gray', 'slate', 'zinc',
  'neutral', 'stone', 'orange', 'amber', 'lime', 'emerald',
  'teal', 'cyan', 'sky', 'indigo', 'violet', 'purple',
  'fuchsia', 'pink', 'rose', 'white', 'black'
];

// Checked prefixes
const COLOR_PREFIXES = [
  'bg-', 'text-', 'border-', 'ring-', 'outline-',
  'fill-', 'stroke-', 'divide-', 'placeholder-',
  'from-', 'via-', 'to-', 'shadow-'
];
```

## Benefits

### 1. Theme Consistency
All colors derived from CSS vars = consistent theming across app.

### 2. Dark Mode Support
Change CSS vars in `.dark` class = automatic dark mode everywhere.

### 3. Design System Enforcement
ESLint blocks non-semantic colors at commit = no design drift.

### 4. Refactoring Safety
Change one CSS var = update entire app's color usage.

## Common Mistakes

### Mistake 1: Using Tailwind opacity modifiers with raw colors

```tsx
// WRONG - raw color with opacity
className="bg-red-500/50"

// CORRECT - semantic with opacity
className="bg-error/50"
```

### Mistake 2: Gradient colors

```tsx
// WRONG - raw gradient colors
className="bg-gradient-to-r from-blue-500 to-purple-500"

// CORRECT - semantic gradient (if defined)
className="bg-gradient-to-r from-accent to-primary"

// Or use CSS directly
style={{ background: 'linear-gradient(var(--color-accent), var(--color-primary))' }}
```

### Mistake 3: Hover/Focus states with raw colors

```tsx
// WRONG
className="hover:bg-blue-600 focus:border-blue-500"

// CORRECT
className="hover:bg-accent focus:border-accent"
```

### Mistake 4: Arbitrary values

```tsx
// WRONG - arbitrary color
className="bg-[#ff6b6b]"

// CORRECT - use CSS var or add to theme
className="bg-error" // If matches theme
// Or: Update tailwind.config.js to add semantic token
```

## Extending the Theme

When you need a new semantic color:

1. **Add CSS variable** in `src/index.css`:
   ```css
   :root {
     --color-warning: theme('colors.yellow.500');
   }
   ```

2. **Add to Tailwind** in `tailwind.config.js`:
   ```javascript
   colors: {
     warning: 'var(--color-warning)',
   }
   ```

3. **Use semantically**:
   ```tsx
   className="bg-warning text-warning"
   ```

## Testing Theming

```bash
# Run ESLint to catch violations
npm run lint

# Check specific file
npx eslint src/components/MyComponent.tsx --rule 'wescobar/no-raw-colors: error'
```

## Resources

- Project theming docs: `docs/THEMING.md`
- ESLint rule: `eslint-rules/no-raw-colors.js`
- CSS variables: `src/index.css`
- Tailwind config: `tailwind.config.js`
