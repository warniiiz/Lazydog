from watchdog.observers.inotify import (
    InotifyEmitter, 
    InotifyObserver
    )

from watchdog.events import (
    FileMovedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    DirCreatedEvent,
    FileDeletedEvent,
    DirDeletedEvent,
    )

from ..events import (
    TrueFileModifiedEvent,
    MetaFileModifiedEvent,
    TrueDirModifiedEvent,
    MetaDirModifiedEvent
    )

#############################################
### Revisiting watchdog.observers.inotify ###
#############################################

class InotifyEmitter(InotifyEmitter):
    """
    inotify(7)-based event emitter. With modified queue_events method, 
    covering specific needs of cerberus

    :param event_queue:
        The event queue to fill with events.
    :param watch:
        A watch object representing the directory to monitor.
    :type watch:
        :class:`watchdog.observers.api.ObservedWatch`
    :param timeout:
        Read events blocking timeout (in seconds).
    :type timeout:
        ``float``
    """

    def queue_events(self, timeout, full_events=False):
        #If "full_events" is true, then the method will report unmatched move events as seperate events
        #This behavior is by default only called by a InotifyFullEmitter
        with self._lock:
            event = self._inotify.read_event()
            if event is None:
                return
            if isinstance(event, tuple):
                move_from, move_to = event
                src_path = self._decode_path(move_from.src_path)
                dest_path = self._decode_path(move_to.src_path)
                cls = DirMovedEvent if move_from.is_directory else FileMovedEvent
                self.queue_event(cls(src_path, dest_path))
                #===============================================================
                # self.queue_event(MetaDirModifiedEvent(os.path.dirname(src_path)))
                # self.queue_event(MetaDirModifiedEvent(os.path.dirname(dest_path)))
                #===============================================================
                #===============================================================
                # if move_from.is_directory and self.watch.is_recursive:
                #     for sub_event in generate_sub_moved_events(src_path, dest_path):
                #         self.queue_event(sub_event)
                #===============================================================
                return

            src_path = self._decode_path(event.src_path)
            if event.is_moved_to:
                if (full_events):
                    cls = DirMovedEvent if event.is_directory else FileMovedEvent
                    self.queue_event(cls(None, src_path))
                else:
                    cls = DirCreatedEvent if event.is_directory else FileCreatedEvent
                    self.queue_event(cls(src_path))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================
                #===============================================================
                # if event.is_directory and self.watch.is_recursive:
                #     for sub_event in generate_sub_created_events(src_path):
                #         self.queue_event(sub_event)
                #===============================================================
            elif event.is_attrib:
                cls = MetaDirModifiedEvent if event.is_directory else MetaFileModifiedEvent
                self.queue_event(cls(src_path))
            elif event.is_modify:
                cls = TrueDirModifiedEvent if event.is_directory else TrueFileModifiedEvent
                self.queue_event(cls(src_path))
            elif event.is_delete or (event.is_moved_from and not full_events):
                cls = DirDeletedEvent if event.is_directory else FileDeletedEvent
                self.queue_event(cls(src_path))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================
            elif event.is_moved_from and full_events:
                cls = DirMovedEvent if event.is_directory else FileMovedEvent
                self.queue_event(cls(src_path, None))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================
            elif event.is_create:
                cls = DirCreatedEvent if event.is_directory else FileCreatedEvent
                self.queue_event(cls(src_path))
                #===============================================================
                # self.queue_event(DirModifiedEvent(os.path.dirname(src_path)))
                #===============================================================


class InotifyObserver(InotifyObserver):
    pass
