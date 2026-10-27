---
name: license-picker
description: Generate a LICENSE file for your repo from a chosen license, name, and year. Use when the user says "add a license to my project", "create a LICENSE file", or "which open source license".
license: MIT
metadata:
  author: JustHandled Labs
  version: 1.0.0
  price: $0
  credits: 0
  triggers:
    - add a license to my project
    - create a LICENSE file
    - which open source license
---

# License Picker

Generate open-source license text from a supported license id, holder name, and year. This generator prints to stdout by default and writes LICENSE only when the user passes --write.

## Workflow

1. Choose a supported license id.
2. Run scripts/generate_license.py with --license, --holder, and --year.
3. Review the generated license text.
4. Write LICENSE only with --write. Existing files require --force.

## Guardrails

- Do not choose a license for the user as legal advice.
- Do not fetch license text from the network.
- Do not overwrite LICENSE unless --force is present.

## Verification

Run tests/test_license.py. The generated MIT fixture must match fixtures/expected/LICENSE.

## Limits

This package ships license templates and fills placeholders. It is not legal advice.

## Licence

This GitHub-distributed package is licensed under the MIT License in the repository's LICENSE.md. Preserve its copyright and permission notice as required by that licence.
