import enum


class SuggestionStatus(str, enum.Enum):
    PENDING = 'pending'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'


class SuggestionType(str, enum.Enum):
    PRICING = 'pricing'
    REORDER = 'reorder'
