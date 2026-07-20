# JustHandled Labs agent skills

Focused, inspectable skills for Claude Code and other agents that read the open `SKILL.md` standard. Each skill handles one repeatable job. Read-only by default; preview before write.

**[Browse all 98 skills](https://justhandledlabs.com/skills/?utm_source=github&utm_medium=repository&utm_campaign=free_skills)** · [Agent-readable catalog](https://justhandledlabs.com/llms.txt) · [About JustHandled Labs](https://justhandledlabs.com/)

## Start with the risk, not the catalog

- Installing community skills? Use the [Skill Injection Scanner](https://justhandledlabs.com/skills/skill-injection-scanner/?utm_source=github&utm_medium=repository&utm_campaign=skill_security) to inspect hidden instructions, obfuscation, secret exfiltration, unsafe commands, and excessive permissions without executing the package.
- Shipping agent-written code? Use the [AI Code Verification Gate](https://justhandledlabs.com/skills/ai-code-verification-gate/?utm_source=github&utm_medium=repository&utm_campaign=code_verification) to require evidence before generated code is accepted.
- Automating a smaller developer chore? Start with one of the 11 free skills below.

## Install

### Claude Code

Add the marketplace once:

```
/plugin marketplace add justhandledlabs/skills
```

Then add the skills you want, for example:

```
/plugin install readme-generator-free@justhandledlabs-skills
```

Or just run `/plugin` to browse and pick.

### Other `SKILL.md` agents

Each portable skill lives at `plugins/<skill-name>/skills/<skill-name>/`. Point your agent's skill installer at that folder, or copy the complete folder into the skills directory documented by your agent. Keep bundled `scripts/` and `references/` files beside `SKILL.md`.

Inspect the source before installation. Skills are instructions with access to whatever tools and permissions you give the agent.

## The skills

| Skill | What it does |
| --- | --- |
| readme-generator-free | Generate a README from your project's actual code. |
| env-doctor-free | Diagnose local environment issues that stop a project from starting. |
| git-commit-writer-free | Write conventional commit messages from your staged changes. |
| env-example-generator | Turn a .env into a shareable .env.example with values stripped. |
| license-picker | Generate a LICENSE file from a chosen license. |
| markdown-table-formatter | Align and normalize messy Markdown tables. |
| robots-sitemap-validator | Check robots.txt and sitemap.xml for crawl-blocking mistakes. |
| todo-fixme-extractor | List every TODO, FIXME, HACK, XXX, and BUG comment in your code. |
| lead-enricher-free | Build a B2B lead profile from a company URL or name. |
| outreach-writer-free | Write a personalized B2B cold email from a lead profile. |
| pipeline-reporter-free | Turn a CRM CSV export into a pipeline report. |

## Paid editions and the full catalog

Several free skills have deeper paid editions. The full catalog contains 98 focused packages across agent security, verification, DevOps, model resilience, handoffs, writing, sales, and creator workflows.

**[Find the skill for your bottleneck](https://justhandledlabs.com/skills/?utm_source=github&utm_medium=repository&utm_campaign=free_skills)**

## License

MIT. See LICENSE.md. The skills here are free to use and adapt.
