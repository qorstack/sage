# order rules

Order lifecycle management

## Business rules
- Order status must be a state machine — no backward transitions (e.g. completed → pending is invalid)
- Stock must be reserved (not deducted) at order creation
- Payment must be confirmed before stock deduction
- Cancellation must release reserved stock

## Common requirements
- Order state machine: draft → confirmed → paid → shipped → completed | cancelled
- Stock reservation on order creation
- Payment flow trigger on order confirmation
- Inventory deduction on payment success
- Notification at each status transition
- Audit log for every order event

## Risk flags
- Race condition on stock reservation under high concurrency
- Payment success webhook may arrive before order status update
- Cancellation after shipment requires manual intervention

## Required workflow
- 1. Validate cart and stock availability
- 2. Create order (reserved stock, status=draft)
- 3. Initiate payment → status=pending_payment
- 4. On payment success webhook: deduct stock, status=paid
- 5. Trigger shipping, notify user

## Questions to ask
- Is partial order fulfillment supported?
- What happens if stock runs out between reservation and payment?
- Can orders be split across multiple shipments?

## Related domains
payment, inventory, notification, shipping, audit

<!-- Edit these rules freely. They're surfaced to the AI for this domain,
     overriding the built-in defaults. Committed to the repo so the team
     shares them. -->
