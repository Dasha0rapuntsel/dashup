"""A deterministic and dependency-free ticket processing baseline."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
import math
from pathlib import Path
import re
from time import perf_counter
from typing import Any


TOKEN_RE = re.compile(r"[a-zа-яё0-9]+", re.IGNORECASE)
PII_PATTERNS = {
    "CARD": re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    "EMAIL": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-zА-Яа-я]{2,}\b"),
    "PHONE": re.compile(r"(?<!\d)(?:\+7|8)[\s()-]*\d{3}[\s()-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\d)"),
}

THEME_KEYWORDS = {
    "notifications": {"уведомления", "уведомление", "рассылка", "email", "письма", "отключить"},
    "payment": {"списали", "списание", "деньги", "карта", "оплата", "платеж", "платёж", "возврат"},
    "access": {"пароль", "войти", "вход", "аккаунт", "код", "взломали"},
    "outage": {"недоступен", "не работает", "ошибка", "сбой", "лежит"},
    "integration": {"api", "интеграция", "webhook", "вебхук"},
}

HIGH_RISK_KEYWORDS = {
    "списали", "списание", "возврат", "карта", "платеж", "платёж", "взломали",
    "мошенничество", "персональные данные", "суд", "претензия",
}
INJECTION_MARKERS = {
    "игнорируй инструкции", "покажи системный промпт", "system prompt",
    "ignore previous instructions", "developer message",
}
AUTO_CLOSE_ALLOWLIST = {"notifications"}


def _tokens(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


@dataclass(frozen=True)
class Ticket:
    ticket_id: str
    channel: str
    text: str


@dataclass(frozen=True)
class Classification:
    theme: str
    confidence: float


@dataclass(frozen=True)
class RetrievedArticle:
    article_id: str
    title: str
    answer: str
    score: float
    version: str


@dataclass(frozen=True)
class Decision:
    ticket_id: str
    action: str
    theme: str
    classification_confidence: float
    risk: str
    pii_types: list[str]
    masked_text: str
    kb_article_id: str | None
    retrieval_score: float
    response: str | None
    reasons: list[str]
    latency_ms: float
    policy_version: str = "poc-policy-1"
    classifier_version: str = "keyword-baseline-1"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SupportPipeline:
    """Fast synchronous safety/routing path with a trusted-content response."""

    def __init__(self, kb_path: Path, audit_path: Path):
        self.kb_path = kb_path
        self.audit_path = audit_path
        self.articles = json.loads(kb_path.read_text(encoding="utf-8"))

    @staticmethod
    def mask_pii(text: str) -> tuple[str, list[str]]:
        masked = text
        found: list[str] = []
        for pii_type, pattern in PII_PATTERNS.items():
            masked, count = pattern.subn(f"[{pii_type}]", masked)
            if count:
                found.append(pii_type)
        return masked, found

    @staticmethod
    def classify(text: str) -> Classification:
        lowered = text.lower()
        tokens = set(_tokens(text))
        scores: dict[str, int] = {}
        for theme, keywords in THEME_KEYWORDS.items():
            scores[theme] = sum(1 for word in keywords if word in tokens or " " in word and word in lowered)
        ranked = sorted(scores.items(), key=lambda item: (-item[1], item[0]))
        theme, top = ranked[0]
        second = ranked[1][1]
        if top == 0:
            return Classification("other", 0.35)
        confidence = min(0.98, 0.68 + 0.08 * top + 0.03 * (top - second))
        return Classification(theme, round(confidence, 3))

    @staticmethod
    def assess_risk(text: str, pii_types: list[str]) -> tuple[str, bool]:
        lowered = text.lower()
        injection = any(marker in lowered for marker in INJECTION_MARKERS)
        if injection or any(keyword in lowered for keyword in HIGH_RISK_KEYWORDS) or "CARD" in pii_types:
            return "HIGH", injection
        if pii_types:
            return "MEDIUM", injection
        return "LOW", injection

    def retrieve(self, text: str, theme: str) -> RetrievedArticle | None:
        query = set(_tokens(text))
        best: RetrievedArticle | None = None
        for article in self.articles:
            if article["status"] != "approved":
                continue
            document = set(_tokens(" ".join([article["title"], *article["keywords"]])))
            overlap = len(query & document)
            denominator = math.sqrt(max(len(query), 1) * max(len(document), 1))
            lexical_score = overlap / denominator
            score = min(1.0, lexical_score + (0.25 if article["topic"] == theme else 0.0))
            candidate = RetrievedArticle(
                article_id=article["id"],
                title=article["title"],
                answer=article["answer"],
                score=round(score, 3),
                version=article["version"],
            )
            if best is None or candidate.score > best.score:
                best = candidate
        return best

    def process(self, ticket: Ticket) -> Decision:
        started = perf_counter()
        masked_text, pii_types = self.mask_pii(ticket.text)
        classification = self.classify(masked_text)
        risk, injection = self.assess_risk(masked_text, pii_types)
        article = self.retrieve(masked_text, classification.theme)

        reasons: list[str] = []
        if injection:
            reasons.append("prompt_injection_signal")
        if risk == "HIGH":
            reasons.append("high_risk_category")
        if classification.confidence < 0.75:
            reasons.append("low_classification_confidence")
        if article is None or article.score < 0.35:
            reasons.append("weak_or_missing_kb_evidence")
        if classification.theme not in AUTO_CLOSE_ALLOWLIST:
            reasons.append("category_not_in_auto_close_allowlist")

        action = "ESCALATE" if reasons else "AUTO_CLOSE"
        response = article.answer if action == "AUTO_CLOSE" and article else None
        elapsed_ms = round((perf_counter() - started) * 1000, 3)
        decision = Decision(
            ticket_id=ticket.ticket_id,
            action=action,
            theme=classification.theme,
            classification_confidence=classification.confidence,
            risk=risk,
            pii_types=pii_types,
            masked_text=masked_text,
            kb_article_id=article.article_id if article else None,
            retrieval_score=article.score if article else 0.0,
            response=response,
            reasons=reasons or ["all_auto_close_gates_passed"],
            latency_ms=elapsed_ms,
        )
        self._audit(decision, ticket.channel)
        return decision

    def _audit(self, decision: Decision, channel: str) -> None:
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        event = {
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "ticket_id": decision.ticket_id,
            "channel": channel,
            "action": decision.action,
            "theme": decision.theme,
            "risk": decision.risk,
            "classification_confidence": decision.classification_confidence,
            "retrieval_score": decision.retrieval_score,
            "kb_article_id": decision.kb_article_id,
            "reasons": decision.reasons,
            "policy_version": decision.policy_version,
            "classifier_version": decision.classifier_version,
            "latency_ms": decision.latency_ms,
        }
        with self.audit_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, ensure_ascii=False) + "\n")

