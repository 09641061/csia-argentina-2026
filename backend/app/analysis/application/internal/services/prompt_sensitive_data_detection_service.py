from __future__ import annotations

import re
from dataclasses import dataclass

from app.analysis.application.internal.services.sensitive_data_detection_service import (
    SensitiveDataDetectionService,
)
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
from app.shared.domain.text_masking import mask_free_text

PROMPT_JSON_PATH = "$.prompt"

_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CARD_PATTERN = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
_AWS_ACCESS_KEY_PATTERN = re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")
_PRIVATE_KEY_PATTERN = re.compile(
    r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----", re.IGNORECASE
)
_CONNECTION_STRING_PATTERN = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis|amqp)://[^\s/:]+:[^\s/@]+@[^\s]+"
)
_KNOWN_TOKEN_PATTERNS = (
    (re.compile(r"\bsk-(?:live|test|proj)[A-Za-z0-9_-]{12,}\b", re.IGNORECASE), AnalysisFindingType.API_KEY),
    (re.compile(r"\bgh[opusr]_[A-Za-z0-9]{16,}\b"), AnalysisFindingType.TOKEN),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{12,}\b"), AnalysisFindingType.TOKEN),
    (re.compile(r"\bSG\.[A-Za-z0-9._-]{12,}\b"), AnalysisFindingType.API_KEY),
    (re.compile(r"\bhvs\.[A-Za-z0-9._-]{12,}\b"), AnalysisFindingType.TOKEN),
    (re.compile(r"\bey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), AnalysisFindingType.ACCESS_TOKEN),
)
_PHONE_PATTERN = re.compile(r"(?<!\w)(?:\+\d{1,3}[ -]?)?(?:\(\d{2,4}\)[ -]?)?\d[\d ()-]{7,}\d(?!\w)")

_LABELED_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], AnalysisFindingType, str], ...] = (
    (
        re.compile(
            r"(?i)\b(?:password|passwd|pwd|contrase(?:n|ñ)a|clave(?:\s+de\s+acceso)?|passphrase)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b|\bser(?:a|á)\b)?\s*[\"']?([^\s\"',;]{4,})"
        ),
        AnalysisFindingType.PASSWORD,
        "password",
    ),
    (
        re.compile(
            r"(?i)\b(?:api[_\- ]?key|clave[_\- ]?api|apikey|secret[_\- ]?key|client[_\- ]?secret)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b)?\s*[\"']?([^\s\"',;]{6,})"
        ),
        AnalysisFindingType.API_KEY,
        "api_key",
    ),
    (
        re.compile(
            r"(?i)\b(?:access[_\- ]?token|refresh[_\- ]?token|bearer|token\s+de\s+acceso|token)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b)?\s*[\"']?([A-Za-z0-9._\-]{8,})"
        ),
        AnalysisFindingType.TOKEN,
        "token",
    ),
    (
        re.compile(
            r"(?i)\b(?:session[_\- ]?id|sesi(?:o|ó)n|cookie|jsessionid|phpsessid)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b)?\s*[\"']?([A-Za-z0-9._\-]{8,})"
        ),
        AnalysisFindingType.SESSION_ID,
        "session_id",
    ),
    (
        re.compile(
            r"(?i)\b(?:cvv|cvc|c(?:o|ó)digo\s+de\s+seguridad|security\s+code)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b)?\s*[\"']?(\d{3,4})\b"
        ),
        AnalysisFindingType.CVV,
        "cvv",
    ),
    (
        re.compile(
            r"(?i)\b(?:dni|nif|nie|c(?:e|é)dula|documento\s+de\s+identidad|national\s+id|ssn)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b|n(?:o|ú)mero)?\s*[\"']?([A-Za-z]?[\d.\-]{6,14}[A-Za-z]?)\b"
        ),
        AnalysisFindingType.PERSONAL_ID,
        "personal_id",
    ),
    (
        re.compile(
            r"(?i)\b(?:pasaporte|passport)\b\s*(?:[:=]|\bes\b|\bis\b|n(?:o|ú)mero)?\s*[\"']?([A-Za-z0-9]{6,12})\b"
        ),
        AnalysisFindingType.PASSPORT,
        "passport",
    ),
    (
        re.compile(
            r"(?i)\b(?:iban|cbu|cvu|swift|bic|routing\s+number|n(?:u|ú)mero\s+de\s+cuenta|account\s+number)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b)?\s*[\"']?([A-Za-z0-9]{8,34})\b"
        ),
        AnalysisFindingType.BANK_ACCOUNT,
        "bank_account",
    ),
    (
        re.compile(
            r"(?i)\b(?:salario|sueldo|salary|income|ingresos|saldo|balance|credit\s+score)\b"
            r"\s*(?:[:=]|\bes\b|\bis\b|de)?\s*[\"']?((?:USD|EUR|ARS|\$|€)?\s?[\d.,]{3,})"
        ),
        AnalysisFindingType.FINANCIAL_DATA,
        "financial_data",
    ),
)

_INJECTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(
            r"(?i)\b(?:ignora|ignore|olvida|forget|descarta|disregard)\b[^.\n]{0,40}"
            r"\b(?:instruc\w+|reglas?|rules?|prompt|indicaciones|directrices)\b"
        ),
        "override_previous_instructions",
    ),
    (
        re.compile(r"(?i)\b(?:system\s+prompt|prompt\s+del\s+sistema|mensaje\s+de\s+sistema)\b"),
        "system_prompt_disclosure",
    ),
    (
        re.compile(
            r"(?i)\b(?:revela|revel(?:a|ar)|muestra|mu(?:e|é)strame|dame|reveal|show|print|dump|list)\b"
            r"[^.\n]{0,40}\b(?:credencial\w*|contrase(?:n|ñ)as?|claves?|secretos?|tokens?|"
            r"credentials?|secrets?|passwords?|api\s*keys?)\b"
        ),
        "credential_exfiltration_request",
    ),
    (
        re.compile(
            r"(?i)\b(?:eres\s+ahora|ahora\s+eres|act(?:ua|úa)\s+como|you\s+are\s+now|act\s+as|"
            r"pretend\s+to\s+be|from\s+now\s+on)\b"
        ),
        "role_redefinition",
    ),
    (
        re.compile(
            r"(?i)\b(?:modo\s+desarrollador|developer\s+mode|jailbreak|\bDAN\b|sin\s+restricciones|"
            r"without\s+restrictions|no\s+filters?|sin\s+filtros?)\b"
        ),
        "guardrail_bypass",
    ),
    (
        re.compile(
            r"(?i)\b(?:no\s+(?:reportes|informes|menciones)|do\s+not\s+report|don't\s+report|"
            r"oculta|hide\s+this)\b"
        ),
        "reporting_suppression",
    ),
    (
        re.compile(
            r"(?i)\b(?:devuelve|responde|return|mark|marca|clasifica)\b[^.\n]{0,25}"
            r"\b(?:low|bajo|allowed|permitido|safe|seguro)\b"
        ),
        "verdict_forcing",
    ),
    (
        re.compile(
            r"(?i)\b(?:omite|salta|bypass|evade|elude|skip)\b[^.\n]{0,30}"
            r"\b(?:seguridad|security|filtro|filter|revisi(?:o|ó)n|an(?:a|á)lisis|validaci(?:o|ó)n)\b"
        ),
        "security_bypass",
    ),
)

_PLACEHOLDER_PATTERN = re.compile(
    r"(?i)^(?:your[_ -]?(?:key|token|password)[_ -]?here|change[_ -]?me|ejemplo|example|placeholder|"
    r"dummy|fake|sample|redacted|masked|<[^>]+>|\$\{[^}]+\}|x{4,}|\*{4,}|123456|abc123)$"
)

# Natural language rarely writes "password: value". People write "la contraseña
# del cliente es SuperSecret123". These two rules cover that shape: a credential
# keyword, then a secret-looking token somewhere in the same clause.
_CREDENTIAL_KEYWORD_PATTERN = re.compile(
    r"(?i)\b(?:password|passwd|pwd|contrase(?:n|ñ)a|clave|passphrase|api[_\- ]?key|apikey|"
    r"secret|secreto|token|credencial(?:es)?|credentials?)\b"
)
_KEYWORD_PROXIMITY_CHARACTERS = 80
_CANDIDATE_TOKEN_PATTERN = re.compile(r"[^\s,;:.\"'()\[\]]{6,128}")
_COMMON_WORD_PATTERN = re.compile(r"(?i)^[a-záéíóúñü]+$")


@dataclass(frozen=True, slots=True)
class _PromptFinding:
    finding_type: AnalysisFindingType
    severity: AnalysisFindingSeverity
    title: str
    description: str
    raw_value: str
    detection_method: str
    confidence: AnalysisConfidence
    data_category: str
    is_placeholder: bool = False
    injection_marker: str | None = None


