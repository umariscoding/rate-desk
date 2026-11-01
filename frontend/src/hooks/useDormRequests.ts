import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import * as api from "../api/dorm";

const LIST_KEY = ["dorm-requests"] as const;
const requestKey = (caseId: string) => ["dorm-request", caseId] as const;

export const useDormRequestList = () => useQuery({ queryKey: LIST_KEY, queryFn: api.listDormRequests });

export const useDormRequest = (caseId: string | null) =>
  useQuery({
    queryKey: requestKey(caseId ?? "none"),
    queryFn: () => api.getDormRequest(caseId as string),
    enabled: caseId !== null,
  });

export function useReplyToRequest() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ caseId, replyText }: { caseId: string; replyText: string }) => api.replyToRequest(caseId, replyText),
    onSuccess: (updated) => {
      queryClient.setQueryData(requestKey(updated.id), updated);
      void queryClient.invalidateQueries({ queryKey: LIST_KEY });
    },
  });
}
