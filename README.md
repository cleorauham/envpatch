# envpatch

> Utility to diff and safely merge `.env` files across environments

---

## Installation

```bash
pip install envpatch
```

Or with [pipx](https://pypa.github.io/pipx/):

```bash
pipx install envpatch
```

---

## Usage

**Diff two `.env` files:**

```bash
envpatch diff .env.example .env.local
```

**Merge missing keys from a source file into a target:**

```bash
envpatch merge .env.example .env.local --output .env.local
```

**Preview changes without writing (dry run):**

```bash
envpatch merge .env.example .env.local --dry-run
```

Example output:

```
+ DB_HOST=localhost       # added from source
~ API_KEY=***             # already present, skipped
- DEBUG=true              # only in target
```

---

## Features

- Safe merge — never overwrites existing values by default
- Clear, colorized diff output
- Supports comments and blank lines in `.env` files
- `--force` flag to override existing keys when needed

---

## License

MIT © [envpatch contributors](https://github.com/yourname/envpatch)