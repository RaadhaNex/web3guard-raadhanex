"use client";

import { AuthForm } from "@/components/auth/AuthForm";

export default function LoginClient() {
  return (
    <main className="min-h-screen bg-ink px-4 py-10 text-white sm:px-6 lg:px-8">
      <section className="mx-auto max-w-5xl">
        <AuthForm mode="login" />
      </section>
    </main>
  );
}
