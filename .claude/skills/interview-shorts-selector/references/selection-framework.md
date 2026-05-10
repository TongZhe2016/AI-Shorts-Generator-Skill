# Selection Framework

Use this framework to choose short-video candidates from interview subtitles. The priority is traffic potential with context integrity.

## Selection modes

### Knowledge/opinion mode, primary

Prioritize clips where the speaker delivers a focused idea that can stand alone:

- A clear claim, judgment, or mental model.
- A counterintuitive explanation or reframing.
- A practical lesson viewers may save or share.
- A strong cause-and-effect chain.
- A concise answer to a question many viewers have.

A strong knowledge/opinion clip usually has:

1. Hook: a sentence that creates curiosity or tension.
2. Development: explanation, evidence, example, or contrast.
3. Payoff: conclusion, implication, advice, or memorable line.

Reject clips that are only topic labels, vague agreement, long setup without payoff, or generic information with no point of view.

### Personal-story mode, fallback

Use this mode when the transcript is more naturally driven by lived experience than abstract ideas.

Prioritize:

- Personal turning points.
- Vulnerability, regret, surprise, or relief.
- A story with setup, obstacle, choice, and consequence.
- A moment that changes how viewers perceive the person.

Reject story clips that lack a payoff or require too much outside context to understand.

### Risky/controversial mode, limited

Controversy can create reach, but never at the cost of fairness. Use only when:

- The speaker's actual meaning is clear.
- The clip includes enough context to prevent a false accusation.
- The suggested title does not exaggerate the target, certainty, or hostility.

Mark risk `中` or `高` when a clip involves personal criticism, institutional accusations, medical/legal/financial claims, identity groups, politics, or reputational harm.

## Virality signals

Rank candidates by these signals:

1. Strong hook: the opening line creates curiosity, surprise, disagreement, or emotional pull.
2. Core claim: the clip has one main point, not several loose topics.
3. Cognitive gap: viewers learn a frame they did not expect.
4. Emotional texture: the speaker shows conviction, vulnerability, humor, anger, or surprise.
5. Retention shape: setup, escalation, turn, and payoff are visible.
6. Shareability: the idea can spark comments, saves, reposts, or debate.
7. Quotability: one sentence can become a title, cover line, or caption opener.
8. Practical value: the viewer can apply or remember the idea.

## Duration rules

Default duration range: 30-120 seconds.

- 30-45 seconds: use for tight claims, punchy reframes, or concise Q&A.
- 45-90 seconds: ideal for most knowledge/opinion clips.
- 90-120 seconds: use for stories or arguments that need setup and payoff.
- Over 120 seconds: avoid unless the user explicitly asks for longer clips.

Do not cut mid-sentence or mid-thought. Add a few seconds before or after when needed to preserve grammar and meaning.

## Multi-segment rules

Prefer continuous clips. Use multiple segments only when the final short becomes more coherent or fair.

Valid multi-segment patterns:

- Hook + explanation: an early sharp line becomes clear only with a later explanation.
- Claim + evidence: two separated parts form one argument chain.
- Setup + payoff: a story's premise and conclusion are separated by filler.
- Context repair: a later line prevents the hook from becoming misleading.

Invalid multi-segment patterns:

- Combining unrelated viral lines.
- Joining contradictory statements without explaining the shift.
- Removing the speaker's caveat to make a stronger claim.
- Creating a conclusion the speaker never made.

Default maximum: 3 segments. If more than 3 segments are needed, the candidate is probably not a good short.

## Context integrity checklist

For each candidate, answer these checks before final output:

- Are the speaker's premise and conclusion both present?
- Is an important caveat, reversal, or limitation missing?
- Is the speaker quoting or describing someone else's view?
- Is the statement a joke, hypothetical, or exaggeration?
- Would the title/caption make the claim sound more absolute than it is?
- Would 5-10 seconds of adjacent context materially reduce misunderstanding?
- Is the clip fair to the guest, interviewer, and named third parties?

Use `context_integrity_check.verdict`:

- `pass`: safe and complete.
- `needs_context`: usable only if the listed context is included.
- `reject`: too misleading or incomplete to recommend.

Do not include `reject` candidates in the final `clips` array unless the user explicitly asks to see rejected candidates.

## Scoring

Assign `score_100` using this weighting:

- `hook_strength` 20 points.
- `core_claim_strength` 20 points.
- `context_integrity` 20 points.
- `retention_structure` 15 points.
- `shareability` 15 points.
- `risk_control` 10 points.

Interpretation:

- 90-100: exceptional; likely top clip if context is safe.
- 80-89: strong candidate; should usually be included.
- 70-79: usable; include if it adds topic diversity.
- 60-69: borderline; include only if few strong clips exist.
- Below 60: do not include by default.

## Dedupe rules

When candidates overlap or repeat the same idea:

1. Keep the candidate with clearer opening hook.
2. Prefer the candidate with a complete claim and payoff.
3. Prefer lower context risk when scores are similar.
4. Avoid multiple clips with the same title angle unless the user wants many clips from one topic.

## Title and caption rules

Titles should be Chinese, specific, and faithful.

Good titles:

- Emphasize the question, tension, or insight.
- Avoid naming a target unless the transcript clearly supports it.
- Avoid absolute claims if the speaker used caveats.

Captions should:

- Open with the hook or viewer-facing question.
- Summarize the idea without adding unsupported claims.
- Invite discussion when appropriate.
