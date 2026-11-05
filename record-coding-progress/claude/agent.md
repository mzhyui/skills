---
name: record-coding-progress
description: Write a clear, durable progress record - an implementation handoff (fix or new capability), an evaluation readout (what an evaluation, benchmark, ablation, or experiment found and what it means), or a session record of research, design, diagnosis, or decisions (what method was discussed and what was decided). Use for substantial coding handoffs, finished evaluations, or when the user asks to record, conclude, summarize, or preserve session findings. Commit only when explicitly requested with this skill.
skills:
  - record-coding-progress
model: inherit
---
Follow the record-coding-progress skill. Choose the record kind (implementation, evaluation, or session) and, for implementation, the change type (fix or new). Write the body so its first section stands alone: the Outcome, the evaluation Readout (question, answer, results table with comparisons and meaning, decision), or the session Takeaways followed by a Method section that defines every term. Capture Git facts with `record_tool.py start` and `custody`, keep commands and custody in the folded appendix, and run `validate` before reporting.
