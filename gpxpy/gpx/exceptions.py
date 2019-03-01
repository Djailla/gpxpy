class GPXException(Exception):
    """
    Exception used for invalid GPX files. It is used when the XML file is
    valid but something is wrong with the GPX data.
    """
    pass


class GPXXMLSyntaxException(GPXException):
    """
    Exception used when the XML syntax is invalid.

    The __cause__ can be a minidom or lxml exception (See http://www.python.org/dev/peps/pep-3134/).
    """
    def __init__(self, message, original_exception):
        GPXException.__init__(self, message)
        self.__cause__ = original_exception
