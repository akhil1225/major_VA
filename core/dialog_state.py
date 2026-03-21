from typing import Callable, Optional, List


class PendingAction:
    def __init__(
        self,
        description: str,
        do: Callable[[], str],
        undo: Optional[Callable[[], str]] = None,
        options: Optional[List[str]] = None
    ):
        self.description = description
        self.do = do
        self.undo = undo
        self.options = options or []


class DialogState:
    def __init__(self):
        self.pending: Optional[PendingAction] = None
        self.last_action: Optional[PendingAction] = None

    # ---------------- CONFIRM ----------------
    def set_pending(self, action: PendingAction):
        self.pending = action

    def confirm(self) -> str:
        if not self.pending:
            return "There is nothing to confirm."

        result = self.pending.do()
        self.last_action = self.pending
        self.pending = None
        return result

    def cancel(self) -> str:
        self.pending = None
        return "Cancelled."

    # ---------------- UNDO ----------------
    def undo(self) -> str:
        if not self.last_action or not self.last_action.undo:
            return "There is nothing to undo."

        result = self.last_action.undo()
        self.last_action = None
        return result

    # ---------------- SELECTION ----------------
    def select(self, index: int) -> str:
        if not self.pending or not self.pending.options:
            return "There is nothing to select."

        try:
            chosen = self.pending.options[index]
        except IndexError:
            return "That option does not exist."

        self.pending.do = lambda: chosen
        return self.confirm()
