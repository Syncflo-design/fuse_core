# Approving Support Tickets

*For whoever signs off requests on the client's side — Fuse user guide*

## Before you start

### Why there is an approval step at all

Some support requests commit somebody's time or money: a change to how the system works,
a training session, a new user account, an idea worth costing. Your organisation may
reasonably want a say before those are raised with support.

Other requests do not wait for anybody. A fault is a fault.

### What waits, and what does not

| Goes straight through | Waits for you |
|---|---|
| Something is broken | I need training |
| Something looks wrong | We need it to work differently |
| Something with Intacct | Nice to have |
| | New user or access |

That split is deliberate and not adjustable per ticket. An approver on leave must never be
able to sit on a system that is down, so faults are never held — not even briefly.

### Who does this

Whoever holds the **Fuse Support Approver** role. Usually one or two people. An
administrator assigns it under the user's own record; the role exists on every Fuse site
but starts out held by nobody.

> **Screenshot 1 — The approver role on a user record**
> *[to be inserted: User form, Roles section, Fuse Support Approver ticked]*

### If nobody holds the role

Nothing waits. Every ticket is sent, including the discretionary ones.

That is on purpose. A gate nobody can open is not a control — it is a queue of requests
quietly going nowhere, and the first anyone hears of it is a client asking why support
never replied. So the gate only closes once somebody is standing at it.

## Deciding on a ticket

### Finding what is waiting

When a ticket needs you, it appears in your **to-do list** — the same place as everything
else assigned to you. An urgent one is marked as such.

You can also open the Fuse Support Ticket list and filter on **Waiting for approval**.

### Reading it

Open the ticket. Everything you need is on one screen:

| What you are looking at | Why it matters |
|---|---|
| Subject and kind | What is being asked for |
| How urgent | What the person raising it thinks, in their words |
| What happened / What was expected | The case for it |
| Raised by, and the screen they were on | Who, and where it came up |
| Site details | Version and site information, captured automatically |

Nothing has been sent yet. The headline at the top of the ticket says so.

> **Screenshot 2 — A ticket waiting for approval**
> *[to be inserted: Fuse Support Ticket, Waiting for approval headline with the two buttons]*

### Approving

Click **Approve and send**.

The ticket is emailed to your support address there and then, and stamped with your name
and the time. The reply goes back to the person who raised it, not to you — you decided
whether it should be asked, not what the answer is.

### Declining

Click **Decline**, and say why.

The reason is required, and it is not a formality. A request that came back declined with
no explanation is how people learn to stop raising them — and then the first thing anyone
hears about a real problem is when it has become a bigger one.

Write the sentence you would say to their face: *"We are already paying for this in the
March scope"*, or *"Let us do it after go-live"*. It is recorded on the ticket and the
person who raised it is told.

> **Screenshot 3 — Declining, with the reason**
> *[to be inserted: the Decline dialog with a reason typed in]*

## Common questions

### Can I edit the request before approving it?

You can edit the ticket like any other document, but think twice. What you send should be
what they asked for. If it needs reframing, that is usually a conversation with them rather
than a rewrite of their words.

### I approved it but it says it did not send

The ticket is approved and saved; only the email failed, almost always because the site has
no outgoing mail account set up. Tell your administrator, then use **Send to support** on
the ticket. Nothing needs retyping.

### Something urgent is stuck waiting for me and I am away

It should not be — a fault never waits. If a genuinely urgent thing was raised as a change
request, decline it and ask them to raise it as a fault, or approve it and let support
judge.

If you are going to be away, the practical answer is to have the role on two people rather
than one.

### How do I turn the approval step off?

An administrator unticks **Discretionary Tickets Need Approval** in Intacct Settings. Every
ticket then goes straight through.

### Can I see what was approved historically?

Yes. The Fuse Support Ticket list holds everything, and each ticket carries who decided,
when, and — where it was declined — why.
