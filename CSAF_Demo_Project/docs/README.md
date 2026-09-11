# Docs

## What this folder contains

Human-facing explanations of the Nozama AI Shopping Assistant: how the system is built, how to present it at a cybersecurity fair, and which features are deliberately left for students.

## Important files

- `ARCHITECTURE.md` — components, trust boundaries, and attack data flow, including Mermaid diagrams.
- `DEMO_GUIDE.md` — numbered presenter script from reset through patched mode.
- `STUDENT_WORK.md` — five reserved tasks with interfaces, acceptance criteria, and official docs links.
- This README — how the documentation set fits the rest of the repo.

Root `README.md` and `TASKS.md` live one directory up so newcomers find setup commands immediately.

## Languages and technologies

These files are Markdown. Diagrams use [Mermaid](https://mermaid.js.org/) so they render on GitHub and in many Markdown previews without a separate drawing tool.

## Why Markdown

The audience is computer-science students and fair volunteers, not a documentation platform. Markdown is diff-friendly in git and does not require a docs generator.

## How this folder connects

Code comments point here (especially `TODO(STUDENT)`). The frontend and backend READMEs link official framework docs; this folder explains *product* behavior: mock vs Gemini, vulnerable vs patched, and what “creating an agent” means (a config + memory space, not training).

## What students should modify

Update `DEMO_GUIDE.md` if you add presenter controls. Extend `STUDENT_WORK.md` when you finish a task so the next teammate knows what is done. Do not copy finished solutions into this folder in a way that replaces the learning; record design choices instead.

## Security considerations

Never paste `GEMINI_API_KEY` values, real emails, or card numbers into docs. Use the fictional customer Alex Rivera and `.invalid` addresses only. When you screenshot X-Ray, check that logs are redacted.

## How to learn more

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
- [Google Gemini API](https://ai.google.dev/gemini-api/docs)
- [OWASP GenAI](https://genai.owasp.org/)
