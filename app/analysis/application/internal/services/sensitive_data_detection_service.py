from __future__ import annotations

import ipaddress
import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from app.analysis.application.internal.services.json_path import append_json_path
from app.analysis.application.internal.services.sensitive_value_masking import (
    mask_sensitive_value,
)
from app.analysis.domain.model.entities.analysis_finding import AnalysisFinding
from app.analysis.domain.model.valueobjects.analysis_confidence import (
    AnalysisConfidence,
)
from app.analysis.domain.model.valueobjects.analysis_finding_severity import (
    AnalysisFindingSeverity,
)
from app.analysis.domain.model.valueobjects.analysis_finding_type import (
    AnalysisFindingType,
)
from app.analysis.domain.model.valueobjects.json_types import JsonContainer, JsonValue

_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_AWS_ACCESS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
_KNOWN_TOKEN_PATTERNS = (
    re.compile(r"\bsk-(?:live|test|proj)[A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b"),
    re.compile(r"\bSG\.[A-Za-z0-9._-]{12,}\b"),
    re.compile(r"\bhvs\.[A-Za-z0-9._-]{12,}\b"),
)
_CONNECTION_STRING_PATTERN = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|amqp)://[^\s/:]+:[^\s/@]+@[^\s]+"
)
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
    re.IGNORECASE,
)
_IPV4_PATTERN = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
_PROMPT_INJECTION_PATTERN = re.compile(
    r"(?i)(ignore\s+(?:all\s+)?previous\s+instructions|system\s+prompt|return\s+(?:a\s+)?low|"
    r"disregard\s+(?:the\s+)?instructions|you\s+are\s+now|reveal\s+(?:the\s+)?secrets?|"
    r"do\s+not\s+report\s+(?:this|findings?))"
)
_PHONE_PATTERN = re.compile(r"(?<!\w)\+?\d[\d ()-]{6,}\d(?!\w)")
_EXPIRATION_PATTERN = re.compile(r"^(?:0[1-9]|1[0-2])[/\-](?:\d{2}|\d{4})$")
_PLACEHOLDER_PATTERN = re.compile(
    r"(?i)(your[_ -]?(?:key|token|password)[_ -]?here|change[_ -]?me|example|placeholder|"
    r"dummy|fake|sample|redacted|masked|<[^>]+>|\$\{[^}]+\}|^x{4,}$|^\*{4,}$)"
)

_PASSWORD_FIELDS = {"password", "passwd", "pwd", "contrasena", "clave", "passphrase"}
_API_KEY_FIELDS = {
    "api_key",
    "apikey",
    "api_secret",
    "client_secret",
    "secret",
    "secret_key",
    "access_key_id",
    "aws_access_key_id",
}
_TOKEN_FIELDS = {"token", "auth_token", "bearer_token", "authorization"}
_ACCESS_TOKEN_FIELDS = {"access_token", "accesstoken"}
_REFRESH_TOKEN_FIELDS = {"refresh_token", "refreshtoken"}
_SESSION_FIELDS = {"session_id", "sessionid", "sid"}
_SESSION_COOKIE_FIELDS = {"session_cookie", "cookie", "set_cookie"}
_CARD_FIELDS = {"card_number", "cardnumber", "pan", "primary_account_number"}
_CARD_LAST4_FIELDS = {"card_last4", "last4", "card_last_four"}
_CVV_FIELDS = {"cvv", "cvc", "security_code", "card_security_code"}
_EXPIRATION_FIELDS = {
    "expires",
    "expiry",
    "expiration",
    "expiration_date",
    "card_expiration",
}
_FULL_NAME_FIELDS = {
    "full_name",
    "fullname",
    "nombre_completo",
    "customer_name",
    "holder",
    "cardholder",
}
_PHONE_FIELDS = {"phone", "telephone", "mobile", "cellphone", "telefono", "celular"}
_PERSONAL_ID_FIELDS = {
    "dni",
    "document_number",
    "national_id",
    "personal_id",
    "identification_number",
    "cedula",
    "identificacion",
}
_PASSPORT_FIELDS = {"passport", "passport_number", "pasaporte"}
_IP_FIELDS = {"ip", "ip_address", "source_ip", "client_ip", "remote_ip"}
_BANK_FIELDS = {
    "iban",
    "cbu",
    "cvu",
    "bank_account",
    "account_number",
    "routing_number",
    "swift",
}
_FINANCIAL_FIELDS = {
    "account_balance",
    "balance",
    "salary",
    "income",
    "credit_score",
    "financial_data",
}
_DEBUG_FIELDS = {
    "debug_payload",
    "raw_request_dump",
    "raw_request",
    "request_dump",
    "full_request",
    "request_payload",
}


