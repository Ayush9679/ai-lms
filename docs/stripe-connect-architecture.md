# Course pricing and future Stripe Connect design

## Implemented now

- `courses.price` is the existing `NUMERIC(10,2)` amount, now represented as `Decimal` in Python.
- `courses.currency` is an explicit `VARCHAR(3)` field. This release accepts INR only; the field is ready to carry future ISO currency codes after adding display, settlement, and validation support.
- Free is represented by price `0.00`; paid is represented by a positive amount. There is no duplicate `is_paid` flag.
- Teachers can set price at creation or update through authenticated course APIs. The backend rejects negative values, more than two decimal places, unsupported currencies, and arbitrary thumbnail URLs.
- Paid course enrollment and student media access remain denied. New paid courses cannot be published until verified checkout is implemented. Existing public course state is not rewritten.
- `TEACHER_REVENUE_SHARE` defaults to `0.90`. The pure minor-unit split helper rounds the teacher share with `ROUND_HALF_UP` and assigns the remainder to the platform, so both shares sum exactly to the verified gross. Nothing currently calls this helper to record earnings; without a completed payment record, recognized earnings remain zero.

## Future payment and payout sequence

1. **Teacher connection.** After confirming Stripe Connect availability for the platform country, create a connected account using Stripe's current Accounts API. Store the account ID against the teacher with a uniqueness constraint. Create onboarding links on the backend only after teacher authorization; treat links as one-use and refresh them after return/expiry. A future `account.updated` webhook should synchronize onboarding and payout capability status. The frontend may then show a real connection state; until that work exists, do not show a working Connect action.
2. **Server-priced checkout.** A student requests checkout for a course ID. The backend loads the course's current `price` and `currency`, checks that the requester is not the owner, and creates the provider checkout using the server-side amount in minor units. Do not accept a client-supplied total. Store a pending purchase with a price/currency snapshot and a unique provider session ID. A redirect or browser success page never grants enrollment.
3. **Verified payment and idempotency.** Receive signed webhook events at a backend HTTPS endpoint, verify the raw request body and signature, then insert the provider event ID into an event table with a unique constraint. In one transaction, reconcile the provider payment ID/status and purchase. Only the verified successful-payment event can mark a purchase paid and create/activate enrollment. Return quickly after durable receipt; retry-safe processing uses the unique event/payment keys.
4. **Commission and payout.** Compute teacher share as 90% of the captured gross in minor units using the documented rounding rule; platform share is the residual 10%. Fees, tax, refunds, disputes, and payout timing need explicit policy before transferring funds. Prefer a held/ledger-based balance and delayed transfer policy until refund exposure is decided. Do not infer earnings from course prices or enrollments.
5. **Refunds and reversals.** Persist each refund as a separate idempotent record/event, adjust recognized net revenue, and reverse any related teacher transfer where possible. Keep an immutable ledger for charge, platform fee, teacher allocation, transfer, refund, reversal, dispute, and adjustment entries.

Likely later database additions are `teacher_payout_accounts`, `course_purchases` (including amount/currency snapshots and unique provider IDs), `payment_events` (unique provider event ID), `payment_refunds`, and an append-only `payment_ledger_entries`/transfer ledger. These require a new Alembic revision after `0003`; none are created in this phase because there is no payment gateway or payment model yet.

### Charge flow decision still required

Stripe documents separate charges and transfers as a platform charge followed by explicit transfers; in that model the platform balance is debited for Stripe fees, refunds, and chargebacks. This may suit delayed teacher settlements but carries platform liability. Select the charge flow only after confirming the platform's country, connected-account country coverage, INR settlement/payout support, merchant-of-record responsibilities, taxes, and refund policy. Stripe's availability is country and flow dependent; an INR catalog alone does not establish Connect payout availability.

Useful Stripe references: [Accounts v2](https://docs.stripe.com/connect/accounts-v2), [separate charges and transfers](https://docs.stripe.com/connect/separate-charges-and-transfers), [webhook signature verification](https://docs.stripe.com/webhooks), and [Connect cross-border payout availability](https://docs.stripe.com/connect/connect-cross-border-payouts).
