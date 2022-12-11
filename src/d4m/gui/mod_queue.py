import queue
from enum import Enum
from threading import Thread

from d4m.gui.context import D4mGlobalContext
from d4m.manage import ModManager


class ModStatus(Enum):
    PENDING = "Pending"
    DOWNLOADING = "Downloading"
    INSTALLING = "Extracting"
    COMPLETE = "Completed"
    ERROR = "Failed"


class PendingMod:
    def __init__(self, origin, id, category):
        self.origin = origin
        self.id = id
        self.category = category
        self.status = ModStatus.PENDING


class D4mInstallWorker(Thread):
    def __init__(self, ready_queue: queue.Queue, mod_manager: ModManager, callback):
        super().__init__()
        self.queue = ready_queue
        self.mod_manager = mod_manager
        self.callback = callback

    def run(self):
        while True:
            mod: PendingMod = self.queue.get(block=True)
            try:
                self.mod_manager.install_mod(mod.id, mod.category, fetch_thumbnail=True, origin=mod.origin)
                self.callback(mod.id, mod.origin, True)
            except Exception as e:
                self.callback(mod.id, mod.origin, False, fail_reason=str(e))


class ModInstallQueue:

    def __init__(self, context: D4mGlobalContext):
        self.context = context
        self.ready_queue = queue.Queue()  # blocking queue for thread safety
        self.user_queue = queue.Queue()  # needs user input (e.g pick variant)
        self.worker = D4mInstallWorker(self.ready_queue, self.context.mod_manager, self.install_complete)
        self.on_complete_callbacks = {}

    def register_callback(self, id, f):
        self.on_complete_callbacks[id] = f

    def deregister_callback(self, id):
        self.on_complete_callbacks.pop(id)

    def install_complete(self, mod_id, origin,
                         success: bool, fail_reason: str = None):  # thread will call this function when it fails/completes/etc
        pass

    def enqueue(self, origin, mod_id, category):
        m = PendingMod(origin, mod_id, category)
        # TODO: check for variants
        self.ready_queue.put(m)