class PromptSensitiveDataDetectionService:
    """
    Deterministic scanner for the free-text prompt.

    A prompt has no structure to walk, so detection combines labelled context
    ("password: ..."), well-known credential shapes, identity shapes validated
    with Luhn or format rules, and an explicit prompt-injection ruleset in
    Spanish and English. Placeholders lower the severity instead of being
    dropped, so a documentation example does not read as a real secret and does
    not vanish from the audit trail either.
    """

    def scan(self, prompt: str) -> list[AnalysisFinding]:
        return self._to_findings(self._detect(prompt))

    def mask_text(self, prompt: str) -> str:
        """
        Return the prompt with every detected value replaced by its masked form.

        Detection and masking share one source of truth here, so anything the
        scanner can find is also removed from the preview stored for the audit
        trail and from the excerpt sent to the security model. The generic
        free-text masker runs afterwards as a second net.
        """

        masked = prompt
        for item in sorted(self._detect(prompt), key=lambda item: -len(item.raw_value)):
            if not item.raw_value:
                continue
            masked = masked.replace(
                item.raw_value, mask_sensitive_value(item.raw_value, item.finding_type)
            )
        return mask_free_text(masked)

    def _detect(self, prompt: str) -> list[_PromptFinding]:
        detected: list[_PromptFinding] = []
        self._detect_injection(prompt, detected)
        self._detect_labeled_secrets(prompt, detected)
        self._detect_credential_patterns(prompt, detected)
        self._detect_identities(prompt, detected)
        self._detect_keyword_proximity_secrets(prompt, detected)
        return detected

    def injection_markers(self, prompt: str) -> tuple[str, ...]:
        markers = {marker for pattern, marker in _INJECTION_PATTERNS if pattern.search(prompt)}
        return tuple(sorted(markers))

    def _detect_injection(self, prompt: str, detected: list[_PromptFinding]) -> None:
        for pattern, marker in _INJECTION_PATTERNS:
            match = pattern.search(prompt)
            if match is None:
                continue
            detected.append(
                _PromptFinding(
                    finding_type=AnalysisFindingType.PROMPT_INJECTION,
                    severity=AnalysisFindingSeverity.HIGH,
                    title="Intento de manipulación de instrucciones",
                    description=(
                        "El texto contiene una instrucción que intenta alterar el comportamiento "
                        "del sistema de seguridad o extraer información interna."
                    ),
                    raw_value=match.group(0),
                    detection_method=f"prompt_injection:{marker}",
                    confidence=AnalysisConfidence.HIGH,
                    data_category="prompt_injection",
                    injection_marker=marker,
                )
            )

    def _detect_labeled_secrets(self, prompt: str, detected: list[_PromptFinding]) -> None:
        for pattern, finding_type, category in _LABELED_SECRET_PATTERNS:
            for match in pattern.finditer(prompt):
                value = match.group(1)
                if not value:
                    continue
                placeholder = self.is_placeholder(value)
                if finding_type == AnalysisFindingType.PERSONAL_ID and not self._looks_like_personal_id(value):
                    continue
                if finding_type == AnalysisFindingType.BANK_ACCOUNT and not re.fullmatch(
                    r"[A-Za-z0-9]{8,34}", value
                ):
                    continue
                detected.append(
                    _PromptFinding(
                        finding_type=finding_type,
                        severity=self._severity_for(finding_type, placeholder),
                        title=self._title_for(finding_type),
                        description=(
                            "La consulta menciona explícitamente este tipo de dato junto a un valor."
                        ),
                        raw_value=value,
                        detection_method="labeled_value_in_text",
                        confidence=AnalysisConfidence.HIGH if not placeholder else AnalysisConfidence.MEDIUM,
                        data_category=category,
                        is_placeholder=placeholder,
                    )
                )

    def _detect_credential_patterns(self, prompt: str, detected: list[_PromptFinding]) -> None:
        if _PRIVATE_KEY_PATTERN.search(prompt):
            detected.append(
                _PromptFinding(
                    finding_type=AnalysisFindingType.PRIVATE_KEY,
                    severity=AnalysisFindingSeverity.CRITICAL,
                    title="Material de clave privada",
                    description="La consulta incluye el encabezado de una clave privada.",
                    raw_value="-----BEGIN PRIVATE KEY-----",
                    detection_method="private_key_marker",
                    confidence=AnalysisConfidence.HIGH,
                    data_category="private_key",
                )
            )
        for match in _CONNECTION_STRING_PATTERN.finditer(prompt):
            detected.append(
                _PromptFinding(
                    finding_type=AnalysisFindingType.CONNECTION_STRING,
                    severity=AnalysisFindingSeverity.HIGH,
                    title="Cadena de conexión con credenciales",
                    description="La consulta incluye una URI de servicio con usuario y contraseña.",
                    raw_value=match.group(0),
                    detection_method="credentialed_uri_pattern",
                    confidence=AnalysisConfidence.HIGH,
                    data_category="connection_string",
                )
            )
        for match in _AWS_ACCESS_KEY_PATTERN.finditer(prompt):
            placeholder = match.group(0) == "AKIAIOSFODNN7EXAMPLE"
            detected.append(
                _PromptFinding(
                    finding_type=AnalysisFindingType.AWS_ACCESS_KEY,
                    severity=self._severity_for(AnalysisFindingType.AWS_ACCESS_KEY, placeholder),
                    title="Clave de acceso de AWS",
                    description="El valor coincide con el formato de una AWS access key.",
                    raw_value=match.group(0),
                    detection_method="aws_access_key_pattern",
                    confidence=AnalysisConfidence.HIGH,
                    data_category="aws_access_key",
                    is_placeholder=placeholder,
                )
            )
        for pattern, finding_type in _KNOWN_TOKEN_PATTERNS:
            for match in pattern.finditer(prompt):
                detected.append(
                    _PromptFinding(
                        finding_type=finding_type,
                        severity=AnalysisFindingSeverity.HIGH,
                        title="Credencial con formato reconocido",
                        description="El valor coincide con el formato de una credencial conocida.",
                        raw_value=match.group(0),
                        detection_method="recognized_credential_pattern",
                        confidence=AnalysisConfidence.HIGH,
                        data_category="api_key"
                        if finding_type == AnalysisFindingType.API_KEY
                        else "token",
                    )
                )

    def _detect_identities(self, prompt: str, detected: list[_PromptFinding]) -> None:
        for match in _EMAIL_PATTERN.finditer(prompt):
            detected.append(
                _PromptFinding(
                    finding_type=AnalysisFindingType.EMAIL,
                    severity=AnalysisFindingSeverity.MEDIUM,
                    title="Dirección de correo electrónico",
                    description="La consulta contiene una dirección de correo identificable.",
                    raw_value=match.group(0),
                    detection_method="email_pattern",
                    confidence=AnalysisConfidence.HIGH,
                    data_category="email",
                )
            )
        for match in _CARD_PATTERN.finditer(prompt):
            digits = re.sub(r"\D", "", match.group(0))
            if 13 <= len(digits) <= 19 and SensitiveDataDetectionService.passes_luhn(digits):
                detected.append(
                    _PromptFinding(
                        finding_type=AnalysisFindingType.CREDIT_CARD,
                        severity=AnalysisFindingSeverity.HIGH,
                        title="Número completo de tarjeta",
                        description="Un número de tarjeta completo supera la validación de Luhn.",
                        raw_value=digits,
                        detection_method="luhn_and_value_pattern",
                        confidence=AnalysisConfidence.HIGH,
                        data_category="payment_card",
                    )
                )
                continue
            if len(digits) >= 7 and not self._is_covered(detected, match.group(0)):
                self._add_phone_if_shaped(match.group(0), detected)
        for match in _PHONE_PATTERN.finditer(prompt):
            self._add_phone_if_shaped(match.group(0), detected)

    def _detect_keyword_proximity_secrets(
        self,
        prompt: str,
        detected: list[_PromptFinding],
    ) -> None:
        already_seen = {(item.finding_type, item.raw_value) for item in detected}
        for keyword in _CREDENTIAL_KEYWORD_PATTERN.finditer(prompt):
            window = prompt[keyword.end() : keyword.end() + _KEYWORD_PROXIMITY_CHARACTERS]
            for candidate in _CANDIDATE_TOKEN_PATTERN.finditer(window):
                value = candidate.group(0)
                if not self._looks_like_secret_value(value):
                    continue
                key = (AnalysisFindingType.PASSWORD, value)
                if key in already_seen or any(
                    value in item.raw_value or item.raw_value in value for item in detected
                ):
                    break
                placeholder = self.is_placeholder(value)
                detected.append(
                    _PromptFinding(
                        finding_type=AnalysisFindingType.PASSWORD,
                        severity=self._severity_for(AnalysisFindingType.PASSWORD, placeholder),
                        title="Credencial mencionada en la consulta",
                        description=(
                            "La consulta menciona una credencial y a continuación aparece un "
                            "valor con forma de secreto."
                        ),
                        raw_value=value,
                        detection_method="credential_keyword_proximity",
                        confidence=AnalysisConfidence.MEDIUM,
                        data_category="password",
                        is_placeholder=placeholder,
                    )
                )
                already_seen.add(key)
                break

    @staticmethod
    def _looks_like_secret_value(value: str) -> bool:
        """
        A token that reads like a secret rather than like a normal word.

        Plain words, even long ones, are rejected; a mix of character classes is
        what separates "SuperSecret123" from "información".
        """

        if len(value) < 6 or len(value) > 128:
            return False
        if _COMMON_WORD_PATTERN.fullmatch(value):
            return False
        classes = sum(
            (
                any(character.islower() for character in value),
                any(character.isupper() for character in value),
                any(character.isdigit() for character in value),
                any(not character.isalnum() for character in value),
            )
        )
        return classes >= 3 or (
            any(character.isdigit() for character in value)
            and any(character.isalpha() for character in value)
        )

    def _add_phone_if_shaped(self, value: str, detected: list[_PromptFinding]) -> None:
        digits = re.sub(r"\D", "", value)
        if not 7 <= len(digits) <= 15:
            return
        if self._is_covered(detected, value.strip()):
            return
        detected.append(
            _PromptFinding(
                finding_type=AnalysisFindingType.PHONE,
                severity=AnalysisFindingSeverity.MEDIUM,
                title="Número de teléfono",
                description="La consulta contiene un valor con forma de número telefónico.",
                raw_value=value.strip(),
                detection_method="formatted_phone_pattern",
                confidence=AnalysisConfidence.MEDIUM,
                data_category="phone",
            )
        )

    def _is_covered(self, detected: list[_PromptFinding], value: str) -> bool:
        compact = re.sub(r"\D", "", value)
        return any(
            compact and compact in re.sub(r"\D", "", item.raw_value) for item in detected
        )

    def _severity_for(
        self,
        finding_type: AnalysisFindingType,
        placeholder: bool,
    ) -> AnalysisFindingSeverity:
        if placeholder:
            return AnalysisFindingSeverity.MEDIUM
        if finding_type == AnalysisFindingType.PRIVATE_KEY:
            return AnalysisFindingSeverity.CRITICAL
        if finding_type in {
            AnalysisFindingType.FINANCIAL_DATA,
            AnalysisFindingType.PERSONAL_ID,
        }:
            return AnalysisFindingSeverity.MEDIUM
        return AnalysisFindingSeverity.HIGH

    def _title_for(self, finding_type: AnalysisFindingType) -> str:
        titles = {
            AnalysisFindingType.PASSWORD: "Contraseña en la consulta",
            AnalysisFindingType.API_KEY: "Clave de API en la consulta",
            AnalysisFindingType.TOKEN: "Token de autenticación en la consulta",
            AnalysisFindingType.SESSION_ID: "Identificador de sesión en la consulta",
            AnalysisFindingType.CVV: "Código de seguridad de tarjeta",
            AnalysisFindingType.PERSONAL_ID: "Documento de identidad",
            AnalysisFindingType.PASSPORT: "Número de pasaporte",
            AnalysisFindingType.BANK_ACCOUNT: "Identificador bancario",
            AnalysisFindingType.FINANCIAL_DATA: "Información financiera",
        }
        return titles.get(finding_type, "Dato sensible detectado")

    def _to_findings(self, detected: list[_PromptFinding]) -> list[AnalysisFinding]:
        grouped: dict[tuple[str, str], tuple[_PromptFinding, int]] = {}
        for item in detected:
            masked = mask_sensitive_value(item.raw_value, item.finding_type)
            key = (item.finding_type.value, masked)
            existing = grouped.get(key)
            grouped[key] = (item, existing[1] + 1) if existing else (item, 1)

        findings: list[AnalysisFinding] = []
        for index, (item, occurrences) in enumerate(grouped.values(), start=1):
            findings.append(
                AnalysisFinding(
                    finding_id=f"f{index}",
                    finding_type=item.finding_type,
                    severity=item.severity,
                    title=item.title,
                    description=item.description,
                    json_path=PROMPT_JSON_PATH,
                    evidence=mask_sensitive_value(item.raw_value, item.finding_type),
                    detection_method=item.detection_method,
                    confidence=item.confidence,
                    occurrences=occurrences,
                    data_category=item.data_category,
                    is_placeholder=item.is_placeholder,
                )
            )
        return findings

    @staticmethod
    def is_placeholder(value: str) -> bool:
        return bool(_PLACEHOLDER_PATTERN.fullmatch(value.strip()))

    @staticmethod
    def _looks_like_personal_id(value: str) -> bool:
        compact = re.sub(r"[.\s-]", "", value)
        return bool(re.fullmatch(r"[A-Za-z]?\d{6,12}[A-Za-z]?", compact))
