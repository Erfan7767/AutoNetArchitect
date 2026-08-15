"""Offline secret and credential leak detection."""
from __future__ import annotations

import math
import re

from .models import Severity, ValidationDiagnostic, ValidationStage


class SecretLeakScanner:
    """Detect likely credential material without returning the secret itself."""

    PATTERNS = (
        ("plaintext_password", re.compile(r"(?i)\b(?:password|passwd)\s+(?:0\s+)?(?!secret://|7\s+|8\s+|9\s+)([^\s]+)")),
        ("enable_password", re.compile(r"(?i)^\s*enable\s+password\s+")),
        ("snmp_community", re.compile(r"(?i)\bsnmp-server\s+community\s+(?!secret://)([^\s]+)")),
        ("radius_shared_secret", re.compile(r"(?i)\b(?:radius|tacacs)(?:-server)?\s+.*\b(?:key|secret)\s+(?!secret://)([^\s]+)")),
        ("pre_shared_key", re.compile(r"(?i)\b(?:pre-shared-key|pre_shared_key|psk)\s+(?!secret://)([^\s]+)")),
        ("wifi_passphrase", re.compile(r"(?i)\b(?:wpa-passphrase|passphrase)\s+(?!secret://)([^\s]+)")),
        ("api_key", re.compile(r"(?i)\b(?:api[_-]?key|token)\s*[:=]\s*(?!secret://)([^\s]+)")),
        ("private_key_block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    )
    SENSITIVE_WORDS = re.compile(r"(?i)(password|secret|token|key|psk|community)")

    def scan(self, config_text: str, vendor: str, platform: str) -> list[ValidationDiagnostic]:
        """Return critical diagnostics while redacting values from context."""
        diagnostics: list[ValidationDiagnostic] = []
        for number, line in enumerate(config_text.splitlines(), 1):
            for secret_type, pattern in self.PATTERNS:
                match = pattern.search(line)
                if match:
                    context = self._redacted_context(line, match.group(0))
                    diagnostics.append(ValidationDiagnostic("SECRET_LEAK", f"Potential {secret_type} detected; value was redacted from the diagnostic.", Severity.CRITICAL, ValidationStage.SECRET_SCAN, number, context, remediation="Use a secret:// reference resolved by SecretManager or an approved hashed form."))
                    break
            if self._high_entropy_candidate(line):
                diagnostics.append(ValidationDiagnostic("HIGH_ENTROPY_SECRET_CANDIDATE", "High-entropy token near a sensitive keyword requires review.", Severity.CRITICAL, ValidationStage.SECRET_SCAN, number, self._redacted_context(line), remediation="Replace the inline token with a secret:// reference."))
        return diagnostics

    @staticmethod
    def _redacted_context(line: str, match_text: str | None = None) -> str:
        text = line.strip()
        if match_text:
            return text.replace(match_text, "<redacted>")
        return re.sub(r"(?i)(password|secret|token|key|psk|community)\s+\S+", r"\1 <redacted>", text)

    def _high_entropy_candidate(self, line: str) -> bool:
        if not self.SENSITIVE_WORDS.search(line):
            return False
        tokens = re.findall(r"[A-Za-z0-9+/=_-]{20,}", line)
        for token in tokens:
            counts = {character: token.count(character) for character in set(token)}
            entropy = -sum((count / len(token)) * math.log2(count / len(token)) for count in counts.values())
            if entropy >= 3.5 and not token.startswith("secret://"):
                return True
        return False
