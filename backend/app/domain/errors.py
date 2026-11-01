"""Typed business errors. The interface layer decides how each one is shown."""


class DomainError(Exception):
    """Base class for every business-rule violation."""


class CaseNotFound(DomainError):
    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case {case_id} does not exist")
        self.case_id = case_id


class InvalidCaseTransition(DomainError):
    def __init__(self, current: str, attempted: str) -> None:
        super().__init__(f"A case in status '{current}' cannot move to '{attempted}'")
        self.current = current
        self.attempted = attempted


class NothingToSend(DomainError):
    def __init__(self) -> None:
        super().__init__("There is no drafted email waiting for approval")


class CaseAlreadyExists(DomainError):
    def __init__(self, case_id: str) -> None:
        super().__init__(f"Case {case_id} already exists")
        self.case_id = case_id


class ProposalNotReady(DomainError):
    def __init__(self) -> None:
        super().__init__("This case has no proposal yet")


class InvalidCredentials(DomainError):
    def __init__(self) -> None:
        super().__init__("The username or password is not right")


class NotAuthenticated(DomainError):
    def __init__(self) -> None:
        super().__init__("Sign in to continue")


class NotPermitted(DomainError):
    def __init__(self) -> None:
        super().__init__("Your role cannot do this")
