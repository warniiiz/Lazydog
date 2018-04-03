

from states import LocalState
from events import CerberusEvent
from revised_watchdog.events import FileSystemEventHandler


class DatedlocaleventQueue(FileSystemEventHandler):
    """Accumulate all the captured events, and date them."""

    def __init__(self, local_states:LocalState):
        self.events_list = []
        self.events_list.clear()
        self.local_states = local_states
        super(DatedlocaleventQueue, self).__init__()

    def on_any_event(self, event):
        """Catch-all event handler.

        :param event:
            The event object representing the file system event.
        :type event:
            :class:`FileSystemEvent`
        """
        super(DatedlocaleventQueue, self).on_any_event(event)
        self.events_list.append(CerberusEvent(event, self.local_states))

    def next(self):
        return self.events_list.pop(0) if not self.is_empty() else None
            
    def size(self):
        return len(self.events_list)

    def is_empty(self):
        return self.size() == 0
    

