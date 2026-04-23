import { type FormEvent, useState } from "react";
import { ShoppingBag } from "lucide-react";

import { useLogin, useRegister } from "@/features/auth";
import { FormField, LoadingButton } from "@/shared/ui";

export function AuthLoginPage() {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [nombre, setNombre] = useState("");
  const [apellido, setApellido] = useState("");

  const loginMut = useLogin();
  // al registrarse exitosamente vuelvo al login y limpio la contraseña
  const registerMut = useRegister(() => {
    setMode("login");
    setPassword("");
  });

  const busy = loginMut.isPending || registerMut.isPending;

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault();
    if (busy) return;
    // dependiendo del modo llamo login o registro
    if (mode === "login") {
      loginMut.mutate({ email: email.trim(), password });
      return;
    }
    registerMut.mutate({
      email: email.trim(),
      password,
      nombre: nombre.trim(),
      apellido: apellido.trim() || null,
    });
  };

  return (
    <div className="flex min-h-[calc(100vh-100px)] w-full items-center justify-center p-4">
      <div className="w-full max-w-sm fade-in">
        <div className="mb-8 flex flex-col items-center text-center">
          <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-2xl bg-accent shadow-sm">
            <ShoppingBag size={24} className="text-white" />
          </div>
          <h1 className="font-outfit text-2xl font-black tracking-tight text-primary md:text-3xl">
            {mode === "login" ? "Te damos la bienvenida" : "Creá tu cuenta"}
          </h1>
          <p className="mt-2 text-sm font-bold tracking-widest text-muted uppercase">
            {mode === "login" ? "Iniciá sesión para continuar" : "Completá tus datos"}
          </p>
        </div>

        <div className="rounded-2xl border border-border bg-white p-6 sm:p-8 shadow-sm">
          <form className="space-y-4" onSubmit={handleSubmit}>
            {mode === "register" && (
              <div className="grid grid-cols-2 gap-4">
                <FormField label="Nombre">
                  <input
                    required
                    placeholder="Tu nombre"
                    className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary transition-all focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent"
                    value={nombre}
                    onChange={(e) => setNombre(e.target.value)}
                  />
                </FormField>
                <FormField label="Apellido">
                  <input
                    placeholder="Tu apellido"
                    className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary transition-all focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent"
                    value={apellido}
                    onChange={(e) => setApellido(e.target.value)}
                  />
                </FormField>
              </div>
            )}

            <FormField label="Correo electrónico">
              <input
                required
                type="email"
                placeholder="usuario@foodstore.com"
                className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary transition-all focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </FormField>

            <FormField label="Contraseña">
              <input
                required
                type="password"
                minLength={mode === "register" ? 8 : 1}
                placeholder="••••••••"
                className="mt-1 w-full rounded-xl border border-border bg-bg-secondary px-4 py-3 text-sm font-bold text-primary transition-all focus:border-accent focus:bg-white focus:outline-none focus:ring-1 focus:ring-accent"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </FormField>

            <div className="pt-2">
                <LoadingButton
                type="submit"
                isLoading={busy}
                className="w-full rounded-xl bg-primary py-3.5 text-sm font-bold text-white shadow-sm transition-all hover:bg-primary-hover active:scale-95"
                >
                {mode === "login" ? "Iniciar Sesión" : "Crear Cuenta"}
                </LoadingButton>
            </div>
          </form>

          <div className="mt-8 text-center text-sm font-medium text-muted border-t border-border pt-6">
            {mode === "login" ? "¿Primera vez acá? " : "¿Ya tenés una cuenta? "}
            <button
              type="button"
              className="font-bold text-accent transition-colors hover:text-accent-hover hover:underline"
              onClick={() => setMode(mode === "login" ? "register" : "login")}
            >
              {mode === "login" ? "Registrate ahora" : "Iniciá sesión"}
            </button>
          </div>

          {mode === "login" && (
            <div className="mt-6 rounded-xl border border-border bg-bg-secondary p-4 text-center text-xs">
              <p className="mb-2 font-bold uppercase tracking-widest text-muted">
                Credenciales de prueba Demo
              </p>
              <div className="flex flex-col gap-1 text-primary">
                <p>
                  User: <span className="font-mono font-bold">admin@foodstore.com</span>
                </p>
                <p>
                  Pass: <span className="font-mono font-bold">Admin1234!</span>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
