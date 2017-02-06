TEXT_FIELDS = {
    "sender.name", "sender.address", "recipients.name", "recipients.address",
    "subject",
}
SUFFIX_CONTAINS = "_contains"

CONTAINS_FIELDS = {field + SUFFIX_CONTAINS for field in TEXT_FIELDS}

ALLOWED_QUERY_FIELDS = {"_id", "read"} | TEXT_FIELDS | CONTAINS_FIELDS