@dataclass(frozen=True, slots=True)
class _DetectedFinding:
    finding_type: AnalysisFindingType
    severity: AnalysisFindingSeverity
    title: str
    description: str
    json_path: str
    evidence: str
    detection_method: str
    confidence: AnalysisConfidence
    data_category: str
    is_placeholder: bool = False


class SensitiveDataDetectionService:
    def scan(self, content: JsonContainer) -> list[AnalysisFinding]:
        detected: list[_DetectedFinding] = []
        self._walk(content, "$", None, detected)
        return self._deduplicate_and_identify(detected)

    def _walk(
        self,
        value: JsonValue,
        path: str,
        field_name: str | None,
        detected: list[_DetectedFinding],
    ) -> None:
        normalized_field = self.normalize_field_name(field_name) if field_name else ""
        if isinstance(value, dict):
            if normalized_field in _DEBUG_FIELDS:
                detected.append(
                    self._finding(
                        AnalysisFindingType.DEBUG_PAYLOAD,
                        AnalysisFindingSeverity.MEDIUM,
                        "Debug request payload detected",
                        "A debug field contains a complete request-like object.",
                        path,
                        "[REDACTED_DEBUG_PAYLOAD]",
                        "field_name",
                        AnalysisConfidence.HIGH,
                        "debug_payload",
                    )
                )
            for key, child in value.items():
                self._walk(child, append_json_path(path, key), key, detected)
            return
        if isinstance(value, list):
            if normalized_field in _DEBUG_FIELDS:
                detected.append(
                    self._finding(
                        AnalysisFindingType.DEBUG_PAYLOAD,
                        AnalysisFindingSeverity.MEDIUM,
                        "Debug request payload detected",
                        "A debug field contains a complete request-like array.",
                        path,
                        "[REDACTED_DEBUG_PAYLOAD]",
                        "field_name",
                        AnalysisConfidence.HIGH,
                        "debug_payload",
                    )
                )
            for index, child in enumerate(value):
                self._walk(child, append_json_path(path, index), field_name, detected)
            return
        self._detect_scalar(value, path, normalized_field, detected)

    def _detect_scalar(
        self,
        value: object,
        path: str,
        field_name: str,
        detected: list[_DetectedFinding],
    ) -> None:
        if value is None or isinstance(value, bool):
            return
        text = str(value).strip()
        if not text:
            return
        placeholder = self.is_placeholder(text)

        if _PROMPT_INJECTION_PATTERN.search(text):
            self._add(
                detected,
                AnalysisFindingType.PROMPT_INJECTION,
                AnalysisFindingSeverity.HIGH,
                "Prompt manipulation instruction detected",
                "Untrusted document text attempts to alter the analysis instructions.",
                path,
                text,
                "prompt_injection_pattern",
                AnalysisConfidence.HIGH,
                "prompt_injection",
            )

        if _PRIVATE_KEY_PATTERN.search(text):
            self._add(
                detected,
                AnalysisFindingType.PRIVATE_KEY,
                AnalysisFindingSeverity.CRITICAL,
                "Private key material detected",
                "The document contains a private key marker.",
                path,
                text,
                "private_key_marker",
                AnalysisConfidence.HIGH,
                "private_key",
            )

        for match in _CONNECTION_STRING_PATTERN.finditer(text):
            severity = (
                AnalysisFindingSeverity.MEDIUM
                if self.is_placeholder(match.group(0))
                else AnalysisFindingSeverity.HIGH
            )
            self._add(
                detected,
                AnalysisFindingType.CONNECTION_STRING,
                severity,
                "Credentialed connection string detected",
                "A service connection string embeds a username and password.",
                path,
                match.group(0),
                "credentialed_uri_pattern",
                AnalysisConfidence.HIGH,
                "connection_string",
                self.is_placeholder(match.group(0)),
            )

        for match in _EMAIL_PATTERN.finditer(text):
            self._add(
                detected,
                AnalysisFindingType.EMAIL,
                AnalysisFindingSeverity.LOW,
                "Email address detected",
                "The document contains an email address.",
                path,
                match.group(0),
                "email_pattern",
                AnalysisConfidence.HIGH,
                "email",
            )

        self._detect_field_context(text, path, field_name, placeholder, detected)
        if (
            field_name not in _PHONE_FIELDS
            and self._looks_like_phone(text)
            and any(character in text for character in "+()-")
        ):
            self._add(
                detected,
                AnalysisFindingType.PHONE,
                AnalysisFindingSeverity.MEDIUM,
                "Phone number detected",
                "A formatted value has the shape of a telephone number.",
                path,
                text,
                "formatted_phone_pattern",
                AnalysisConfidence.MEDIUM,
                "phone",
            )
        self._detect_pattern_credentials(text, path, detected)
        self._detect_cards(text, path, field_name, detected)
        self._detect_ip_addresses(text, path, field_name, detected)

    def _detect_field_context(
        self,
        text: str,
        path: str,
        field_name: str,
        placeholder: bool,
        detected: list[_DetectedFinding],
    ) -> None:
        credential_severity = (
            AnalysisFindingSeverity.MEDIUM
            if placeholder
            else AnalysisFindingSeverity.HIGH
        )
        if field_name in _PASSWORD_FIELDS:
            self._add(
                detected,
                AnalysisFindingType.PASSWORD,
                credential_severity,
                "Password field detected",
                "A password-like field contains a value.",
                path,
                text,
                "field_name",
                AnalysisConfidence.HIGH,
                "password",
                placeholder,
            )
        if field_name in _API_KEY_FIELDS:
            finding_type = (
                AnalysisFindingType.AWS_ACCESS_KEY
                if "access_key" in field_name
                else AnalysisFindingType.API_KEY
            )
            category = (
                "aws_access_key"
                if finding_type == AnalysisFindingType.AWS_ACCESS_KEY
                else "api_key"
            )
            self._add(
                detected,
                finding_type,
                credential_severity,
                "API or access key field detected",
                "A credential field contains key material.",
                path,
                text,
                "field_name",
                AnalysisConfidence.HIGH,
                category,
                placeholder,
            )
        if field_name in _ACCESS_TOKEN_FIELDS:
            self._add_token(
                detected,
                AnalysisFindingType.ACCESS_TOKEN,
                "Access token detected",
                text,
                path,
                placeholder,
            )
        elif field_name in _REFRESH_TOKEN_FIELDS:
            self._add_token(
                detected,
                AnalysisFindingType.REFRESH_TOKEN,
                "Refresh token detected",
                text,
                path,
                placeholder,
            )
        elif field_name in _TOKEN_FIELDS:
            self._add_token(
                detected,
                AnalysisFindingType.TOKEN,
                "Authentication token detected",
                text,
                path,
                placeholder,
            )
        if field_name in _SESSION_FIELDS:
            self._add_token(
                detected,
                AnalysisFindingType.SESSION_ID,
                "Session identifier detected",
                text,
                path,
                placeholder,
            )
        if field_name in _SESSION_COOKIE_FIELDS:
            self._add_token(
                detected,
                AnalysisFindingType.SESSION_COOKIE,
                "Session cookie detected",
                text,
                path,
                placeholder,
            )
        if field_name in _FULL_NAME_FIELDS and self._looks_like_full_name(text):
            self._add(
                detected,
                AnalysisFindingType.FULL_NAME,
                AnalysisFindingSeverity.LOW,
                "Full name detected",
                "A name-like field contains a full name.",
                path,
                text,
                "field_name_and_value_shape",
                AnalysisConfidence.MEDIUM,
                "full_name",
            )
        if field_name in _PHONE_FIELDS and self._looks_like_phone(text):
            self._add(
                detected,
                AnalysisFindingType.PHONE,
                AnalysisFindingSeverity.MEDIUM,
                "Phone number detected",
                "A phone field contains a telephone number.",
                path,
                text,
                "field_name_and_phone_pattern",
                AnalysisConfidence.HIGH,
                "phone",
            )
        if field_name in _PERSONAL_ID_FIELDS and self._looks_like_personal_id(text):
            self._add(
                detected,
                AnalysisFindingType.PERSONAL_ID,
                AnalysisFindingSeverity.MEDIUM,
                "Personal identifier detected",
                "A personal document field contains an identifier.",
                path,
                text,
                "field_name_and_identifier_pattern",
                AnalysisConfidence.HIGH,
                "personal_id",
            )
        if field_name in _PASSPORT_FIELDS and re.fullmatch(r"[A-Za-z0-9-]{5,20}", text):
            self._add(
                detected,
                AnalysisFindingType.PASSPORT,
                AnalysisFindingSeverity.HIGH,
                "Passport identifier detected",
                "A passport field contains an identifier.",
                path,
                text,
                "field_name_and_identifier_pattern",
                AnalysisConfidence.HIGH,
                "passport",
            )
        if field_name in _CVV_FIELDS and re.fullmatch(r"\d{3,4}", text):
            self._add(
                detected,
                AnalysisFindingType.CVV,
                AnalysisFindingSeverity.HIGH,
                "Card verification code detected",
                "A card security-code field contains a CVV/CVC.",
                path,
                text,
                "field_name_and_cvv_pattern",
                AnalysisConfidence.HIGH,
                "cvv",
            )
        if field_name in _EXPIRATION_FIELDS and _EXPIRATION_PATTERN.fullmatch(text):
            self._add(
                detected,
                AnalysisFindingType.CARD_EXPIRATION,
                AnalysisFindingSeverity.MEDIUM,
                "Card expiration detected",
                "A payment-card expiration field contains a date.",
                path,
                text,
                "field_name_and_expiration_pattern",
                AnalysisConfidence.HIGH,
                "card_expiration",
            )
        if field_name in _BANK_FIELDS and len(re.sub(r"\W", "", text)) >= 6:
            self._add(
                detected,
                AnalysisFindingType.BANK_ACCOUNT,
                AnalysisFindingSeverity.HIGH,
                "Banking identifier detected",
                "A banking field contains account information.",
                path,
                text,
                "field_name",
                AnalysisConfidence.MEDIUM,
                "bank_account",
            )
        if field_name in _FINANCIAL_FIELDS:
            self._add(
                detected,
                AnalysisFindingType.FINANCIAL_DATA,
                AnalysisFindingSeverity.MEDIUM,
                "Financial information detected",
                "A financial field contains a monetary or credit value.",
                path,
                text,
                "field_name",
                AnalysisConfidence.MEDIUM,
                "financial_data",
            )
        if field_name in _DEBUG_FIELDS:
            self._add(
                detected,
                AnalysisFindingType.DEBUG_PAYLOAD,
                AnalysisFindingSeverity.MEDIUM,
                "Debug request payload detected",
                "A debug field contains request-like content.",
                path,
                text,
                "field_name",
                AnalysisConfidence.HIGH,
                "debug_payload",
            )

    def _detect_pattern_credentials(
        self,
        text: str,
        path: str,
        detected: list[_DetectedFinding],
    ) -> None:
        for match in _AWS_ACCESS_KEY_PATTERN.finditer(text):
            placeholder = (
                self.is_placeholder(match.group(0))
                or match.group(0) == "AKIAIOSFODNN7EXAMPLE"
            )
            severity = (
                AnalysisFindingSeverity.MEDIUM
                if placeholder
                else AnalysisFindingSeverity.HIGH
            )
            self._add(
                detected,
                AnalysisFindingType.AWS_ACCESS_KEY,
                severity,
                "AWS access key detected",
                "The value matches the AWS access-key format.",
                path,
                match.group(0),
                "aws_access_key_pattern",
                AnalysisConfidence.HIGH,
                "aws_access_key",
                placeholder,
            )
        for pattern in _KNOWN_TOKEN_PATTERNS:
            for match in pattern.finditer(text):
                placeholder = self.is_placeholder(match.group(0))
                severity = (
                    AnalysisFindingSeverity.MEDIUM
                    if placeholder
                    else AnalysisFindingSeverity.HIGH
                )
                finding_type = (
                    AnalysisFindingType.API_KEY
                    if match.group(0).lower().startswith(("sk-", "sg."))
                    else AnalysisFindingType.TOKEN
                )
                category = (
                    "api_key"
                    if finding_type == AnalysisFindingType.API_KEY
                    else "token"
                )
                self._add(
                    detected,
                    finding_type,
                    severity,
                    "Credential pattern detected",
                    "The value matches a recognized API credential format.",
                    path,
                    match.group(0),
                    "recognized_credential_pattern",
                    AnalysisConfidence.HIGH,
                    category,
                    placeholder,
                )

    def _detect_cards(
        self,
        text: str,
        path: str,
        field_name: str,
        detected: list[_DetectedFinding],
    ) -> None:
        if field_name in _CARD_LAST4_FIELDS:
            return
        for match in _CARD_PATTERN.finditer(text):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and self.passes_luhn(digits):
                self._add(
                    detected,
                    AnalysisFindingType.CREDIT_CARD,
                    AnalysisFindingSeverity.HIGH,
                    "Complete payment card detected",
                    "A complete payment-card number passes Luhn validation.",
                    path,
                    digits,
                    "luhn_and_value_pattern",
                    AnalysisConfidence.HIGH,
                    "payment_card",
                )

    def _detect_ip_addresses(
        self,
        text: str,
        path: str,
        field_name: str,
        detected: list[_DetectedFinding],
    ) -> None:
        if field_name not in _IP_FIELDS and "." not in text:
            return
        for match in _IPV4_PATTERN.finditer(text):
            try:
                ipaddress.ip_address(match.group(0))
            except ValueError:
                continue
            self._add(
                detected,
                AnalysisFindingType.IP_ADDRESS,
                AnalysisFindingSeverity.LOW,
                "IP address detected",
                "The document contains a valid IP address.",
                path,
                match.group(0),
                "ip_address_pattern",
                AnalysisConfidence.HIGH,
                "ip_address",
            )

    def _add_token(
        self,
        detected: list[_DetectedFinding],
        finding_type: AnalysisFindingType,
        title: str,
        value: str,
        path: str,
        placeholder: bool,
    ) -> None:
        severity = (
            AnalysisFindingSeverity.MEDIUM
            if placeholder
            else AnalysisFindingSeverity.HIGH
        )
        self._add(
            detected,
            finding_type,
            severity,
            title,
            "A token or session field contains credential material.",
            path,
            value,
            "field_name",
            AnalysisConfidence.HIGH,
            finding_type.value,
            placeholder,
        )

    def _add(
        self,
        detected: list[_DetectedFinding],
        finding_type: AnalysisFindingType,
        severity: AnalysisFindingSeverity,
        title: str,
        description: str,
        path: str,
        raw_evidence: object,
        method: str,
        confidence: AnalysisConfidence,
        category: str,
        placeholder: bool = False,
    ) -> None:
        detected.append(
            self._finding(
                finding_type,
                severity,
                title,
                description,
                path,
                mask_sensitive_value(raw_evidence, finding_type),
                method,
                confidence,
                category,
                placeholder,
            )
        )

    def _finding(
        self,
        finding_type: AnalysisFindingType,
        severity: AnalysisFindingSeverity,
        title: str,
        description: str,
        path: str,
        evidence: str,
        method: str,
        confidence: AnalysisConfidence,
        category: str,
        placeholder: bool = False,
    ) -> _DetectedFinding:
        return _DetectedFinding(
            finding_type=finding_type,
            severity=severity,
            title=title,
            description=description,
            json_path=path,
            evidence=evidence,
            detection_method=method,
            confidence=confidence,
            data_category=category,
            is_placeholder=placeholder,
        )

    def _deduplicate_and_identify(
        self, detected: Iterable[_DetectedFinding]
    ) -> list[AnalysisFinding]:
        grouped: dict[tuple[str, str, str], tuple[_DetectedFinding, int, set[str]]] = {}
        for item in detected:
            key = (item.finding_type.value, item.json_path, item.evidence)
            existing = grouped.get(key)
            if existing is None:
                grouped[key] = (item, 1, {item.detection_method})
                continue
            representative, occurrences, methods = existing
            if item.detection_method in methods:
                occurrences += 1
            methods.add(item.detection_method)
            grouped[key] = (representative, occurrences, methods)
        findings: list[AnalysisFinding] = []
        for index, (item, occurrences, methods) in enumerate(grouped.values(), start=1):
            findings.append(
                AnalysisFinding(
                    finding_id=f"f{index}",
                    finding_type=item.finding_type,
                    severity=item.severity,
                    title=item.title,
                    description=item.description,
                    json_path=item.json_path,
                    evidence=item.evidence,
                    detection_method="+".join(sorted(methods)),
                    confidence=item.confidence,
                    occurrences=occurrences,
                    data_category=item.data_category,
                    is_placeholder=item.is_placeholder,
                )
            )
        return findings

    @staticmethod
    def passes_luhn(digits: str) -> bool:
        if not digits.isdigit() or not 13 <= len(digits) <= 19 or len(set(digits)) == 1:
            return False
        total = 0
        for index, character in enumerate(reversed(digits)):
            digit = int(character)
            if index % 2:
                digit *= 2
                if digit > 9:
                    digit -= 9
            total += digit
        return total % 10 == 0

    @staticmethod
    def is_placeholder(value: str) -> bool:
        return bool(_PLACEHOLDER_PATTERN.search(value.strip()))

    @staticmethod
    def normalize_field_name(field_name: str | None) -> str:
        if not field_name:
            return ""
        normalized = unicodedata.normalize("NFKD", field_name)
        ascii_name = normalized.encode("ascii", "ignore").decode("ascii").lower()
        return re.sub(r"[^a-z0-9]+", "_", ascii_name).strip("_")

    @staticmethod
    def _looks_like_full_name(value: str) -> bool:
        parts = value.split()
        return 2 <= len(parts) <= 6 and all(
            re.fullmatch(r"[A-Za-zÀ-ÿ'\-]{2,}", part) for part in parts
        )

    @staticmethod
    def _looks_like_phone(value: str) -> bool:
        digits = re.sub(r"\D", "", value)
        return 7 <= len(digits) <= 15 and bool(_PHONE_PATTERN.fullmatch(value))

    @staticmethod
    def _looks_like_personal_id(value: str) -> bool:
        compact = re.sub(r"[.\s-]", "", value)
        return bool(re.fullmatch(r"[A-Za-z]?\d{6,12}[A-Za-z]?", compact))
