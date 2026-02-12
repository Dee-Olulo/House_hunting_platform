"""
services/listing_scheduler.py
─────────────────────────────
Background scheduler for Requirement 6: Automatic Listing Confirmation Every 30 Days.

Timeline per property (from last_confirmed):
  Day 0   → landlord confirms (or listing is first created)
  Day 25  → early reminder notification sent
  Day 30  → reminder notification sent  →  confirmation_pending = True
  Day 45  → final warning notification sent
  Day 60  → property auto-deactivated, landlord notified

All actions are logged to the `listing_confirmation_logs` collection for audit trail
and admin analytics.

Depends on:
  - APScheduler  (pip install apscheduler)
  - extensions.mongo  (your existing Flask-PyMongo wrapper)
"""

from datetime import datetime, timedelta
from bson import ObjectId
from extensions import mongo   # re-use your existing mongo instance


# ──────────────────────────────────────────────────────────
# CONFIGURATION — tweak these constants as needed
# ──────────────────────────────────────────────────────────
EARLY_REMINDER_DAYS   = 25   # first heads-up
REMINDER_DAYS         = 30   # main "please confirm" nudge
FINAL_WARNING_DAYS    = 45   # last chance before deactivation
AUTO_DEACTIVATE_DAYS  = 60   # property goes inactive


# ──────────────────────────────────────────────────────────
# HELPERS
# ──────────────────────────────────────────────────────────
def _days_since(dt: datetime) -> float:
    """Return whole days elapsed since *dt*."""
    return (datetime.utcnow() - dt).days


def _create_notification(user_id: str, title: str, message: str,
                         notification_type: str, link: str | None = None):
    """Insert one notification document — mirrors the shape used by
    notification_routes.py / admin_notification_routes.py."""
    mongo.db.notifications.insert_one({
        "user_id":            user_id,
        "title":              title,
        "message":            message,
        "notification_type":  notification_type,
        "link":               link,
        "is_read":            False,
        "created_at":         datetime.utcnow(),
        "sent_by":            "system"          # distinguishes automated msgs
    })


def _log_action(property_id: str, landlord_id: str, action: str,
                detail: str | None = None):
    """Append one row to the audit log collection."""
    mongo.db.listing_confirmation_logs.insert_one({
        "property_id":  property_id,
        "landlord_id":  landlord_id,
        "action":       action,              # reminder_early | reminder | warning | deactivated | confirmed
        "detail":       detail,
        "timestamp":    datetime.utcnow()
    })


