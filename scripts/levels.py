"""Private Fox – protection levels 0–4.

prepare_tree.py generates distribution/policies-level0.json … level4.json from this file.
Which one applies is decided on startup by the file "privatefox-level" in the user app folder
(written by the shield button in the toolbar).

Policy docs: https://mozilla.github.io/policy-templates/
uBlock Origin admin settings: https://github.com/gorhill/uBlock/wiki/Deploying-uBlock-Origin
"""

UBO_ID = "uBlock0@raymondhill.net"
UBO_URL = "https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"

NAMES = ["Off", "Balanced", "Strong", "Extreme", "Paranoid"]

# uBlock Origin filter lists (internal uBO list IDs)
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

# Extra static uBO filters. Can be allowed again per site in the uBO popup.
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


UPDATE_BASE = "https://no-pixel21.github.io/PrivateFox/update"


def build_policies(level: int, version: str, platform: str = "") -> dict:
    """Complete policies.json for one level. platform: win64 / mac / linux64 (update feed)."""
    p = {
        # --- always: no data collection, no ads, no Mozilla promos ---
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
        # New tab: just the logo and the search box. No shortcuts (bookmarks are on the
        # bookmarks bar instead), no stories, no highlights, no sponsored anything.
        "FirefoxHome": {
            "Search": True,
            "TopSites": False,
            "SponsoredTopSites": False,
            "Highlights": False,
            "Pocket": False,
            "SponsoredPocket": False,
            "Snippets": False,
            "Locked": False,
        },
        # No Firefox account / sync button and no sign-in prompts at any level.
        "DisableFirefoxAccounts": True,
        "FirefoxSuggest": {
            "WebSuggestions": False,
            "SponsoredSuggestions": False,
            "ImproveSuggest": False,
            "Locked": False,
        },
        "Homepage": {"URL": "https://duckduckgo.com/", "Locked": False},
        "ExtensionSettings": {
            "*": {"installation_mode": "allowed"},
            UBO_ID: {
                "installation_mode": "force_installed",
                "install_url": UBO_URL,
                "private_browsing": True,
            },
        },
        "3rdparty": {"Extensions": {UBO_ID: _ubo_settings(level)}},
        # --- depends on the level ---
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
    }

    # Automatic updates from our own feed (never Mozilla's), at every level.
    if platform:
        p["AppAutoUpdate"] = True
        p["AppUpdateURL"] = f"{UPDATE_BASE}/{platform}/update.xml"

    if level >= 2:
        p["DNSOverHTTPS"] = {
            "Enabled": True,
            "ProviderURL": "https://dns.quad9.net/dns-query",
            "Fallback": level < 3,  # from Extreme on: no fallback to unencrypted DNS
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
