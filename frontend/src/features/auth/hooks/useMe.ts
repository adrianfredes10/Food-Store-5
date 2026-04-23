import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";

import { getMe } from "@/shared/api/endpoints/auth";
import { useAuthStore } from "@/shared/store/auth-store";

export function useMe() {
  const token = useAuthStore((s) => s.access_token);
  const setUser = useAuthStore((s) => s.setUser);
  const q = useQuery({
    queryKey: ["me"] as const,
    queryFn: getMe,
    enabled: Boolean(token),
    staleTime: 5 * 60 * 1000,
  });

  useEffect(() => {
    if (!q.data) return;
    setUser({
      id: q.data.id,
      nombre: q.data.nombre,
      apellido: q.data.apellido,
      email: q.data.email,
      roles: q.data.roles,
      created_at: q.data.created_at,
    });
  }, [q.data, setUser]);

  return q;
}
