# Agent Instructions

## Instruction Changes: Clarity Check
- Whenever you change narration or operational instructions, review the surrounding guidance for potential ambiguity, overlap, or contradiction introduced by the change.
- If any phrasing could be misunderstood (e.g., does it end a response vs. change ordering), revise the language in the same edit until the flow is unambiguous and consistent with related files.

## OpenAPI Schemas for ChatGPT GPT Actions

When creating or modifying OpenAPI schemas intended for use as ChatGPT GPT Actions:

### Confirmation Behavior (`x-openai-isConsequential`)
- **GET requests**: No user confirmation required (default behavior).
- **POST/PUT/DELETE requests**: User confirmation required by default.
- To **skip confirmation** for POST requests that have no side effects (read-only operations), add:
  ```yaml
  x-openai-isConsequential: false
  ```
- Only use `false` when the endpoint:
  - Does not modify server state
  - Has no side effects
  - Is essentially a "query" operation using POST for technical reasons (e.g., complex parameters, URL length limits)

### When to Use POST vs GET
- **GET**: Simple queries with few, short parameters.
- **POST**: Prefer when:
  - Parameters include lists or complex structures (e.g., `content_boxes`, `content_waves`)
  - Parameter values may be long (box names, wave names)
  - URL length could exceed browser/server limits (~2000 chars)

### Automatic Application
When adding or modifying OpenAPI schemas for GPT Actions in this repository:
1. Always consider whether POST endpoints need `x-openai-isConsequential: false`.
2. Document the rationale in the schema description if not obvious.
3. Ensure the CGI/backend supports both GET and POST where practical.
