import { useQuery } from "@tanstack/react-query";

import { getAdminDashboard } from "@/shared/api/endpoints/admin";

export function useAdminDashboard() {
  return useQuery({
    queryKey: ["admin", "dashboard"] as const,
    queryFn: getAdminDashboard,
  });
}