# ──────────────────────────────────────────────────────────
# MAIN JOB  — called by APScheduler once per day
# ──────────────────────────────────────────────────────────
def run_listing_confirmation_check():
    """
    Scans every *active* property and acts based on how long it has been
    since the landlord last confirmed the listing.

    Safe to call repeatedly — each threshold fires at most once thanks to
    the `confirmation_reminders_sent` set stored on the property doc.
    """
    print("[ListingScheduler] Starting confirmation check …")

    now = datetime.utcnow()

    # ── fetch all active properties ─────────────────────────────────
    active_properties = list(mongo.db.properties.find({
        "status": "active"
    }))

    reminders_sent   = 0
    warnings_sent    = 0
    deactivations    = 0

    for prop in active_properties:
        prop_id      = str(prop["_id"])
        landlord_id  = str(prop.get("landlord_id", ""))
        title        = prop.get("title", "Your Property")

        # ── determine the reference date ────────────────────────────
        # If landlord has never confirmed we fall back to created_at.
        last_confirmed = prop.get("last_confirmed") or prop.get("created_at")

        if not last_confirmed:
            # Edge-case: very old doc with neither field — skip safely
            continue

        days_elapsed = _days_since(last_confirmed)

        # ── which reminders have already fired? ─────────────────────
        already_sent: set[str] = set(prop.get("confirmation_reminders_sent", []))

        # ── AUTO-DEACTIVATION (≥ 60 days) ───────────────────────────
        if days_elapsed >= AUTO_DEACTIVATE_DAYS and "deactivated" not in already_sent:
            mongo.db.properties.update_one(
                {"_id": prop["_id"]},
                {"$set": {
                    "status":                    "inactive",
                    "deactivated_at":            now,
                    "deactivated_reason":        "auto_confirmation_timeout"
                },
                 "$addToSet": {"confirmation_reminders_sent": "deactivated"}}
            )
            _create_notification(
                user_id           = landlord_id,
                title             = f"Property Deactivated: {title}",
                message           = (
                    f"Your listing \"{title}\" has been automatically deactivated "
                    f"because it was not confirmed within 60 days. "
                    f"Please re-activate and confirm the listing if it is still available."
                ),
                notification_type = "property_deactivated",
                link              = f"/landlord/properties/edit/{prop_id}"
            )
            _log_action(prop_id, landlord_id, "deactivated",
                        f"Auto-deactivated after {days_elapsed} days without confirmation")
            deactivations += 1
            continue   # no further checks needed for this property

        # ── FINAL WARNING (≥ 45 days) ───────────────────────────────
        if days_elapsed >= FINAL_WARNING_DAYS and "warning" not in already_sent:
            mongo.db.properties.update_one(
                {"_id": prop["_id"]},
                {"$addToSet": {"confirmation_reminders_sent": "warning"}}
            )
            _create_notification(
                user_id           = landlord_id,
                title             = f"⚠️ Final Warning – Confirm \"{title}\"",
                message           = (
                    f"Your listing \"{title}\" will be automatically deactivated in "
                    f"{AUTO_DEACTIVATE_DAYS - days_elapsed} days if you do not confirm it. "
                    f"Please confirm the listing to keep it active."
                ),
                notification_type = "property_expiring",
                link              = f"/landlord/properties"
            )
            _log_action(prop_id, landlord_id, "warning",
                        f"Final warning sent at {days_elapsed} days")
            warnings_sent += 1

        # ── MAIN REMINDER (≥ 30 days) ───────────────────────────────
        elif days_elapsed >= REMINDER_DAYS and "reminder" not in already_sent:
            mongo.db.properties.update_one(
                {"_id": prop["_id"]},
                {"$set":       {"confirmation_pending": True},
                 "$addToSet":  {"confirmation_reminders_sent": "reminder"}}
            )
            _create_notification(
                user_id           = landlord_id,
                title             = f"Please Confirm Your Listing: {title}",
                message           = (
                    f"It has been 30 days since you last confirmed \"{title}\". "
                    f"Please confirm whether this property is still available for rent."
                ),
                notification_type = "property_expiring",
                link              = f"/landlord/properties"
            )
            _log_action(prop_id, landlord_id, "reminder",
                        "30-day confirmation reminder sent")
            reminders_sent += 1

        # ── EARLY REMINDER (≥ 25 days) ──────────────────────────────
        elif days_elapsed >= EARLY_REMINDER_DAYS and "reminder_early" not in already_sent:
            mongo.db.properties.update_one(
                {"_id": prop["_id"]},
                {"$addToSet": {"confirmation_reminders_sent": "reminder_early"}}
            )
            _create_notification(
                user_id           = landlord_id,
                title             = f"Upcoming – Confirm \"{title}\" Soon",
                message           = (
                    f"Your listing \"{title}\" will need confirmation in "
                    f"{REMINDER_DAYS - days_elapsed} days. "
                    f"A quick confirmation keeps your listing visible to tenants."
                ),
                notification_type = "booking_reminder",
                link              = f"/landlord/properties"
            )
            _log_action(prop_id, landlord_id, "reminder_early",
                        "Early (25-day) confirmation reminder sent")
            reminders_sent += 1

    print(
        f"[ListingScheduler] Done — reminders: {reminders_sent}, "
        f"warnings: {warnings_sent}, deactivations: {deactivations}"
    )


# ──────────────────────────────────────────────────────────
# CONFIRMATION HELPER  — called by the property route when
#   a landlord explicitly confirms a listing
# ──────────────────────────────────────────────────────────
def confirm_listing(property_id: str) -> bool:
    """
    Reset the 30-day clock for *property_id*.

    Returns True on success, False if the property was not found.
    """
    result = mongo.db.properties.update_one(
        {"_id": ObjectId(property_id)},
        {"$set": {
            "last_confirmed":            datetime.utcnow(),
            "confirmation_pending":      False,
            "confirmation_reminders_sent": []   # clear so future reminders re-arm
        }}
    )
    if result.matched_count == 0:
        return False

    # Log the confirmation
    prop = mongo.db.properties.find_one({"_id": ObjectId(property_id)}, {"landlord_id": 1})
    if prop:
        _log_action(property_id, str(prop.get("landlord_id", "")), "confirmed",
                    "Landlord confirmed listing")
    return True