---
name: generate
description: >-
  House writing style for plain-language documentation that a non-technical
  reader — an executive, a CEO, a new joiner, a content editor — can fully
  understand without knowing how to code. Turns any prompt output or draft into
  a clear, well-structured, jargon-free doc. Use ONLY when the user explicitly
  invokes /non-tech-content:generate, or explicitly asks to write, generate, rewrite, or
  "make understandable" a doc, guide, README, explainer, or answer in this
  non-technical / plain-language / "so a CEO can read it" style. Project- and
  stack-agnostic — do not auto-apply to normal doc or code requests.
---

# non-tech-content

Write (or rewrite) so a smart person who does **not** know the tech can read
it once and act on it. The test: *would a busy CEO understand this without
asking a follow-up?* If not, it isn't done.

Works two ways:
1. **Generate** — produce a new doc from a request in this style.
2. **Rewrite** — take an existing prompt output / draft and re-express it in
   this style, keeping every fact, changing only the words and shape.

This skill is about *how* to write, not *what* the project is. It carries no
project, stack, or tool names of its own. Learn the subject from the codebase,
the user, or the draft you're given, then write it in plain language.

---

## Step 0 — before writing, know two things

1. **Who reads this and what do they already know?** Assume no technical
   background unless told otherwise. When unsure, aim lower — clear never hurts
   an expert.
2. **What one job does the reader need to do after reading?** Write toward that.
   Cut anything that doesn't help them do it.

If either is genuinely unclear and changes the content, ask. Otherwise proceed.

---

## The principles

**1. Lead with the one mental model.** Open with the single idea everything else
depends on — a short "the one thing to understand first" up top. Give the reader
the map before the streets.

**2. Say who it's for and reassure them.** One line near the top: who this is for
and that they can do it. e.g. *"You don't need to know how to code. If you can
fill in a form and press Save, you can do this."*

**3. Make the abstract concrete with an analogy.** Compare the unfamiliar thing
to something everyday (a stack of slides, a filing cabinet, a recipe). One good
analogy beats a paragraph of definition.

**4. Second person, short sentences, plain verbs.** Write to "you." Prefer
*change, edit, open, press Save, hide, add, reorder* over *configure, invoke,
instantiate, persist, execute*. One idea per sentence.

**5. Explain every term the first time — or don't use it.** No unexplained
jargon, acronyms, or code names. When a technical name is unavoidable, map it to
a friendly name once and keep using the friendly one: *"the profile record (the
app calls it `UserEntity`)."* A small **"Words to know"** glossary near the top
earns its place when the doc has several such terms.

**6. Use tables for choices and mappings.** When the reader must pick, or match
one thing to another, a small table beats prose:

| You want to change… | Where it lives | Can you change it yourself? |
| --- | --- | --- |
| … | … | ✅ / ❌ |

**7. Call out the #1 mistake, in bold.** Most tasks have one thing people always
get wrong. Name it loudly: *"**This is the number-one thing people get wrong.**"*

**8. Turn processes into numbered, do-this-then-that steps.** A safe routine the
reader can follow top to bottom, each step an action with a visible result.

**9. Fence the scope — say what this does NOT cover.** A short *"Things that are
NOT done here"* list stops the reader hunting in the wrong place. Point them to
where those things *do* live.

**10. Bold the decisive words.** Bold the contrast that matters (*Save* vs
*Publish*, *on* vs *off*), not whole sentences. Bold is a spotlight; overusing
it blinds.

**11. Be honest about gaps.** If something needs info you don't have (a real
URL, a screenshot, a confirmed label), write a clear **TODO** placeholder rather
than guessing. Mark a doc as a skeleton if it is one.

**12. Cross-link, don't repeat.** Send the reader to the one place a thing is
explained ("see *Getting started*") instead of restating it. One source of
truth per fact.

**13. Scope tight to what the reader actually touches.** Cut anything outside
their world — other platforms, edge cases they'll never hit, internals they
can't change. Depth on what matters beats breadth on what doesn't.

---

## Word swaps (default direction)

| Instead of | Write |
| --- | --- |
| configure / set the configuration | set up / change the setting |
| invoke / execute / trigger | run / press / open |
| instantiate / initialize | create / start |
| persist / store to disk | save |
| authenticate | log in |
| deprecated | no longer used |
| leverage / utilize | use |
| endpoint / API returns | the app asks for / the app gets back |
| parameter / argument | the value you enter |
| the user | you |

Keep exact technical terms only when the reader must recognize them in the real
tool (a button label, a menu name, an error string) — then define them once.

---

## Recommended shape (adapt, don't force)

```
# <Plain title — what this helps you do>

<One line: who it's for + reassurance.>

## The one thing to understand first
<The core mental model, with an analogy.>

## Words to know        (only if several terms need it)
- **Term** — plain meaning.

## <How to do the main job>
1. Step (action → visible result)
2. …
   **<the #1 mistake, in bold>**

## Things that are NOT done here
- X → lives over there (link).
```

Drop any section a given doc doesn't need. Structure serves the reader, not the
template.

---

## Self-check before finishing

- [ ] A non-technical reader could act on this without a follow-up question.
- [ ] The one core idea is stated up front, with an analogy.
- [ ] Every acronym / code name is explained on first use (or removed).
- [ ] Choices and mappings are in tables, not buried in prose.
- [ ] The most common mistake is called out in bold.
- [ ] Processes are numbered steps with visible results.
- [ ] Scope is fenced — the reader knows what's out of scope and where it lives.
- [ ] No facts were lost from the source (rewrite mode).
- [ ] Gaps are honest TODOs, not guesses.

---

## Example — rewrite in action

**Before (developer output):**

> The `PublishController` persists the entity as a draft on `save()`. To
> propagate to the client, invoke `publish()`, which flips the `status` flag to
> `LIVE`. Note: `save()` alone does not trigger cache invalidation on the CDN.

**After (non-tech-content):**

> The system keeps **two versions** of anything you edit:
>
> - **Draft** — your saved work. **Customers do not see a draft.**
> - **Published** — the live version customers see.
>
> So there are two separate actions:
>
> - **Save** stores your draft. It does **not** go live.
> - **Publish** makes it live.
>
> **Editing and only Saving will not update what customers see — you must
> Publish.** This is the number-one thing people get wrong.

Same facts. Fewer nouns, no code names, the trap in bold, the reader knows
exactly what to press.
