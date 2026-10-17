from prometheus_client import Counter, Histogram

REQUESTS_TOTAL = Counter(
    "photobooking_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
REQUEST_DURATION = Histogram(
    "photobooking_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)
RATE_LIMITED_TOTAL = Counter(
    "photobooking_rate_limited_total",
    "Requests rejected by the rate limiter",
    ["path"],
)
BOOKINGS_TOTAL = Counter(
    "photobooking_bookings_total",
    "Booking lifecycle operations",
    ["operation", "provider", "status"],
)
