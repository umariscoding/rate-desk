import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as api from "../api/cases";
import type { CaseDetail } from "../api/types";

const LIST_KEY = ["cases"] as const;
const caseKey = (caseId: string) => ["case", caseId] as const;

export const useCaseList = () => useQuery({ queryKey: LIST_KEY, queryFn: api.listCases });

export const useCase = (caseId: string | null) =>
  useQuery({
    queryKey: caseKey(caseId ?? "none"),
    queryFn: () => api.getCase(caseId as string),
    enabled: caseId !== null,
  });

/** Every action returns the updated case: store it, and refresh the list that shows its status. */
function useCaseAction<Variables>(action: (variables: Variables) => Promise<CaseDetail>) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: action,
    onSuccess: (updated) => {
      queryClient.setQueryData(caseKey(updated.id), updated);
      void queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
  });
}

export const useSubmitClientEmail = () =>
  useCaseAction(({ caseId, emailText }: { caseId: string; emailText: string }) =>
    api.submitClientEmail(caseId, emailText),
  );

export const useSendPendingEmail = () => useCaseAction((caseId: string) => api.sendPendingEmail(caseId));

export const useGenerateProposal = () => useCaseAction((caseId: string) => api.generateProposal(caseId));
