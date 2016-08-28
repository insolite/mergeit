"""
Solution of separating Colored/non-colored log by formatters/handlers:
https://github.com/hynek/structlog/pull/73#issuecomment-222931463
"""


import logging


class ProcessorFormatter(logging.Formatter):
    """Custom stdlib logging formatter for structlog ``event_dict`` messages.

    Apply a structlog processor to the ``event_dict`` passed as
    ``LogRecord.msg`` to convert it to loggable format (a string).

    """

    def __init__(self, processor, fmt=None, datefmt=None, style='%'):
        """Keep reference to the ``processor``."""
        super().__init__(fmt=fmt, datefmt=datefmt, style=style)
        self.processor = processor

    def format(self, record):
        """Extract structlog's ``event_dict`` from ``record.msg``.

        Process a copy of ``record.msg`` since the some processors modify the
        ``event_dict`` and the ``LogRecord`` will be used for multiple
        formatting runs.

        """
        if isinstance(record.msg, dict):
            msg_repr = self.processor(
                record._logger, record._name, record.msg.copy())
            return msg_repr
        return record.getMessage()


def event_dict_to_message(logger, name, event_dict):
    """Pass the event_dict to stdlib handler for special formatting."""
    return ((event_dict,), {'extra': {'_logger': logger, '_name': name}})
