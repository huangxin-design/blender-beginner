# Blender 开工助手 · Blender Beginner

**A Codex skill that helps beginners set up Blender, assess references and rendering requirements, and create editable `.blend` projects using everyday language.**

[简体中文](README.md) · [Quick start](docs/quickstart.md) · [Example project](projects/green-desk-lamp/README.md)

![Blender Beginner: from an idea or reference to an editable Blender project](docs/assets/hero.png)

*The cover is AI-generated concept art. The downloadable lamp project and actual Blender renders appear in the example below.*

**v05 / Early Preview.** Describe the result you want, share a reference, or provide an existing project. Codex uses this skill to select the relevant setup, assessment, scripting, and preview checks for that request.

## Install

1. Download this repository using **Code → Download ZIP**, then extract it.
2. Copy the entire `skills/blender-beginner` folder into `$HOME/.agents/skills/` for personal use, or into `.agents/skills/` inside your working project. Keep the `scripts`, `references`, `assets`, and `agents` folders alongside `SKILL.md`.
3. In Codex, ask it to use `$blender-beginner` and describe your task. If the skill is not detected, restart Codex.

These locations follow the [official Codex skill instructions](https://learn.chatgpt.com/docs/build-skills). The [detailed quick start](docs/quickstart.md) is currently in Chinese.

## Start with a request

Once installed, try:

> Set up Blender and put the application and projects in my chosen location. Check for an existing installation first.

> Assess how we could recreate this reference and whether my computer is suitable for a 4K still. Give me an assessment and recommendations before creating anything.

> Open this project and make the lampshade look like matte ceramic. Keep the base and composition unchanged, save a new version, and show me a preview.

## What it helps with

| Your question | How the skill approaches it |
| --- | --- |
| How do I install Blender and organize the files? | Checks the existing environment and prepares the application, configuration, and project locations as requested |
| Can my computer handle 4K or animation? | Inspects the target device and runs bounded scene tests when relevant, with separate conclusions for previews, stills, and animation |
| How feasible is this reference? | Assesses geometry, materials, lighting and camera, asset dependencies, and device budget; explains uncertainties and possible approaches |
| How do I ask for “frosted,” “soft,” or “dreamlike”? | Translates the description into visual goals, scene or node choices, parameter directions, and acceptance criteria |
| Why does the result look too plastic or blurry? | Diagnoses the relevant cause and makes a focused revision while preserving a useful comparison view |
| The file exists—but does it work? | Saves a new project, reopens it independently, checks its structure, renders, and inspects the preview |

Codex turns the brief into Blender objects, materials, lighting, and camera settings through scripts. You can keep describing revisions in everyday language without learning node names first.

## A workflow matched to the request

![Workflow: choose the task, check what matters, preview, revise, verify, and deliver](docs/assets/workflow.png)

- **Explanation or assessment:** returns the analysis and missing information. It does not automatically install software or start rendering.
- **Creation:** resolves information that materially affects the result, starts with an appropriate preview, and develops the scene from there.
- **Revision:** reads your specified latest saved project, reuses applicable setup and assessment evidence, and saves a new version.
- **Conflicting requirements:** keeps the original goal separate from proposed simplifications and identifies the specific blocker.

A reference's **0–100 feasibility score is a reasoned assessment of an approach**, accompanied by evidence, confidence, and expected differences. It is not a reconstruction percentage or success probability. Missing evidence remains unresolved, and unseen parts of an object require explicit assumptions.

## v05: observed usage and render progress

![Local progress panel with illustrative render and token data](docs/assets/progress-panel-v05.png)

*This interface example uses simulated data, not measured usage or render times for the showcased projects.*

Token records cover one explicitly supplied local Codex source from a recorded baseline. Reports distinguish cached input and reasoning output as subsets, pending usage, and untracked sources. They cannot reconstruct usage from old `.blend` files, separate mixed-project turns, merge subagents automatically, or calculate subscription credits or fees.

The local progress page shows the render launched by the runner, without a model call every second. Controlled PNG frame plans enable output counts and a low-confidence ETA range after the first frame plus three further complete frames. Estimates can rise or be withdrawn. Process exit and file presence do not establish visual acceptance. GUI-started renders and video encoding are outside this first version.

See [usage, boundaries, and verification](docs/usage-progress.md) (Chinese). v05 adds boundary tests, actual tiny PNG renders, timeout/failure integration checks, and desktop/mobile browser checks. Real Mac execution and complex animation remain unverified.

## A real material revision

Request: **“Make the shade look like green matte ceramic. Keep the base and composition unchanged.”**

![Actual Blender renders before and after the lampshade material revision](docs/assets/material-comparison.png)

This trial continued from a lamp project with an adjusted camera. Codex read that file, separated the relevant material shared with the base, updated the shade and green cap, then saved, reopened, and rendered the new version.

The recorded checks confirmed preservation of the camera, aspect ratio, geometry, transforms, and other parts within their scope. Both previews were inspected: the shade's concentrated highlights became softer, while the fine surface texture was difficult to see at preview size. The result demonstrates the revision workflow for this particular project.

**[Explore the example and its source files →](projects/green-desk-lamp/README.md)**

To download an individual project, open a version's `scene.blend` on GitHub and choose **Download raw file**. Both versions are also included in the repository ZIP under `projects/green-desk-lamp/versions/`; open the desired `scene.blend` in Blender. The example uses Blender 5.2.1. See the project README for commands that recreate each version from its Python script.

## Projects, source files, and condensed conversations

These are the author's GitHub showcase materials, independent of the installable skill. The three earliest projects come from the September 6, 2026 archive, followed by the lamp revision demo.

![Three early projects: a pink installation, a plush rabbit knight, and floating geometry animation](docs/assets/early-works.jpg)

| Project | Included material |
| --- | --- |
| [Pink installation · early practice](projects/pink-installation/README.md) | Retouched image, editable 3D base, native render, prompts, process summary, and credits |
| [Plush rabbit knight · early practice](projects/plush-rabbit-knight/README.md) | Retouched image, editable fur scene, native render, prompts, and credits |
| [Floating geometry · early practice](projects/floating-geometry-animation/README.md) | 30-second film, five-palette animation project, prompts, process summary, and credits |
| [Green desk lamp · v001 / v002](projects/green-desk-lamp/README.md) | Versioned `.blend` files, scripts, previews, briefs, and a [production recap](projects/green-desk-lamp/conversation.md) |

The two early stills received generative image edits that were not written back to their `.blend` files. Their six-round prompts are retrospective rewrites. These works document early practice, not validation of the current Skill. See the [project index](projects/README.md) for downloads and source details.

Repository maintainers can use the [project archive convention](docs/project-archive.md) when preparing showcase materials. Ordinary use of the skill does not require this process.

A project's `conversation.md` connects key requests, revisions, and feedback to the corresponding versions. The [conversation guide](docs/conversation-archive.md) explains how to distinguish direct excerpts from summaries and preserve meaningful failed attempts. The lamp example is a retrospective recap based on its version records; no original chat excerpts are included.

## Support and verification

| Area | Current status |
| --- | --- |
| Automated Windows installation | Windows x64 and Blender 5.2 series in a separate directory; an existing usable installation is preferred |
| Windows creation and verification | Actual execution and the lamp example verified with Blender 5.2.1 |
| Mac device assessment | Paths for Intel / Apple Silicon, unified memory, and Metal are implemented; testing on a real Mac is pending |
| Linux | A complete installation and production verification record is not yet available |
| 4K / animation | Assessed for the target scene and settings; a simple still does not establish the cost or stability of a complex animation |

v04 completed **14 execution checks, 5 text-only decision trials, and 1 independent project revision trial**. Interruption handling was checked through simulation. These are limited development checks and do not establish quality across arbitrary references.

Process completion, project structure, and the rendered preview are checked separately. The basic inspector covers a subset of static-scene issues. Visual quality, topology, 3D printing, and complex animation require checks suited to the intended use. The time-limited runner controls the Blender process it launches; it does not fully sandbox arbitrary scripts.

## Repository layout

```text
skills/blender-beginner/
  SKILL.md            # Skill entry point for Codex
  agents/             # Skill display metadata
  references/         # Assessment, production, feedback, and acceptance guides
  scripts/            # Installation, inspection, bounded execution, and checks
  assets/             # Starter lamp scene template
docs/                 # Getting started and visual assets
projects/             # Work, editable sources, and condensed conversations
templates/            # Version brief and conversation templates
```

The skill uses local Blender scripts and file delivery. A live MCP connection can be added when needed; this repository does not preconfigure one.

See the [quick start](docs/quickstart.md) to install it, or read the [skill instructions](skills/blender-beginner/SKILL.md) for the full workflow.
