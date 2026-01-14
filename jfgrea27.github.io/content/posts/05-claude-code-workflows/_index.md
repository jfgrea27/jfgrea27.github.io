---
title: "Claude Code: Lessons from the Trenches"
author: "James"
date: "2026-01-14"
summary: "A practical guide to Claude Code through 8 progressive exercises - from basic prompting to MCPs and context management."
hideBackToTop: true
tags: ["claude-code", "ai", "developer-tools"]
draft: false
hideHeader: true
math: false
---

[Claude Code](https://code.claude.com/) is Anthropic's CLI tool for AI-assisted software development. After working through a series of hands-on exercises, I've compiled the key lessons learned at each stage. All the code referenced here is from my [claude-exercises](https://github.com/jfgrea27/claude-exercises) repository.

> **Note:** The code blocks showing Claude Code output contain ASCII box-drawing characters (┌─┬─┐) that render as tables in the terminal but may appear misaligned in your browser.

This article walks through 8 exercises, each building on the previous, covering:

- [00 - Basic Usage](#00---basic-usage): Simple prompting
- [01 - CLAUDE.md](#01---claudemd): Project context and workflows
- [02 - Plan Mode](#02---plan-mode): Planning before implementing
- [03 - Subagents](#03---subagents): Specialized AI workflows
- [04 - Skills](#04---skills): Domain knowledge without new context
- [05 - MCPs](#05---mcps): Extending Claude with external tools
- [06 - Third-Party MCPs](#06---third-party-mcps): Jira integration example
- [07 - Context Management](#07---context-management): Managing long sessions

---

## 00 - Basic Usage

The simplest way to use Claude Code is just prompting it directly:

```sh
claude
```

Then provide your request:

```txt
Add more logging to books_api
- info for starting/ending of requests.
- debug for any db interaction
```

Claude Code explores the codebase, understands the structure, and makes the changes. The output confirms what was done:

```
Done. I've added logging to the books_api:

  Info logging for requests (routes.py):
  - All endpoints now log "request started" at the beginning
  - All endpoints log "request completed" at the end

  Debug logging for DB interactions (db/books.py):
  - get_all_books: logs query start and number of books retrieved
  - get_book_by_id: logs query and whether book was found
  - create_book: logs the data being created and the resulting book id
```

### Lesson Learned

**Without configuration, Claude Code completes the task but skips quality checks.** The formatting was off and it didn't run tests. The feature works, but you're left manually verifying everything passed. This leads us to exercise 01.

---

## 01 - CLAUDE.md

Claude Code reads `CLAUDE.md` files to understand project context, tools, and workflows. From the [best practices guide](https://www.anthropic.com/engineering/claude-code-best-practices), this file tells Claude what commands to run and when.

Here's a minimal example:

```md
# books-api

- Run `just typecheck` after making changes
- Run `just fmt` to format code
- These can be run without asking permission
```

Running the same logging task now produces:

```
I can see the logger is already set up. I'll add the logging statements.
...
Now I'll run typecheck and format as per the project instructions.
...
Bash(just typecheck)
Bash(just fmt)
...
Done. Typecheck passed and code was formatted.
```

### Lesson Learned

**CLAUDE.md turns Claude Code from a code writer into a workflow executor.** It automatically runs your linting, formatting, and type checking. Keep the file succinct though - it's part of the context window, and verbose instructions consume tokens you'll need for actual work.

---

## 02 - Plan Mode

For larger changes, ask Claude Code to create a plan before implementing:

```txt
Add a PATCH books endpoint.
Update the README.md, .http file, tests and src
Create a plan for the changes above and ask me to approve it before making the changes.
```

Claude enters plan mode and outputs a structured proposal:

```
PATCH /books/{book_id} Implementation Plan

Files to modify (6 total):
┌─────────────────┬─────────────────────────────────────────────────────────────┐
│      File       │                           Change                            │
├─────────────────┼─────────────────────────────────────────────────────────────┤
│ schemas.py      │ Add BookUpdate model with all optional fields               │
│ routes.py       │ Add PATCH endpoint using existing update_book() db function │
│ README.md       │ Document the new endpoint                                   │
│ .http           │ Add PATCH request examples                                  │
│ test_routes.py  │ Add TestPatchBook class with 4 test cases                   │
│ test_schemas.py │ Add tests for BookUpdate schema                             │
└─────────────────┴─────────────────────────────────────────────────────────────┘

Key details:
- Uses existing update_book() function from db layer
- Returns 404 if book not found
- Returns the updated book as BookResponse
```

After approval, Claude executes the plan and verifies: 49 tests passed, typecheck passed, code formatted.

### Lesson Learned

**Plans serve two purposes: alignment and context management.** First, you review the approach before Claude writes code. Second, if your session runs out of context, you can start fresh and paste the plan as a reference. This is especially useful for features touching many files.

---

## 03 - Subagents

Subagents are specialized AI agents for task-specific workflows. Create one with `/agent`:

```sh
/agent
```

Define its purpose:

```txt
You are an expert bug fixer that uses TDD approach: write test, fix bug, see test pass.
```

Claude saves this as a markdown file (e.g., `.claude/agents/bug-fixer-tdd.md`). When you report a bug:

```txt
There is a bug in the code, I see two times the same book title in the database.
```

Claude Code recognizes the bug-fixer agent is relevant and invokes it:

```
I'll use the bug-fixer-tdd agent to investigate and fix the duplicate books issue.
...
bug-fixer-tdd(Fix duplicate books bug)
...
The bug has been fixed:

  Problem: The Book model had no unique constraint on the title field.

  Fix: Added unique=True to the title column in models/books.py:10:
  title: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)

  Test added: test_cannot_create_duplicate_book_with_same_title verifies
  that attempting to create a duplicate book now raises IntegrityError.

  All 50 tests pass, typecheck passes, and formatting is correct.
```

### Lesson Learned

**Subagents create a fresh context for specialized workflows.** The TDD agent follows a specific pattern: understand bug → write failing test → implement fix → see test pass. This is different from skills (exercise 04) which provide knowledge without creating new context. Use subagents when the workflow itself is specialized.

---

## 04 - Skills

Skills provide domain knowledge that loads only when relevant. Unlike subagents, they don't create a new context - they inject knowledge into the current session.

Create a skill at `.claude/skills/project-structure.md`:

```md
# Project Structure

When creating new REST resources, follow this structure:

./books-api/src/books_api
./http/MODEL/routes # REST API endpoints
./http/MODEL/schemas # Request/Response schemas
./models/MODEL # Pydantic models
./db/MODEL.py # Database operations

Mirror this structure in the test directory.
```

Now when you ask:

```txt
Can you create the CRUD operations for users, borrowings.
Users can borrow books.
```

Claude reads the skill and creates both resources following your established patterns:

```
Users (/users)
- Model: models/users.py - User with id, name, email fields
- DB operations: db/users.py - CRUD functions
- HTTP endpoints: GET, POST, PATCH, DELETE

Borrowings (/borrowings)
- Model: models/borrowings.py - Borrowing with user_id, book_id, timestamps
- DB operations: db/borrowings.py - CRUD + return_book function
- HTTP endpoints: full CRUD + POST /borrowings/{id}/return

Tests created following existing patterns. Typecheck and formatting passed.
```

### Lesson Learned

**Skills are lightweight knowledge injection; subagents are heavy workflow delegation.** Use skills when you want Claude to follow patterns consistently. Use subagents when the task requires a completely different approach (like TDD). Skills stay in your current context window; subagents spawn a fresh one.

---

## 05 - MCPs

[Model Context Protocol (MCP)](https://modelcontextprotocol.io/) servers extend Claude Code with external tools and data sources.

The `books-mcp` server exposes three tools:

- `get_books` - Get all available books
- `get_book_by_id` - Get a specific book by ID
- `search_books` - Search books by title or author

Configure it in `.mcp.json`:

```json
{
  "mcpServers": {
    "books": {
      "type": "sse",
      "url": "http://localhost:8080/sse"
    }
  }
}
```

Start the MCP server (`just mcp`), then restart Claude Code. Now you can query:

```txt
What books are available in the books-mcp?
Can you add them to our books-api?
Can you then use the api to list the books?
```

Claude discovers and uses the MCP tools:

```
I found 5 books in the books-mcp:
┌───────────────────────────────────┬────────────────────────┬──────┐
│             Title                 │         Author         │ Year │
├───────────────────────────────────┼────────────────────────┼──────┤
│ To Kill a Mockingbird             │ Harper Lee             │ 1960 │
│ 1984                              │ George Orwell          │ 1949 │
│ Pride and Prejudice               │ Jane Austen            │ 1813 │
│ The Great Gatsby                  │ F. Scott Fitzgerald    │ 1925 │
│ One Hundred Years of Solitude     │ Gabriel Garcia Marquez │ 1967 │
└───────────────────────────────────┴────────────────────────┴──────┘

Done. I:
1. Queried the books-mcp using the MCP tool and found 5 books
2. Added all 5 books to the books-api via POST requests
3. Listed the books from the API - all 5 books are now available
```

### Lesson Learned

**MCPs turn Claude Code into a universal integration layer.** Instead of manually querying systems and copy-pasting data, Claude can interact with external tools directly. The MCP provides both context (data to read) and actions (operations to perform).

---

## 06 - Third-Party MCPs

Beyond local MCPs, you can integrate third-party services. [Atlassian Rovo](https://www.atlassian.com/platform/remote-mcp-server) connects Claude Code to Jira.

Given a Jira epic "Add book type" with linked tasks:

- DEV-5: Update db schema of books to include book_type
- DEV-6: Update REST endpoints for books to include book_type

Prompt Claude:

```txt
Can you implement ticket DEV-4.
- Create a branch dev-4
- For each task in the epic:
  - Create a commit with implementation
```

Claude fetches the epic from Jira, creates a plan, and executes:

```
I found the epic. DEV-4: Add book type requires:
- Adding a book type field (fiction, non_fiction, unknown)
- Maintaining 80% code coverage

Found 2 tasks:
1. DEV-5: Update db schema (use enums)
2. DEV-6: Update REST endpoints (default to unknown)
```

The resulting git log:

```
commit f5902a4 (HEAD -> dev-4)
    DEV-6: Update REST endpoints for books to include book_type
    Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>

commit 8e60b64
    DEV-5: Update db schema of books to include book_type
    Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### Lesson Learned

**Third-party MCPs close the loop between ticket and implementation.** Claude reads the requirements from Jira, plans the implementation, creates appropriately-scoped commits, and references the ticket IDs. For larger epics, consider using subagents per task to keep each context focused.

---

## 07 - Context Management

Long sessions consume context. Use `/context` to inspect:

```
Context Usage
claude-opus-4-5-20251101 · 27k/200k tokens (13%)

⛁ System prompt:    3.0k tokens (1.5%)
⛁ System tools:    17.4k tokens (8.7%)
⛁ Custom agents:     391 tokens (0.2%)
⛁ Memory files:       80 tokens (0.0%)
⛁ Skills:            686 tokens (0.3%)
⛁ Messages:         5.2k tokens (2.6%)
⛶ Free space:       128k (64.1%)
⛝ Autocompact:     45.0k tokens (22.5%)
```

Key components:

| Component          | Description                             | Configuration         |
| :----------------- | :-------------------------------------- | :-------------------- |
| System prompt      | Anthropic's core instructions           | Fixed                 |
| System tools       | Built-in tools (Bash, Read, Edit, etc.) | Add custom via MCP    |
| Custom agents      | Your subagent definitions               | `.claude/agents/*.md` |
| Memory files       | Your CLAUDE.md files                    | `./CLAUDE.md`         |
| Skills             | Skill definitions                       | `.claude/skills/*.md` |
| Messages           | Conversation history                    | `/clear` to reset     |
| Autocompact buffer | Triggers automatic summarization        | Managed automatically |

Useful commands:

- `/resume` - Pick up a previous session
- `/clear` - Reset conversation, keep configuration
- `/compact` - Summarize conversation to free tokens

### Lesson Learned

**Context is a finite resource - manage it proactively.** The breakdown shows what's consuming tokens. If messages grow large, use `/compact` or `/clear`. For multi-feature sessions, consider using plans (exercise 02) that you can reference in a fresh context. The autocompact buffer triggers automatic summarization before you hit limits.

---

## Summary

<div style="display: flex; justify-content: center;">

| Exercise | Feature          | Key Takeaway                                               |
| :------- | :--------------- | :--------------------------------------------------------- |
| 00       | Basic prompting  | Works, but no quality checks                               |
| 01       | CLAUDE.md        | Automates linting, formatting, testing                     |
| 02       | Plan mode        | Align before implementing, save plans for context recovery |
| 03       | Subagents        | Fresh context for specialized workflows                    |
| 04       | Skills           | Knowledge injection without context switch                 |
| 05       | Local MCPs       | Extend Claude with custom tools                            |
| 06       | Third-party MCPs | Integrate external systems like Jira                       |
| 07       | Context          | Monitor usage, use /resume, /clear, /compact               |

</div>

The progression is intentional: start simple, add project configuration, then layer in specialized agents and external integrations. Each exercise builds on the previous, and together they form a practical toolkit for AI-assisted development.
