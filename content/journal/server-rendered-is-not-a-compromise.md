---
title: Server-rendered is not a compromise
date: 2026-03-18
dek: Fast pages are not a nostalgia project. They are how a studio stays honest about what a website is for.
---

A client once asked, politely, when we would rebuild their "real app." What they had was a twelve-page studio site: a story, three case studies, a journal, and a form. What they meant was a client-rendered shell that fetched the same words after a spinner.

We declined. Not because we cannot ship JavaScript — we do, for a menu and a theme and a form that speaks JSON — but because the site was a document. Documents should arrive whole.

## What a page owes you

A first visit should not negotiate with a bundler. The headline, the work, and the way to write us ought to be in the HTML. If the network is slow, you still have the words. If a partner forwards the URL into a due-diligence folder, the page still reads. If we write a test that asserts "Selected work" is on the homepage, that test is about the product, not about a snapshot of a virtual DOM.

Flask is unfashionable in the way a well-cut coat is unfashionable. It does not pretend to be an operating system. Routes return templates. Templates inherit a base. The CSS is a visual system, not a byproduct of components fighting for specificity. When something is wrong, the stack trace points at a function with a name.

## Hospitality, not purity

This is not a sermon against interaction. Cobalt Room needed a booking brief. Meridian needed two paths from the first screen. The inquiry inbox at `/studio` is a small, token-protected tool, not a SaaS. We add movement where it helps — a fade that respects `prefers-reduced-motion` — and we stop before the page performs for us.

The honesty is in the constraint. If the work does not need a client-side router, we do not buy one and then spend a quarter justifying the purchase. Server-rendered is not a compromise. It is the default for sites whose job is to be read, trusted, and handed to the next person who has to ship a change on a Thursday afternoon.
