import { apiClient } from "@/shared/api/client";

const BASE = "/direcciones";

export type DireccionDTO = {
  id: number;
  usuario_id: number;
  alias: string | null;
  calle: string;
  numero: string;
  piso_dpto: string | null;
  ciudad: string;
  codigo_postal: string;
  referencias: string | null;
  es_principal: boolean;
  activo: boolean;
};

export type DireccionCreateBody = {
  alias?: string | null;
  calle: string;
  numero: string;
  piso_dpto?: string | null;
  ciudad: string;
  codigo_postal: string;
  referencias?: string | null;
  es_principal?: boolean;
};

export type DireccionUpdateBody = Partial<{
  alias: string | null;
  calle: string;
  numero: string;
  piso_dpto: string | null;
  ciudad: string;
  codigo_postal: string;
  referencias: string | null;
  es_principal: boolean;
  activo: boolean;
}>;

export async function listDirecciones(): Promise<DireccionDTO[]> {
  const { data } = await apiClient.get<DireccionDTO[]>(BASE);
  return data;
}

export async function createDireccion(body: DireccionCreateBody): Promise<DireccionDTO> {
  const { data } = await apiClient.post<DireccionDTO>(BASE, body);
  return data;
}

export async function updateDireccion(id: number, body: DireccionUpdateBody): Promise<DireccionDTO> {
  const { data } = await apiClient.patch<DireccionDTO>(`${BASE}/${id}`, body);
  return data;
}

export async function marcarDireccionPrincipal(id: number): Promise<DireccionDTO> {
  const { data } = await apiClient.patch<DireccionDTO>(`${BASE}/${id}/principal`);
  return data;
}

export async function deleteDireccion(id: number): Promise<void> {
  await apiClient.delete(`${BASE}/${id}`);
}
