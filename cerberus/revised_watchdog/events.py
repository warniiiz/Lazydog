from watchdog.events import (
    FileModifiedEvent, 
    DirModifiedEvent, 
    FileSystemEvent,
    FileSystemEventHandler, 
    EVENT_TYPE_MOVED, 
    EVENT_TYPE_CREATED, 
    EVENT_TYPE_DELETED
    )

#############################################
### watchdog.events                       ###
#############################################

EVENT_TYPE_C_MODIFIED = 'modified' # content-only modification
EVENT_TYPE_M_MODIFIED = 'metadata' # metadata-only modification

class MetaFileModifiedEvent(FileModifiedEvent):
    """File system event representing metadata file modification on the file system."""

    event_type = EVENT_TYPE_M_MODIFIED

    def __init__(self, src_path):
        super(MetaFileModifiedEvent, self).__init__(src_path)

class TrueFileModifiedEvent(FileModifiedEvent):
    """File system event representing true file modification on the file system."""

    event_type = EVENT_TYPE_C_MODIFIED

    def __init__(self, src_path):
        super(TrueFileModifiedEvent, self).__init__(src_path)

class MetaDirModifiedEvent(DirModifiedEvent):
    """File system event representing metadata directory modification on the file system."""

    event_type = EVENT_TYPE_M_MODIFIED

    def __init__(self, src_path):
        super(MetaDirModifiedEvent, self).__init__(src_path)

class TrueDirModifiedEvent(DirModifiedEvent):
    """File system event representing true directory modification on the file system."""

    event_type = EVENT_TYPE_C_MODIFIED

    def __init__(self, src_path):
        super(TrueDirModifiedEvent, self).__init__(src_path)

class FileSystemEventHandler(FileSystemEventHandler):
    """
    Base file system event handler that you can override methods from.
    With modified dispatch method, added on_xxxx_modified methods,
    thus covering specific needs of cerberus.
    """

    def dispatch(self, event):
        """Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        self.on_any_event(event)
        _method_map = {
            EVENT_TYPE_M_MODIFIED: self.on_meta_modified,
            EVENT_TYPE_C_MODIFIED: self.on_data_modified,
            EVENT_TYPE_MOVED: self.on_moved,
            EVENT_TYPE_CREATED: self.on_created,
            EVENT_TYPE_DELETED: self.on_deleted,
        }
        event_type = event.event_type
        _method_map[event_type](event)


    def on_data_modified(self, event):
        """Called when a file or directory true content is modified.

        :param event:
            Event representing file/directory modification.
        :type event:
            :class:`DirModifiedEvent` or :class:`FileModifiedEvent`
        """
        self.on_modified(event)
        
    def on_meta_modified(self, event):
        """Called when a file or directory metadata is modified.

        :param event:
            Event representing file/directory modification.
        :type event:
            :class:`DirModifiedEvent` or :class:`FileModifiedEvent`
        """
        self.on_modified(event)

class FileSystemEvent(FileSystemEvent):
    pass
