# Security policy

## Reporting a vulnerability

Do not open a public issue for a security problem. Email the
maintainer at saifullahrao089@gmail.com with a description of the
problem and how to reproduce it. You will get a reply within a few
days, and the fix will be published as a new release.

## What to check before you report

- This repo has no server, no database, and no credentials by design.
  The demo runs locally and calls no external service.
- Your own `business.json` is gitignored. Do not commit it, and do
  not paste a real phone number or API key into an issue.
- The optional voice rendering runs a local script you choose. Only
  point it at a script you trust, and never at a script that sends
  your voice reference audio to a service you have not checked.

## Supported versions

Only the latest release is supported with security fixes. Older
versions are not patched.
