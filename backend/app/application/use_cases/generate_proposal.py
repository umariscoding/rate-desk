from app.application.activity import ActivityFeed, reporting
from app.application.ports import CaseRepository, DocumentStore, ProposalComposer, ProposalHandoff
from app.domain.case import Case, ProposalDocument


class GenerateProposal:
    """With rates confirmed, fill the proposal template and store it, then have the cover email written."""

    def __init__(
        self,
        composer: ProposalComposer,
        handoff: ProposalHandoff,
        documents: DocumentStore,
        cases: CaseRepository,
        feed: ActivityFeed,
    ) -> None:
        self._composer = composer
        self._handoff = handoff
        self._documents = documents
        self._cases = cases
        self._feed = feed

    async def execute(self, case_id: str) -> Case:
        case = self._cases.get(case_id)
        request, reply, quote = case.begin_proposal()
        async with reporting(self._feed, case_id, "Building the proposal") as publish:
            composed = await self._composer.compose(request, quote, reply, publish)
            case.add_cost(composed.cost)
            document = composed.value
            document_id = self._documents.save(case_id, document.file_name, document.content)
            case.record_proposal(ProposalDocument(document.file_name, document_id, document.verification_problems))
        self._cases.save(case)  # The proposal is safe even if the handoff below fails.
        async with reporting(self._feed, case_id, "Writing the cover email") as publish:
            handed_off = await self._handoff.hand_off(request, quote, reply, publish)
            case.add_cost(handed_off.cost)
            case.record_handoff(handed_off.value)
        self._cases.save(case)
        return case
