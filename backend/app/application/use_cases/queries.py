from app.application.ports import CaseRepository, DocumentStore
from app.domain.case import Case
from app.domain.errors import CaseNotFound, ProposalNotReady


class GetCase:
    def __init__(self, cases: CaseRepository) -> None:
        self._cases = cases

    def execute(self, case_id: str) -> Case:
        return self._cases.get(case_id)


class ListCases:
    def __init__(self, cases: CaseRepository) -> None:
        self._cases = cases

    def execute(self) -> list[Case]:
        return self._cases.list_recent()


class GetProposalFile:
    def __init__(self, cases: CaseRepository, documents: DocumentStore) -> None:
        self._cases = cases
        self._documents = documents

    def execute(self, case_id: str) -> tuple[str, bytes]:
        proposal = self._cases.get(case_id).proposal
        if proposal is None:
            raise ProposalNotReady()
        return proposal.file_name, self._documents.load(proposal.document_id)


class ListDormRequests:
    """The DORM's inbox: only cases whose rate request has actually been sent to them."""

    def __init__(self, cases: CaseRepository) -> None:
        self._cases = cases

    def execute(self) -> list[Case]:
        return [case for case in self._cases.list_recent() if case.has_reached_dorm]


class GetDormRequest:
    def __init__(self, cases: CaseRepository) -> None:
        self._cases = cases

    def execute(self, case_id: str) -> Case:
        case = self._cases.get(case_id)
        if not case.has_reached_dorm:
            raise CaseNotFound(case_id)  # To the DORM, a request that has not been sent does not exist.
        return case
