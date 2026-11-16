"""Explicit Mozilla trust bundle for portable Python runtimes without system CAs."""
import ssl
import certifi


def verified_context():
    return ssl.create_default_context(cafile=certifi.where())
