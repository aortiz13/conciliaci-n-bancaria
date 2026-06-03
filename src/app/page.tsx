export default function Home() {
  return (
    <main className="mx-auto flex min-h-screen max-w-2xl flex-col justify-center gap-6 px-6 py-16">
      <div>
        <p className="text-sm font-medium uppercase tracking-wide text-neutral-500">
          MVP · Fase 0
        </p>
        <h1 className="mt-2 text-3xl font-bold">Conciliación Bancaria</h1>
        <p className="mt-4 text-neutral-600 dark:text-neutral-300">
          Plataforma SaaS de recepción conversacional y conciliación de
          facturas para PYMES. El proveedor envía la factura por Telegram o
          email, el sistema la extrae y valida, y el equipo interno la concilia
          contra el extracto bancario.
        </p>
      </div>

      <div className="rounded-lg border border-neutral-200 p-4 text-sm dark:border-neutral-800">
        <p className="font-medium">Estado del scaffold</p>
        <ul className="mt-2 list-inside list-disc text-neutral-600 dark:text-neutral-300">
          <li>Next.js (App Router) + TypeScript + Tailwind</li>
          <li>Clientes Supabase (browser / server / admin)</li>
          <li>Migraciones del schema con RLS por tenant</li>
        </ul>
      </div>
    </main>
  );
}
