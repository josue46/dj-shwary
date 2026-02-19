SECRET_KEY = "fake-key"
INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.sites",
    "django.contrib.auth",
    "dj_shwary",
]
SITE_ID = 1
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}
SHWARY = {
    "MERCHANT_ID": "test_id",
    "MERCHANT_KEY": "test_key",
}
ROOT_URLCONF = "tests.urls"