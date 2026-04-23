import { apiClient } from "@/shared/api/client";

export type MeDTO = {
  id: number;
  nombre: string;
  apellido: string | null;
  email: string;
  roles: string[];
  created_at: string;
};

export type LoginBody = {
  email: string;
  password: string;
};

export type LoginResponseDTO = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
};

export type RegisterBody = {
  email: string;
  password: string;
  nombre: string;
  apellido?: string | null;
};

export async function loginRequest(body: LoginBody): Promise<LoginResponseDTO> {
  const { data } = await apiClient.post<LoginResponseDTO>("/auth/login", body);
  return data;
}

export async function registerRequest(body: RegisterBody): Promise<{ id: number; email: string }> {
  const { data } = await apiClient.post<{ id: number; email: string }>("/auth/register", body);
  return data;
}

export async function getMe(): Promise<MeDTO> {
  const { data } = await apiClient.get<MeDTO>("/auth/me");
  return data;
}

export async function refreshRequest(body: { refresh_token: string }): Promise<LoginResponseDTO> {
  const { data } = await apiClient.post<LoginResponseDTO>("/auth/refresh", body);
  return data;
}
