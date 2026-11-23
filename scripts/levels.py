"""Private Fox – Definition der Schutzstufen 0–4.

Hieraus erzeugt prepare_tree.py die Dateien distribution/policies-level0.json … level4.json.
Welche davon gilt, entscheidet beim Start die Datei "privatefox-level" im Benutzerordner
(wird vom Schutz-Knopf in der Symbolleiste geschrieben).

Doku der Richtlinien: https://mozilla.github.io/policy-templates/
uBlock-Origin-Verwaltung: https://github.com/gorhill/uBlock/wiki/Deploying-uBlock-Origin
"""

UBO_ID = "uBlock0@raymondhill.net"
UBO_URL = "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"

NAMES = ["Aus", "Ausgewogen", "Stark", "Extrem", "Paranoid"]

# uBlock-Origin-Filterlisten (interne uBO-Kennungen)
_BASE = [
    "user-filters",
    "ublock-filters",
    "ublock-badware",
    "ublock-privacy",
    "ublock-quick-fixes",
    "ublock-unbreak",
    "easylist",
    "easyprivacy",
    "DEU-0",  # EasyList Germany
]
_STRONG = _BASE + ["urlhaus-1", "plowe-0"]
_EXTREME = _STRONG + [
    "fanboy-cookiemonster",
    "ublock-cookies-easylist",
    "fanboy-annoyance",
    "ublock-annoyances",
]
UBO_LISTS = {0: ["user-filters"], 1: _BASE, 2: _STRONG, 3: _EXTREME, 4: _EXTREME}

# Zusätzliche statische uBO-Filter. Pro Seite lassen sie sich im uBO-Popup wieder erlauben.
UBO_FILTERS = {
    0: [],
    1: [],
    2: [],
    3: ["*$font,3p", "*$object,3p"],
    4: ["*$font,3p", "*$object,3p", "*$script,3p", "*$frame,3p"],
}


def _ubo_settings(level: int) -> dict:
    user_settings = [
        ["hyperlinkAuditingDisabled", "true"],
        ["prefetchingDisabled", "true"],
        ["webrtcIPAddressHidden", "true" if level >= 2 else "false"],
        ["advancedUserEnabled", "true" if level >= 3 else "false"],
    ]
    return {
        "toOverwrite": {
            "filterLists": UBO_LISTS[level],
            "filters": UBO_FILTERS[level],
        },
        "userSettings": user_settings,
    }


def build_policies(level: int, version: str) -> dict:
    """Komplette policies.json für eine Stufe."""
    langpack_url = (
        f"https://archive.mozilla.org/pub/firefox/releases/{version}/linux-x86_64/xpi/de.xpi"
    )

    p = {
        # --- immer: keine Datensammlung, keine Werbung, kein Mozilla-Kram ---
        "DisableTelemetry": True,
        "DisableFirefoxStudies": True,
        "DisablePocket": True,
        "DisableFeedbackCommands": True,
        "DisableSetDesktopBackground": True,
        "DontCheckDefaultBrowser": True,
        "NoDefaultBookmarks": True,
        "OverrideFirstRunPage": "",
        "OverridePostUpdatePage": "",
        "UserMessaging": {
            "ExtensionRecommendations": False,
            "FeatureRecommendations": False,
            "UrlbarInterventions": False,
            "SkipOnboarding": True,
            "MoreFromMozilla": False,
            "Locked": False,
        },
        "FirefoxHome": {
            "SponsoredTopSites": False,
            "SponsoredPocket": False,
            "Pocket": False,
            "Snippets": False,
            "Locked": False,
        },
        "FirefoxSuggest": {
            "WebSuggestions": False,
            "SponsoredSuggestions": False,
            "ImproveSuggest": False,
            "Locked": False,
        },
        "Homepage": {"URL": "https://duckduckgo.com/", "Locked": False},
        "RequestedLocales": ["de"],
        "PasswordManagerEnabled": True,
        "ExtensionSettings": {
            "*": {"installation_mode": "allowed"},
            UBO_ID: {
                "installation_mode": "force_installed",
                "install_url": UBO_URL,
                "private_browsing": True,
            },
            # Deutsches Sprachpaket genau passend zur gebauten Version
            "langpack-de@firefox.mozilla.org": {
                "installation_mode": "normal_installed",
                "install_url": langpack_url,
            },
        },
        "3rdparty": {"Extensions": {UBO_ID: _ubo_settings(level)}},
        # --- abhängig von der Stufe ---
        "EnableTrackingProtection": {
            "Value": level >= 1,
            "Cryptomining": level >= 1,
            "Fingerprinting": level >= 1,
            "EmailTracking": level >= 1,
            "Locked": False,
        },
        "Cookies": {
            "Behavior": "reject-foreign" if level >= 4 else "reject-tracker-and-partition-foreign",
            "Locked": False,
        },
        "Permissions": {
            "Location": {"BlockNewRequests": level >= 1, "Locked": False},
            "Notifications": {"BlockNewRequests": level >= 1, "Locked": False},
            "Camera": {"BlockNewRequests": level >= 3, "Locked": False},
            "Microphone": {"BlockNewRequests": level >= 3, "Locked": False},
            "Autoplay": {"Default": "block-audio-video" if level >= 3 else "block-audio", "Locked": False},
        },
        "HttpsOnlyMode": "force_enabled" if level >= 3 else ("enabled" if level >= 2 else "allowed"),
        "DisableFormHistory": level >= 3,
        "DisableFirefoxAccounts": level >= 3,
    }

    if level >= 2:
        p["DNSOverHTTPS"] = {
            "Enabled": True,
            "ProviderURL": "https://dns.quad9.net/dns-query",
            "Fallback": level < 3,  # ab Extrem kein Rückfall auf unverschlüsseltes DNS
            "Locked": False,
        }

    if level >= 4:
        p["SanitizeOnShutdown"] = {
            "Cache": True,
            "Cookies": True,
            "Sessions": True,
            "OfflineApps": True,
            "History": False,
            "Locked": False,
        }

    return {"policies": p}
