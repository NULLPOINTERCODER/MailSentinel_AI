import re

# Rule-based signal weights
POSITIVE_SIGNALS = {
    "offer": (r"\b(job offer|official offer|offer letter|employment offer)\b", 40),
    "interview": (r"\b(interview|technical interview|hr interview|screening call|coding test|assessment|online assessment|hackerrank|codility)\b", 35),
    "shortlisted": (r"\b(shortlisted|selected for|advancing to next round|next steps|application status)\b", 30),
    "recruiter": (r"\b(recruiter|talent acquisition|hiring manager|headhunter)\b", 20),
    "security_alert": (r"\b(security alert|unusual activity|suspicious login|password reset|verify your account|otp|2fa|verification code)\b", 30),
    "deadline": (r"\b(deadline|due date|expires on|urgent action required|action needed by|by today|by tomorrow)\b", 25),
    "payment_due": (r"\b(payment due|invoice due|bill reminder|past due|payment required)\b", 25),
    "meeting": (r"\b(meeting invitation|rescheduled meeting|calendar invite|zoom meeting|google meet)\b", 15),
}

NEGATIVE_SIGNALS = {
    "promotions": (r"\b(sale|discount|% off|promo code|clearance|special deal|limited time offer|black friday|coupon)\b", -35),
    "newsletter": (r"\b(newsletter|weekly digest|monthly digest|unsubscribe|view in browser|manage preferences)\b", -30),
    "marketing": (r"\b(no-reply@marketing|marketing@|promotions@|sponsored|advertisement)\b", -25),
    "social_notification": (r"\b(new follower|connected with you|view post|liked your|shared a post)\b", -20),
}


class ImportanceScorer:
    """Calculates deterministic preliminary rule scores and determines if Groq AI triage is warranted."""

    @staticmethod
    def calculate_rule_score(subject: str, body_text: str, sender_email: str, is_unread: bool = True) -> dict:
        combined_text = f"{subject} {body_text} {sender_email}".lower()
        score = 10 if is_unread else 0
        detected_positive = []
        detected_negative = []

        # Evaluate positive signals
        for name, (pattern, weight) in POSITIVE_SIGNALS.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += weight
                detected_positive.append({"signal": name, "weight": weight})

        # Evaluate negative signals
        for name, (pattern, weight) in NEGATIVE_SIGNALS.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                score += weight
                detected_negative.append({"signal": name, "weight": weight})

        # Bound score between 0 and 100
        final_score = max(0, min(100, score))

        # Determine if potentially important for Groq LLM processing
        # Conditions:
        # 1. Has positive signals (interview, offer, security, etc.) AND score >= 35
        # 2. Or final score >= 40 without dominant spam signals
        has_critical_signal = any(s["signal"] in {"offer", "interview", "shortlisted", "security_alert"} for s in detected_positive)
        is_potentially_important = (has_critical_signal and final_score >= 30) or (final_score >= 40)

        return {
            "rule_score": final_score,
            "is_potentially_important": is_potentially_important,
            "positive_signals": detected_positive,
            "negative_signals": detected_negative,
        }
