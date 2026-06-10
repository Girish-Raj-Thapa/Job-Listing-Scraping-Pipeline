class RetryableScrapeError(Exception):
    """Raised for transient scrape failures that should be retried."""


class NonRetryableScrapeError(Exception):
    """Raised for terminal scrape failures that should not be retried."""
